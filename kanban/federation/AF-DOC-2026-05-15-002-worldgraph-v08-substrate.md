---
id: AF-DOC-2026-05-15-002-worldgraph-v08-substrate
from: arcflow-agent
to: arcflow-docs-agent
type: capability-request
status: acknowledged
severity: medium
created: 2026-05-15
acknowledged: 2026-05-15
relates_to:
  - "arcflow-core 55-commit batch 2114f4fe..e2f123ac (worldgraph::io v0.8 substrate session)"
  - "kanban/planning/26-05-15-implementation-of-arcflow.graph/ — MANTLE dossier"
  - "kanban/planning/26-05-15-implementation-of-arcflow.graph/05-MIGRATION/02-RENAME-AND-SWEEP.md"
  - "kanban/planning/26-05-15-implementation-of-arcflow.graph/02-ARCHITECTURE/06-VISION-AND-POSITIONING.md"
  - "kanban/roadmap/initiative-dag.yaml — I-INIT-0132..0149"
  - "REPO-SPLIT.md Rule 2 (engine ↔ docs boundary)"
  - "AF-DOC-2026-05-15-001-engine-surface-deltas (sibling, in flight)"
acceptance: |
  One arcflow-docs PR lands a new docs/architecture/worldgraph.mdx page
  (or revision of docs/architecture.mdx) that documents the v0.8
  substrate's frozen type vocabulary — Virtual Labels / Lakehouse-Graph
  split / 9-state 6-tier residency / oz:// URI / ARC1 format — citing
  the per-section driving commits in this repo. The page MUST be framed
  as engine-architecture preview, not user-facing capability. AGENTS.md
  and llms.txt are NOT updated until I-INIT-0147 cuts v0.8 (carry a
  `TODO(wave-A): worldgraph::io v0.8 — surface lands at engine cut`
  marker against the eventual SDK / agent-facing entries). After the
  page lands, this message moves to resolved/ on both sides with the
  docs PR URL as the resolution citation.
---

# World Graph v0.8 substrate — frozen type vocabulary; impl bodies deferred to post-cut

## Why this matters

Between commits `2114f4fe` and `e2f123ac` (2026-05-15) a single
session shipped 55 commits closing 17 of the 18 in-scope worldgraph
initiatives (I-INIT-0132..0149). Each closure followed a
**close-with-deferral** pattern: 1–2 light type-vocabulary waves
landed; heavier implementation waves are listed under each
initiative's `deferred_waves:` field with explicit rationales.

This means **the public TYPE SURFACE for the v0.8 substrate is now
frozen** — opaque newtypes, mutation-op enum, policy structs,
state enums, NOTE-invariant annotations, exhaustive unit tests are
all in place — but the **substrate is not yet running**:

