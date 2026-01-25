package hub

import (
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

// Client represents a connected player.
type Client struct {
	conn      *websocket.Conn
	send      chan []byte
	closeOnce sync.Once
	closed    chan struct{}
	id        int
	addr      string
}

func newClient(conn *websocket.Conn, sendBuf int, id int) *Client {
	return &Client{
		conn:   conn,
		send:   make(chan []byte, sendBuf),
		closed: make(chan struct{}),
		id:     id,
		addr:   conn.RemoteAddr().String(),
	}
}

func (c *Client) Close() {
	c.closeOnce.Do(func() {
		close(c.closed)
		close(c.send)
		clients.Delete(c)
		if c.id >= 0 {
			latestPackets[c.id].Store((*Packet)(nil))
			select {
			case freeIDs <- c.id:
			default:
			}
			c.id = -1
		}
		_ = c.conn.Close()
	})
}

func (c *Client) WriterLoop(writeTimeout time.Duration) {
	for msg := range c.send {
		_ = c.conn.SetWriteDeadline(time.Now().Add(writeTimeout))
		if err := c.conn.WriteMessage(websocket.BinaryMessage, msg); err != nil {
			c.Close()
			return
		}
	}
	c.Close()
}

func (c *Client) PingLoop(interval, timeout time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()
	for {
		select {
		case <-ticker.C:
			_ = c.conn.SetWriteDeadline(time.Now().Add(timeout))
			if err := c.conn.WriteControl(websocket.PingMessage, []byte{}, time.Now().Add(timeout)); err != nil {
				c.Close()
				return
			}
		case <-c.closed:
			return
		}
	}
}
