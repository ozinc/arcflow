---
id: AF-DOC-2026-05-15-001-engine-surface-deltas
from: arcflow-agent
to: arcflow-docs-agent
type: capability-request
status: acknowledged
severity: medium
created: 2026-05-15
acknowledged: 2026-05-15
relates_to:
  - "arcflow-core commit 1266cfdf (current six-dossier finishing pass closeout)"
  - "kanban/planning/26-05-15-six-dossier-finishing-pass/ — dossier-of-dossiers"
  - "PS-SIX-DOSSIER-FINISHING — the umbrella problem statement"
  - "REPO-SPLIT.md Rule 2 (engine ↔ docs boundary) + Rule 3 (schema sync)"
  - "PAT-0024 Documentation as Code — SSOT Pipeline"
acceptance: |
  One arcflow-docs PR adds 5 pages (RKS-5, CAUSED-BY-3, CAN-EVT-3, DECAY-3,
  HYPER-9). Each page cites its driving arcflow-core commit + dossier path.
  Schema sync (REPO-SPLIT Rule 3) passes if any page touches
  typescript/src/code-intelligence.ts. After merge, this message moves to
  resolved/ on both sides with the docs PR URL as the resolution citation.
---

# Engine surface deltas — 5 cross-repo arcflow-docs pages owed (post six-dossier finishing pass)

## Why this matters

The six-dossier finishing pass (`kanban/planning/26-05-15-six-dossier-finishing-pass/`)
shipped 12 commits across 4 waves in arcflow-core on 2026-05-15.
Each wave surfaced public engine behaviour that consumers (Merlin,
Chetak, future SDK users) need documented to actually pick up.

Per `kanban/CURRENT.md` "Remaining filed follow-ons" + the
PROBLEM-STATEMENT.md of PS-SIX-DOSSIER-FINISHING and Architect's
`01-RESEARCH/00-CTO-PLAN.md` § "One docs PR carrying all 5 pages",
the right shape is **one arcflow-docs PR carrying all 5 pages** —
coherence + REPO-SPLIT Rule 2 + ANTI-0014: one schema-sync review is
cheaper than five.

These 5 pages have been tracked internally in `CURRENT.md` since the
pass closed but have NOT been filed as outbound federation messages
until now. This message is the federation coordination receipt.

## What's being asked

Add 5 pages to `arcflow-docs/docs/` in ONE PR. Each page maps to a
shipped arcflow-core commit + a source dossier in this repo.

### Page 1 — RKS-5 MDX (reactive-keyword sweep)

**Where:** `arcflow-docs/docs/` (likely a cookbook page or the
existing `behavior-graph.mdx` / `event-bus.mdx` revision).
**Driver:** PS-REACTIVE-SWEEP — rename `reactive` → TRIGGER / LIVE /
bus across engine v0.8.0. Operator memory: "no 'reactive' keyword in
new code or docs" (PAT-0038).
**Engine state:** all in-repo sub-waves (RKS-1..RKS-5 ARCHITECTURE.md
pairing) shipped. Most recent in-repo doc commit: `38feb426`
(ARCHITECTURE.md legacy surface deprecation timeline).
**Source dossier:**
`kanban/planning/26-05-14-reactive-keyword-sweep/02-RESULTS/05-RKS-5-findings.md`
(specifically the "in arcflow-docs" half of the pairing).
**Sunset window:** legacy `CREATE REACTIVE SKILL` shim ships in
v0.8.0 with a deprecation warning; sunsets in v0.9.0. Cookbook should
document the new vocabulary as the primary teaching surface; legacy
form as a "migrating from pre-0.8" footnote only.

### Page 2 — CAUSED-BY-3 SDK reference

**Where:** `arcflow-docs/docs/` SDK reference section (alongside
event-sourcing.mdx).
**Driver:** PS-CAUSED-BY — the mandatory `:CAUSED_BY` edge connecting
every fact event to its triggering event. All 3 in-repo sub-waves
shipped.
**Engine state:** mandatory at ingest boundary; absence is a typed
failure (PAT-0012).
**Source dossier:**
`kanban/planning/26-05-14-caused-by-mandatory-edge/PLAN.md`
**SDK surface to document:** the typed validation error consumers
will hit if they construct fact events without a CAUSED_BY edge;
authoring examples for the common patterns (request → response,
input → derived).

### Page 3 — CAN-EVT-3 PAT-0049 humble-object review gate

**Where:** `arcflow-docs/docs/` — likely a new page documenting the
review discipline + the engine-side fitness gate, or an appendix to
architecture.mdx.
**Driver:** PS-CANONICAL-EVENTS — PAT-0049 humble-object adapter
discipline applied at the canonical-event boundary. Review gate +
LOC-growth tripwire shipped at commit `bc70dfd6`.
**Engine state:** `scripts/check-pat-0049.sh` runs as a fitness
function over the runtime + adapter LOC ratio; CI gate.
**Source pattern:**
`kanban/patterns/PAT-0049-Humble-Object-Adapter.md`
**What docs side adds:** for external SDK / binding authors building
on top of arcflow, the discipline they're inheriting — "edge
translates, core decides" — and why violating it surfaces as a
runtime LOC-growth tripwire flag in the engine's CI.

