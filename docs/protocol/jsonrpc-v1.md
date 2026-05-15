# ArcFlow JSON-RPC Protocol — Version 1

The wire protocol the ArcFlow daemon speaks over Unix Domain Sockets. This is the **public, stable, semver-versioned** interface contract — closed engine implementation, open protocol surface. Anyone can reimplement a daemon serving this protocol.

**Status:** Stable as of 2026-05-13. 49 methods. Specification version `v1`.

**License of this document:** Apache 2.0 (reimplementation-permissive — see end of file).

Companion files:

- [`LICENSE-FAQ.md`](../../LICENSE-FAQ.md) — licensing model + Q&A
- [`reproducible-build.md`](../reproducible-build.md) — verify the daemon binary matches its source
- [`../../cookbooks/`](../../cookbooks/) — example client code in TypeScript, Python, Rust, shell

---

## Why this spec exists

ArcFlow Core is proprietary free-to-use software (see [LICENSE-FAQ.md](../../LICENSE-FAQ.md)). The engine's implementation is not open source. **But the wire protocol is.** This spec is your guarantee that you are not locked into OZ as a vendor — if you ever needed to, you could write a competing daemon implementing this protocol and your application code would not change.

This is the same pattern NVIDIA established with CUDA + PTX: closed implementation, open virtual ISA. The PTX spec gave third parties (AMD ROCm, Apple Metal, Intel oneAPI) a compatibility target — paradoxically reducing competitive pressure on NVIDIA by giving customers an exit valve they almost never use. We're doing the same thing.

