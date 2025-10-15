package main

import (
	"log"
	"net/http"
	"time"

	"github.com/gorilla/websocket"
)

func main() {
	http.HandleFunc("/ws", handleConnection)
	go broadcastLoop()

	log.Println("Servidor WebSocket corriendo en :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

// broadcastLoop envía datos a todos los clientes cada 0,1s
func broadcastLoop() {
	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop()

	accum := []DataCliente{}
	const maxAccum = 5000

	for {
		select {
		case d := <-dataChan:
			accum = append(accum, d)
			if len(accum) > maxAccum {
				accum = accum[len(accum)/2:] // recorta si crece demasiado
			}
		case <-ticker.C:
			if len(accum) == 0 {
				continue
			}

			message := serializeSlice(accum)
			accum = nil

			clients.Lock()
			for client := range clients.conns {
				if err := client.WriteMessage(websocket.BinaryMessage, message); err != nil {
					client.Close()
					delete(clients.conns, client)
				}
			}
			clients.Unlock()
		}
	}
}
