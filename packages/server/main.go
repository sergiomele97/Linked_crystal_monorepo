package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/gorilla/websocket"
	"github.com/joho/godotenv"
)

// ------------------ NUEVO MODELO ------------------
type Packet struct {
	PlayerID    uint32
	PlayerX     int32
	PlayerY     int32
	MapNumber   int32
	MapBank     int32
	IsOverworld uint32
}

// ------------------ CONFIG ------------------

const (
	MaxClients       = 1024
	BroadcastMs      = 100
	SendBufPerClient = 32
	ReadLimit        = 1024
	IdleReadDeadline = 30 * time.Second
)

// ------------------ WEBSOCKET CORE ------------------

var upgrader = websocket.Upgrader{
	CheckOrigin:       func(r *http.Request) bool { return true },
	ReadBufferSize:    256,
	WriteBufferSize:   256,
	EnableCompression: false,
}

// ------------------ IDs y slots ------------------

var freeIDs = make(chan int, MaxClients)
var latestPackets []atomic.Value
var clients sync.Map

// ------------------ SERVERS LIST ------------------

var (
	serversMu sync.RWMutex
	servers   []string
)

// ------------------ MÉTRICAS ------------------

type metricSample struct {
	timestamp time.Time
	recvCount int
	sendCount int
	latSum    time.Duration
	latCount  int
}

var (
	metricsMu sync.Mutex
	metrics   []metricSample
	windowDur = 60 * time.Second
)

func recordMetrics(recv, send int, lat time.Duration) {
	now := time.Now()
	metricsMu.Lock()
	defer metricsMu.Unlock()

	metrics = append(metrics, metricSample{
		timestamp: now,
		recvCount: recv,
		sendCount: send,
		latSum:    lat,
		latCount:  btoi(lat > 0),
	})

	cutoff := now.Add(-windowDur)
	i := 0
	for ; i < len(metrics); i++ {
		if metrics[i].timestamp.After(cutoff) {
			break
		}
	}
	if i > 0 {
		metrics = metrics[i:]
	}
}

func getAverages() (recvRate, sendRate, latencyMs float64) {
	metricsMu.Lock()
	defer metricsMu.Unlock()

	var recvTotal, sendTotal int
	var latSum time.Duration
	var latCount int
	cutoff := time.Now().Add(-windowDur)

	for _, m := range metrics {
		if m.timestamp.After(cutoff) {
			recvTotal += m.recvCount
			sendTotal += m.sendCount
			latSum += m.latSum
			latCount += m.latCount
		}
	}

	recvRate = float64(recvTotal) / windowDur.Seconds()
	sendRate = float64(sendTotal) / windowDur.Seconds()
	if latCount > 0 {
		latencyMs = float64(latSum.Milliseconds()) / float64(latCount)
	}
	return
}

func btoi(b bool) int {
	if b {
		return 1
	}
	return 0
}

// ------------------ MEMORIA ------------------

var bufferPool = sync.Pool{
	New: func() any {
		return bytes.NewBuffer(make([]byte, 0, 24*100))
	},
}

// ------------------ CLIENT ------------------

type Client struct {
	conn      *websocket.Conn
	send      chan []byte
	closeOnce sync.Once
	closed    chan struct{}
	id        int
	addr      string
}

func newClient(conn *websocket.Conn, sendBuf int, id int) *Client {
	return &Client{
		conn:   conn,
		send:   make(chan []byte, sendBuf),
		closed: make(chan struct{}),
		id:     id,
		addr:   conn.RemoteAddr().String(),
	}
}

func (c *Client) close() {
	c.closeOnce.Do(func() {
		close(c.closed)
		close(c.send)
		clients.Delete(c)
		if c.id >= 0 {
			latestPackets[c.id].Store((*Packet)(nil))
			select {
			case freeIDs <- c.id:
			default:
			}
			log.Printf("Cliente desconectado: id=%d addr=%s", c.id, c.addr)
			c.id = -1
		}
		_ = c.conn.Close()
	})
}

func (c *Client) writerLoop(writeTimeout time.Duration) {
	for msg := range c.send {
		_ = c.conn.SetWriteDeadline(time.Now().Add(writeTimeout))
		if err := c.conn.WriteMessage(websocket.BinaryMessage, msg); err != nil {
			c.close()
			return
		}
	}
	c.close()
}

func (c *Client) pingLoop(interval, timeout time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()
	for {
		select {
		case <-ticker.C:
			_ = c.conn.SetWriteDeadline(time.Now().Add(timeout))
			if err := c.conn.WriteControl(websocket.PingMessage, []byte{}, time.Now().Add(timeout)); err != nil {
				c.close()
				return
			}
		case <-c.closed:
			return
		}
	}
}

// ------------------ MAIN ------------------

func init() {
	// Cargar .env si existe
	if err := godotenv.Load(); err != nil {
		log.Println("⚠️ No se encontró .env, usando variables de entorno del sistema")
	}

	envServers := os.Getenv("SERVERS")
	if envServers == "" {
		log.Println("Variable de entorno SERVERS vacia, usando default value")
		servers = []string{"ws://localhost:8080/ws"}
	} else {
		list := strings.Split(envServers, ",")
		servers = make([]string, 0, len(list))
		for _, s := range list {
			s = strings.TrimSpace(s)
			if s != "" {
				servers = append(servers, s)
			}
		}
	}

	latestPackets = make([]atomic.Value, MaxClients)
	for i := 0; i < MaxClients; i++ {
		freeIDs <- i
		latestPackets[i].Store((*Packet)(nil))
	}
}

