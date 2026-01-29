# Build stage
FROM golang:1.25.3-alpine AS builder

WORKDIR /app

# Copy go mod and sum files
COPY src/go.mod src/go.sum ./
RUN go mod download

# Copy source code
COPY src/ ./

# Build the binary
RUN CGO_ENABLED=0 GOOS=linux go build -v -ldflags="-s -w" -o server ./cmd/server

# Final stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates tzdata

WORKDIR /root/

# Copy the binary from builder
COPY --from=builder /app/server .

# Copy .env if it exists in cmd/server (optional, usually handled by compose)
# COPY src/cmd/server/.env .

EXPOSE 8080

CMD ["./server"]
