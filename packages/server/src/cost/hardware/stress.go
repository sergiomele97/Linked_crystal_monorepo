package main

import (
	"encoding/binary"
	"fmt"
	"log"
	"math/rand"
	"sync"
	"sync/atomic"
	"time"

	"github.com/gorilla/websocket"
)

func main() {
	address := "ws://127.0.0.1:8080/ws?token=demo_token"
	numClients := 500

	var connected int32
	var errors int32
	var wg sync.WaitGroup

	log.Printf("🧪 Simulando %d jugadores moviéndose...", numClients)

	for i := 0; i < numClients; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()

			c, _, err := websocket.DefaultDialer.Dial(address, nil)
			if err != nil {
				atomic.AddInt32(&errors, 1)
				return
			}
			defer c.Close()

			atomic.AddInt32(&connected, 1)

			// 🛡️ LECTOR EN SEGUNDO PLANO:
			// El servidor envía broadcasts periódicos. Si no los leemos, el buffer se llena y el server nos cierra.
			go func() {
				for {
					_, _, err := c.ReadMessage()
					if err != nil {
						return // La conexión se ha cerrado
					}
				}
			}()

			posX, posY := int32(5), int32(4)
			path := [][2]int32{{2, 4}, {2, 6}, {4, 6}, {4, 4}}
			currentTarget := 0

			time.Sleep(time.Duration(rand.Intn(1000)) * time.Millisecond)

			ticker := time.NewTicker(16 * time.Millisecond)
			defer ticker.Stop()

			for range ticker.C {
				target := path[currentTarget]
				if posX < target[0] {
					posX++
				} else if posX > target[0] {
					posX--
				}
				if posY < target[1] {
					posY++
				} else if posY > target[1] {
					posY--
				}

				if posX == target[0] && posY == target[1] {
					currentTarget = (currentTarget + 1) % len(path)
				}

				payload := make([]byte, 25)
				payload[0] = 0x01
				binary.LittleEndian.PutUint32(payload[1:5], uint32(0))
				binary.LittleEndian.PutUint32(payload[5:9], uint32(posX))
				binary.LittleEndian.PutUint32(payload[9:13], uint32(posY))
				binary.LittleEndian.PutUint32(payload[13:17], uint32(4))
				binary.LittleEndian.PutUint32(payload[17:21], uint32(24))
				binary.LittleEndian.PutUint32(payload[21:25], uint32(1))

				if err := c.WriteMessage(websocket.BinaryMessage, payload); err != nil {
					atomic.AddInt32(&connected, -1)
					atomic.AddInt32(&errors, 1)
					return
				}
			}
		}(i)

		if i%10 == 0 {
			time.Sleep(20 * time.Millisecond)
		}
	}

	for {
		time.Sleep(1 * time.Second)
		fmt.Printf("\r📊 [STRESS] Jugadores Activos: %d | Fallos: %d", atomic.LoadInt32(&connected), atomic.LoadInt32(&errors))
	}
}