func main() {
	staticToken := os.Getenv("STATIC_TOKEN")
	if staticToken == "" {
		staticToken = "demo_token"
		log.Println("⚠️ STATIC_TOKEN no definido, usando default")
	}

	http.HandleFunc("/ws", func(w http.ResponseWriter, r *http.Request) {
		token := r.URL.Query().Get("token")
		if token != staticToken {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		handleConnection(w, r)
	})

	http.HandleFunc("/health", handleHealth)
	http.HandleFunc("/servers", handleServers)

	go broadcastLoop()

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
		log.Println("⚠️ STATIC_TOKEN no definido, usando default")
	}
	log.Println("Servidor WebSocket corriendo en :" + port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}

// ------------------ HANDLERS ------------------

func handleConnection(w http.ResponseWriter, r *http.Request) {
	var id int
	select {
	case id = <-freeIDs:
	default:
		http.Error(w, "server full", http.StatusServiceUnavailable)
		return
	}

	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		select {
		case freeIDs <- id:
		default:
		}
		return
	}

	conn.SetReadLimit(ReadLimit)
	conn.SetReadDeadline(time.Now().Add(IdleReadDeadline))
	conn.SetPongHandler(func(string) error {
		_ = conn.SetReadDeadline(time.Now().Add(IdleReadDeadline))
		return nil
	})

	client := newClient(conn, SendBufPerClient, id)
	clients.Store(client, id)
	log.Printf("Cliente conectado: id=%d addr=%s", client.id, client.addr)

	go client.writerLoop(5 * time.Second)
	go client.pingLoop(10*time.Second, 5*time.Second)

	for {
		_, msg, err := conn.ReadMessage()
		if err != nil {
			break
		}
		if len(msg) < 24 {
			continue
		}

		start := time.Now()
		var p Packet
		p.PlayerID = uint32(client.id)
		p.PlayerX = int32(binary.LittleEndian.Uint32(msg[4:8]))
		p.PlayerY = int32(binary.LittleEndian.Uint32(msg[8:12]))
		p.MapNumber = int32(binary.LittleEndian.Uint32(msg[12:16]))
		p.MapBank = int32(binary.LittleEndian.Uint32(msg[16:20]))
		p.IsOverworld = binary.LittleEndian.Uint32(msg[20:24])

		latestPackets[client.id].Store(&p)
		recordMetrics(1, 0, time.Since(start))
	}

	client.close()
}

// ------------------ HEALTH ------------------

func handleHealth(w http.ResponseWriter, _ *http.Request) {
	count := 0
	clients.Range(func(key, value any) bool {
		count++
		return true
	})

	recvRate, sendRate, latencyMs := getAverages()
	resp := map[string]any{
		"status":     "ok",
		"clients":    count,
		"recv_rate":  recvRate,
		"send_rate":  sendRate,
		"latency_ms": latencyMs,
		"timestamp":  time.Now().UTC(),
	}
	json.NewEncoder(w).Encode(resp)
}

// ------------------ SERVERS ------------------

func handleServers(w http.ResponseWriter, _ *http.Request) {
	serversMu.RLock()
	defer serversMu.RUnlock()
	json.NewEncoder(w).Encode(servers)
}

// ------------------ BROADCAST ------------------

func broadcastLoop() {
	ticker := time.NewTicker(time.Millisecond * time.Duration(BroadcastMs))
	defer ticker.Stop()

	for {
		<-ticker.C
		accum := make([]Packet, 0, 256)
		for id := 0; id < MaxClients; id++ {
			v := latestPackets[id].Load()
			if v == nil {
				continue
			}
			if p, ok := v.(*Packet); ok && p != nil {
				accum = append(accum, *p)
				latestPackets[id].Store((*Packet)(nil))
			}
		}

		if len(accum) == 0 {
			continue
		}

		processAndBroadcast(accum)
	}
}

func processAndBroadcast(accum []Packet) {
	start := time.Now()
	message := serializePackets(accum)

	sent := 0
	clients.Range(func(key, value any) bool {
		c := key.(*Client)
		select {
		case c.send <- message:
			sent++
		default:
			c.close()
		}
		return true
	})

	recordMetrics(0, sent, time.Since(start))
}

func serializePackets(data []Packet) []byte {
	buf := bufferPool.Get().(*bytes.Buffer)
	buf.Reset()

	var tmp [24]byte
	for _, p := range data {
		binary.LittleEndian.PutUint32(tmp[0:4], p.PlayerID)
		binary.LittleEndian.PutUint32(tmp[4:8], uint32(p.PlayerX))
		binary.LittleEndian.PutUint32(tmp[8:12], uint32(p.PlayerY))
		binary.LittleEndian.PutUint32(tmp[12:16], uint32(p.MapNumber))
		binary.LittleEndian.PutUint32(tmp[16:20], uint32(p.MapBank))
		binary.LittleEndian.PutUint32(tmp[20:24], p.IsOverworld)
		buf.Write(tmp[:])
	}

	b := append([]byte(nil), buf.Bytes()...)
	bufferPool.Put(buf)
	return b
}
