# Rust SDK · Algo-Trading World Model

The same three-step recipe as the Python version (`../`), routed through
the shipped Rust SDK surface. The first two steps are identical in shape;
**step 2 escapes the Python polling fallback** — it uses `CREATE LIVE
VIEW` + `arcflow_sdk::subscribe(&db, "view_name")` to receive
push-based delta updates within ~20 ms of any mutation, instead of
re-executing the queries on each tick. **Step 3 attaches a continuous
proof** to the fusion view, so divergence between the maintained result
and a batch recompute is caught the moment it happens.

## What's different from the Python recipe

| Pattern | Python today | Rust today |
|---|---|---|
| `AS OF seq` replay | ✓ (`db.execute(q, params={"s": seq})`) | ✓ same shape, plus `JournaledStore` for durable WAL across restarts |
| Window functions in queries | ✓ | ✓ |
| Two-tier ingest | ✓ | ✓ |
| `CREATE LIVE VIEW` + maintained results | ✗ (polling fallback) | **✓** |
| `subscribe(view) -> DeltaReceiver` | ✗ | **✓** |
| `register_live_proof(view, NonEmpty)` continuous proof | ✗ | **✓** |
| In-process, no FFI marshalling cost | ✗ (JSON via the C ABI) | **✓** |

The fixture (`src/lib.rs`) and query strings are intentionally identical
to `_load.py` and the Python step scripts — same 8 symbols, same 60
days, same restatement landmine, same multi-source predicted layer. The
binding swap is the *only* difference; that's the point.

## Run

```bash
cargo run --release --bin 01-persistent-memory
cargo run --release --bin 02-orchestrated-live-context
cargo run --release --bin 03-confidence-weighted-fusion
```

## Cargo layout

```
rust/
├── Cargo.toml                              # arcflow-sdk via git, tokio, rand
├── src/
│   ├── lib.rs                              # make_db() — shared fixture
│   └── bin/
│       ├── 01-persistent-memory.rs         # AS OF seq replay
│       ├── 02-orchestrated-live-context.rs # CREATE LIVE VIEW + subscribe
│       └── 03-confidence-weighted-fusion.rs # fusion view + register_live_proof
```

## When to pick Rust over Python

- Latency-sensitive agent loops where per-tick polling round-trips
  matter (in-process Rust is microsecond-scale; Python via FFI is
  millisecond-scale once JSON marshalling and the GIL are paid).
- LIVE views with confidence-aware continuous proof — the maintained-vs-
  batch divergence check is the structural answer to "my backtest
  doesn't match live."
- Multi-agent shared state — multiple Rust agents in the same process
  reading/writing one `ConcurrentStore` with full provenance of who
  changed what when.
- Cases where `db.subscribe(view, callback)` would be the Python shape
  — you can have that today in Rust.
