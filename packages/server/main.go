package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

type DataCliente struct {
	ID int32
	X  int32
	Y  int32
	Z  int32
}

// ------------------ WEBSOCKET CORE ------------------

var upgrader = websocket.Upgrader{
	CheckOrigin:       func(r *http.Request) bool { return true },
	ReadBufferSize:    256,
	WriteBufferSize:   256,
	EnableCompression: false,
}

var (
	dataChan = make(chan DataCliente, 2000)
	clients  sync.Map // reemplaza el struct con RWMutex
)

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

// ------------------ MEMORIA (reutilización) ------------------

var bufferPool = sync.Pool{
	New: func() any {
		return bytes.NewBuffer(make([]byte, 0, 16*100))
	},
}

// ------------------ MAIN ------------------

func main() {
	http.HandleFunc("/ws", handleConnection)
	http.HandleFunc("/health", handleHealth)
	http.HandleFunc("/servers", handleServers)

	go broadcastLoop()

	log.Println("Servidor WebSocket corriendo en :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

// ------------------ HANDLERS ------------------

func handleConnection(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		return
	}

	conn.SetReadLimit(1024)
	conn.SetReadDeadline(time.Now().Add(30 * time.Second))
	conn.SetPongHandler(func(string) error {
		conn.SetReadDeadline(time.Now().Add(30 * time.Second))
		return nil
	})

	// Añadir cliente (thread-safe)
	clients.Store(conn, true)

	// Ping cada 10 s
	go func(c *websocket.Conn) {
		ticker := time.NewTicker(10 * time.Second)
		defer ticker.Stop()
		for range ticker.C {
			if err := c.WriteControl(websocket.PingMessage, []byte{}, time.Now().Add(5*time.Second)); err != nil {
				c.Close()
				break
			}
		}
	}(conn)

	for {
		_, msg, err := conn.ReadMessage()
		if err != nil {
			break
		}
		if len(msg) < 16 {
			continue
		}

		start := time.Now()
		data := DataCliente{
			ID: int32(binary.LittleEndian.Uint32(msg[0:4])),
			X:  int32(binary.LittleEndian.Uint32(msg[4:8])),
			Y:  int32(binary.LittleEndian.Uint32(msg[8:12])),
			Z:  int32(binary.LittleEndian.Uint32(msg[12:16])),
		}
		select {
		case dataChan <- data:
			recordMetrics(1, 0, time.Since(start))
		default:
		}
	}

	// Eliminar cliente
	clients.Delete(conn)
	conn.Close()
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

// ------------------ BROADCAST LOOP ------------------

func broadcastLoop() {
	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop()

	accum := make([]DataCliente, 0, 5000)

	for {
		select {
		case d := <-dataChan:
			accum = append(accum, d)
			// Si se alcanza el tamaño máximo, se envía inmediatamente
			if len(accum) >= 5000 {
				processAndBroadcast(accum)
				accum = accum[:0]
			}

		case <-ticker.C:
			if len(accum) > 0 {
				processAndBroadcast(accum)
				accum = accum[:0]
			}
		}
	}
}

// Helper que serializa y envía a todos los clientes activos
func processAndBroadcast(accum []DataCliente) {
	start := time.Now()
	message := serializeSlice(accum)

	sent := 0
	clients.Range(func(key, value any) bool {
		c := key.(*websocket.Conn)
		if err := c.WriteMessage(websocket.BinaryMessage, message); err != nil {
			c.Close()
			clients.Delete(c)
		} else {
			sent++
		}
		return true
	})

	recordMetrics(0, sent, time.Since(start))
}

// ------------------ SERIALIZACIÓN ------------------

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
