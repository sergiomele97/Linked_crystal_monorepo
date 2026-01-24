package main

import (
	"sync"
	"testing"
	"time"

	"github.com/gorilla/websocket"
)

// 6. Concurrency & Stress Tests
func TestStress(t *testing.T) {
	s := startTestServer()
	defer s.Close()
	url := getWSURL(s.URL, "/ws", "test_token")

	// STRESS-02: Rapid Connect/Disconnect
	t.Run("STRESS-02 Race Conditions", func(t *testing.T) {
		var wg sync.WaitGroup
		clientCount := 50 // Reduced for speed, but enough to trigger races

		for i := 0; i < clientCount; i++ {
			wg.Add(1)
			go func() {
				defer wg.Done()
				conn, _, err := websocket.DefaultDialer.Dial(url, nil)
				if err != nil {
					// It's acceptable if the server rejects under load, but here we expect it to hold
					t.Logf("Stress connection failed: %v", err)
					return
				}
				// Handshake
				_, _, _ = conn.ReadMessage()

				// Keep alive briefly
				time.Sleep(10 * time.Millisecond)
				conn.Close()
			}()
		}

		done := make(chan struct{})
		go func() {
			wg.Wait()
			close(done)
		}()

		select {
		case <-done:
			// Success
		case <-time.After(5 * time.Second):
			t.Fatal("Stress test timed out (deadlock?)")
		}
	})
}
