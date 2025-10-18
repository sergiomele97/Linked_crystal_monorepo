package main

import (
	"bytes"
	"encoding/binary"
	"log"
)

// DataCliente representa la info de cada cliente
type DataCliente struct {
	ID int32
	X  int32
	Y  int32
	Z  int32
}

// serializeData convierte un DataCliente a binario
func serializeData(d DataCliente) []byte {
	buf := bytes.NewBuffer(make([]byte, 0, 16))
	if err := binary.Write(buf, binary.LittleEndian, d.ID); err != nil {
		log.Println("binary.Write error:", err)
	}
	if err := binary.Write(buf, binary.LittleEndian, d.X); err != nil {
		log.Println("binary.Write error:", err)
	}
	if err := binary.Write(buf, binary.LittleEndian, d.Y); err != nil {
		log.Println("binary.Write error:", err)
	}
	if err := binary.Write(buf, binary.LittleEndian, d.Z); err != nil {
		log.Println("binary.Write error:", err)
	}
	return buf.Bytes()
}

// serializeSlice convierte un slice de DataCliente a binario
func serializeSlice(data []DataCliente) []byte {
	buf := bytes.NewBuffer(make([]byte, 0, len(data)*16))
	for _, d := range data {
		buf.Write(serializeData(d))
	}
	return buf.Bytes()
}
