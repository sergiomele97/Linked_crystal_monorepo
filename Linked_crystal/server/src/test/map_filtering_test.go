package main

import (
	"encoding/binary"
	"testing"
	"time"

	"github.com/gorilla/websocket"
)

type testConn struct {
	t    *testing.T
	conn *websocket.Conn
	id   int
	msgs chan []byte
	done chan struct{}
}

func newTestConn(t *testing.T, url string) *testConn {
	conn, id := connectClient(t, url)
	tc := &testConn{
		t:    t,
		conn: conn,
		id:   id,
		msgs: make(chan []byte, 100),
		done: make(chan struct{}),
	}
	go tc.readLoop()
	return tc
}

func (tc *testConn) readLoop() {
	defer close(tc.done)
	for {
		_, msg, err := tc.conn.ReadMessage()
		if err != nil {
			return
		}
		tc.msgs <- msg
	}
}

func (tc *testConn) close() {
	tc.conn.Close()
	<-tc.done
}

func (tc *testConn) verifyReceivedFrom(expectedID int, label string) {
	timeout := time.After(2 * time.Second)
	for {
		select {
		case <-timeout:
			tc.t.Fatalf("Timeout: failed to receive broadcast from %s", label)
		case msg := <-tc.msgs:
			if len(msg) >= 25 && msg[0] == 0x01 {
				senderID := int(binary.LittleEndian.Uint32(msg[1:5]))
				if senderID == expectedID {
					return // Success
				}
			}
		}
	}
}

func (tc *testConn) verifyNotReceivedFrom(unexpectedID int, label string) {
	// Wait a bit to ensure any broadcast would have arrived
	time.Sleep(300 * time.Millisecond)
	// Drain channel
	for {
		select {
		case msg := <-tc.msgs:
			if len(msg) >= 25 && msg[0] == 0x01 {
				senderID := int(binary.LittleEndian.Uint32(msg[1:5]))
				if senderID == unexpectedID {
					tc.t.Fatalf("❌ Error: received broadcast from %s when it should be filtered", label)
				}
			}
		default:
			return
		}
	}
}

func TestMapFiltering(t *testing.T) {
	s := startTestServer()
	defer s.Close()
	url := getWSURL(s.URL, "/ws", "test_token")

	t.Run("Static Filtering", func(t *testing.T) {
		tcA := newTestConn(t, url)
		defer tcA.close()
		tcB := newTestConn(t, url)
		defer tcB.close()
		tcC := newTestConn(t, url)
		defer tcC.close()

		sendMapPacket(t, tcA.conn, 0, 1)
		sendMapPacket(t, tcB.conn, 0, 1)
		sendMapPacket(t, tcC.conn, 0, 2)
		time.Sleep(100 * time.Millisecond)

		sendGamePacket(t, tcA.conn, 0, 1, 100)
		tcB.verifyReceivedFrom(tcA.id, "A (Same Map)")
		tcC.verifyNotReceivedFrom(tcA.id, "A (Diff Map)")
	})

	t.Run("Dynamic Map Switching", func(t *testing.T) {
		tcA := newTestConn(t, url) // Map 1
		defer tcA.close()
		sendMapPacket(t, tcA.conn, 0, 1)

		tcB := newTestConn(t, url) // Map 2
		defer tcB.close()
		sendMapPacket(t, tcB.conn, 0, 2)

		tcM := newTestConn(t, url) // Mover
		defer tcM.close()
		sendMapPacket(t, tcM.conn, 0, 1)

		time.Sleep(200 * time.Millisecond)

		// 1. M sees A
		sendGamePacket(t, tcA.conn, 0, 1, 10)
		tcM.verifyReceivedFrom(tcA.id, "A while in Map 1")

		// 2. M doesn't see B
		sendGamePacket(t, tcB.conn, 0, 2, 20)
		tcM.verifyNotReceivedFrom(tcB.id, "B while in Map 1")

		// 3. M moves to Map 2
		sendMapPacket(t, tcM.conn, 0, 2)
		time.Sleep(200 * time.Millisecond)

		// 4. M sees B now
		sendGamePacket(t, tcB.conn, 0, 2, 30)
		tcM.verifyReceivedFrom(tcB.id, "B after moving to Map 2")

		// 5. M doesn't see A anymore
		sendGamePacket(t, tcA.conn, 0, 1, 40)
		tcM.verifyNotReceivedFrom(tcA.id, "A after moving to Map 2")
	})
}

func sendGamePacket(t *testing.T, conn *websocket.Conn, bank, number, x int32) {
	pkt := make([]byte, 25)
	pkt[0] = 0x01
	binary.LittleEndian.PutUint32(pkt[5:9], uint32(x))
	binary.LittleEndian.PutUint32(pkt[13:17], uint32(number))
	binary.LittleEndian.PutUint32(pkt[17:21], uint32(bank))
	binary.LittleEndian.PutUint32(pkt[21:25], 1)
	conn.WriteMessage(websocket.BinaryMessage, pkt)
}

func sendMapPacket(t *testing.T, conn *websocket.Conn, bank, number int32) {
	pkt := make([]byte, 25)
	pkt[0] = 0x01
	binary.LittleEndian.PutUint32(pkt[13:17], uint32(number))
	binary.LittleEndian.PutUint32(pkt[17:21], uint32(bank))
	conn.WriteMessage(websocket.BinaryMessage, pkt)
}
