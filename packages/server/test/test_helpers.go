package main

import (
	"encoding/binary"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"sync"
	"testing"

	"example.com/hello/src/game"

	"github.com/gorilla/websocket"
)

var (
	testServer *httptest.Server
	testOnce   sync.Once
)

// Helper to start a test server with the Auth middleware
func startTestServer() *httptest.Server {
	// Initialize game state
	game.InitGame()

	// Ensure token is set for tests
	os.Setenv("STATIC_TOKEN", "test_token")
	staticToken := "test_token"

	mux := http.NewServeMux()
	mux.HandleFunc("/ws", func(w http.ResponseWriter, r *http.Request) {
		token := r.URL.Query().Get("token")
		if token != staticToken {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		game.HandleConnection(w, r)
	})
	mux.HandleFunc("/link", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Query().Get("token") != staticToken {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		game.HandleLink(w, r)
	})

	// Avoid multiple broadcast loops in tests if possible, or just accept one global
	testOnce.Do(func() {
		go game.BroadcastLoop()
	})

	return httptest.NewServer(mux)
}

func getWSURL(serverURL string, endpoint string, token string) string {
	wsURL := strings.Replace(serverURL, "http", "ws", 1) + endpoint
	if token != "" {
		wsURL += "?token=" + token
	}
	return wsURL
}

func connectClient(t *testing.T, url string) (*websocket.Conn, int) {
	conn, resp, err := websocket.DefaultDialer.Dial(url, nil)
	if err != nil {
		if resp != nil && resp.StatusCode == http.StatusUnauthorized {
			return nil, -1 // Expected for auth fail
		}
		t.Fatalf("Failed to connect to %s: %v", url, err)
	}

	// Read Welcome ID (Raw 4 bytes)
	_, message, err := conn.ReadMessage()
	if err != nil {
		t.Fatalf("Failed to read welcome message: %v", err)
	}
	if len(message) != 4 {
		t.Fatalf("Expected 4 byte welcome ID, got %d", len(message))
	}
	id := int(binary.LittleEndian.Uint32(message))
	return conn, id
}
