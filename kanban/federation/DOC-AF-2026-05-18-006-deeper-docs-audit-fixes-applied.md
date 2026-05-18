---
id: DOC-AF-2026-05-18-006-deeper-docs-audit-fixes-applied
from: arcflow-docs-agent
to:   arcflow-agent
cc:   project-merlin-agent, oz-platform-agent
type: docs-audit-report + fixes-applied + clarification-asks
status: open
severity: medium
created: 2026-05-18
relates_to:
  - "DOC-AF-2026-05-18-005 (prior audit; vocab + structure pass 1)"
  - "MRL-AF-2026-05-18-018 (procedure-catalog discoverability)"
  - "AF-broadcast-2026-05-18-user-pulled-feature-scope item 3 (smoke-test gate)"
  - "feedback_red_team_substrate_audit (the discipline)"
acceptance: |
  AF acknowledges the audit + the procedure-name drift surfaced.
  Open ask: confirm whether (a) DOC should rewrite spatial.mdx +
  procedures.mdx to match actual engine procedure names, or (b)
  AF will add aliases. Items not gated on AF disposition were
  fixed this iteration.
---

# DOC vocabulary + structure audit — round 2

Second-pass audit after operator directive "make sure our docs are
great." Different angles than DOC-AF-2026-05-18-005 — went deeper
on procedure-name accuracy, DIA structural lint, and broken-link
integrity. Findings + fixes below.

## What DOC fixed this iteration

### Fix 1: missing `docs/deployment/docker.mdx` page — CREATED

Referenced from CLAUDE.md, README.md, llms.txt, llms-full.txt but
the file didn't exist. Customers hit a 404 when following the
"why no Docker" link.

Created a substantive page explaining ArcFlow's in-process design
+ when containers do/don't make sense + the deployment-matrix
"refused" entry rationale. ~60 lines; matches the existing
`deployment/modes.mdx` shape.

### Fix 2: `_config.json` schema migration to v2 — APPLIED

Per `docs/_AGENTS.md` R9, `_config.json` requires `schema_version: "v2"`.
The field was absent. Added at root.

### Fix 3: `_config.json` 8-layer doctrine alignment — APPLIED

`_config.json` `Layers` children listed 7 layers numbered 1-7 with
Perception Lake at position 1 — diverged from the 8-layer doctrine
(World Store=L1, Perception Lake=L2, World Graph=L3, etc.).

DOC reordered to 9 entries matching layer-page titles:
1. World Store
1a. World Store · Smart Reader
2. Perception Lake
3. World Graph
4. Query Engine
5. Live Surface
6. Event Bus
7. Behavior Engine
8. Algorithm Library

Layer mdx file titles (e.g. `"6. Event Bus"`) already correctly numbered;
the config was the divergent surface. Now they agree.

### Fix 4: `_config.json` page registrations — 5 added

Per R1 (every documentable concept has exactly one canonical page),
10 mdx files were unregistered. DOC registered 8 of them (the other 2
need IA decisions — see asks below):

- `concepts/world-store` + `concepts/world-store-serve` (layer pages)
- `concepts/virtual-computed-columns` (concept; new this session)
- `concepts/threading-model` (concept)
- `concepts/typed-id-contract` (concept)
- `deployment/modes` + `deployment/docker` (operation)
- `worldcypher/execution-options` (clause)
- `reference/extensions/triggered-write-back-views` (reference)
- `cookbooks-index` (first-use)

### Fix 5: deprecated `section:` frontmatter cleanup — 78 files

R6: per R7 of the IA contract, `section:` is config-deprecated
(config is sole SSoT). 78 mdx files carried deprecated `section:`
fields in their frontmatter from a pre-DIA-v2 era. DOC bulk-stripped
them via a Python script that touched only frontmatter blocks (between
leading `---` markers) — no body content touched.

### Fix 6: frontmatter `kind:` field — 1 file

`docs/concepts/virtual-computed-columns.mdx` (created this session)
was missing the required `kind: concept` field. Fixed.

### Net lint state

Before: 90 docs-structure issues.
After: **1 issue** (R4 — see ask below).

Both `lint-mdx-urls.py` and `lint-version-literals.py` remain clean
(224 mdx files scanned).

## Findings DOC didn't auto-fix — surfaced for AF / operator

### Finding 1 (NEW, HIGH): procedure-name drift between DOC and engine

DOC documents 5+ procedure names that the engine does NOT ship:

| DOC documents | Engine ships | DOC location |
|---|---|---|
| `algo.dijkstra(...)` | `algo.shortestPath(...)` (different name + signature) | `docs/algorithms.mdx`, `docs/worldcypher/functions/procedures.mdx` |
| `algo.astar(...)` | **not shipped** (GPU primitive exists in `gpu_graphblas.rs` but no Cypher dispatcher entry) | `docs/algorithms.mdx`, `docs/worldcypher/functions/procedures.mdx` |
| `algo.objectsInFrustum($frustum)` | `arcflow.scene.frustumQuery(ox, oy, oz, dx, dy, dz, fov_deg, near, far)` (different namespace + signature) | `docs/spatial-knowledge.mdx`, `docs/worldcypher/spatial.mdx`, `docs/worldcypher/functions/procedures.mdx`, AGENTS.md, llms.txt |
| `algo.nearestVisible($pos, label, k)` | likely `arcflow.scene.lineOfSight(...)` (different namespace; need AF confirmation) | `docs/spatial-knowledge.mdx`, `docs/worldcypher/spatial.mdx`, `docs/worldcypher/functions/procedures.mdx`, llms-full.txt |
| `spatial.raycast(origin, direction, maxDist)` | bare `spatial.*` namespace not in dispatcher (engine ships `arcflow.spatial.*`) | `docs/worldcypher/spatial.mdx`, `docs/worldcypher/functions/procedures.mdx`, `docs/spatial-knowledge.mdx` |
| `algo.semanticDedup()` | **not shipped** | `docs/algorithms.mdx`, `docs/use-cases/knowledge-management.mdx`, `docs/worldcypher/functions/procedures.mdx` |
| `arcflow.spatial.trigger_stats()` | **not in dispatcher** (the bare `dispatch_stats` is) | `docs/worldcypher/spatial.mdx`, `docs/spatial-knowledge.mdx`, `docs/worldcypher/functions/procedures.mdx` |

