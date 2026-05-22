# Rust SDK · Temporal Counterfactual Replay

The same three patterns as the Python version (`../`) — fraud decision
audit, robotics control replay, IoT alarm triage — routed through the
shipped Rust SDK surface. Each binary is self-contained and uses
in-memory `ConcurrentStore`; for durable WAL across process restarts,
swap in `JournaledStore` at the open site.

## When the Rust version pays off

- **Durable replay across process restarts.** `JournaledStore` keeps
  the WAL on disk — replay queries work months later from a cold
  start, with no application-layer state to rehydrate.
- **`provenance_chain()` walks ancestry in one call.** Every audit
  ends with *"trace the fact back to its source"* — through
  DERIVED_FROM / SOURCE / EXTRACTED_FROM edges. The Rust SDK exposes
  this as one function; the Python equivalent requires a hand-rolled
  multi-hop MATCH chain.
- **In-process audit alongside live operation.** Multi-agent stacks
  can have one Rust agent processing decisions on the live graph
  while another runs replay queries against past seqs — same store,
  no IPC.

## Run

```bash
cargo run --release --bin 01-fraud-decision-audit
cargo run --release --bin 02-robotics-control-replay
cargo run --release --bin 03-iot-trigger-replay
```

## Cargo layout

```
rust/
├── Cargo.toml
└── src/
    └── bin/
        ├── 01-fraud-decision-audit.rs    # risk score AS OF decision time
        ├── 02-robotics-control-replay.rs # perception state at avoid fire
        └── 03-iot-trigger-replay.rs      # cross-sensor at alarm time
```
