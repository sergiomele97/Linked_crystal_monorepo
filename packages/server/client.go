package main

import (
	"encoding/binary"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool { return true },
}

// Canal global para recibir datos de clientes
var dataChan = make(chan DataCliente, 2000)

// Mapa de clientes activos
var clients = struct {
	sync.RWMutex
	conns map[*websocket.Conn]bool
}{conns: make(map[*websocket.Conn]bool)}

// handleConnection maneja cada cliente
func handleConnection(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Println("Upgrade error:", err)
		return
	}
	defer conn.Close()

	conn.SetReadLimit(1024)                                // límite de mensaje
	conn.SetReadDeadline(time.Now().Add(30 * time.Second)) // timeout lectura
	conn.SetPongHandler(func(string) error {
		conn.SetReadDeadline(time.Now().Add(30 * time.Second))
		return nil
	})

	clients.Lock()
	clients.conns[conn] = true
	clients.Unlock()

	for {
		_, msg, err := conn.ReadMessage() // binario
		if err != nil {
			log.Println("Read error:", err)
			break
		}
		if len(msg) < 16 {
			continue
		}

		data := DataCliente{
			ID: int32(binary.LittleEndian.Uint32(msg[0:4])),
			X:  int32(binary.LittleEndian.Uint32(msg[4:8])),
			Y:  int32(binary.LittleEndian.Uint32(msg[8:12])),
			Z:  int32(binary.LittleEndian.Uint32(msg[12:16])),
		}

		select {
		case dataChan <- data:
		default:
			// canal lleno, descartamos
		}
	}

	clients.Lock()
	delete(clients.conns, conn)
	clients.Unlock()
}
