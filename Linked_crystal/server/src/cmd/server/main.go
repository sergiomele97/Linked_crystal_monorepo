package main

import (
	"log"
	"net/http"
	"net/http/pprof"
	"os"

	"example.com/hello/internal/hub"
)

func main() {
	hub.InitConfig()
	hub.InitHub()

	env := getEnv("ENV", "local")
	staticToken := getEnv("STATIC_TOKEN", "demo_token")
	port := getEnv("PORT", "8080")

	mux := http.NewServeMux()

	// --- [CUT] Seguridad: pprof solo disponible en local ---
	if env == "local" {
		log.Println("🛠️  Modo local detectado: Habilitando pprof en /debug/pprof/")
		mux.HandleFunc("/debug/pprof/", pprof.Index)
		mux.HandleFunc("/debug/pprof/cmdline", pprof.Cmdline)
		mux.HandleFunc("/debug/pprof/profile", pprof.Profile)
		mux.HandleFunc("/debug/pprof/symbol", pprof.Symbol)
		mux.HandleFunc("/debug/pprof/trace", pprof.Trace)
	}

	// Rutas protegidas
	mux.HandleFunc("/ws", authMiddleware(hub.HandleConnection, staticToken))
	mux.HandleFunc("/link", authMiddleware(hub.HandleLink, staticToken))

	// Rutas públicas
	mux.HandleFunc("/health", hub.HandleHealth)
	mux.HandleFunc("/servers", hub.HandleServers)

	go hub.BroadcastLoop()
	go hub.StartHardwareMonitor()

	log.Printf("🚀 Servidor [%s] corriendo en el puerto %s", env, port)
	log.Fatal(http.ListenAndServe(":"+port, mux))
}

func getEnv(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	log.Printf("⚠️  %s no definido, usando default: %s", key, fallback)
	return fallback
}

func authMiddleware(next http.HandlerFunc, staticToken string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Query().Get("token") != staticToken {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		next(w, r)
	}
}