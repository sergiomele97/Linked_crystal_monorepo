package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"sync"
	"sync/atomic"
	"time"

	"github.com/gorilla/websocket"
)

type DataCliente struct {
	ID int32
	X  int32
	Y  int32
	Z  int32
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
var latestData []atomic.Value
var clients sync.Map

// ------------------ SERVERS LIST ------------------

var (
	serversMu sync.RWMutex
	servers   = []string{
		"wss://server1.example.com/ws",
		"wss://server2.example.com/ws",
	}
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
		return bytes.NewBuffer(make([]byte, 0, 16*100))
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
			latestData[c.id].Store((*DataCliente)(nil))
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
	latestData = make([]atomic.Value, MaxClients)
	for i := 0; i < MaxClients; i++ {
		freeIDs <- i
		latestData[i].Store((*DataCliente)(nil))
	}
}

func main() {
	// cargar token del entorno
	staticToken := os.Getenv("STATIC_TOKEN")
	if staticToken == "" {
        // fallback para entorno local
        staticToken = "demo_token"
        log.Println("⚠️ STATIC_TOKEN no definido, usando token de desarrollo")
    }

	http.HandleFunc("/ws", func(w http.ResponseWriter, r *http.Request) {
		// validar token antes de aceptar
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

	log.Println("Servidor WebSocket corriendo en :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
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
		if len(msg) < 12 {
			continue
		}

		start := time.Now()
		var d DataCliente
		if len(msg) >= 16 {
			d.X = int32(binary.LittleEndian.Uint32(msg[4:8]))
			d.Y = int32(binary.LittleEndian.Uint32(msg[8:12]))
			d.Z = int32(binary.LittleEndian.Uint32(msg[12:16]))
		} else {
			d.X = int32(binary.LittleEndian.Uint32(msg[0:4]))
			d.Y = int32(binary.LittleEndian.Uint32(msg[4:8]))
			d.Z = int32(binary.LittleEndian.Uint32(msg[8:12]))
		}

		d.ID = int32(client.id)
		latestData[client.id].Store(&d)
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
		accum := make([]DataCliente, 0, 256)
		for id := 0; id < MaxClients; id++ {
			v := latestData[id].Load()
			if v == nil {
				continue
			}
			if p, ok := v.(*DataCliente); ok && p != nil {
				accum = append(accum, *p)
				latestData[id].Store((*DataCliente)(nil))
			}
		}

		if len(accum) == 0 {
			continue
		}

		processAndBroadcast(accum)
	}
}

func processAndBroadcast(accum []DataCliente) {
	start := time.Now()
	message := serializeSlice(accum)

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

func serializeSlice(data []DataCliente) []byte {
	buf := bufferPool.Get().(*bytes.Buffer)
	buf.Reset()

	var tmp [16]byte
	for _, d := range data {
		binary.LittleEndian.PutUint32(tmp[0:4], uint32(d.ID))
		binary.LittleEndian.PutUint32(tmp[4:8], uint32(d.X))
		binary.LittleEndian.PutUint32(tmp[8:12], uint32(d.Y))
		binary.LittleEndian.PutUint32(tmp[12:16], uint32(d.Z))
		buf.Write(tmp[:])
	}

	b := append([]byte(nil), buf.Bytes()...)
	bufferPool.Put(buf)
	return b
}
