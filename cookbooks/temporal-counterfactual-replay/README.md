# Temporal Counterfactual Replay

**What you'll build:** Three small standalone scripts demonstrating
`AS OF seq <param>` — the temporal-replay primitive — across three
domains: fraud audit, robotics control review, IoT alarm triage. Each
shows the same pattern: a system makes a decision based on world-model
state at some moment, time moves on, and an investigator needs to
reconstruct exactly what was visible at decision time.

**Audience:** python, data-engineer, compliance, agent.

**Runtime:** under 1 minute total.

## Why this pattern matters

Most data systems answer "what does it look like now?" Auditors,
debuggers, and compliance reviewers need a different question: **what
did it look like THEN?** Logs and event-sourcing pipelines can
reconstruct that, but only with bespoke tooling and only if every
relevant fact was logged.

ArcFlow's WAL is the world model's history. Every `execute()` mutation
advances the seq by one. `MATCH (n) AS OF seq $param RETURN n` is a
deterministic, bit-for-bit replay of the world model at any past seq —
no separate audit table, no event-replay pipeline.

The same query syntax. A different time.

## The three recipes

| Recipe | Domain | Question |
|---|---|---|
| `01-fraud-decision-audit.py` | Banking / fraud | "What was the customer's risk score when the transfer was approved?" |
| `02-robotics-control-replay.py` | Robotics safety | "What did the robot's perception show when the avoid-action fired?" |
| `03-iot-trigger-replay.py` | Smart building / IoT | "What did the OTHER sensors say when this alarm fired? (real or calibration drift?)" |

Same primitive, three contexts. Pick the one that matches your domain
and adapt the schema.

## Run

```bash
uv sync
uv run python 01-fraud-decision-audit.py
uv run python 02-robotics-control-replay.py
uv run python 03-iot-trigger-replay.py
```

Each script is self-contained — no shared loader, no fixture files. The
scripts use `execute()` throughout (no bulk_create_*) so the AS OF
replay path is clean; see the related cookbook
[`spatiotemporal-tactical-queries`](../spatiotemporal-tactical-queries/)
for the bulk-load pattern alongside.

## Engine context

- AS OF seq requires a persistent (`data_dir`) ArcFlow instance — the
  in-memory form has no WAL. Each recipe creates and cleans up a temp
  directory.
- `execute()` mutations are WAL-tracked (and thus replayable). A
  comma-separated `SET d.a = 1, d.b = 2` produces **two** WAL entries,
  not one — fine-grained per-property audit.

## See Also

- [`spatiotemporal-tactical-queries`](../spatiotemporal-tactical-queries/) — temporal replay alongside confidence-weighted ER and observed-vs-predicted fusion.
- [Temporal Queries](/temporal) — full reference for `AS OF seq` semantics.
- [Snapshot-Pinned Reads](/concepts/snapshots) — content-addressed snapshot URIs for citing exact world-states in reports.
