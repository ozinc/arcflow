# Rust SDK · Spatiotemporal Tactical Queries

The same three pattern queries as the Python version (`../`), routed
through the shipped Rust SDK surface. The Rust-only payoff for this
recipe: `register_skill` on entity-resolution mutations for live
cross-source-disagreement alerts, and `provenance_chain(&db, node_id)`
walking the source attribution of any resolved entity in one call.

## When the Rust version pays off

- **Live ER disagreement alerts.** `register_skill(NodeCreated{Entity},
  cross_source_check)` fires the cross-source predicate every time a
  new Entity (or new identifier) is added — the agent learns about a
  collision the moment it appears, not on the next polling tick.
- **One-call provenance walks.** `arcflow_sdk::provenance_chain(&db,
  entity_node_id)` returns the ancestry through DERIVED_FROM / SOURCE
  / EXTRACTED_FROM edges up to depth 10. Implementing the same in
  Python takes a hand-rolled multi-hop MATCH chain per call.
- **`AS OF seq` against a `JournaledStore`.** For replays spanning
  process restarts (months of WAL), the persistent variant gives the
  same query language without needing to keep the source live.

## Run

```bash
cargo run --release --bin 01-counterfactual-replay
cargo run --release --bin 02-confidence-entity-resolution
cargo run --release --bin 03-observed-vs-predicted
```

## Cargo layout

```
rust/
├── Cargo.toml
├── src/
│   ├── lib.rs                              # 22 entities + multi-namespace IDs + planted disagreement
│   └── bin/
│       ├── 01-counterfactual-replay.rs     # AS OF seq replay
│       ├── 02-confidence-entity-resolution.rs # cross-namespace ER
│       └── 03-observed-vs-predicted.rs     # calibration analysis
```
