# Rust SDK · Sensor Fusion with Trust-Weighted Live Alerts

The same three-step recipe as the Python version (`../`), routed
through the shipped Rust SDK surface. Step 04 is the headline upgrade:
where Python polls (no `CREATE LIVE VIEW` from Python yet), Rust
registers the trust-weighted fusion as a maintained view, subscribes to
push-based deltas, and attaches a continuous proof catching sensor
dropout the moment it happens.

## When the Rust version pays off

- **Frame-time alert latency.** `CREATE LIVE VIEW` + `subscribe` means
  the agent gets the updated weighted mean within ~20 ms of any new
  Reading, regardless of how many sensors the fleet has. Polling
  re-traverses the whole graph every tick.
- **Sensor-dropout early warning via continuous proof.**
  `register_live_proof(view, NonEmpty)` FAILs immediately if the
  fusion view goes empty — the agent learns the moment a sensor stops
  reporting, not at the next polling boundary.
- **In-process at low latency.** No FFI marshalling tax, no GIL on the
  alert path. Multi-agent shared state works directly: multiple Rust
  agents in one process can subscribe to the same view, each receiving
  its own delta stream.

## Run

```bash
cargo run --release --bin 02-load-stream
cargo run --release --bin 03-trust-weighted-alerts
cargo run --release --bin 04-live-views-and-subscribe
```

## Cargo layout

```
rust/
├── Cargo.toml
├── src/
│   ├── lib.rs                          # 3 robots × 2 sensors × 100 frames
│   └── bin/
│       ├── 02-load-stream.rs           # bulk-load mirror
│       ├── 03-trust-weighted-alerts.rs # fusion query, one MATCH
│       └── 04-live-views-and-subscribe.rs # CREATE LIVE VIEW + subscribe + proof
```