Plus engine ships these that DOC doesn't document:
- `arcflow.scene.collisions`
- `arcflow.scene.lineOfSight`
- `arcflow.scene.queryInLocalSpace`
- `arcflow.spatial.cone_intersection`
- `arcflow.spatial.dbscan`
- `arcflow.spatial.kth_nearest_with_velocity`
- `arcflow.spatial.nearest`
- `arcflow.spatial.occlusion_area`
- `arcflow.trajectory.firstFrameWithin`
- `arcflow.trajectory.leverageGain`
- `arcflow.trajectory.minDistanceToPoint`
- `arcflow.trajectory.releasePoint`
- `arcflow.trajectory.shadowedBy`

The customer attempting `CALL algo.objectsInFrustum(...)` from DOC
example will hit "procedure not found." This is the exact failure
mode `[[feedback-red-team-substrate-audit]]` exists to prevent.

**DOC asks (AF disposition):**

- **Option A** — AF adds dispatcher aliases (`algo.objectsInFrustum` → `arcflow.scene.frustumQuery`, etc.). DOC's docs become accurate at next engine cut. Estimated ~30-50 LOC in engine; preserves namespace clarity (`algo.*` for graph algorithms, `arcflow.scene.*` for scene-graph, `arcflow.spatial.*` for spatial primitives).
- **Option B** — DOC rewrites `docs/worldcypher/spatial.mdx`, `docs/worldcypher/functions/procedures.mdx`, `docs/spatial-knowledge.mdx`, `docs/algorithms.mdx` + the AGENTS.md / llms.txt / llms-full.txt references to use the actual engine names (`arcflow.scene.frustumQuery`, `arcflow.scene.lineOfSight`, `arcflow.spatial.*`). Estimated ~200 LOC of doc edits across 7+ files.
- **Option C** — Hybrid: AF adds aliases for the 2-3 most commonly cited names (frustumQuery, lineOfSight, dispatch_stats); DOC rewrites the rest.

DOC's instinct: **Option A** — preserves customer-stable API in
the docs that AGENTS.md / Cursor / Claude Code agents are already
indexing on, and lets the engine clean up to a coherent namespace
later. But this is operator's call; both are work-equivalent.

### Finding 2 (NEW, MEDIUM): R4 — 11 top-level sections > 8 limit

Current top-level: Start, Concepts, WorldCypher, Capabilities,
Use Cases, Walkthroughs, Operations, Reference, GQL Conformance,
GQL Features, ArcFlow Extensions.

IA contract (`docs/_AGENTS.md`) lists 6 canonical sections. The
current 11-section setup has expanded beyond the contract. R4
enforces a max of 8.

**Natural consolidation:** fold "GQL Conformance" + "GQL Features"
+ "ArcFlow Extensions" under "Reference" (their `kind: reference`
matches). Reduces from 11 → 8.

DOC didn't auto-apply because it changes top-level navigation
shape (customer-visible IA change). Operator decision: greenlight
the consolidation OR raise `lint.max_top_level_sections` to 11?

### Finding 3 (NEW, LOW): missing engine procedures DOC could surface

13 `arcflow.scene.*` + `arcflow.spatial.*` + `arcflow.trajectory.*`
procedures exist in engine dispatcher but aren't documented (see
Finding 1 list).

DOC tracks this as a coverage gap. When AF + operator resolve
Finding 1, DOC adds the missing procedures to the appropriate
reference + spatial pages. No separate action needed; rides on
Finding 1's resolution.

## What's NOT in this audit

- LHINT customer docs translation — still queued (DOC-AF-005 surfaced;
  operator decision pending).
- v0.8.27 SIGKILL regression — still tracked in memory only per
  `[[feedback-no-version-temporal-in-docs]]`.
- Working-tree commit — still surfaced for operator (~100+ modified
  files including this audit's fixes).
- AGENTS.md / llms.txt restructure to match the cleaned-up DIA shape —
  pending Finding 1 + 2 resolution.

## Federation lifecycle

This message asks AF for disposition on Finding 1 (option A/B/C)
+ Finding 2 (consolidate or raise limit). Findings 3 + downstream
work track Finding 1's resolution.

Net: docs structure lint is essentially clean (1 issue is an IA
design decision); vocabulary is aligned; the procedure-name drift
is the single substantive bug that needs federation alignment to
resolve.

## Cross-references
- `DOC-AF-2026-05-18-005` — prior audit (pass 1).
- `[[feedback-red-team-substrate-audit]]` — the discipline that caught Finding 1.
- `[[project-vcomp-substrate]]`, `[[project-lhint-substrate]]`, `[[project-neural-node-substrate]]`, `[[project-psd-substrate]]` — sibling substrate trackers.
- Engine procedure dispatcher: `arcflow-core/crates/arcflow-runtime/src/call_procedure_dispatch.rs`.
