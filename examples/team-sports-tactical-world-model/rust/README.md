# Rust SDK · Team-Sports Tactical World Model

The same three-step tactical recipe as the Python version (`../`), routed
through the shipped Rust SDK surface. Reaches the live-alert surface that
Python can't today: `arcflow_sdk::register_skill(&db, "tactics",
"pressing-alert", NodeCreated{"Position"}, query)` fires the named
pattern query every time a position mutation matches the trigger — no
polling loop, frame-time latency.

## When the Rust version pays off

- **Live tactical alerts during a match.** `register_skill` fires on
  every relevant mutation. The pressing-alert query computes the
  defender-within-radius count and surfaces the alert the same frame
  the conditions are met. The polling fallback the Python recipe uses
  re-executes the query on a timer — fine for replays, not fine for
  real-time.
- **Frame-time multi-agent coordination.** Multiple Rust agents in the
  same process can share one `ConcurrentStore` — one writes positions
  from the tracker, another reads tactical alerts via `subscribe`, a
  third writes coach-intent updates as predicted facts. Every read sees
  the same world model with full provenance.
- **`register_live_proof` on tactical views.** A `LIVE VIEW` for "active
  pressing triggers" with `ProofAssertion::NonEmpty` FAILs immediately
  if the maintained alert pipeline goes silent — early-warning for
  schema or threshold drift.

## Run

```bash
cargo run --release --bin 01-tactical-world-model
cargo run --release --bin 02-pattern-detection
cargo run --release --bin 03-tactical-replay-and-fusion
```

## Cargo layout

```
rust/
├── Cargo.toml
├── src/
│   ├── lib.rs                              # make_db() — shared fixture
│   └── bin/
│       ├── 01-tactical-world-model.rs      # substrate sanity
│       ├── 02-pattern-detection.rs         # press / line-break / compression / counter
│       └── 03-tactical-replay-and-fusion.rs # AS OF + register_skill
```
