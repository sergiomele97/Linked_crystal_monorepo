# Client Functional Specification

This document defines the expected behavior of the Client application (Python/Kivy). It serves as the basis for manual and automated testing.

## 1. Configuration & Environment

The application configuration is managed via `env.py` (with overrides in `config.py`).

- **`ENV`**: Execution mode (`local`, `desarrollo`, `production`). Affects SSL and URL construction.
- **`URL` / `SSL_URL`**: Base host for WebSocket connections.
- **`STATIC_TOKEN`**: Authentication token sent as a query parameter (`?token=...`).
- **`PORT`**: Port used primarily in `local` mode.

## 2. Main Connection (Multiplexed Data)

Managed by `SocketClient` and `PacketDispatcher`.

### Handshake
1. **Connection**: Connects to `ws://{host}/ws?token={token}`.
2. **ID Assignment**: The first message received is exactly 4 bytes (Little-Endian Uint32) containing the `my_id`.
3. **State Update**: `my_id` is stored in `AppData.userID`.

### Input Protocol (Server -> Client)
The first byte defines the packet type.

#### Type `0x01`: Game Data (Dynamic Sprites)
- **Format**: `[0x01] [Payload(N * 24 bytes)]`
- **Behavior**:
    - Clears current `serverPackets` store.
    - Decodes multiple 24-byte packets.
    - Filters out packets where `player_id == my_id`.
    - Updates `AppData.serverPackets`.

#### Type `0x02`: Chat Message
- **Format**: `[0x02] [SenderID(4 bytes LE)] [Message(UTF-8 String)]`
- **Behavior**: Passes `SenderID` and `Message` to `ChatManager.receive_message`.

### Output Protocol (Client -> Server)
- **Game Data**: Sent periodically (approx. 10Hz) as `[0x01] [Payload(24 bytes)]`.
- **Chat**: Sent as `[0x02] [Message(String)]`.

## 3. Link Cable Connection (Raw Bridge)

Managed by `LinkClient`. Provides a low-latency byte tunnel for emulator communication.

### Handshake & Rendezvous
1. **Connection**: Connects to `ws://{host}/link?token={token}&id={my_id}&target={target_id}`.
2. **Bridged Signal**: If the server sends a string `"bridged"`, `LinkClient.bridged` is set to `True`.
3. **Queue Cleanup**: On connection, both `recv_queue` and `send_queue_async` are cleared to ensure synchronization.

### Data Transmission
- **Incoming**: Binary frames are iterated and bytes are put into a fixed-size `recv_queue` (max 10,000). If full, the oldest byte is dropped.
- **Outgoing**: Bytes are pulled from `send_queue_async`.
- **Batching**: To optimize performance, outgoing bytes are batched into a single payload if they are available in the queue (up to 128 bytes or 64 iterations).

### Emulator Integration
- **`get_byte()`**: Blocks for up to 1ms waiting for data. Returns `0xFF` if timeout occurs (emulating idle link).
- **`send_byte(b)`**: Thread-safe injection of a byte into the async loop for transmission.

## 4. Error Handling & Resilience
- **Reconnection**: `LinkClient` attempts to reconnect every 2 seconds if the connection is lost.
- **SSL Context**: Uses `certifi` to provide CA certificates when `ENV != "local"`.
- **Thread Safety**: Uses `loop.call_soon_threadsafe` to bridge between emulator threads and the `asyncio` loop.

## 5. User Scenarios (Behavioral Specification)

These scenarios define the expected user journey and UI states, serving as the basis for the Test Plan.

### Scenario 1: Setup & Initial Connection (`menu_screen.py`)
1.  **App Startup**: The application opens in the Menu Screen.
2.  **ROM Selection**: User opens the file explorer, selects a valid `.gbc` ROM.
    - *Result*: `AppData.romPath` is updated.
    - *UI*: `label_rom` shows the filename. `rom_cargado` becomes `True`, unlocking the "Elegir Servidor" button.
3.  **Server Discovery**: User clicks "Elegir Servidor".
    - *Result*: `UrlRequest` is sent to `URL/servers`.
    - *UI*: A list of available servers is displayed in a modal; `loading` spinner is active during the request.
4.  **Server Selection**: User selects a server from the list.
    - *Result*: `selected_server` is set. `ConnectionLoop` starts automatically.
    - *UI*: Modal closes. `label_servidor` shows the chosen server. `servidor_elegido` becomes `True`, unlocking the "Jugar" button.
5.  **Game Start**: User clicks "Jugar".
    - *Result*: Navigation to `EmulatorScreen`.

### Scenario 2: Emulation & Tools (`emulator_screen.py`)
1.  **Auto-Emulation**: On entering the screen, the emulator starts with the selected ROM.
    - *Result*: `EmulatorCoreInterface` is initialized and running.
    - *Feedback*: Video display is updating, audio output is active, and gamepad inputs (D-Pad, A, B, Start, Select) respond correctly.
2.  **Chat Interaction**: User opens the chat interface.
    - *Action*: User writes a message and sends it.
    - *Result*: Message is sent via `ConnectionLoop` (type `0x02`).
    - *UI*: Message appears in the local chat history.
    - *Persistence*: User can close and reopen the chat; the message history must persist.
3.  **Options & Link Cable**: User opens the options menu and selects "Cable Link".
    - *Action*: User enters a Target ID and clicks "Conectar".
    - *Result*: `LinkClient` starts connection to `/link`. `EmulatorScreen` starts polling link stats.
    - *UI*: Link interface closes. `link_stats_panel` becomes visible (`opacity=1`).
    - *State (Waiting)*: If the other user hasn't connected, the panel shows "Waiting..." (Yellow) and `TX > 0`, `RX = 0`.

### Scenario 3: Synchronization (Background)
1.  **Position Broadcast**: The client sends its `0x01` packet every 100ms.
2.  **Remote Rendering**: When the server broadcasts other players' data, the client updates `AppData.serverPackets`.
    - *Result*: Remote players (other player IDs) are visible and moving on the local screen according to their coordinates.
    - *Filtering*: The client MUST NOT render its own ID from the server broadcast.

### Scenario 4: Two-Player Interaction (Linked State)
1.  **Bidirectional Bridge**: Both users connect to the same target IDs.
    - *Result*: Server establishes the raw bridge. `LinkClient` receives `"bridged"`.
    - *UI*: `link_status_dot` changes to "Linked!" (Green).
2.  **Data Exchange**: Data (TX/RX) starts flowing between emulators.
    - *Result*: Users can perform in-game Link Cable actions (Trade/Battle).
3.  **Chat During Link**: Users can still use the Chat interface while the Link Cable is active without interference.
