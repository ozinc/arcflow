# ArcFlow

**The operational world model layer.** Spatial, temporal, confidence-scored, embedded.

ArcFlow is an in-process database for systems that need to reason about the physical world in real time. It runs inside your application — no server, no round-trip — and unifies graph relationships, geospatial indexes, time-versioned history, vector search, full-text search, and live standing queries behind a single ISO GQL surface.

```bash
# CLI — shell-native, ≤10ms cold start
curl -fsSL https://staging.oz.com/install/arcflow | sh

# Python — embedded in-process, 5MB binary bundled in the wheel
pip install --index-url https://staging.oz.com/pypi/simple/ oz-arcflow

# Browser — try it before installing
open https://staging.oz.com/engine
```

Engine version 1.6.6 (alpha). [Live install matrix](https://staging.oz.com/docs/installation).

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

ArcFlow is designed to be addressable by agents — Claude Code, Codex, Cursor, Gemini CLI, Aider, MCP-aware chat UIs. Three agent-native surfaces:

```bash
# 1. CLI — shell-native, composable like grep, exits in <10ms
arcflow query "MATCH (e:Entity) RETURN e.name LIMIT 5" --json

# 2. Filesystem projection — write the world model to a directory tree
arcflow project ./world-model --json
# → agents grep / cat / rg the directory directly, no Cypher required

# 3. MCP server — for cloud chat UIs (Claude.ai, browser agents)
npx arcflow-mcp
```

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
| [`docs/cli/project.mdx`](docs/cli/project.mdx) | Filesystem projection — the agent-grep workflow |
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

| Operation | Throughput |
|---|---|
| Spatial KNN (11K entities) | ≥ 2,000 queries/sec |
| Node creates | 9.3M/sec |
| PageRank (154M nodes) | <1 second |
| Geofence trigger latency | <20ms |
| Temporal `AS OF` query | Same as current-state query — no separate index |
| openCypher TCK | 100% (3,881 / 3,881) |
| ISO/IEC 39075 GQL | V2 native |

---

## What you can build

| Domain | Why ArcFlow |
|---|---|
| **Robotics & perception** | Sensor fusion — observed/predicted tracks, lidar provenance, confidence-filtered spatial queries, emergency-stop standing queries |
| **Autonomous fleets** | Shared world model across all agents — spatial task assignment, formation coordination, temporal audit |
| **Sports & motion analytics** | 60 Hz live tracking + auxiliary streams (3D scene reconstruction, biomechanical telemetry, sparse events) reconciled to one canonical timeline |
| **Digital twins** | Live spatial replica of a physical facility — temporal history, anomaly detection, downstream topology |
| **AI agent infrastructure** | Persistent working memory across sessions — confidence-scored observations, multi-agent coordination, durable workflows |
| **Trusted RAG** | Confidence-filtered retrieval; detect stale information via temporal queries; provenanced answers via snapshot URIs |
| **Fraud detection** | Circular transaction patterns, shared identity clusters, confidence-scored entity links — graph patterns SQL can't write |
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

-- One of 27 built-in graph algorithms — no projection, no catalog
CALL algo.pageRank() YIELD nodeId, score
```

---

## Install

The [install matrix](https://staging.oz.com/docs/installation) renders from a release manifest that CI keeps in sync with what's actually shipped — it's the authoritative source for what works today.

| Surface | Status | Command |
|---|---|---|
| Browser playground | ✓ shipped | [staging.oz.com/engine](https://staging.oz.com/engine) — zero install |
| Native CLI binary | ✓ shipped | `curl -fsSL https://staging.oz.com/install/arcflow \| sh` |
| Python (in-process) | ✓ shipped | `pip install --index-url https://staging.oz.com/pypi/simple/ oz-arcflow` |
| Node.js (napi-rs) | planned | — |
| Rust crate | planned | — |
| Docker image | refused | ArcFlow is a 5MB embedded library; shipping as Docker would subvert the in-process design. [Why](docs/deployment/docker.mdx). |

Pre-built native binaries for macOS (Apple Silicon + Intel), Linux (x86_64 GNU + musl, ARM64 GNU + musl). No build tools required.

---

## Documentation

| | |
|---|---|
| [Quickstart](https://staging.oz.com/docs/quickstart) | First world model in minutes |
| [World Model concept](https://staging.oz.com/docs/concepts/world-model) | What a world model is and why it matters |
| [Snapshot-Pinned Reads](https://staging.oz.com/docs/concepts/snapshots) | Provenanced, replayable query results |
| [Filesystem Projection](https://staging.oz.com/docs/cli/project) | The agent-grep workflow |
| [Live Queries](https://staging.oz.com/docs/live-queries) | Standing queries, incrementally maintained |
| [WorldCypher reference](https://staging.oz.com/docs/worldcypher) | Query language (ISO/IEC 39075, Cypher-compatible) |
| [GQL Conformance](https://staging.oz.com/docs/reference/gql-conformance) | Standards lineage, TCK results, full ISO GQL V2 details |
| [Use cases](https://staging.oz.com/docs/use-cases) | Robotics, fleets, digital twins, RAG, fraud, agents, more |

---

## License

| Component | License |
|---|---|
| SDK wrapper code (this repo) | [MIT](LICENSE) |
| ArcFlow engine (compiled binary) | [OZ Intent-Source License](legal/ENGINE-LICENSE.md) |

The SDK is MIT. The compiled engine binary is licensed under the [OZ Intent-Source License (OISL)](legal/INTENT-SOURCE-TERM-SHEET.md) — freely usable in commercial products, source proprietary, contributions via [Intent Relay](legal/ENGINE-LICENSE.md).
