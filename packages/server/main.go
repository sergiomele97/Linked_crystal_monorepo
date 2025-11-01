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
	clients  sync.Map // almacenar *Client como clave
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

	// podar antiguas muestras > windowDur
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

// ------------------ CLIENT TYPE (writer loop y cierre seguro) ------------------

type Client struct {
	conn      *websocket.Conn
	send      chan []byte
	closeOnce sync.Once
	closed    chan struct{}
}

func newClient(conn *websocket.Conn, sendBuf int) *Client {
	return &Client{
		conn:   conn,
		send:   make(chan []byte, sendBuf),
		closed: make(chan struct{}),
	}
}

func (c *Client) close() {
	c.closeOnce.Do(func() {
		// cerrar recursos de forma segura
		close(c.closed)
		// cerrar canal send evita writer goroutine
		close(c.send)
		// eliminar de clients map
		clients.Delete(c)
		// cerrar conexión TCP
		_ = c.conn.Close()
	})
}

// writer loop: consume mensajes desde c.send y los escribe en la conexión
func (c *Client) writerLoop(writeTimeout time.Duration) {
	for msg := range c.send {
		// cada escritura con deadline para no bloquear indefinidamente
		_ = c.conn.SetWriteDeadline(time.Now().Add(writeTimeout))
		if err := c.conn.WriteMessage(websocket.BinaryMessage, msg); err != nil {
			// fallo en escritura -> limpiar y salir
			c.close()
			return
		}
	}
	// canal cerrado -> limpiar
	c.close()
}

// ping loop: intenta pings periódicos; si falla, cierra cliente
func (c *Client) pingLoop(interval, timeout time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()
	for {
		select {
		case <-ticker.C:
			// usar WriteControl para ping con deadline
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
	// read deadline renovada por pong handler
	conn.SetReadDeadline(time.Now().Add(30 * time.Second))
	conn.SetPongHandler(func(string) error {
		_ = conn.SetReadDeadline(time.Now().Add(30 * time.Second))
		return nil
	})

	// crear client con buffer de envío (ajustable)
	const sendBufSize = 32
	client := newClient(conn, sendBufSize)

	// almacenar client
	clients.Store(client, true)

	// iniciar writer y ping loops
	go client.writerLoop(5 * time.Second)
	go client.pingLoop(10*time.Second, 5*time.Second)

	// lectura (reader) en este goroutine
	for {
		_, msg, err := conn.ReadMessage()
		if err != nil {
			// lectura fallida (cliente desconectado o timeout) -> cleanup
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
			// canal lleno: registrar métrica mínima (no spam de logs)
			recordMetrics(0, 0, 0)
		}
	}

	// reader sale -> cerrar client (esto también despierta writer/ping)
	client.close()
}

// ------------------ HEALTH ------------------

func handleHealth(w http.ResponseWriter, _ *http.Request) {
	count := 0
	clients.Range(func(key, value any) bool {
		// key es *Client
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
			// flush por tamaño
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

// processAndBroadcast envía el mensaje serializado a cada cliente,
// usando el canal per-client para evitar bloqueos de escritura.
func processAndBroadcast(accum []DataCliente) {
	start := time.Now()
	message := serializeSlice(accum)

	sent := 0
	// iterar sobre clients; si el canal de un cliente está lleno, se elimina el cliente
	clients.Range(func(key, value any) bool {
		c := key.(*Client)
		select {
		case c.send <- message:
			sent++
		default:
			// buffer lleno -> cliente lento, cerramos para mantener throughput
			c.close()
		}
		return true
	})

	recordMetrics(0, sent, time.Since(start))
}

// ------------------ SERIALIZACIÓN ------------------

// serializeSlice usa PutUint32 y bufferPool para minimizar allocations.
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

	// devolvemos una copia porque buf puede ser reutilizado por el pool
	b := append([]byte(nil), buf.Bytes()...)
	bufferPool.Put(buf)
	return b
}
