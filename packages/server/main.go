package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"log"
	"net/http"
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
	MaxClients       = 1024             // configurable: máximo de clientes simultáneos
	BroadcastMs      = 100              // cada cuánto hacer broadcast (ms)
	SendBufPerClient = 32               // tamaño del buffer de envío por cliente
	ReadLimit        = 1024             // límite de lectura por conexión
	IdleReadDeadline = 30 * time.Second // read deadline renovado por PONG
)

// ------------------ WEBSOCKET CORE ------------------

var upgrader = websocket.Upgrader{
	CheckOrigin:       func(r *http.Request) bool { return true }, // override más abajo si quieres restringir
	ReadBufferSize:    256,
	WriteBufferSize:   256,
	EnableCompression: false,
}

// ------------------ IDs y slots ------------------

// Pool de IDs libres: si vacío -> no aceptamos más conexiones.
var freeIDs = make(chan int, MaxClients)

// latestData: slice indexado por ID; cada entry guarda *DataCliente (o nil) usando atomic.Value
var latestData []atomic.Value // length = MaxClients

// clients: map de clientes a su ID (valor int)
var clients sync.Map // key: *Client, value: int (id)

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
	id        int // id asignado por servidor, -1 si ninguno
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
		// cerrar recursos de forma segura
		close(c.closed)
		// cerrar canal send evita writer goroutine
		close(c.send)
		// eliminar de clients map
		clients.Delete(c)
		// liberar ID y limpiar su slot
		if c.id >= 0 {
			// limpiar slot
			latestData[c.id].Store((*DataCliente)(nil))
			// devolver ID al pool (non-blocking: pero canal tiene capacidad MaxClients así que no bloqueará)
			select {
			case freeIDs <- c.id:
			default:
				// si no cabe (no debería), lo descartamos
			}
			log.Printf("Cliente desconectado: id=%d addr=%s", c.id, c.addr)
			c.id = -1
		}
		// cerrar conexión TCP
		_ = c.conn.Close()
	})
}

// writer loop: consume mensajes desde c.send y los escribe en la conexión
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

// ping loop: intenta pings periódicos; si falla, cierra cliente
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
	// inicializar pool de IDs y latestData
	latestData = make([]atomic.Value, MaxClients)
	for i := 0; i < MaxClients; i++ {
		freeIDs <- i
		latestData[i].Store((*DataCliente)(nil))
	}
}

func main() {
	// ejemplo: restringir orígenes aquí si quieres (descomenta/edita)
	// upgrader.CheckOrigin = func(r *http.Request) bool {
	//	  origin := r.Header.Get("Origin")
	//	  return origin == "https://mi-frontend.com" || origin == "http://localhost:5173"
	// }

	http.HandleFunc("/ws", handleConnection)
	http.HandleFunc("/health", handleHealth)
	http.HandleFunc("/servers", handleServers)

	go broadcastLoop()

	log.Println("Servidor WebSocket corriendo en :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

// ------------------ HANDLERS ------------------

func handleConnection(w http.ResponseWriter, r *http.Request) {
	// intentar asignar ID
	var id int
	select {
	case id = <-freeIDs:
		// got an ID
	default:
		// sin IDs libres: rechazar conexión
		http.Error(w, "server full", http.StatusServiceUnavailable)
		return
	}

	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		// devolver ID al pool porque no se terminó la conexión
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

	// crear client con ID asignada
	client := newClient(conn, SendBufPerClient, id)
	clients.Store(client, id)

	// log de conexión
	log.Printf("Cliente conectado: id=%d addr=%s", client.id, client.addr)

	// iniciar writer y ping loops
	go client.writerLoop(5 * time.Second)
	go client.pingLoop(10*time.Second, 5*time.Second)

	// reader en este goroutine
	for {
		_, msg, err := conn.ReadMessage()
		if err != nil {
			// cliente desconectado o timeout
			break
		}
		// esperamos al menos 12 bytes (X Y Z) o 16 si tu cliente sigue mandando ID (lo ignoramos)
		if len(msg) < 12 {
			continue
		}

		start := time.Now()
		// leer campos (si el cliente sigue mandando ID en los primeros 4 bytes, lo ignoramos y usamos nuestro id)
		var d DataCliente
		// si el cliente envía 16 bytes: [id(4) X(4) Y(4) Z(4)] -> leer desde 4
		if len(msg) >= 16 {
			d.X = int32(binary.LittleEndian.Uint32(msg[4:8]))
			d.Y = int32(binary.LittleEndian.Uint32(msg[8:12]))
			d.Z = int32(binary.LittleEndian.Uint32(msg[12:16]))
		} else {
			// si envía sólo X Y Z (12 bytes)
			d.X = int32(binary.LittleEndian.Uint32(msg[0:4]))
			d.Y = int32(binary.LittleEndian.Uint32(msg[4:8]))
			d.Z = int32(binary.LittleEndian.Uint32(msg[8:12]))
		}

		// asignar ID del servidor
		d.ID = int32(client.id)

		// almacenar en el slot del cliente (sobrescribe cualquier valor anterior)
		latestData[client.id].Store(&d)

		recordMetrics(1, 0, time.Since(start))
	}

	// reader sale -> cerrar client (esto también libera ID y limpia slot)
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

// ------------------ BROADCAST LOOP ------------------

func broadcastLoop() {
	ticker := time.NewTicker(time.Millisecond * time.Duration(BroadcastMs))
	defer ticker.Stop()

	for {
		<-ticker.C

		// recolectar todos los latestData no nil
		accum := make([]DataCliente, 0, 256)
		for id := 0; id < MaxClients; id++ {
			v := latestData[id].Load()
			if v == nil {
				continue
			}
			// extraer valor y limpiar slot (atomically store nil)
			if p, ok := v.(*DataCliente); ok && p != nil {
				accum = append(accum, *p)
				// limpiar slot para no reenviar mismo dato en siguiente tick
				latestData[id].Store((*DataCliente)(nil))
			}
		}

		if len(accum) == 0 {
			continue
		}

		processAndBroadcast(accum)
	}
}

// processAndBroadcast envía el mensaje serializado a cada cliente,
// usando el canal per-client para evitar bloqueos de escritura.
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
			// cliente lento -> cerramos para mantener throughput
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
