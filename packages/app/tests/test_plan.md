# Client Test Plan

This document outlines the test cases for the Linked Crystal client application, derived from the [Functional Specification](file:///home/sergio/work/Linked_crystal_monorepo/packages/app/specs.md).

## 1. Test Strategy

- **Unit Testing**: Focus on protocol logic (Packet serialization, ConnectionLoop state machine).
- **Integration Testing**: Verify communication between the client and a mock/local server.
- **Functional/UI Testing**: Manual or automated validation of user scenarios and screen flows.

---

## 2. Protocol & Logic Tests (Unit/Integration)

### T-PRO-01: Packet Serialization
- **Objective**: Verify `Packet` class correctly encodes/decodes data.
- **Pre-condition**: None.
- **Input**: Create `Packet(player_id=1, x=10, y=20, ...)`.
- **Expected Result**: 
    - `to_bytes()` returns a 24-byte buffer.
    - `from_bytes(buffer)` recreates an identical object.

### T-PRO-02: Link Cable ID Assignment
- **Objective**: Verify the client correctly sets `my_id` from the initial handshake.
- **Pre-condition**: Mock WebSocket server sends a 4-byte LE Uint32 (e.g., `0x00000005`).
- **Expected Result**: 
    - `PacketDispatcher.my_id` becomes `5`.
    - `AppData.userID` is updated.

### T-PRO-03: Chat Multiplexing
- **Objective**: Verify chat messages are correctly dispatched.
- **Input**: Server sends frame `[0x02] [SenderID(4b)] [Message("Hello")]`.
- **Expected Result**: `ChatManager.receive_message` is called with correct ID and text.

---

## 3. UI Scenario Tests (Functional)

### T-UI-01: Setup Flow (Scenario 1)
- **Steps**:
    1. Start App.
    2. Click browse → Select `.gbc` file.
    3. Click "Elegir Servidor" → Select a server.
    4. Click "Jugar".
- **Expected Result**: 
    - File selection unlocks Server button.
    - Server selection unlocks Play button.
    - Click Play transitions to `EmulatorScreen`.

### T-UI-02: Emulator Tools (Scenario 2)
- **Steps**:
    1. Enter `EmulatorScreen`.
    2. Open Chat → Send "Test message" → Close Chat → Reopen.
    3. Open Menu → Cable Link → Enter ID → Connect.
- **Expected Result**: 
    - Video/Audio are active.
    - Chat message persists after reopening.
    - Link stats panel appears showing "Waiting...".

### T-UI-03: Multi-player Sync (Scenario 3)
- **Steps**:
    1. Launch two clients.
    2. Move Player A.
- **Expected Result**: 
    - Player B's screen renders Player A's sprite moving correctly.
    - Player A does NOT see a duplicate of itself rendered by the server.

### T-UI-04: Link Cable Bridge (Scenario 4)
- **Steps**:
    1. Setup link between Client A and Client B.
    2. Server sends `"bridged"` signal.
- **Expected Result**: 
    - Link stats dot turns Green ("Linked!").
    - TX/RX counters increment as emulators exchange data.
    - Chat remains functional during the bridge.

---

## 4. Resilience & Performance

### T-RES-01: Reconnection
- **Objective**: Verify auto-reconnect logic.
- **Steps**: Kill the server while client is connected. Wait 5 seconds. Restart server.
- **Expected Result**: Client automatically establishes connection within `backoff` window.

### T-RES-02: Link Buffer Management
- **Objective**: Verify `LinkClient` handles queue overflow safely.
- **Steps**: Flood the `recv_queue` with 11,000 bytes.
- **Expected Result**: Queue size remains at 10,000; oldest bytes are dropped; no crash.