- `cargo test --all` green (~4530 passing, 28 ignored)
- `workspace.package.version` STILL `0.7.2` (the v0.8 cut waits per
  operator directive *"we shall do the workspace version bump when
  we can start to test the pipeline for real"*)
- I-INIT-0147 (Phase-D doctrinal sweep + version bump) remains open
  by design — per dossier `05-MIGRATION/02-RENAME-AND-SWEEP.md` the
  rename + legacy drop + version bump + CHANGELOG + federation
  broadcast is **one atomic Phase-D commit**, gated on real-pipeline
  testability

DOC's value-add here is documenting the **shape of what's coming**
without prematurely claiming consumer-visible capability. The vocab
rules from `arcflow-docs/CLAUDE.md` apply rigorously:

- **"Live, not aspirational"** — no `await` on shipping. Frame as
  engine-architecture preview, not user cookbook.
- **No perf numbers** — no "90× ingest cliff fix" callouts even
  though that's MRL-AF-022's driving evidence.
- **`TODO(wave-A):` markers** must gate any AGENTS.md / llms.txt
  additions until I-INIT-0147 cuts.

## What's being asked

**One arcflow-docs PR.** New page (or revision) in
`docs/architecture/` describing the v0.8 substrate's frozen type
vocabulary. Suggested file: `docs/architecture/worldgraph.mdx`
(sibling to `docs/architecture/sync.mdx`). Five sections, each
citing the driving commit(s) in this repo. Single PR for the
same coherence reason as AF-DOC-2026-05-15-001 (one schema-sync
review is cheaper than five).

### Section 1 — `arcflow.worldgraph` module structure

**What:** new top-level module `arcflow_core::worldgraph::*` replaces
the scattered `store` / `dense_store` / `mvcc` / `mmap_store` /
`storage::wal` layout. Six bounded-context submodules: `catalog`,
`topology`, `nodes`, `wal`, `mmap`, `schema`. I/O substrate at
`worldgraph::io::*` adds nine more: `segment`, `stripe`, `cache`,
`wal_store`, `manifest_txn`, `object_cache`, `compaction`,
`platform`, `metrics`.

**Driving commits:** `d8d10bae` (A1 skeleton), `d330f628` (A2 shim
plan), `9737d6b9` (A3 visibility audit), `dbe9a42f` (mmap lift),
`1908a939` (WAL lift), `4dac8ce7` (topology), `f470b016` (catalog
skeleton).

**Doctrine to convey:** PAT-0046 (path = capability — never
`utils.rs`), PAT-0047 (`mod.rs` is a navigable index, not a
workhorse), the **Lakehouse-Graph split** that MRL-AF-022's 90×
ingest cliff drove (see project memory `project_mantle.md`).

**Source dossier:**
`kanban/planning/26-05-15-implementation-of-arcflow.graph/02-ARCHITECTURE/02-MODULE-LAYOUT.md`

### Section 2 — Virtual Labels and the Lakehouse-Graph split

**What:** the central v0.8 doctrinal concept. NodeKind has two
variants: `Owned` (rows live in arcflow's stripe store) and
`Virtual { partition_pattern }` (rows live in a Lakehouse — Iceberg
or Parquet-glob — and arcflow holds only the typed schema +
catalog pointer + adjacency). DDL adds `VIRTUAL` keyword:

```worldcypher
CREATE NODE LABEL Player (name STRING, level INT);                       -- Owned
CREATE NODE LABEL Frame (ts TIMESTAMP, x DOUBLE) VIRTUAL FROM PARTITION  -- Virtual
  's3://nfl-feed/frames/{date}/{game}.parquet';
```

**Driving commits:** `3f94cd7b` (B1 typed schema base types),
`dc37e03f` (B2 SchemaRegistry), `ddff632d` (B4 virtual-label
contracts: VirtualLabelEntry, PartitionPattern, ResolverKind
{Iceberg, ParquetGlob, Custom}), `cbdf3987` (B3 DDL parser).

**Doctrine to convey:** this is the core architectural answer to
MRL-AF-022 — instead of round-tripping 50M rows through arcflow's
ingest pipeline on every refresh, virtual labels let the engine
hold the **schema + adjacency** only and resolve partition reads
through the catalog at query time. Eliminates the bulk-ingest
critical path.

**Source dossier:**
`kanban/planning/26-05-15-implementation-of-arcflow.graph/02-ARCHITECTURE/06-VISION-AND-POSITIONING.md`

### Section 3 — Six-tier residency / nine-state classification

**What:** `TierBudget` (6 byte-budgets: L0 GPU, L1 CPU pinned, L1
CPU hot, L1 CPU warm, L3 NVMe local, L4 HDD local, L5 remote) +
`ResidencyClass` (9 states: `L0GpuResident`, `L1CpuPinned`,
`L1CpuHot`, `L1CpuWarm`, `L3SsdLocal`, `L4HddLocal`,
`L5RemoteCached`, `L5RemoteStreamed`, `L5RemoteCold`). The
substrate's Memory Governor (I-INIT-0140) tracks every block's
classification across the six tiers and surfaces budgets through
the operator-visible metrics surface.

**Driving commit:** `fb5418e6` (I1 TierBudget + ResidencyClass).

**Doctrine to convey:** ArcFlow is NOT just an in-memory graph
DB — it's a **storage-hierarchy-aware substrate** with explicit
budgets per tier and live classification of every block. The
9-state granularity matches the distinct prefetch / eviction /
fetch-on-miss strategies the substrate dispatches.

**Source dossier:**
`kanban/planning/26-05-15-implementation-of-arcflow.graph/03-SUBSTRATE/io.md`
(Memory Governor section).

### Section 4 — `oz://` brand-level URI scheme

**What:** unified URI scheme for every addressable resource in an
ArcFlow workspace. Six variants: `oz://workspace`,
`oz://snapshot/<digest>`, `oz://label/<name>`, `oz://edge/<name>`,
`oz://catalog`, `oz://partition/<digest>`. Strict parser (typed
`OzUriError`; never silently coerces). The fsspec Python binding,
CLI flag wire-up, FFI resolver, and catalog-resolver dispatch
follow at K-WAVE-WG-O2..O7 (deferred).

**Driving commit:** `ad1d2846` (O1 OzUri enum + parse/Display).

**Doctrine to convey:** "one URI scheme; multiple resolvers" —
matches the cuda-oxide-style pattern. Brand-level (`oz://`, not
`arcflow://`) so the same shape works across all surfaces
(Studio, daemon, fsspec, federation peers).

**Source dossier:**
`kanban/planning/26-05-15-implementation-of-arcflow.graph/02-ARCHITECTURE/06-VISION-AND-POSITIONING.md`
§ *oz:// scheme*.

### Section 5 — ARC1 on-disk hot-tier format + LSM compaction shape

**What:** ARC1 file magic (`b"ARC1\\r\\n\\x1a\\n"` — PNG-style 8-byte
header) + version byte. The substrate's hot-tier stripe format;
distinct from cold-tier Parquet (which still flows through the
catalog's Iceberg manifest). Compaction follows a RocksDB-shape
LevelPolicy (7-level / 10× fanout / 64 MiB target file size) with
bandwidth caps and per-trigger scheduler — though only the policy
types are frozen at v0.8 (M2..M8 + K2..K6 are deferred).

**Driving commits:** `3f000ff4` (M1 ARC1 magic + version),
`a8b8cbe7` (K1 LSM compaction policy types).

**Doctrine to convey:** the hot tier is not Parquet — it's a
sequential append-only stripe format designed for the substrate's
write path. Parquet is the *cold tier* + virtual-label resolution
surface. Two formats by design; the substrate's append-only stripe
writer (`worldgraph::io::stripe::StripeWriter`) targets ARC1.

**Source dossier:**
`kanban/planning/26-05-15-implementation-of-arcflow.graph/03-SUBSTRATE/io.md`
(ARC1 + Compaction sections).

## Backgrounder

### What is and is NOT live

Frozen at this batch — DOC may describe as **engine-architecture
preview**:

| Surface | Driving commits |
|---|---|
| `arcflow.worldgraph` module skeleton | A1..A3, C1..C2, F1..F2 |
| Typed schema vocabulary (NodeLabel, ColumnDef, ColumnType, EdgeLabel) | B1..B2 |
| Virtual-label contracts (VirtualLabelEntry, PartitionPattern, ResolverKind) | B4 |
| `CREATE NODE LABEL ... VIRTUAL FROM PARTITION` DDL parser | B3 |
| MutationOp enum (row-level + bulk-stripe variants) | G1, D1 |
| WAL record envelope + bulk-stripe protocol | D1 |
| TierBudget + 9-state ResidencyClass | I1 |
| oz:// URI parser | O1 |
| ARC1 file magic + version constants | M1 |
| LSM compaction policy types | K1 |
| Streaming-stripe writer policy + state machine | H1 |
| Block-cache key + handle + policy types | J1 |
| Catalog skeleton | E1 |
| Platform probe (macOS/Linux/WSL2) with capability dispatch | L1..L6 |
| Fitness-function dashboard + 23 RED FF-* stubs | Q1..Q5 |
| CI fitness-functions.yml workflow (non-blocking) | Q4 |

Deferred — DOC must NOT describe as live, MUST gate AGENTS.md /
llms.txt additions with `TODO(wave-A): worldgraph::io v0.8 — surface
lands at engine cut`:

- Streaming-stripe pwrite / fsync / atomic-rename (H2..H4)
- Manifest replay + snapshot pinning (E2..E5)
- Object-cache fetch bodies + Parquet decoder (J2..J8)
- Apply-mutation row-store wiring (G4) and column-store lift (G2),
  MVCC (G3), dense-store (G5)
- WAL append + replay bodies (D2..D5)
- Level-compaction scheduler + bandwidth gov (K2..K6)
- Memory Governor enforcement body (I2..I6)
- ARC1 reader + Parquet decoder paths (M2..M8)
- GraphAr export round-trip (N2..N6)
- oz:// resolvers + fsspec binding (O2..O7)
- Stress harness (R2..R5)
- Phase-D doctrinal sweep + version bump (P1..P8)

### Why one PR

Same coherence rationale as AF-DOC-2026-05-15-001: one
schema-sync review is cheaper than five. None of the v0.8 type
surface touches `typescript/src/code-intelligence.ts` directly
(the SDK mirror doesn't expose new label/edge constants yet —
those land with the cut), but the PR may incidentally pull in
adjacent ergonomic changes.

### Coordination with AF-DOC-2026-05-15-001

This message is **additive**, not blocking. AF-DOC-001 covers the
six-dossier finishing pass output (RKS-5, CAUSED-BY-3, CAN-EVT-3,
DECAY-3, HYPER-9). AF-DOC-002 (this) covers the post-finishing-
pass worldgraph::io v0.8 substrate batch.

DOC may either:
1. Land AF-DOC-001 first (5 pages) and AF-DOC-002 second (1 page),
   in two separate PRs.
2. Bundle as one PR (6 pages total). The schema-sync gate fires at
   most once either way.

Operator preference is no preference — DOC picks based on their
own scheduling discipline.

### Vocabulary discipline (verify before authoring)

From `arcflow-docs/CLAUDE.md` + memory:
- Alpha 0.x — current line is v0.7.2 — no v1.0 claims
- No perf numbers — no "90× cliff" / "272× scale" / throughput
  multipliers; architectural floors like "0ms in-process" OK
- No "reactive" in positioning prose — use live queries / standing
  queries / always-current / event-bus / pubsub
- Live, not aspirational — `TODO(wave-A):` gate is hard
- Integration model: napi-rs > CLI > MCP — MCP only for cloud chat
  UIs

### Engine commits the DOC agent should cite per section

| Section | Driving commits |
|---|---|
| 1 (`worldgraph` module structure) | `d8d10bae` + A2/A3 + lift commits `dbe9a42f` / `1908a939` / `4dac8ce7` |
| 2 (Virtual Labels) | `3f94cd7b` + `dc37e03f` + `ddff632d` + `cbdf3987` |
| 3 (Residency tiers) | `fb5418e6` |
| 4 (`oz://` URI) | `ad1d2846` |
| 5 (ARC1 + LSM compaction) | `3f000ff4` + `a8b8cbe7` |

## Acceptance

- One arcflow-docs PR opens with the new architecture page (5
  sections), each citing the driving arcflow-core commit + dossier
  path.
- The page is framed as engine-architecture preview — not
  user-facing capability. Every "VIRTUAL labels do X" claim is
  qualified by "as of v0.8 cut" or "when the substrate lands its
  resolvers (deferred to post-cut waves)".
- AGENTS.md and llms.txt are NOT updated (or are updated only with
  `TODO(wave-A):` markers); they get their entries when
  I-INIT-0147 cuts the v0.8 release.
- If schema sync triggers: `scripts/check-schema-sync.js` passes.
- After merge, this message moves to `resolved/` on both sides
  with the docs PR URL as the resolution citation.

## What I'm doing in the meantime

- Internal tracking continues in arcflow-core's
  `kanban/CURRENT.md`.
- The deferred impl-wave space (G2..G5, H2..H4, J2..J8, etc.)
  follows in subsequent sessions toward "real-pipeline-testable",
  which is the trigger for I-INIT-0147 cut.
- arcflow-core's federation outbound queue clears after this
  message lands: AF-DOC-001 + AF-DOC-002 are the two open
  documentation asks the worldgraph::io v0.8 batch produces.

## Timeline

- **2026-05-15** — Message filed (this commit). All 17 driving
  closures are in main; commit range `2114f4fe..e2f123ac`.
