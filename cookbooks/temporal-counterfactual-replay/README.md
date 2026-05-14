# Temporal Counterfactual Replay

> **`AS OF seq` — the temporal-replay primitive — applied across three
> domains: fraud audit, robotics control review, IoT alarm triage.**

**Audience:** python · data-engineer · compliance · agent
**Runtime:** under 1 minute total
**Pins:** `oz-arcflow==0.7.2`

Three small standalone scripts demonstrating the same pattern in three
different contexts. A system makes a decision based on world-model
state at some moment; time moves on; an investigator needs to
reconstruct exactly what was visible at decision time.

## The four hard problems this addresses

Counterfactual replay — *"what did the system see when it made that
decision?"* — is a question every audit-bound system needs to answer,
and most can't. Four failures the bespoke audit pipeline ships in
production:

1. **Current-state-only databases need a parallel audit log.** Standard
   databases answer "what does it look like now?" Reconstructing past
   state requires an audit table (or event-sourcing pipeline) that has
   to be kept in sync with every mutation. The audit table drifts the
   moment someone forgets to update it, fixes a typo without logging,
   or schema-migrates without replaying. The bug surfaces months later
   when the auditor asks a question the audit table can't answer.

2. **Event-sourcing pipelines need bespoke replay code.** Even a
   well-maintained event log doesn't answer "what did this entity look
   like at moment T" — it answers "here is the sequence of events." A
   replay tool has to be written per event type, kept in sync with
   every schema change, and re-validated every time the underlying
   model changes. `AS OF seq $param` against a WAL-backed graph reads
   the past state directly with the same query language used for the
   present.

3. **Decision-time state is multi-table; replay is multi-pipeline.** A
   fraud decision read the customer profile, the transaction history,
   the merchant risk, and the device fingerprint — four tables, four
   replay pipelines, four chances for one to drift. The graph version:
   the same MATCH chain over the same edges, with one `AS OF seq`
   keyword saying "evaluate against the past."

4. **Per-property audit granularity requires per-property logging.**
   "Did the engineer change `eps` before flipping the `revision` flag,
   or after?" requires per-property audit log entries that most
   audit-table schemas don't maintain. ArcFlow's WAL records one seq
   per `execute()` call — split the multi-property update into
   multiple `execute()` statements (each gets its own seq) and the
   intermediate state is fully replayable. Comma-`SET` within a single
   statement is atomic and gets one seq; the choice is the engineer's,
   not the audit-system's.

## Three patterns this recipe ships

| Recipe | Domain | Question |
|---|---|---|
| `01-fraud-decision-audit.py` | Banking / fraud | "What was the customer's risk score when the transfer was approved?" |
| `02-robotics-control-replay.py` | Robotics safety | "What did the robot's perception show when the avoid-action fired?" |
| `03-iot-trigger-replay.py` | Smart building / IoT | "What did the other sensors say when this alarm fired — real event or calibration drift?" |

Same primitive, three contexts. Pick the one that matches your domain
and adapt the schema.

## Run

```bash
uv sync
uv run python 01-fraud-decision-audit.py
uv run python 02-robotics-control-replay.py
uv run python 03-iot-trigger-replay.py
```

Each script is self-contained — no shared loader, no fixture files.
The scripts use `execute()` throughout so the AS OF replay path is
clean; see [`spatiotemporal-tactical-queries`](../spatiotemporal-tactical-queries/)
for the bulk-load pattern alongside.

## Engine context

- `AS OF seq` requires a persistent (`data_dir`) ArcFlow instance —
  the in-memory form has no WAL. Each recipe creates and cleans up a
  temp directory.
- Each `execute()` call advances the WAL by exactly one monotonic seq.
  For fine-grained per-property audit trails, write each property
  update as its own `execute()` statement (each gets its own seq).
  Comma-`SET` within a single statement is atomic and gets one seq.

## Capabilities exercised

| Capability | What it does for decision audit |
|---|---|
| `MATCH (n) AS OF seq $param RETURN n` | Replay the world model at any past WAL seq — same query language, exact past-state reconstruction |
| Persistent `JournaledStore` | Durable WAL survives process restarts; replay works months after the original session |
| One seq per `execute()` call | Engineer controls audit granularity — multiple statements for per-property trail, comma-SET for atomic update |
| Same MATCH chain reads present and past | No separate replay pipeline; no per-event-type tool to maintain |

## Rust SDK alongside

The `rust/` subfolder ships the same three patterns via the Rust SDK
with `JournaledStore` for durable WAL backing — and the Rust-only
payoff: `provenance_chain(&db, node_id)` walks ancestry through
DERIVED_FROM / SOURCE / EXTRACTED_FROM edges in one call, the kind of
"trace the fact back to its source" question every audit ends with.

## See also

- [`spatiotemporal-tactical-queries`](../spatiotemporal-tactical-queries/) — temporal replay alongside confidence-weighted ER and observed-vs-predicted fusion
- [`algo-trading-world-model`](../algo-trading-world-model/) — `AS OF seq` as the audit trail for an LLM-driven trading agent
- [`fraud-graph-traversal`](../fraud-graph-traversal/) — multi-hop AML pattern detection that pairs naturally with audit-time replay
