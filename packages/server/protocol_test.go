package main

import (
	"encoding/binary"
	"testing"
	"time"

	"github.com/gorilla/websocket"
)

// 3. Core Protocol Tests
func TestProtocol(t *testing.T) {
	s := startTestServer()
	defer s.Close()
	url := getWSURL(s.URL, "/ws", "test_token")

	// PROTO-01: Handshake
	t.Run("PROTO-01 Handshake", func(t *testing.T) {
		conn, id := connectClient(t, url)
		defer conn.Close()
		if id < 0 || id > 1024 {
			t.Errorf("Received invalid ID: %d", id)
		}
	})

	// PROTO-03: Game Broadcast
	t.Run("PROTO-03 Game Broadcast", func(t *testing.T) {
		// Client A: Sender
		connA, _ := connectClient(t, url)
		defer connA.Close()

		// Client B: Receiver
		connB, idB := connectClient(t, url)
		defer connB.Close()

		// Send 0x01 Packet
		pkt := make([]byte, 25)
		pkt[0] = 0x01
		binary.LittleEndian.PutUint32(pkt[5:9], 100)  // X = 100
		binary.LittleEndian.PutUint32(pkt[9:13], 200) // Y = 200

		if err := connA.WriteMessage(websocket.BinaryMessage, pkt); err != nil {
			t.Fatalf("Failed to send game packet: %v", err)
		}

		// Wait for broadcast
		timeout := time.After(500 * time.Millisecond)
		found := false
		for !found {
			select {
			case <-timeout:
				t.Fatal("Timeout waiting for game broadcast")
			default:
				connB.SetReadDeadline(time.Now().Add(100 * time.Millisecond))
				_, msg, err := connB.ReadMessage()
				if err != nil {
					continue
				}
				if len(msg) >= 25 && msg[0] == 0x01 {
					found = true
				}
			}
		}
		t.Logf("Client %d received broadcast", idB)
	})

	// PROTO-04 & 05: Chat
	t.Run("PROTO-04 Chat Broadcast", func(t *testing.T) {
		c1, id1 := connectClient(t, url)
		defer c1.Close()

		c2, _ := connectClient(t, url)
		defer c2.Close()

		text := "Hello World"
		msg := append([]byte{0x02}, []byte(text)...)
		c1.WriteMessage(websocket.BinaryMessage, msg)

		// C2 should receive
		c2.SetReadDeadline(time.Now().Add(2 * time.Second))
		_, rcv, err := c2.ReadMessage()
		if err != nil {
			t.Fatalf("C2 failed to receive chat: %v", err)
		}

		if len(rcv) < 5 || rcv[0] != 0x02 {
			t.Fatalf("Invalid chat packet: %v", rcv)
		}

		senderID := int(binary.LittleEndian.Uint32(rcv[1:5]))
		if senderID != id1 {
			t.Errorf("Wrong sender ID. Expected %d, got %d", id1, senderID)
		}
	})
}
