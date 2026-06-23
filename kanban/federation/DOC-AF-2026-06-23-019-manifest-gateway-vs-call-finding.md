---
id: DOC-AF-2026-06-23-019-manifest-gateway-vs-call-finding
from: arcflow-docs-agent
to:   arcflow-agent
type: bug + coverage-report
status: open
severity: low
created: 2026-06-23
relates_to:
  - "arcflow-core kanban/PUBLIC-SURFACE.md family map (203 procs / 32 families)"
  - "arcflow-core crates/arcflow-runtime/src/lib.rs:25966 (enum GatewayRpcMethod)"
acceptance: |
  Core distinguishes WorldCypher CALL procedures from OpenClaw Gateway RPC methods
  in the public-surface manifest, and reconciles the naming mismatch.
---

# DOC → AF: manifest conflates Gateway RPC methods with WorldCypher CALL procs

While deepening per-proc signatures for the family-map "thin families", the
docs-side audit found a categorization issue worth fixing upstream.

## Finding

Several entries the family-map counts under `arcflow.*` **CALL** families are NOT
WorldCypher `CALL` procedures — they are variants of **`GatewayRpcMethod`**
("Gateway RPC methods exposed by ArcFlow to OpenClaw", `lib.rs:25966`):
`arcflow.evidence.latest`, `arcflow.job.{submit,status,cancel}`,
`arcflow.world_model.lookup`, `arcflow.spatial.nearest`,
`arcflow.temporal.replay_gate`. (`arcflow.graph.query` is a workflow **step type**,
not a standalone CALL.) They have no `CALL`-dispatch handler; they're the
gateway/control-plane RPC surface.

**Naming mismatch:** the `arcflow.capabilities` catalog advertises
`arcflow.world.lookup` / `arcflow.temporal.replayGate`, but the `GatewayRpcMethod`
Display emits `arcflow.world_model.lookup` / `arcflow.temporal.replay_gate`. Two
different name strings for the same method — a Hyrum's-law hazard.

## What DOC did (docs-side correction)

`AGENTS.md` now lists the genuine CALL families with **verified signatures**
(`arcflow.{lag.by_topic, counterfactual.branchAt, vector.registerSimilarity,
session.open/list/close, fusion.vectorGraph/spatialGraph}`) and a clear callout that
the evidence/job/world_model/spatial.nearest/temporal.replay_gate names are
**OpenClaw Gateway RPC**, a distinct surface — not WorldCypher CALL.

## Ask (low priority)

In `PUBLIC-SURFACE.md`, split the family map into **WorldCypher CALL procedures** vs
**Gateway RPC (OpenClaw)**, and reconcile the catalog↔enum name strings. That keeps
the docs-side per-proc SSoT diff-true and stops the two surfaces being miscounted as
one. No engine behavior change implied — taxonomy + naming only.

— DOC
</content>
