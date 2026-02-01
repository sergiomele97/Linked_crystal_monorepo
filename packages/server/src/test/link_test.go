package main

import (
	"testing"
	"time"

	"github.com/gorilla/websocket"
)

// 5. Link System Tests
func TestLinkSystem(t *testing.T) {
	s := startTestServer()
	defer s.Close()
	url := getWSURL(s.URL, "/link", "test_token")
	idA := "200"
	idB := "201"

	// LINK-01, 02, 03
	t.Run("LINK-0x Bridge Establishment", func(t *testing.T) {
		doneA := make(chan bool)

		go func() {
			u := url + "&id=" + idA + "&target=" + idB
			conn, _, err := websocket.DefaultDialer.Dial(u, nil)
			if err != nil {
				t.Error("Client A dial failed:", err)
				doneA <- false
				return
			}
			defer conn.Close()

			// Wait for "bridged" signal first
			conn.SetReadDeadline(time.Now().Add(2 * time.Second))
			_, msg, err := conn.ReadMessage()
			if err != nil {
				t.Error("Client A Read bridged Error:", err)
				doneA <- false
				return
			}
			if string(msg) != "bridged" {
				t.Error("Client A Expected 'bridged', got:", string(msg))
				doneA <- false
				return
			}

			// Wait for actual data
			_, msg, err = conn.ReadMessage()
			if err != nil {
				t.Error("Client A Read data Error:", err)
				doneA <- false
				return
			}
			if string(msg) != "HelloFromB" {
				t.Error("Client A Expected 'HelloFromB', got:", string(msg))
				doneA <- false
				return
			}
			doneA <- true
		}()

		time.Sleep(100 * time.Millisecond)

		// Connect B
		u := url + "&id=" + idB + "&target=" + idA
		connB, _, err := websocket.DefaultDialer.Dial(u, nil)
		if err != nil {
			t.Fatalf("Client B fail dial: %v", err)
		}
		defer connB.Close()

		if err := connB.WriteMessage(websocket.TextMessage, []byte("HelloFromB")); err != nil {
			t.Fatalf("Client B Write Error: %v", err)
		}

		if success := <-doneA; !success {
			t.Fatal("Link test failed")
		}
	})
}
