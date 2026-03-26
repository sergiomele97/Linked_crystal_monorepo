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

		// IMPORTANT: Client B must send a packet to initialize its map on server
		pktB := make([]byte, 29)
		pktB[0] = 0x01
		binary.LittleEndian.PutUint32(pktB[13:17], 0) // MapNumber = 0
		binary.LittleEndian.PutUint32(pktB[17:21], 0) // MapBank  = 0
		if err := connB.WriteMessage(websocket.BinaryMessage, pktB); err != nil {
			t.Fatalf("Failed to initialize receiver map: %v", err)
		}

		// Client A: Sender
		// (Already connected at line 29)

		// Send 0x01 Packet WITH Map info (Bank 0, Map 0)
		pktA := make([]byte, 29)
		pktA[0] = 0x01
		binary.LittleEndian.PutUint32(pktA[5:9], 100)  // X = 100
		binary.LittleEndian.PutUint32(pktA[9:13], 200) // Y = 200
		binary.LittleEndian.PutUint32(pktA[13:17], 0)  // MapNumber = 0
		binary.LittleEndian.PutUint32(pktA[17:21], 0)  // MapBank = 0
		binary.LittleEndian.PutUint32(pktA[21:25], 1)  // IsOverworld = 1
		binary.LittleEndian.PutUint32(pktA[25:29], 0)  // Speed = 0

		if err := connA.WriteMessage(websocket.BinaryMessage, pktA); err != nil {
			t.Fatalf("Failed to send game packet: %v", err)
		}

		// Wait for broadcast
		connB.SetReadDeadline(time.Now().Add(1 * time.Second))
		found := false
		for !found {
			_, msg, err := connB.ReadMessage()
			if err != nil {
				t.Fatalf("Timeout or Read error: %v", err)
			}
			if len(msg) >= 29 && msg[0] == 0x01 {
				found = true
			}
		}
		t.Logf("✅ Client %d received broadcast", idB)
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
