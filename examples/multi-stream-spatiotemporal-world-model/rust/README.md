# Rust SDK · Multi-Stream Spatiotemporal World Model

Four high-leverage steps from the Python recipe (`../`), routed through
the shipped Rust SDK surface — including the LIVE VIEW + `subscribe` +
`register_skill` + `register_live_proof` surfaces the Python binding
can't reach today.

| Binary | What it shows |
|---|---|
| `04-tracking-bulk-load` | Build the canonical Session + Frame + Entity + OBSERVED_AT substrate; spatial coordinates on the edge property |
| `07-spatial-queries` | KNN / radius / bbox queries via the R*-tree over edge properties (sub-millisecond regardless of session size) |
| `09-live-views-and-subscribe` | `CREATE LIVE VIEW` + `arcflow_sdk::subscribe(&db, view)` — push-based deltas within ~20 ms of any mutation |
| `10-triggers-and-skills` | `register_skill(NodeCreated{Frame}, proximity_query)` for per-frame live analytics + `register_live_proof(NonEmpty)` for sensor-dropout detection |

## When the Rust version pays off

- **Sub-frame standing-query latency.** The Python recipe polls; the
  Rust recipe subscribes. At 60 Hz tick, the maintained-result delta
  arrives within ~20 ms of any mutation, faster than the next frame.
- **Event-driven skills, no scheduler.** `register_skill` fires the
  named query on every mutation matching the trigger. The proximity
  query in `10-triggers-and-skills` runs against every new Frame; the
  formation/collision/hand-off analytics writes itself.
- **Continuous proof on the substrate.** `register_live_proof(view,
  NonEmpty)` catches sensor dropout the moment a frame goes empty —
  before downstream analytics surface confused output.
- **In-process, no FFI marshalling.** Rust SDK runs the bulk-load,
  spatial-query, and live-view paths without the JSON marshalling
  tax the Python binding pays per call.

## Run

```bash
cargo run --release --bin 04-tracking-bulk-load
cargo run --release --bin 07-spatial-queries
cargo run --release --bin 09-live-views-and-subscribe
cargo run --release --bin 10-triggers-and-skills
```

## Cargo layout

```
rust/
├── Cargo.toml
├── src/
│   ├── lib.rs                          # 22 entities × 60 frames substrate
│   └── bin/
│       ├── 04-tracking-bulk-load.rs    # Session/Frame/Entity/OBSERVED_AT
│       ├── 07-spatial-queries.rs       # KNN, radius, bbox
│       ├── 09-live-views-and-subscribe.rs # LIVE VIEW + subscribe
│       └── 10-triggers-and-skills.rs   # register_skill + register_live_proof
```
