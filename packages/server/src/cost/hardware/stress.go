package main

import (
	"encoding/binary"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"math/rand"
	"net/http"
	"os"
	"sync"
	"sync/atomic"
	"time"

	"github.com/gorilla/websocket"
)

type HealthResponse struct {
	HW struct {
		CPUUsage       float64 `json:"cpu_percent"`
		MemPerClientKB float64 `json:"mem_per_client_kb"`
		TotalRSSMB     float64 `json:"total_rss_mb"`
	} `json:"hw"`
	Net struct {
		LatencyMs float64 `json:"latency_ms"`
	} `json:"net"`
}

func main() {
	benchMode := flag.Bool("bench", false, "Run in benchmark mode (output JSON and exit)")
	duration := flag.Int("duration", 20, "Duration in seconds for benchmark mode")
	numClients := flag.Int("clients", 500, "Number of clients to simulate")
	flag.Parse()

	address := "ws://127.0.0.1:8080/ws?token=demo_token"
	healthURL := "http://127.0.0.1:8080/health"

	var connected int32
	var errors int32
	var wg sync.WaitGroup

	if !*benchMode {
		log.Printf("🧪 Simulando %d jugadores moviéndose...", *numClients)
	}

	for i := 0; i < *numClients; i++ {
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

			go func() {
				for {
					_, _, err := c.ReadMessage()
					if err != nil {
						return
					}
				}
			}()

			posX, posY := int32(5), int32(4)
			path := [][2]int32{{2, 4}, {2, 6}, {4, 6}, {4, 4}}
			currentTarget := 0

			time.Sleep(time.Duration(rand.Intn(1000)) * time.Millisecond)

			ticker := time.NewTicker(16 * time.Millisecond)
			defer ticker.Stop()

			// Si estamos en benchMode, cerramos después del tiempo indicado
			stopChan := make(chan struct{})
			if *benchMode {
				time.AfterFunc(time.Duration(*duration)*time.Second, func() {
					close(stopChan)
				})
			}

			for {
				select {
				case <-ticker.C:
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
				case <-stopChan:
					return
				}
			}
		}(i)

		if i%10 == 0 {
			time.Sleep(20 * time.Millisecond)
		}
	}

	if *benchMode {
		time.Sleep(time.Duration(*duration+2) * time.Second)

		resp, err := http.Get(healthURL)
		if err != nil {
			log.Fatalf("Error fetching health: %v", err)
		}
		defer resp.Body.Close()

		var h HealthResponse
		if err := json.NewDecoder(resp.Body).Decode(&h); err != nil {
			log.Fatalf("Error decoding health: %v", err)
		}

		results := []map[string]any{
			{"name": "CPU Usage", "value": h.HW.CPUUsage, "unit": "%"},
			{"name": "Latency", "value": h.Net.LatencyMs, "unit": "ms"},
			{"name": "RAM per Client", "value": h.HW.MemPerClientKB, "unit": "KB"},
			{"name": "Failure Count", "value": atomic.LoadInt32(&errors), "unit": "count"},
			{"name": "Active Players", "value": atomic.LoadInt32(&connected), "unit": "count"},
		}

		json.NewEncoder(os.Stdout).Encode(results)
		return
	}

	for {
		time.Sleep(1 * time.Second)
		fmt.Printf("\r📊 [STRESS] Jugadores Activos: %d | Fallos: %d", atomic.LoadInt32(&connected), atomic.LoadInt32(&errors))
	}
}
