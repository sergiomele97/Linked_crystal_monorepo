package hub

import (
	"bytes"
	"encoding/binary"
	"sync"
)

// Packet represents the game state for a single player.
type Packet struct {
	PlayerID    uint32
	PlayerX     int32
	PlayerY     int32
	MapNumber   int32
	MapBank     int32
	IsOverworld uint32
}

var bufferPool = sync.Pool{
	New: func() any {
		return bytes.NewBuffer(make([]byte, 0, 24*100))
	},
}

// SerializePackets converts a slice of Packets into a binary broadcast message.
func SerializePackets(data []Packet) []byte {
	buf := bufferPool.Get().(*bytes.Buffer)
	buf.Reset()

	buf.WriteByte(0x01) // Game Data Type

	var tmp [24]byte
	for _, p := range data {
		binary.LittleEndian.PutUint32(tmp[0:4], p.PlayerID)
		binary.LittleEndian.PutUint32(tmp[4:8], uint32(p.PlayerX))
		binary.LittleEndian.PutUint32(tmp[8:12], uint32(p.PlayerY))
		binary.LittleEndian.PutUint32(tmp[12:16], uint32(p.MapNumber))
		binary.LittleEndian.PutUint32(tmp[16:20], uint32(p.MapBank))
		binary.LittleEndian.PutUint32(tmp[20:24], p.IsOverworld)
		buf.Write(tmp[:])
	}

	b := append([]byte(nil), buf.Bytes()...)
	bufferPool.Put(buf)
	return b
}
