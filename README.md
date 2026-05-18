# ArcFlow

**The blazing-fast graph engine for modeling the real world.** Spatial, temporal, confidence-scored, in-process.

**Eight engines. One query language. One coherent data model.** Graph storage, query execution, live streaming views, an event bus, a behavior engine, an algorithm library, durability, and language bindings — pre-integrated, designed from scratch for spatial-temporal workloads. One ISO GQL dialect describes the schema, the query, the live view, the trigger, and the algorithm call.

ArcFlow runs inside your application — no server, no round-trip — and unifies graph relationships, geospatial indexes, time-versioned history, vector search, full-text search, and live standing queries behind a single surface. The operational world model layer of your stack: what neural world models simulate, ArcFlow records.

```bash
# CLI — shell-native (the only shipped install today)
curl -fsSL https://staging.oz.com/install/arcflow | sh

# Python — embedded in-process, 5MB binary bundled in the wheel
#   planned for RAM-C2 / 2026-Q3 on public PyPI:
#   pip install oz-arcflow

# Browser — try it before installing
open https://staging.oz.com/engine
```

Alpha. [Live install matrix](https://staging.oz.com/docs/installation).

---

## License at a glance

**Free to build. Free to ship within generous limits. Paid when you scale, need premium capability, or require enterprise control.**

| | What's covered |
|---|---|
| **✅ Free for everyone** | Commercial + non-commercial use of ArcFlow Core within the Free Use Limits. Develop, test, ship, run in production. Embed ArcFlow inside your app + redistribute the binary unmodified. Build with AI coding assistants (Codex, Claude Code, Cursor, Copilot). Your data, graphs, queries, and outputs are yours — OZ claims zero ownership. Zero telemetry. |
| **🛒 Paid plans for** | Managed ArcFlow Cloud · distributed production clusters above the per-node thresholds · premium algorithm packs · enterprise SSO + audit logs + compliance reports · private support + SLA · custom deployment / re-licensing |
| **🚫 Not allowed** | Offering ArcFlow Core itself as a competing standalone product / managed service (i.e., reselling the runtime as your hosted offering). Embedding ArcFlow inside a broader product where it is one component of substantial OTHER value is explicitly fine — that's the SQLite / Postgres embedded pattern. |

Reference class: the same model as **NVIDIA CUDA · Unreal Engine · Docker Desktop · GitHub Copilot · Vercel · Firebase · Cloudflare Workers · Hugging Face**. Proprietary core, open developer surface, free baseline, paid for scale. The full legal text is in [LICENSE-CORE.md](./LICENSE-CORE.md); the plain-English FAQ is in [LICENSE-FAQ.md](./LICENSE-FAQ.md). AI agents see [ARCFLOW_FOR_AI_AGENTS.md](./ARCFLOW_FOR_AI_AGENTS.md). This repo's contents (cookbook, SDK source, install scripts, docs) are [MIT](./LICENSE).

---

## 30-second example

```python
from arcflow import ArcFlow

with ArcFlow() as db:
    # Entities with positions, observation class, and confidence
    db.execute("""
      CREATE (e:Entity {
        name: 'Unit-01', x: 12.4, y: 8.7, z: 0.0,
        _observation_class: 'observed',
        _confidence: 0.97
      })
    """)

    # Spatial KNN composed with epistemic filter — single statement, single engine
    result = db.execute("""
      CALL algo.nearestNodes(point({x: 0, y: 0}), 'Entity', 10)
        YIELD node AS e, distance
      WHERE e._observation_class = 'observed'
        AND e._confidence > 0.85
      RETURN e.name, distance
    """)

    # Every result carries the snapshot URI it observed — provenanced answers
    print(result.snapshot_uri)   # arcflow://snapshot/9c3b…
```

```typescript
import { open } from 'arcflow'

const db = open('./data/world-model')

// Standing query — incrementally maintained, fires on every relevant mutation
db.subscribe(`
  MATCH (e:Entity)
  WHERE e._confidence > 0.85
    AND distance(point({x: e.x, y: e.y}), point({x: 0, y: 0})) < 5.0
  RETURN e.name, e.x, e.y
`, (event) => {
  if (event.added.length > 0) triggerAlert()
})
```

---

## Built for AI coding agents

ArcFlow is designed to be addressable by agents — Claude Code, Codex, Cursor, Gemini CLI, Aider, MCP-aware chat UIs. The agent-native tier ladder (preferred → fallback):

```bash
# 1. CLI + --json fastpath (★ PRIMARY for CLI agents)
arcflow query "MATCH (e:Entity) RETURN e.name LIMIT 5" --json

# 2. Filesystem mount — the world model as files; grep / cat / rg over typed memory
arcflow mount ~/.arcflow/workspace ./world-fs
find ./world-fs/nodes/Entity -name '*.json' | xargs jq '.confidence'

# 3. napi-rs / PyO3 / FFI (★ PRIMARY for in-process embedded apps)
#    pip install oz-arcflow / npm install arcflow

# 4. MCP server (cloud chat UIs only — Claude.ai, ChatGPT)
npx arcflow-mcp
```

If an agent has a shell, give it the CLI; MCP is the integration of last resort for chat surfaces that don't. See [Threading Model](docs/concepts/threading-model.mdx) for the many-reader / one-writer concurrency contract that lets agents fan out reads freely.

Every result envelope — CLI JSON, SDK return value, HTTP response, MCP tool envelope — carries a snapshot URI of the form `arcflow://snapshot/<hex>`. Agents can replay any historical query bit-for-bit:

```bash
arcflow query "MATCH (n) RETURN count(*)" --at-snapshot arcflow://snapshot/9c3b…
```

For complete API context, point your agent at:

| File | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Full public API reference — types, GQL extensions, all surfaces |
| [`llms.txt`](llms.txt) | Compact reference for quick orientation |
| [`llms-full.txt`](llms-full.txt) | Complete reference with every procedure and WorldCypher extension |
| [`docs/guides/filesystem-workspace.mdx`](docs/guides/filesystem-workspace.mdx) | Filesystem mount — the world model as files, browsable with `cat` / `find` / `grep` / `jq` |
| [`docs/concepts/threading-model.mdx`](docs/concepts/threading-model.mdx) | Concurrency contract — lock-free reads via MVCC; typed-error guard on writes |
| [`docs/concepts/snapshots.mdx`](docs/concepts/snapshots.mdx) | Snapshot-pinned reads — provenanced, replayable answers |

---

## What makes a world model different from a database

| Dimension | Conventional database | ArcFlow World Model |
|---|---|---|
| **Space** | Numeric columns | Spatial index — frustum, KNN, polygon containment, native composition with graph traversal |
| **Time** | Timestamps on rows | Every mutation versioned; `AS OF` queries on the same graph, same syntax |
| **Confidence** | Binary (present or absent) | Scored `[0.0, 1.0]` on every node and edge |
| **Observation class** | Not modeled | First-class: `observed`, `inferred`, `predicted` on every fact |
| **Provenance** | Application code | Built-in — every result carries `arcflow://snapshot/<hex>` |
| **Relationships** | Joins computed at query time | Stored first-class edges with properties and direction |
| **Live queries** | Poll for changes | `CREATE LIVE VIEW` — incrementally maintained, fires on every relevant mutation |

These are not features — they are the minimum requirements for a system that reasons about the physical world.

---

## Three epistemic states on every fact

The world model distinguishes what was measured from what was inferred from what was predicted. This drives operational decisions, not just metadata.

```cypher
-- Only act on high-confidence observed facts
MATCH (e:Entity)
WHERE e._observation_class = 'observed'
  AND e._confidence > 0.85
RETURN e.name, e.x, e.y

-- Flag predictions for verification
MATCH ()-[r:DETECTS]->(contact:Entity)
WHERE contact._observation_class = 'predicted'
  AND r._confidence < 0.5
RETURN contact.name, r.sensor, r._confidence
ORDER BY r._confidence ASC

-- Confidence-weighted PageRank — the most trusted entities rank highest
CALL algo.confidencePageRank() YIELD nodeId, score
```

Neural world models simulate possible futures. ArcFlow records what actually happened. Different tools for different jobs — neural model outputs land here as `_observation_class: 'predicted'` facts. Sensor observations land here as `_observation_class: 'observed'` facts. Both are queryable in the same statement.

---

## Performance

Throughput depends on host hardware and graph shape. Measure on your
own host:

```bash
# From the ozinc/arcflow repo:
cargo bench
```

Conformance and standards:

| | |
|---|---|
| openCypher TCK | 100% (3,881 / 3,881) |
| ISO/IEC 39075 GQL | V2 native |
| Temporal `AS OF` query | Same execution path as current-state query — no separate index |

---

## What you can build

| Domain | Why ArcFlow |
|---|---|
| **Robotics & perception** | Sensor fusion — observed/predicted tracks, lidar provenance, confidence-filtered spatial queries, emergency-stop standing queries |
| **Autonomous fleets** | Shared world model across all agents — spatial task assignment, formation coordination, temporal audit |
| **Sports & motion analytics** | 60 Hz live tracking + auxiliary streams (3D scene reconstruction, biomechanical telemetry, sparse events) reconciled to one canonical timeline; built-in trajectory primitives (`shadowedBy`, `leverageGain`, `releasePoint`, `nearestAtFrame`) compose into per-play coverage descriptors in one Cypher block |
| **Digital twins** | Live spatial replica of a physical facility — temporal history, anomaly detection, downstream topology |
| **AI agent infrastructure** | Persistent working memory across sessions — confidence-scored observations, multi-agent coordination, durable workflows |
| **Counterfactual analysis** | Branch the World Graph at any WAL seq (`arcflow.counterfactual.branchAt`); fan out N rollouts; score each in isolation against the canonical timeline; drop or keep based on the score |
| **Trusted RAG** | Confidence-filtered retrieval; detect stale information via temporal queries; provenanced answers via snapshot URIs; causal-lineage walks justify every inferred fact |
| **Fraud detection** | Circular transaction patterns, shared identity clusters, confidence-scored entity links — graph patterns SQL can't write |
| **Multi-source data reconciliation** | Built-in `multi_source_disagreement` TVF resolves contested observations across sources (categorical / numeric / spatial-Weiszfeld-geomedian); pairs with `causalLineage` to trace conflicting claims back to their observations |
| **Game AI** | NPCs with persistent spatial memory, behavior trees grounded in live world state, formation algorithms |

Working examples for each: [`cookbooks/`](https://github.com/ozinc/arcflow/tree/main/cookbooks).

---

## One engine, no stack

Building a world model without ArcFlow means assembling infrastructure piece by piece:

```
What the fragmented approach requires      What ArcFlow provides
──────────────────────────────────────     ──────────────────────────────────────────
A graph store for entity relationships  →  Native ISO GQL graph store (Cypher-compatible)
A spatial system for positions          →  Spatial index — composes with graph traversal
A time-series store for history         →  Every mutation versioned — AS OF on the same graph
A vector database for embeddings        →  Built-in HNSW vector index
A search service for full-text          →  Built-in full-text index
A message broker for streaming updates  →  CDC + standing queries, no external broker
A workflow engine for durable pipelines →  Graph-native durable workflows (behavior graphs)
An audit log for provenance             →  Snapshot URIs on every result envelope
```

Each system in the left column has its own consistency model, its own failure modes, its own operational surface. Queries that cross two of them require a join with no atomicity guarantee. ArcFlow collapses all of it into one `GraphStore`. One process. Zero serialization between modules.

---

## Query language: ISO GQL (WorldCypher)

ArcFlow implements [ISO/IEC 39075 GQL](https://www.iso.org/standard/76120.html) — the international standard for graph query languages, published 2024. 100% openCypher TCK (3,881 / 3,881). Full ISO GQL V2.

If you know Cypher, you already know WorldCypher. The extensions are additive:

```cypher
-- Temporal: query any past state
MATCH (e:Entity) AS OF seq 5000 RETURN e.name, e.x, e.y

-- Spatial: composable with graph traversal
CALL algo.nearestNodes(point({x: 0, y: 0}), 'Entity', 10)
  YIELD node AS e, distance
WHERE distance < 20.0
MATCH (e)-[:MEMBER_OF]->(f:Formation {name: 'Alpha'})
RETURN e.name, distance, f.pattern

-- Live view — incrementally maintained, fires on every relevant mutation
CREATE LIVE VIEW trusted_contacts AS
  MATCH (e:Entity)
  WHERE e._observation_class = 'observed' AND e._confidence > 0.85
  RETURN e.name, e.x, e.y, e._confidence

-- One of 37 built-in graph algorithms — no projection, no catalog
CALL algo.pageRank() YIELD nodeId, score

-- Causal reasoning: walk CAUSED_BY edges with cumulative confidence decay
CALL arcflow.causalLineage(start_node: id(s), depth: 4)
  YIELD node_id, hop, node_label, cumulative_confidence

-- Multi-source disagreement: reconcile contested observations across sources
CALL arcflow.multi_source_disagreement(
  entity_label: "Charting", group_property: "play_id",
  source_property: "source", value_property: "run_pass",
  disagreement_kind: "categorical")
  YIELD source, value, agreement_class, group_consensus, dispute_score

-- Trajectory analytics: NFL coverage descriptor in one block
CALL arcflow.trajectory.shadowedBy(
  entity_label: "Player",
  attacker_filter_property: "player_id", attacker_filter_value: 5,
  target_filter_property: "player_id",   target_filter_value: 12,
  defender_filter_property: "player_id", defender_filter_value: 28,
  angle_tol_rad: 0.1) YIELD frame

-- Counterfactual branching: fork the World Graph at a WAL seq for swarm rollouts
CALL arcflow.counterfactual.branchAt(name: 'rollout-1', seq: 42)
  YIELD branch, base_seq, status
```

Bounded latency for live UX — wall-clock deadlines compose naturally with any query:

```python
# Deadline-over-completeness: the engine returns what it has at the deadline
# with result.transport_outcome == 'truncated' (vs 'complete' for full result).
result = db.execute(
    "MATCH (f:Frame) WHERE f.play_id = 1024 RETURN f LIMIT 100",
    options=arcflow.QueryOptions(deadline_ms=500),
)
result.transport_outcome   # 'truncated' | 'complete' | None
result.io_stats            # IoStats(decoded_bytes=…, lane_used=…, ...)
```

---

## Install

The [install matrix](https://staging.oz.com/docs/installation) renders from a release manifest that CI keeps in sync with what's actually shipped — it's the authoritative source for what works today.

| Surface | Status | Command |
|---|---|---|
| Browser playground | ✓ shipped | [staging.oz.com/engine](https://staging.oz.com/engine) — zero install |
| Native CLI binary | ✓ shipped | `curl -fsSL https://staging.oz.com/install/arcflow \| sh` |
| Python (in-process) | planned RAM-C2 / 2026-Q3 | `pip install oz-arcflow` (pending public PyPI publish) |
| Node.js (napi-rs) | planned RAM-C2 / 2026-Q3 | `npm install arcflow` (pending) |
| Rust crate | planned RAM-C3 / 2026-Q4 | `cargo add arcflow` (pending) |
| Docker image | refused | ArcFlow is a 5MB embedded library; shipping as Docker would subvert the in-process design. [Why](docs/deployment/docker.mdx). |

Pre-built native binaries for macOS (Apple Silicon + Intel), Linux (x86_64 GNU + musl, ARM64 GNU + musl). No build tools required.

---

## Documentation

| | |
|---|---|
| [Quickstart](https://staging.oz.com/docs/quickstart) | First world model in minutes |
| [World Model concept](https://staging.oz.com/docs/concepts/world-model) | What a world model is and why it matters |
| [Architecture — 8 layers](https://staging.oz.com/docs/architecture) | World Store → Perception Lake → World Graph → Query Engine → Live Surface → Event Bus → Behavior Engine → Algorithm Library |
| [Smart Reader (World Store · serve)](https://staging.oz.com/docs/concepts/layers/world-store-serve) | Format-aware read planner — footer-only count, row-group skip, column projection, lane-explicit transport |
| [Threading Model](https://staging.oz.com/docs/concepts/threading-model) | MVCC-snapshot reads (lock-free); per-handle write guard with typed `HANDLE_BUSY_CONCURRENT_WRITER` error |
| [Snapshot-Pinned Reads](https://staging.oz.com/docs/concepts/snapshots) | Provenanced, replayable query results |
| [Filesystem Workspace](https://staging.oz.com/docs/guides/filesystem-workspace) | The world model as files — `arcflow mount`, the agent-grep workflow |
| [Live Queries](https://staging.oz.com/docs/live-queries) | Standing queries, incrementally maintained |
| [Graph Algorithms](https://staging.oz.com/docs/algorithms) | 37 algorithms — centrality, community, causal reasoning, multi-source disagreement, trajectory, counterfactual branching |
| [Execution Options](https://staging.oz.com/docs/worldcypher/execution-options) | `QueryOptions(deadline_ms=…)`, `result.transport_outcome`, `result.io_stats` |
| [WorldCypher reference](https://staging.oz.com/docs/worldcypher) | Query language (ISO/IEC 39075, Cypher-compatible) |
| [GQL Conformance](https://staging.oz.com/docs/reference/gql-conformance) | Standards lineage, TCK results, full ISO GQL V2 details |
| [Cookbooks (13 recipes)](https://staging.oz.com/docs/cookbooks-index) | Runnable end-to-end recipes — knowledge graph, fraud, RAG, trajectory analytics, deadline-aware queries, more |

---

## License

| Component | License |
|---|---|
| SDK wrapper code (this repo) | [MIT](LICENSE) |
| ArcFlow engine (compiled binary) | [OZ Intent-Source License](legal/ENGINE-LICENSE.md) |

The SDK is MIT. The compiled engine binary is licensed under the [OZ Intent-Source License (OISL)](legal/INTENT-SOURCE-TERM-SHEET.md) — freely usable in commercial products, source proprietary, contributions via [Intent Relay](legal/ENGINE-LICENSE.md).