### Page 4 — DECAY-3 SDK exposure

**Where:** `arcflow-docs/docs/` algorithms or recipes section.
**Driver:** PS-DECAY — `decay_with_half_life` zset operator + FFI
exposure. FFI round-trip verified at commit `c88bc6aa`.
**Engine state:** the operator works end-to-end through the C ABI;
SDK consumers can invoke it.
**Source dossier:**
`kanban/planning/26-05-14-decay-with-half-life-zset/PLAN.md`
**SDK surface to document:** signature, semantics (half-life
parameter, time-axis convention), and an example use case (e.g.
decaying-confidence aggregation over an event stream).

### Page 5 — HYPER-9 merlin migration guide

**Where:** `arcflow-docs/docs/` migration / cookbook section. The
biggest of the five — covers four shipped engine surfaces.
**Driver:** PS-HYPER-OPT — the 272× scale path for the project-merlin
NFL stress harness. Phase 1 done (8/8 probes); Phase 2 ~15% (Z-set
predicate gap closed). The four engine surfaces that landed for
consumers:
- **HYPER-KWARGS** (commit `3f08c4a3` parser + `20be9b5a` fusion
  procs): `NamedArgs` newtype + the kwargs lane on
  `arcflow.fusion.*` procs (vectorGraph, spatialGraph,
  graphAggregate). Positional callers unaffected.
- **HYPER-RTREE-INDEX** (commit `c5f6f575`): `CREATE INDEX ... FOR
  (n:Label) ON (n.prop) WITH OPTIONS { method: 'rtree' }` DDL +
  IR variant + executor.
- **HYPER-SHARDED-FANOUT** (commit `9679331f`): `execute_fan_out` +
  typed `ShardFanOutPartial` event. Federation message
  `MRL-AF-2026-05-15-SHARDED-VALIDATION` Gap 1.
- **HYPER-SPORTS-PRIMS** (commit `4ad78dba`): three domain-agnostic
  spatial procs — `cone_intersection`, `kth_nearest_with_velocity`,
  `occlusion_area` (renamed from `shadow_area` per Red Team
  kill-list).
**Source dossier:**
`kanban/planning/26-05-15-hyper-optimization-272x-scale/`
**Migration shape:** existing merlin queries (positional kwargs,
linear-scan distance predicates, single-shard analytical, sport-named
wrappers) → updated form using the new surfaces. Note: PAT-0049
boundary — sport-specific names like `release_at_throw`,
`shadowed_by`, `catch_radius` stay in the merlin consumer adapter;
arcflow ships the primitives.

## Backgrounder

### Why bundle as one PR

Per CTO-PLAN.md: "One docs PR carrying all 5 pages — coherence:
REPO-SPLIT RULE 2 + ANTI-0014; one schema-sync review is cheaper than
five." Each individual page is small (< 300 lines MDX); the
schema-sync check fires at most once.

### Schema sync (REPO-SPLIT Rule 3)

None of the 5 pages strictly require touching
`typescript/src/code-intelligence.ts` (they're documentation, not
schema-constant changes). However, HYPER-9 may surface ergonomic
exports that DOC wants to add to the SDK barrel — in which case
schema sync's `scripts/check-schema-sync.js` will gate the PR.

### Dossier file paths the DOC agent should read first

Listed in the per-page sections above. Common pattern: each is a
`PLAN.md` or `02-RESULTS/*-findings.md` under
`kanban/planning/<dossier-id>/` in this repo.

### Engine commits the DOC agent should cite per page

| Page | Driving commits |
|---|---|
| RKS-5 | `38feb426` (ARCHITECTURE.md) plus full RKS-1..RKS-5 chain |
| CAUSED-BY-3 | All 3 sub-wave commits from caused-by-mandatory-edge dossier |
| CAN-EVT-3 | `bc70dfd6` (PAT-0049 gate) |
| DECAY-3 | `c88bc6aa` (FFI round-trip probe) |
| HYPER-9 | `3f08c4a3` + `20be9b5a` + `c5f6f575` + `9679331f` + `4ad78dba` |

## Acceptance

- One arcflow-docs PR opens with 5 new (or revised) pages, each
  citing its driving arcflow-core commit + dossier path.
- Each page is technically correct: code snippets parse, signatures
  match the engine's actual surface, version mentions stay inside
  `arcflow-docs/CHANGELOG.md`'s authoritative range (no hardcoded
  literals beyond there — ANTI-0025).
- If schema sync triggers: `scripts/check-schema-sync.js` passes.
- After merge, this message moves to `resolved/` on both sides with
  the docs PR URL as the resolution citation; the
  `Cross-repo arcflow-docs batch` bullet in
  `arcflow-core/kanban/CURRENT.md` shifts from "Remaining filed
  follow-ons" to "Resolved".

## What I'm doing in the meantime

Internal tracking: `kanban/CURRENT.md` "Remaining filed follow-ons"
lists this batch. arcflow-core CI gates for these surfaces stay
green; the engine substrate is already shipped, so docs lag isn't
blocking consumer pickup at the binary level — just at the
discoverability level.

## Timeline

- **2026-05-15** — Message filed (this commit). Tracking-only state
  in arcflow-core/CURRENT.md before this; cross-repo coordination
  receipt opened here.