The protocol surface is **forwards-compatible** — minor versions add methods or optional parameters, never break existing clients. **Backwards-incompatible changes** require a major version bump (v1 → v2) and at least 180 days of co-existence (both servers run simultaneously). See §[Versioning](#versioning).

---

## Transport

JSON-RPC 2.0 over Unix Domain Socket, newline-framed.

```
Client → daemon: one JSON object per line, terminated by '\n'.
Daemon → client: one JSON object per line, terminated by '\n'.
```

Default socket path: `/tmp/arcflow.sock` (override with `--socket /path/to/sock`).

**Request envelope:**

```json
{"id": 42, "method": "topic.publish", "params": {"topic": "events", "data": {"x": 1}}}
```

- `id` — optional `u64`. If present, the response echoes it. Used for correlating requests on multiplexed connections. Omit for fire-and-forget.
- `method` — string. The method name (see [§Methods](#methods)).
- `params` — object. Method-specific parameters. Type-checked per-method.

**Response envelope (success):**

```json
{"id": 42, "result": {"sequence": 7}}
```

**Response envelope (error):**

```json
{"id": 42, "error": {"code": "TOPIC_NOT_FOUND", "message": "Topic 'events' does not exist"}}
```

- `code` — string. One of the typed error codes documented per-method, plus the protocol-level codes (see [§Error Codes](#error-codes)).
- `message` — human-readable detail. Stable across patch versions for the same `code`; may vary in wording across minor versions.

---

## Methods

49 methods across 9 families. Each family is documented in its own section below.

| Family | Methods | Purpose |
|---|---|---|
| [Health + introspection](#health--introspection) | 3 | `ping`, `daemon.info`, `daemon.audit` |
| [Topics](#topics) | 11 | Topic lifecycle, publish, replay |
| [Consumers](#consumers) | 8 | Durable consumer registration + ack/nack |
| [Consumer groups](#consumer-groups) | 7 | Multi-consumer queue-group sharing |
| [Sliding windows](#sliding-windows) | 4 | Time-bounded aggregations |
| [Topic patterns](#topic-patterns) | 6 | NATS-style wildcard subscriptions |
| [Request-reply](#request-reply) | 6 | Synchronous request-reply over the bus |
| [Stream functions](#stream-functions) | 5 | Lag/Lead/Delta scalar derivatives |
| [Snapshot](#snapshot) | 1 | Coherent per-topic watermark for fusion reads |
| [Cypher](#cypher) | 1 | Generic Cypher execution over the wire |

Method names use dot-separated namespaces (`topic.publish`, `consumer.register`). Bare method names (`ping`, `request`, `reply`) are reserved for protocol-fundamental operations.

---

### Health + introspection

#### `ping`

Liveness probe. Returns `{"pong": true}`.

```jsonrpc
→ {"id":N, "method":"ping"}
← {"id":N, "result": {"pong": true}}
```

#### `daemon.info`

Identity + uptime + active-config snapshot.

```jsonrpc
→ {"id":N, "method":"daemon.info"}
← {"id":N, "result": {
    "version": "0.8.0",
    "uptime_seconds": 12345,
    "wal_durability": true,
    "limits": {"max_line_bytes": 1048576, "max_connections": 256},
    "counts": {"topics": 4, "consumers": 12, "consumer_groups": 2}
  }}
```

#### `daemon.audit`

Run consistency + operational audits.

```jsonrpc
→ {"id":N, "method":"daemon.audit", "params": {"lag_threshold": 100}}
← {"id":N, "result": {
    "healthy": true,
    "orphan_consumers": {"count": 0, "violations": []},
    "lagging_consumers": {"threshold": 100, "count": 1, "rows": [...]},
    "consumers_ahead_of_head": {"count": 0, "violations": []},
    "orphan_dlq_nodes": {"count": 0, "violations": []},
    "cross_workspace_edges": {"count": 0, "rows": []}
  }}
```

`healthy` is gated on invariant audits only (orphan consumers, consumers ahead of head, orphan DLQ nodes). Operational summaries (lagging consumers, cross-workspace edges) don't gate it.

---

### Topics

Eleven methods covering topic lifecycle, publish, retention, and event replay. Topics are the fundamental pub/sub unit — every event is published to exactly one topic and read by zero-or-more consumers.

#### `topic.create`

```jsonrpc
→ {"id":N, "method":"topic.create", "params": {
    "name": "events",
    "max_events": 100000,    // optional retention cap
    "max_age_ms": 3600000    // optional retention cap (1 hour)
  }}
← {"id":N, "result": {"id": 7, "name": "events"}}
```

#### `topic.delete`

```jsonrpc
→ {"id":N, "method":"topic.delete", "params": {"name": "events"}}
← {"id":N, "result": {"deleted": true}}
```

#### `topic.list`

```jsonrpc
→ {"id":N, "method":"topic.list"}
← {"id":N, "result": {"topics": [
    {"id": 7, "name": "events", "max_events": null, "max_age_ms": null, "head_seq": 42},
    ...
  ]}}
```

#### `topic.purge`

Remove all events from a topic without deleting the topic itself.

```jsonrpc
→ {"id":N, "method":"topic.purge", "params": {"name": "events"}}
← {"id":N, "result": {"purged": 42}}
```

#### `topic.set_retention`

Update retention policy on an existing topic.

```jsonrpc
→ {"id":N, "method":"topic.set_retention", "params": {
    "name": "events",
    "max_events": 50000,
    "max_age_ms": 1800000
  }}
← {"id":N, "result": {"updated": true}}
```

#### `topic.checkpoint`

Force a snapshot of pub/sub state to disk. Used for explicit durability points outside the normal WAL flush cadence.

```jsonrpc
→ {"id":N, "method":"topic.checkpoint", "params": {"path": "/data/snap.bin", "truncate_wal": false}}
← {"id":N, "result": {"snapshot_path": "/data/snap.bin"}}
```

#### `topic.publish`

Publish a single event to a topic.

```jsonrpc
→ {"id":N, "method":"topic.publish", "params": {
    "topic": "events",
    "data": {"x": 1, "y": "hello"},
    "headers": {"trace_id": "abc123"}    // optional
  }}
← {"id":N, "result": {"sequence": 7}}
```

`data` must be a **flat** property map (no nested objects, no heterogeneous arrays). SDKs that need to send nested data should JSON-stringify it under a `payload` key first. Strict by default; rejects with `INVALID_PAYLOAD_SHAPE`.

#### `topic.publish_batch`

Publish multiple events in one call. Atomic at the per-topic level.

```jsonrpc
→ {"id":N, "method":"topic.publish_batch", "params": {
    "topic": "events",
    "events": [
      {"data": {"x": 1}, "headers": {}},
      {"data": {"x": 2}, "headers": {}}
    ]
  }}
← {"id":N, "result": {"first_sequence": 8, "count": 2}}
```

#### `topic.events_after`

Replay events on a topic starting from a sequence number. Used for catch-up reads.

```jsonrpc
→ {"id":N, "method":"topic.events_after", "params": {
    "topic": "events",
    "after_seq": 0,
    "limit": 100
  }}
← {"id":N, "result": {"events": [...], "has_more": false}}
```

#### `topic.next_seq`

Get the next-to-be-assigned sequence number for a topic. Used for "how far ahead am I" calculations.

```jsonrpc
→ {"id":N, "method":"topic.next_seq", "params": {"topic": "events"}}
← {"id":N, "result": {"next_seq": 43}}
```

---

### Consumers

Eight methods for durable consumer state. A consumer is a named position in a topic; it survives daemon restart via WAL replay.

#### `consumer.register`

```jsonrpc
→ {"id":N, "method":"consumer.register", "params": {
    "name": "worker-a",
    "topic": "events",
    "start": "beginning"     // "beginning" | "latest" | <integer seq>
  }}
← {"id":N, "result": {"registered": true}}
```

#### `consumer.drop`

Remove a consumer registration.

```jsonrpc
→ {"id":N, "method":"consumer.drop", "params": {"name": "worker-a", "topic": "events"}}
← {"id":N, "result": {"dropped": true}}
```

#### `consumer.list`

```jsonrpc
→ {"id":N, "method":"consumer.list"}
← {"id":N, "result": {"consumers": [
    {"name": "worker-a", "topic": "events", "cursor": 42, "lag": 0},
    ...
  ]}}
```

#### `consumer.reset`

Reset a consumer's cursor.

```jsonrpc
→ {"id":N, "method":"consumer.reset", "params": {"name": "worker-a", "topic": "events", "to": 0}}
← {"id":N, "result": {"reset_to": 0}}
```

#### `consumer.ack`

Acknowledge that the consumer has processed events up through a sequence number.

```jsonrpc
→ {"id":N, "method":"consumer.ack", "params": {"name": "worker-a", "topic": "events", "up_to_seq": 42}}
← {"id":N, "result": {"acked_to": 42}}
```

#### `consumer.nack`

Mark an event as unprocessable. Routes the original event to the `:DLQ` graph nodes (the per-topic dead-letter store).

```jsonrpc
→ {"id":N, "method":"consumer.nack", "params": {"name": "worker-a", "topic": "events", "seq": 42, "reason": "validation failed"}}
← {"id":N, "result": {"nacked": 42, "dlq_node": 1234}}
```

#### `consumer.pending`

Get pending (unacked) events for a consumer.

```jsonrpc
→ {"id":N, "method":"consumer.pending", "params": {"name": "worker-a", "topic": "events", "limit": 100}}
← {"id":N, "result": {"events": [...], "has_more": true}}
```

#### `consumer.subscribe` (streaming)

Long-lived streaming subscription. The daemon pushes events as they arrive. Special: this method does NOT use the standard JSON-RPC response envelope — instead the daemon streams one JSON object per line indefinitely until the client disconnects.

```jsonrpc
→ {"id":N, "method":"consumer.subscribe", "params": {"name": "worker-a", "topic": "events", "poll_ms": 30}}
← {"event": {...}}
← {"event": {...}}
← ...
```

---

### Consumer groups

Seven methods for queue-group (NATS-style) consumer-group sharing. A consumer group has multiple members; each event is delivered to exactly one member of the group.

Methods mirror the per-consumer ones with group semantics: `group.register_member`, `group.drop_member`, `group.list`, `group.ack`, `group.nack`, `group.pending`, `group.subscribe`. Wire shapes are analogous to the consumer family with an additional `group` parameter where relevant.

See cookbook recipes for full per-method examples.

---

### Sliding windows

Four methods for time-bounded aggregations:

- `window.register` — register a sliding-window aggregator (count, sum, mean, min, max)
- `window.feed` — push a value into a window
- `window.drop` — remove a window registration
- `window.list` — list all registered windows

Computational state (not WAL-journaled — same discipline as stream functions). Re-feed from source topic after restart.

---

### Topic patterns

Six methods for NATS-style wildcard topic subscriptions. The wildcard semantics:

- `*` — matches exactly one topic-name segment
- `>` — matches one or more trailing segments (must be the final segment)

Example: pattern `fusion.*.v1` matches `fusion.stride.v1`, `fusion.gait.v1`, `fusion.suspension.v1` but not `fusion.stride.v2` or `fusion.stride.subkey.v1`.

#### `pattern.subscribe`

Register a stored Cypher query that fires on every matching topic, including future topics that match the pattern.

```jsonrpc
→ {"id":N, "method":"pattern.subscribe", "params": {
    "name": "fusion-watcher",
    "pattern": "fusion.*.v1",
    "query": "MATCH (n) WHERE n.confidence < 0.5 RETURN n"
  }}
← {"id":N, "result": {"subscribed": true, "matched_topics": ["fusion.stride.v1", "fusion.gait.v1"]}}
```

WAL-journaled as `SubscribePattern` — survives restart, auto-binds future matching topics.

#### `pattern.register_consumer`

Register a durable consumer that follows a pattern. Each matching topic gets its own per-topic consumer instance at the registered `start` offset.

```jsonrpc
→ {"id":N, "method":"pattern.register_consumer", "params": {
    "name": "welfare-fusion",
    "pattern": "fusion.*.v1",
    "start": "latest"
  }}
← {"id":N, "result": {"registered": true, "matched_topics": [...]}}
```

#### `pattern.drop_consumer`

Drop a pattern-consumer registration AND cascade-drop every per-topic consumer it spawned.

```jsonrpc
→ {"id":N, "method":"pattern.drop_consumer", "params": {"name": "welfare-fusion", "pattern": "fusion.*.v1"}}
← {"id":N, "result": {"dropped": true}}
```

#### `pattern.topics_matching`

List every currently-present topic name matching a pattern. Lexicographic order.

```jsonrpc
→ {"id":N, "method":"pattern.topics_matching", "params": {"pattern": "fusion.*.v1"}}
← {"id":N, "result": {"topics": ["fusion.back.v1", "fusion.gait.v1", "fusion.stride.v1"]}}
```

#### `pattern.list_subscriptions` / `pattern.list_consumers`

Admin / observability listings — all stored-query subscriptions and all pattern-consumer registrations respectively.

---

### Request-reply

Six methods for synchronous request-reply over the bus. The engine allocates a `_correlation_id` (format `_REQ.<n>`) and a per-request reply topic (`_REPLY._REQ.<n>`). Request-reply state is NOT WAL-journaled (RPC-grade transient state — matches NATS-core).

#### `request`

Publish a request event + register a pending-reply entry.

```jsonrpc
→ {"id":N, "method":"request", "params": {
    "topic": "calibration.fetch",
    "data": {"session_id": "sess-A"},
    "headers": {},
    "timeout_ms": 5000
  }}
← {"id":N, "result": {
    "correlation_id": "_REQ.42",
    "reply_topic": "_REPLY._REQ.42",
    "request_seq": 1234,
    "deadline_ms": 1700000005000
  }}
```

The published event carries engine-controlled headers `_correlation_id` + `_reply_to` (engine wins on collision with caller-supplied headers — prevents redirect attacks).

#### `reply`

Record a reply for a pending request. Publishes the reply event on the reply topic AND records it in the pending-replies map.

```jsonrpc
→ {"id":N, "method":"reply", "params": {
    "correlation_id": "_REQ.42",
    "data": {"calibration": {...}},
    "headers": {}
  }}
← {"id":N, "result": {"replied": true, "reply_seq": 1}}
```

#### `poll_reply`

Non-blocking take. Returns the reply if it has arrived; otherwise reports `pending` / `timed_out` / `unknown`.

```jsonrpc
→ {"id":N, "method":"poll_reply", "params": {"correlation_id": "_REQ.42"}}
← {"id":N, "result": {"replied": true, "data": {...}, "headers": {...}, "replied_at_ms": ...}}
   // or {"replied": false, "pending": true}
   // or {"replied": false, "timed_out": true}
   // or {"replied": false, "unknown": true}
```

#### `cancel_request`

Drop a pending request without resolving it.

```jsonrpc
→ {"id":N, "method":"cancel_request", "params": {"correlation_id": "_REQ.42"}}
← {"id":N, "result": {"cancelled": true}}
```

#### `sweep_expired_requests`

Transition all `Awaiting` requests past their deadline to `TimedOut`. Returns the swept correlation IDs.

```jsonrpc
→ {"id":N, "method":"sweep_expired_requests", "params": {"now_ms": 1700000010000}}
← {"id":N, "result": {"swept": 2, "correlation_ids": ["_REQ.41", "_REQ.42"]}}
```

#### `pending_requests`

Observability list. Shows every pending entry with state.

```jsonrpc
→ {"id":N, "method":"pending_requests"}
← {"id":N, "result": {"pending": [
    {"correlation_id": "_REQ.42", "request_topic": "...", "reply_topic": "...", "created_at_ms": ..., "deadline_ms": ..., "state": "awaiting"},
    ...
  ]}}
```

**Note: `wait_for_reply` is deliberately NOT exposed over UDS** — it would block the daemon dispatcher thread. Clients compose `request` + `poll_reply` loop client-side.

---

### Stream functions

Five methods for per-stream scalar derivatives (Lag(n), Lead(n), Delta). State is computational (not WAL-journaled).

#### `stream_fn.register`

```jsonrpc
→ {"id":N, "method":"stream_fn.register", "params": {"name": "hoof-y-delta", "kind": "Delta"}}
← {"id":N, "result": {"registered": true}}

→ {"id":N, "method":"stream_fn.register", "params": {"name": "lag-3", "kind": {"Lag": 3}}}
→ {"id":N, "method":"stream_fn.register", "params": {"name": "lead-2", "kind": {"Lead": 2}}}
```

`kind` accepts:
- `"Delta"` — current minus previous (≡ Lag(1) as diff)
- `{"Lag": n}` — emit value from n feeds ago
- `{"Lead": n}` — emit retroactive output for the event n samples earlier

Lowercase aliases `"delta"`, `{"lag": n}`, `{"lead": n}` are also accepted.

#### `stream_fn.feed`

```jsonrpc
→ {"id":N, "method":"stream_fn.feed", "params": {"name": "hoof-y-delta", "value": 12.5}}
← {"id":N, "result": {"outputs": [{"name": "hoof-y-delta", "at_event": 2, "input_value": 12.5, "fn_value": 2.5}], "warmup": false}}
   // or {"outputs": [], "warmup": true}  during the warmup window
```

#### `stream_fn.drop`, `stream_fn.list`, `stream_fn.get`

Standard lifecycle methods. See cookbook for examples.

---

### Snapshot

One method for coherent per-topic watermarks.

#### `snapshot.now`

Returns a watermark vector pinning every topic at its current `head_seq`. Used to make fusion reads observably-consistent — clients re-issue the same per-topic `events_after(topic, from_seq=watermark[topic])` to read the exact frontier the snapshot pinned.

```jsonrpc
→ {"id":N, "method":"snapshot.now", "params": {"include_watermarks": true}}
← {"id":N, "result": {
    "uri": "arcflow://snapshot/daemon?at_ms=1700000000000&topics=4&seq_sum=156",
    "topic_count": 4,
    "captured_at_ms": 1700000000000,
    "seq_sum": 156,
    "watermarks": {"events": 42, "alerts": 7, ...}
  }}
```

`include_watermarks: false` returns the URI + summary fields without the per-topic map (cheaper for URI-only callers).

---

### Cypher

One method for generic Cypher execution.

#### `cypher.execute`

Execute Cypher over the wire. Read queries route through the read-optimized engine; mutating queries route through the writer. Auto-detected from query shape; can be overridden with `mode`.

```jsonrpc
→ {"id":N, "method":"cypher.execute", "params": {
    "query": "MATCH (n:User) WHERE n.id = $target RETURN n.name LIMIT 10",
    "params": {"target": 42},     // optional, JSON object
    "mode": "auto"                 // optional: "auto" | "read" | "write"
  }}
← {"id":N, "result": {
    "columns": ["n.name"],
    "rows": [["Alice"], ["Bob"]],
    "row_count": 2,
    "gqlstatus": "00000",
    "mutating": false
  }}
```

`mode: "read"` rejects mutating queries with `MALFORMED_PARAMS`. `mode: "write"` forces writer routing even on non-mutating queries (no-op for reads; forward-compat with explicit transaction control).

`rows` is column-major-friendly arrays (`Vec<Vec<Value>>`) in column order. Cell values are best-effort typed (int, float, bool, null, nested object/array), falling back to strings.

`gqlstatus` follows ISO/IEC 39075:2024 — `"00000"` (success with rows), `"02000"` (success with zero rows). Errors return via the JSON-RPC error envelope.

CALL procedures (e.g., `CALL algo.fusion.weighted_centroid(...)`) work via the same method.

---

## Error codes

Protocol-level error codes (shared across all methods):

| Code | Meaning |
|---|---|
| `MALFORMED_PARAMS` | Required parameter missing or wrong type; daemon validation rejected before reaching the store |
| `INVALID_JSON` | Request line was not valid JSON |
| `UNKNOWN_METHOD` | `method` not in the dispatch table |
| `INVALID_PAYLOAD_SHAPE` | `data` or `headers` violated the flat-property contract |
| `CONNECTION_LIMIT` | Daemon at max connections — back off and retry |

Method-specific error codes are documented per-method in the per-method sections above; common examples:

| Code | Method family | Meaning |
|---|---|---|
| `TOPIC_NOT_FOUND` | topic.* | Named topic doesn't exist |
| `TOPIC_ALREADY_EXISTS` | topic.create | Duplicate name |
| `CONSUMER_NOT_FOUND` | consumer.* | Named consumer doesn't exist |
| `REQUEST_NOT_FOUND` | reply, poll_reply, cancel_request | Unknown correlation_id |
| `REQUEST_ALREADY_RESOLVED` | reply | Request has a reply already |
| `REQUEST_TIMED_OUT` | reply | Request's deadline passed before this reply arrived |
| `REQUEST_TOPIC_EMPTY` | request | Empty topic name |
| `REQUEST_TIMEOUT_ZERO` | request | timeout_ms == 0 |
| `STREAM_FN_NOT_FOUND` | stream_fn.feed | Named stream-fn not registered |
| `INVALID_STREAM_FN_N` | stream_fn.register | Lag/Lead n must be >= 1 |
| `UNIQUE_CONSTRAINT_VIOLATION` | topic.publish, cypher.execute | Unique constraint blocked the write |
| `INVALID_CYPHER_SYNTAX` | cypher.execute | Parse error |
| `STALE_LEASE_TOKEN` | (sharded writes) | INV-15 fencing — your writer handle is stale; re-acquire lease |

Every error response carries `code` + `message`. The code is stable across minor versions; the message is human-readable detail that may be refined.

---

## Versioning

This document specifies `v1` of the protocol.

**Within v1:**

- **Patch versions** (`v1.0` → `v1.0.1`) — clarifications to the spec; no wire change.
- **Minor versions** (`v1.0` → `v1.1`) — additive: new methods, new optional parameters, new error codes, new response fields. Existing clients continue to work unchanged. Servers may advertise the supported minor version in `daemon.info`.
- **Backwards-incompatible changes** require a major version bump (`v1` → `v2`). When a major version is published, the prior major version is supported for at least 180 days from the announcement (typical: 12 months). During co-existence, servers may speak both versions on different sockets or via a version-negotiation handshake.

**Spec lifecycle:**

- This file (`docs/protocol/jsonrpc-v1.md`) is the canonical v1 spec.
- A future v2 spec would live at `docs/protocol/jsonrpc-v2.md` with a co-existence period documented.
- Material changes to this file are announced on release notes.

---

## Reimplementation

The protocol described in this document is **open** under the Apache 2.0 license (see end of file). Anyone may implement a daemon serving this protocol. We do not assert proprietary rights over the wire format itself.

Client SDKs talking this protocol are in this repo:
- TypeScript: [`typescript/`](../../typescript/)
- Python: planned RAM-C2 / 2026-Q3 (public PyPI publish pending)
- Shell: `arcflow rpc --socket /path '{"method":"...","params":{...}}'`
- Rust crate: planned 2026-Q4
- Node napi-rs: planned 2026-Q3

If you implement a competing server, contact us at gudjon@oz.com if you'd like your implementation listed alongside this spec.

---

## Stability commitment

**This protocol is the public contract.** Closed-source engine implementation, open-source protocol surface. Paid-tier features in ArcFlow Cloud (managed hosting, distributed clusters, premium algorithms, enterprise governance) do **not** change the protocol — they add capacity, observability, or wire-compatible extensions under new method namespaces.

A user of ArcFlow today, building against this v1 protocol, can:

- Switch to a self-hosted daemon at any time without code changes
- Verify the daemon binary they run matches a specific source SHA via sigstore attestations
- Rebuild the daemon from source themselves (per the engine's reproducible-build instructions) and verify the binary they get is byte-identical to what we ship
- In principle, fork the protocol implementation and run their own competing daemon

Lock-in escape valves are explicit. The product earns its keep on engine quality + cookbook ecosystem + paid-tier value, not on you being stuck.

---

## License of this document

```
Copyright (c) 2026 OZ Global Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

Apache 2.0 is chosen over MIT for this document specifically because of the explicit patent grant — relevant for graph-algorithm protocol features that may be related to patent applications. The MIT-licensed cookbook and SDK source files are unaffected.

---

## Timeline

- **2026-05-13** — v1 spec published. 49 methods documented. Closes the federation thread CHK-AF-2026-05-13-004 + -005 + AF-CHK-2026-05-13-001 (engine-side ship sequence).
- **Earlier** — protocol grew organically from 30 methods (D-EDGE-14.B..H + I delivery) to 49 over the 2026-05-12 / 2026-05-13 SWMR + multi-writer + cypher.execute work. This file is the first formal external publication.
