package hub

import (
	"sync"
	"sync/atomic"
	"time"
)

var (
	freeIDs       = make(chan int, MaxClients)
	latestPackets = make([]atomic.Value, MaxClients)
	clients       sync.Map
)

// InitHub prepares the client registry and ID pool.
func InitHub() {
	for i := 0; i < MaxClients; i++ {
		select {
		case freeIDs <- i:
		default:
		}
		latestPackets[i].Store((*Packet)(nil))
	}
}

// BroadcastLoop periodically sends accumulated game state to all clients.
func BroadcastLoop() {
	ticker := time.NewTicker(time.Millisecond * time.Duration(BroadcastMs))
	defer ticker.Stop()

	for {
		<-ticker.C
		accum := make([]Packet, 0, 256)
		for id := 0; id < MaxClients; id++ {
			v := latestPackets[id].Load()
			if v == nil {
				continue
			}
			if p, ok := v.(*Packet); ok && p != nil {
				accum = append(accum, *p)
				latestPackets[id].Store((*Packet)(nil))
			}
		}

		if len(accum) == 0 {
			continue
		}

		message := SerializePackets(accum)
		start := time.Now()
		sent := 0

		clients.Range(func(key, value any) bool {
			c := key.(*Client)
			select {
			case c.send <- message:
				sent++
			default:
				c.Close()
			}
			return true
		})

		RecordMetrics(0, sent, time.Since(start))
	}
}
