package hub

import (
	"encoding/binary"
	"encoding/json"
	"log"
	"net/http"
	"time"

	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	CheckOrigin:       func(r *http.Request) bool { return true },
	ReadBufferSize:    1024, // ✂️ Subido de 256 para evitar fragmentación en stress
	WriteBufferSize:   1024,
	EnableCompression: false,
}

func HandleConnection(w http.ResponseWriter, r *http.Request) {
	var id int
	select {
	case id = <-freeIDs:
	default:
		http.Error(w, "server full", http.StatusServiceUnavailable)
		return
	}

	// ✂️ SEGURIDAD: Validar que el ID sea válido para el array latestPackets
	if id < 0 || id >= len(latestPackets) {
		log.Printf("⚠️ ID recibido fuera de rango: %d", id)
		select {
		case freeIDs <- id:
		default:
		}
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

	welcome := make([]byte, 4)
	binary.LittleEndian.PutUint32(welcome, uint32(id))
	if err := conn.WriteMessage(websocket.BinaryMessage, welcome); err != nil {
		conn.Close()
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

	go client.WriterLoop(5 * time.Second)
	go client.PingLoop(10*time.Second, 5*time.Second)

	for {
		_, msg, err := conn.ReadMessage()
		if err != nil {
			break
		}
		if len(msg) < 1 {
			continue
		}

		typeByte := msg[0]
		payload := msg[1:]

		if typeByte == 0x01 { // Game Data
			// ✂️ SEGURIDAD: Payload debe ser suficiente para los offsets usados
			if len(payload) < 24 {
				continue
			}

			start := time.Now()
			var p Packet
			p.PlayerID = uint32(client.id)

			// Usamos offsets consistentes con el payload[1:]
			p.PlayerX = int32(binary.LittleEndian.Uint32(payload[4:8]))
			p.PlayerY = int32(binary.LittleEndian.Uint32(payload[8:12]))
			p.MapNumber = int32(binary.LittleEndian.Uint32(payload[12:16]))
			p.MapBank = int32(binary.LittleEndian.Uint32(payload[16:20]))
			p.IsOverworld = binary.LittleEndian.Uint32(payload[20:24])

			// ✂️ El punto del PANIC: Validamos el ID antes de guardar
			if client.id >= 0 && client.id < len(latestPackets) {
				latestPackets[client.id].Store(&p)
				RecordMetrics(1, 0, time.Since(start))
			}

		} else if typeByte == 0x02 { // Chat Message
			if len(payload) > 0 {
				broadcastChatMessage(client.id, string(payload))
			}
		}
	}

	client.Close()
}

func broadcastChatMessage(senderID int, msg string) {
	buf := make([]byte, 1+4+len(msg))
	buf[0] = 0x02
	binary.LittleEndian.PutUint32(buf[1:5], uint32(senderID))
	copy(buf[5:], []byte(msg))

	clients.Range(func(key, value any) bool {
		c := key.(*Client)
		if c.id == senderID {
			return true
		}
		select {
		case c.send <- buf:
		default:
			// Si el canal está lleno, cerramos cliente lento para proteger el server
			c.Close()
		}
		return true
	})
}

func HandleHealth(w http.ResponseWriter, _ *http.Request) {
	clientCount := 0
	clients.Range(func(_, _ any) bool { clientCount++; return true })

	recvRate, sendRate, latency := GetAverages()
	hw := GetHardwareStats()

	resp := map[string]any{
		"status": "ok",
		"net": map[string]any{
			"clients":    clientCount,
			"recv_rate":  recvRate,
			"send_rate":  sendRate,
			"latency_ms": latency,
		},
		"hw": map[string]any{
			"mem_per_client_kb": hw.MemPerClientKB,
			"total_rss_mb":      hw.TotalRSS_MB,
			"cpu_percent":       hw.CPU_Usage,
		},
		"uptime_sec": time.Since(startTime).Seconds(),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func HandleServers(w http.ResponseWriter, _ *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(Servers)
}
