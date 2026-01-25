# Backend Functional Specification (`main.go`)

This document defines the expected behavior of the WebSocket server. It serves as the source of truth for testing.

## 1. Environment variables

-   `ENV`: Environment mode (e.g., `local`, `production`).
-   `PORT`: Server port (default: `8080`).
-   `STATIC_TOKEN`: Shared secret for authentication (default: `demo_token`).
-   `SERVERS`: Comma-separated list of known server URLs for `/servers` endpoint.

## 2. Parameters
-   **Max Clients**: 1024 simultaneous connections. Returns `503 Service Unavailable` if full.
-   **Max Packet Size**: 1024 bytes. Exceeding this closes the connection.
-   **Broadcast Rate**: 10Hz (Every 100ms).
-   **Send Buffer**: 32 messages per client. If the client is too slow and buffer fills, connection is closed.

## 3. Main WebSocket Endpoint (`/ws`)

### Connection Lifecycle
1.  **Handshake**: Client connects with valid token.
2.  **ID Assignment**: Server assigns a unique `ClientID` (0-1023).
3.  **Welcome Message**: Server sends a **raw 4-byte Little-Endian UInt32** containing the `ClientID`.
4.  **Heartbeat (Keep-Alive)**:
    -   **Server**: Sends `Ping` every 10 seconds.
    -   **Client**: Must respond with `Pong` or send data.
    -   **Timeout**: If no data/pong received for 30 seconds, server disconnects client.
5.  **Disconnect**: ID is freed and made available for new clients.

### Input Protocol (Client -> Server)
The first byte defines the packet type.

#### Type `0x01`: Game Data (Position)
-   **Format**: `[0x01] [Payload(24 bytes)]`
-   **Payload Structure** (24 bytes, Little-Endian):
    -   `PlayerID` (Uint32) - *Ignored by server (server uses connection ID)*
    -   `PlayerX` (Int32)
    -   `PlayerY` (Int32)
    -   `MapNumber` (Int32)
    -   `MapBank` (Int32)
    -   `IsOverworld` (Uint32)
-   **Behavior**: Server accepts only **latest** packet per 100ms window. Updates internal state for that `ClientID`. Does not broadcast immediately.

#### Type `0x02`: Chat Message
-   **Format**: `[0x02] [Message(UTF-8 String)]`
-   **Behavior**: Server immediately broadcasts this message to **all other connected clients**.
-   **Validation**: Server does not filter content.

### Error Handling Policy
-   **Malformed Packets**: Any packet following an incorrect format (e.g., too short) is ignored or causes a specific logic skip, but generally does **not immediately disconnect** unless it violates the WebSocket protocol frames.
-   **Protocol Violation**: Sending text frames instead of binary (or vice versa where not expected) or exceeding read limits causes an **immediate disconnect**.

### Output Protocol (Server -> Client)

#### Game Broadcast (Periodic)
-   **Frequency**: Every 100ms.
-   **Format**: `[0x01] [Packet1(24b)] [Packet2(24b)] ...`
-   **Content**: Concatenation of the latest position packet for every active client.

#### Chat Broadcast (Immediate)
-   **Format**: `[0x02] [SenderID(4 bytes LE)] [Message(String)]`
-   **Trigger**: Whenever another client sends a valid `0x02` message.

## 3. Link System Endpoint (`/link`)
-   **Parameters**: `id` (My ID), `target` (Target ID).
-   **Behavior**:
    -   Acts as a rendezvous point.
    -   The request with `(id=A, target=B)` matches with `(id=B, target=A)`.
    -   **First connection**: Blocks and waits (up to 45s).
    -   **Second connection**: Triggers a "Bridge".
    -   **Bridge**: Creates a bidirectional raw byte tunnel. What A sends, B receives, and vice-versa. Protocol agnostic.

## 4. Operational Endpoints
-   **GET /health**: Returns JSON with `status`, `clients` (count), `recv_rate`, `send_rate`, `latency_ms`.
-   **GET /servers**: Returns JSON list of available server URLs (from `SERVERS` env var).
