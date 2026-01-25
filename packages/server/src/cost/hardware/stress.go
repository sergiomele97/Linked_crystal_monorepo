package main

import (
	"fmt"
	"log"
	"sync"
	"sync/atomic"
	"time"

	"github.com/gorilla/websocket"
)

func main() {
	// Hardcoded para eliminar variables de flag en este test de diagnóstico
	address := "ws://127.0.0.1:8080/ws?token=demo_token"
	numClients := 1024
	
	var connected int32
	var errors int32
	var wg sync.WaitGroup

	log.Printf("🧪 Diagnóstico: Intentando conectar %d clientes a %s", numClients, address)

	for i := 0; i < numClients; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()

			// Dialer con timeout corto para no esperar eternamente
			dialer := websocket.Dialer{
				HandshakeTimeout: 5 * time.Second,
			}

			c, resp, err := dialer.Dial(address, nil)
			if err != nil {
				atomic.AddInt32(&errors, 1)
				// SOLO printeamos el primer error para no inundar la consola
				if atomic.LoadInt32(&errors) == 1 {
					status := "N/A"
					if resp != nil {
						status = resp.Status
					}
					log.Printf("❌ ERROR CRÍTICO [Cliente %d]: %v | Status HTTP: %s", id, err, status)
				}
				return
			}
			defer c.Close()

			atomic.AddInt32(&connected, 1)
			
			// Mantener la conexión viva leyendo
			for {
				if _, _, err := c.ReadMessage(); err != nil {
					atomic.AddInt32(&connected, -1)
					return
				}
			}
		}(i)
		
		// Un pequeño respiro cada 10 conexiones
		if i%10 == 0 {
			time.Sleep(10 * time.Millisecond)
		}
	}

	// Monitor rápido
	for {
		time.Sleep(1 * time.Second)
		fmt.Printf("\r📊 [DEBUG] Conectados: %d | Errores: %d", atomic.LoadInt32(&connected), atomic.LoadInt32(&errors))
		if atomic.LoadInt32(&errors) > 0 && atomic.LoadInt32(&connected) == 0 {
			fmt.Print(" <- Algo va mal, revisa el error arriba.")
		}
	}
}