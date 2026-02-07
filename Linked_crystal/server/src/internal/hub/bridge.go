package hub

import (
	"log"
	"net/http"
	"strconv"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

var linkMatches sync.Map

type LinkWaiter struct {
	conn *websocket.Conn
	peer chan *websocket.Conn
	done chan struct{}
}

// HandleLink handles the rendezvous for the peer-to-peer bridge.
func HandleLink(w http.ResponseWriter, r *http.Request) {
	idStr := r.URL.Query().Get("id")
	targetStr := r.URL.Query().Get("target")
	id, _ := strconv.Atoi(idStr)
	target, _ := strconv.Atoi(targetStr)

	if id == target {
		http.Error(w, "invalid target", http.StatusBadRequest)
		return
	}

	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		return
	}

	p1, p2 := id, target
	if p1 > p2 {
		p1, p2 = p2, p1
	}
	pairKey := strconv.Itoa(p1) + "-" + strconv.Itoa(p2)

	actual, loaded := linkMatches.LoadOrStore(pairKey, &LinkWaiter{
		conn: conn,
		peer: make(chan *websocket.Conn, 1),
		done: make(chan struct{}),
	})

	waiter := actual.(*LinkWaiter)

	if loaded {
		select {
		case waiter.peer <- conn:
			<-waiter.done
		default:
			conn.Close()
		}
		linkMatches.Delete(pairKey)
	} else {
		select {
		case peerConn := <-waiter.peer:
			bridge(conn, peerConn)
			close(waiter.done)
		case <-time.After(45 * time.Second):
			linkMatches.Delete(pairKey)
			conn.Close()
		}
	}
}

func bridge(c1, c2 *websocket.Conn) {
	log.Println("[Bridge] Iniciando túnel entre dos emuladores")
	c1.WriteMessage(websocket.TextMessage, []byte("bridged"))
	c2.WriteMessage(websocket.TextMessage, []byte("bridged"))

	done := make(chan struct{}, 2)

	copyWS := func(dst, src *websocket.Conn) {
		defer func() { done <- struct{}{} }()
		for {
			mt, msg, err := src.ReadMessage()
			if err != nil {
				return
			}
			if err := dst.WriteMessage(mt, msg); err != nil {
				return
			}
		}
	}

	go copyWS(c1, c2)
	go copyWS(c2, c1)

	<-done
	c1.Close()
	c2.Close()
	log.Println("[Bridge] Túnel cerrado por desconexión de un extremo")
}
