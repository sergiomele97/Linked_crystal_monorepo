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
	startTime     time.Time
	stopChan      = make(chan struct{})
)

// InitHub prepares the client registry and ID pool.
func InitHub() {
	startTime = time.Now()
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
		select {
		case <-ticker.C:
			// 1. Group packets by Map (Bank + Number)
			// Key: (MapBank << 16) | MapNumber
			mapGroups := make(map[int32][]Packet)

			for id := 0; id < MaxClients; id++ {
				v := latestPackets[id].Load()
				if v == nil {
					continue
				}
				if p, ok := v.(*Packet); ok && p != nil {
					mapKey := (p.MapBank << 16) | p.MapNumber
					mapGroups[mapKey] = append(mapGroups[mapKey], *p)
					// Reset so we don't send the same position twice if no update
					latestPackets[id].Store((*Packet)(nil))
				}
			}

			if len(mapGroups) == 0 {
				continue
			}

			// 2. Pre-serialize messages for each map
			serializedMaps := make(map[int32][]byte)
			for mapKey, packets := range mapGroups {
				serializedMaps[mapKey] = SerializePackets(packets)
			}

			start := time.Now()
			sent := 0

			// 3. Send to clients based on their current map
			clients.Range(func(key, value any) bool {
				c := key.(*Client)

				c.mu.RLock()
				clientMapKey := (c.MapBank << 16) | c.MapNumber
				c.mu.RUnlock()

				// Only send if we have data for this map
				if msg, ok := serializedMaps[clientMapKey]; ok {
					select {
					case c.send <- msg:
						sent++
					default:
						c.Close()
					}
				}
				return true
			})

			RecordMetrics(0, sent, time.Since(start))
		case <-stopChan:
			return
		}
	}
}

// StopBroadcast stops the global broadcast loop.
func StopBroadcast() {
	select {
	case stopChan <- struct{}{}:
	default:
	}
}
