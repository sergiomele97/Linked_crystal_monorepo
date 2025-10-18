# Etapa de compilación
FROM golang:1.25-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o server .

# Imagen final mínima
FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/server .
EXPOSE 8080
CMD ["./server"]
