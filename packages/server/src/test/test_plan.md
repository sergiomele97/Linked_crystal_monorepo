# Backend Test Plan
> Derived from `backend_spec.md`

This document lists the systematic tests required to validate the server compliance with the specification. Each test targets a specific requirement.

## 1. Auth & Configuration Tests
| ID | Requirement | Test Case | Expected Result |
|----|-------------|-----------|-----------------|
| **AUTH-01** | All endpoints must require `token` param matching env var. | Connect to `/ws` without `token`. | HTTP 401 Unauthorized. |
| **AUTH-02** | Invalid token rejection. | Connect to `/ws` with `token=invalid`. | HTTP 401 Unauthorized. |
| **AUTH-03** | Valid token acceptance. | Connect to `/ws` with `token=demo_token`. | HTTP 101 Switching Protocols (Connection Upgrade). |

## 2. Protocol Limits Tests
| ID | Requirement | Test Case | Expected Result |
|----|-------------|-----------|-----------------|
| **LIM-01** | Max payload size (1024 bytes). | Send a binary message of 2000 bytes. | Connection closed with policy violation error (or generic close). |
| **LIM-02** | Text frame violation. | Send a Text Message frame to `/ws`. | Connection closed immediately. |

## 3. Core Protocol Tests (`/ws`)
| ID | Requirement | Test Case | Expected Result |
|----|-------------|-----------|-----------------|
| **PROTO-01** | Initial Handshake (ID Assignment). | Connect a client. Read first message. | Receive 4 bytes. Parse as UInt32 ID (e.g., 0). |
| **PROTO-02** | Game Data Input (`0x01`). | Send `0x01` + 24 bytes of dummy position data. | No immediate response (broadcast is async). Server connection remains open. |
| **PROTO-03** | Game Broadcast (`0x01`). | Connect Client A and Client B. A sends pos. Wait 150ms. | Client B receives `0x01` + payload containing A's data. |
| **PROTO-04** | Chat Input/Output (`0x02`). | Connect A and B. A sends `0x02` + "Hello". | Client B receives `0x02` + A_ID(4b) + "Hello" immediately. |
| **PROTO-05** | Chat Self-Echo suppression. | Connect A. A sends `0x02` + "Test". | Client A does **not** receive the message back. |

## 4. Heartbeat Tests
| ID | Requirement | Test Case | Expected Result |
|----|-------------|-----------|-----------------|
| **HB-01** | Server sends Ping. | Connect client, wait 15s. | Client receives at least one Ping control frame. |
| **HB-02** | Timeout on inactivity. | Connect, disable auto-pong, send nothing. Wait 35s. | Connection closed by server. |

## 5. Link System Tests (`/link`)
| ID | Requirement | Test Case | Expected Result |
|----|-------------|-----------|-----------------|
| **LINK-01** | Blocking Wait. | Connect Client A to `/link?id=1&target=2`. | Connection holds open, no data received immediately. |
| **LINK-02** | Bridge Establishment. | A connects (1->2). Then B connects (2->1). | Both receive "Bridge Established" (or simply data flows). |
| **LINK-03** | P2P Data Tunneling. | Establish bridge. A sends random bytes. | B reads exact same random bytes. |
| **LINK-04** | Disconnect while waiting. | A connects. A disconnects. B connects. | B should wait (not crash or link to ghost). |
| **LINK-05** | Disconnect during bridge. | Bridge established. A disconnects. | B should detect closure/EOF immediately. |

## 6. Concurrency & Stress Tests
| ID | Requirement | Test Case | Expected Result |
|----|-------------|-----------|-----------------|
| **STRESS-01** | Max Clients Rejection. | Fill server (mocking `MaxClients=2`). Connect 3rd. | HTTP 503 Service Unavailable. |
| **STRESS-02** | Race Conditions. | 100 clients connect/disconnect rapidly. | No deadlocks or panics. |
