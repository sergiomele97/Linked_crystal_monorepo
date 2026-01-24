package main

import (
	"log"
	"net/http"
	"os"

	"example.com/hello/src/game"
)

func main() {
	game.InitGame()

	staticToken := os.Getenv("STATIC_TOKEN")
	if staticToken == "" {
		staticToken = "demo_token"
		log.Println("⚠️ STATIC_TOKEN no definido, usando default")
	}

	http.HandleFunc("/ws", func(w http.ResponseWriter, r *http.Request) {
		token := r.URL.Query().Get("token")
		if token != staticToken {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		game.HandleConnection(w, r)
	})

	http.HandleFunc("/link", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Query().Get("token") != staticToken {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		game.HandleLink(w, r)
	})

	http.HandleFunc("/health", game.HandleHealth)
	http.HandleFunc("/servers", game.HandleServers)

	go game.BroadcastLoop()

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
		log.Println("⚠️ PORT no definido, usando default 8080")
	}
	log.Println("Servidor WebSocket corriendo en :" + port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
