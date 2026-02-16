package hub

import (
	"log"
	"os"
	"strings"
	"time"

	"github.com/joho/godotenv"
)

// ------------------ CONFIG ------------------

const (
	MaxClients       = 500
	BroadcastMs      = 100
	SendBufPerClient = 32
	ReadLimit        = 1024
	IdleReadDeadline = 30 * time.Second
	ServerVersion    = "0.1"
)

var (
	Servers []string
)

// InitConfig loads environment variables and initializes global configuration.
func InitConfig() {
	// Cargar .env: Intentar local y parent directory (para flexibilidad src vs root)
	if err := godotenv.Load(); err != nil {
		// Fallback: Try loading from parent
		if err := godotenv.Load("../.env"); err != nil {
			log.Println("⚠️ No se encontró .env, usando variables de entorno del sistema")
		}
	}

	envServers := os.Getenv("SERVERS")
	if envServers == "" {
		log.Println("Variable de entorno SERVERS vacia, usando default value")
		Servers = []string{"ws://localhost:8080/ws"}
	} else {
		list := strings.Split(envServers, ",")
		Servers = make([]string, 0, len(list))
		for _, s := range list {
			s = strings.TrimSpace(s)
			if s != "" {
				Servers = append(Servers, s)
			}
		}
	}
}
