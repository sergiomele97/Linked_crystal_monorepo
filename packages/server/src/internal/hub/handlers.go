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
	ReadBufferSize:    256,
	WriteBufferSize:   256,
	EnableCompression: false,
}

// HandleConnection handles WebSocket requests from clients.
func HandleConnection(w http.ResponseWriter, r *http.Request) {
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

	welcome := make([]byte, 4)
	binary.LittleEndian.PutUint32(welcome, uint32(id))
	if err := conn.WriteMessage(websocket.BinaryMessage, welcome); err != nil {
		log.Println("Error enviando ID de bienvenida:", err)
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
			if len(payload) < 24 {
				continue
			}
			start := time.Now()
			var p Packet
			p.PlayerID = uint32(client.id)
			p.PlayerX = int32(binary.LittleEndian.Uint32(payload[4:8]))
			p.PlayerY = int32(binary.LittleEndian.Uint32(payload[8:12]))
			p.MapNumber = int32(binary.LittleEndian.Uint32(payload[12:16]))
			p.MapBank = int32(binary.LittleEndian.Uint32(payload[16:20]))
			p.IsOverworld = binary.LittleEndian.Uint32(payload[20:24])

			latestPackets[client.id].Store(&p)
			RecordMetrics(1, 0, time.Since(start))
		} else if typeByte == 0x02 { // Chat Message
			broadcastChatMessage(client.id, string(payload))
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
			c.Close()
		}
		return true
	})
}

// HandleHealth returns server health metrics.
func HandleHealth(w http.ResponseWriter, _ *http.Request) {
	count := 0
	clients.Range(func(key, value any) bool {
		count++
		return true
	})

	recvRate, sendRate, latencyMs := GetAverages()
	resp := map[string]any{
		"status":     "ok",
		"clients":    count,
		"recv_rate":  recvRate,
		"send_rate":  sendRate,
		"latency_ms": latencyMs,
		"timestamp":  time.Now().UTC(),
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

// HandleServers returns the list of known servers.
func HandleServers(w http.ResponseWriter, _ *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(Servers)
}
