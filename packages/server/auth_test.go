package main

import (
	"strings"
	"testing"

	"github.com/gorilla/websocket"
)

// 1. Auth & Configuration Tests
func TestAuth(t *testing.T) {
	s := startTestServer()
	defer s.Close()

	// AUTH-01: No token
	t.Run("AUTH-01 No Token", func(t *testing.T) {
		_, _, err := websocket.DefaultDialer.Dial(strings.Replace(s.URL, "http", "ws", 1)+"/ws", nil)
		if err == nil {
			t.Error("Expected error for missing token, got nil")
		}
	})

	// AUTH-02: Wrong token
	t.Run("AUTH-02 Wrong Token", func(t *testing.T) {
		_, _, err := websocket.DefaultDialer.Dial(getWSURL(s.URL, "/ws", "bad"), nil)
		if err == nil {
			t.Error("Expected error for wrong token, got nil")
		}
	})

	// AUTH-03: Valid token
	t.Run("AUTH-03 Valid Token", func(t *testing.T) {
		conn, id := connectClient(t, getWSURL(s.URL, "/ws", "test_token"))
		defer conn.Close()
		if id < 0 {
			t.Error("Expected valid ID")
		}
		t.Logf("Connected with ID: %d", id)
	})
}
