# ArcFlow

**The correct architectural separation.** Spatial-temporal, confidence-scored, embedded.

The neural world model research community is trying to collapse simulation, memory, spatial grounding, and calibrated uncertainty into a single generative model. MosaicMem, PERSIST, and similar papers are adding persistence into the neural layer. It is the wrong direction.

Simulation belongs in the neural layer. Persistence belongs in a separate, deterministic, queryable layer. These are not the same problem. Neural world models simulate. **ArcFlow records.**

ArcFlow is that layer. Not a vector index. Not a document store. A persistent, spatially grounded, temporally versioned store of what entities exist, where they are, how confident we are in each fact, and what the world looked like at any previous moment. Neural model outputs land here as `_observation_class: 'predicted'` facts. Sensor observations land here as `_observation_class: 'observed'` facts. Everything is queryable with the same ISO GQL syntax.

That infrastructure hasn't existed as a product. It's been assembled from pieces — a spatial system for positions, a time-series store for history, a graph layer for relationships, application code for confidence scoring. Each boundary introduces latency, consistency risk, and complexity that compounds at scale.

ArcFlow is one in-process engine. No server. No round-trip. Space and time are first-class dimensions, not extensions. Every mutation is versioned. Every fact carries an observation class and a confidence score. The entire history is queryable with ISO GQL — in the same syntax as the current state.

**[Try it — oz.com/engine](https://oz.com/engine)** — runs in your browser, zero install.

```bash
npm install arcflow
```

---

```typescript
import { open } from 'arcflow'

const db = open('./data/world-model')

// Entities with spatial positions, epistemic state, and confidence
db.mutate(`
  CREATE (e1:Entity {
    name: 'Unit-01', x: 12.4, y: 8.7, z: 0.0,
    vx: 0.5, vy: 0.0,
    _observation_class: 'observed',
    _confidence: 0.97
  })
  CREATE (e2:Entity {
    name: 'Contact-X', x: 80.0, y: 90.0, z: 5.0,
    _observation_class: 'predicted',
    _confidence: 0.38
  })
`)

// Spatial: nearest trusted entities — R*-tree backed, ≥ 2,000 queries/sec at 11K entities
const nearby = db.query(`
  CALL algo.nearestNodes(point({x: 0, y: 0}), 'Entity', 10)
    YIELD node AS e, distance
  WHERE e._observation_class = 'observed'
    AND e._confidence > 0.85
  RETURN e.name, distance
  ORDER BY distance
`)

// Temporal: where was the world 5 seconds ago?
const past = db.query(`
  MATCH (e:Entity) AS OF (timestamp() - 5000)
  RETURN e.name, e.x, e.y, e._confidence
`)

// Live: standing query fires the instant anything enters a 5m radius
db.subscribe(
  `CALL algo.nearestNodes(point({x: 0, y: 0}), 'Entity', 10)
     YIELD node AS e, distance
   WHERE distance < 5.0
     AND e._observation_class = 'observed'
     AND e._confidence > 0.8
   RETURN e.name, e.x, e.y`,
  (event) => {
    if (event.added.length > 0) triggerEmergencyStop()
  }
)
```

Spatial query composing with epistemic filter and graph traversal — in a single statement, in one engine, in your process.

---

## What makes a world model different from a database

| Dimension | Conventional database | ArcFlow World Model |
|---|---|---|
| **Space** | Coordinates as numeric columns | R*-tree indexed — frustum queries, KNN, proximity algorithms native |
| **Time** | Timestamps on rows | Every mutation versioned — `AS OF seq N` on the same graph, same syntax |
| **Confidence** | Binary (present or absent) | Scored `[0.0, 1.0]` on every node and relationship |
| **Provenance** | Absent or in a separate log | Built-in — every edge records which sensor, model, or process produced it |
| **Observation class** | Not modeled | First-class: `observed`, `inferred`, or `predicted` on every fact |
| **Relationships** | Foreign keys derived at query time | Stored first-class edges with properties and direction |
| **Reactivity** | Poll for changes | `db.subscribe()` — standing queries fire on every relevant mutation |

These are not features. They are the minimum requirements for a system that needs to reason about the physical world.

---

## Three epistemic states on every fact

The world model distinguishes what was measured from what was inferred from what was predicted. This distinction drives operational decisions, not just metadata.

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

-- Confidence-weighted centrality: most trusted entities rank highest
CALL algo.confidencePageRank()
YIELD nodeId, score
```

A safety system running on confidence thresholds is fundamentally different from one running on boolean flags.

---

## Performance

| Operation | Throughput |
|---|---|
| Spatial KNN (R*-tree, 11K entities) | ≥ 2,000 queries/sec |
| Node creates | 9.3M/sec |
| PageRank (154M nodes) | <1 second |
| Geofence trigger latency | <20ms |
| Temporal `AS OF` query | Same as current-state query — no separate index |

---

## What you can build

| | Why ArcFlow |
|---|---|
| **Robotics perception** | Sensor fusion pipeline — observed/predicted tracks, lidar provenance, confidence-filtered spatial queries, emergency-stop live monitoring |
| **Autonomous fleets** | Shared world model across all agents — spatial task assignment, formation coordination, temporal audit |
| **Digital twins** | Live spatial replica of a physical facility — temporal history, anomaly detection, downstream topology |
| **AI agent infrastructure** | Persistent working memory across sessions — confidence-scored observations, multi-agent coordination, durable workflows |
| **Fraud detection** | Circular transaction patterns, shared identity clusters, confidence-scored entity links — graph patterns SQL can't write |
| **Game AI** | NPCs with persistent spatial memory, behavior trees grounded in live world state, formation algorithms |
| **Knowledge graphs** | Entity linking, confidence-scored facts, provenance-tracked sources — semantic + graph + full-text in one engine |
| **Trusted RAG** | Confidence-filtered retrieval — query only high-confidence facts, detect stale information via temporal queries |

---

## One engine, no stack

Building a world model without ArcFlow means assembling infrastructure piece by piece:

```
What the fragmented approach requires      What ArcFlow provides
──────────────────────────────────────     ──────────────────────────────────────────
A graph layer for entity relationships  →  GQL graph store (ISO/IEC 39075, Cypher-compatible)
A spatial system for positions          →  R*-tree spatial index, composable with graph traversal
A time-series store for history         →  Every mutation versioned — AS OF seq N on the same graph
An in-memory layer for hot state        →  In-memory, zero-copy
A vector database for embeddings        →  HNSW vector index, 27 built-in graph algorithms
A message broker for streaming updates  →  CDC + standing queries, no external broker
A workflow engine for durable pipelines →  Graph-native durable workflows
```

Each system in the left column has its own consistency model, its own failure modes, its own operational surface. Queries that cross two of them require a join with no atomicity guarantee.

ArcFlow collapses all of it into one `GraphStore`. One process. Zero serialization between modules.

---

## Query language: ISO GQL (WorldCypher)

ArcFlow implements [ISO/IEC 39075 GQL](https://www.iso.org/standard/76120.html) — the international standard for graph query languages, published 2024. 100% openCypher TCK (3,881/3,881 scenarios). Full ISO GQL V2.

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

-- Live: standing query fires on every relevant mutation
CREATE LIVE VIEW trusted_contacts AS
  MATCH (e:Entity)
  WHERE e._observation_class = 'observed' AND e._confidence > 0.85
  RETURN e.name, e.x, e.y, e._confidence

-- Graph algorithm — no projection, no catalog
CALL algo.pageRank() YIELD nodeId, score
```

---

## Install

| | Command |
|---|---|
| Browser | **[oz.com/engine](https://oz.com/engine)** — zero install |
| npm | `npm install arcflow` |
| Binary | `curl -fsSL https://oz.com/install \| sh` |
| Python | `pip install arcflow` |
| Rust | `cargo add arcflow` |
| Docker | `docker run ghcr.io/ozinc/arcflow:latest` |
| CLI (coding agents) | `arcflow query '...'` — exits in <10ms, composable like grep |
| MCP (cloud chat UIs) | `npx arcflow-mcp` |

Pre-built native binaries for macOS (Apple Silicon + Intel), Linux (x64 + ARM64), and Windows (x64). No build tools required.

---

## Documentation

| | |
|---|---|
| [World Model](docs/concepts/world-model.mdx) | What a world model is and why it matters |
| [Building a World Model](docs/guides/world-model.mdx) | Step-by-step: entities, spatial queries, temporal memory, live monitoring |
| [GQL / WorldCypher](docs/worldcypher.mdx) | Query language reference (ISO/IEC 39075, Cypher-compatible) |
| [GQL Conformance](docs/reference/gql-conformance.mdx) | Standards lineage, TCK results, full ISO GQL V2 conformance details |
| [Autonomous Systems](docs/use-cases/autonomous-systems.mdx) | Robot fleets, UAVs, self-driving vehicles |
| [Digital Twins](docs/use-cases/digital-twins.mdx) | Live spatial replicas of physical facilities |
| [Robotics & Perception](docs/use-cases/robotics.mdx) | Sensor fusion, ROS integration, track lifecycle |
| [Quickstart](docs/quickstart.mdx) | First world model in minutes |

---

## For AI coding agents

| File | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Full context — API, GQL (WorldCypher), spatial/temporal extensions, all procedures |
| [`llms.txt`](llms.txt) | Compact reference for quick orientation |
| [`llms-full.txt`](llms-full.txt) | Complete reference with every procedure and WorldCypher extension |

---

## License

| Component | License |
|---|---|
| SDK wrapper code (this repo) | [MIT](LICENSE) |
| ArcFlow engine (compiled binary) | [OZ Intent-Source License](legal/ENGINE-LICENSE.md) |

The SDK is MIT. The compiled engine binary is licensed under the [OZ Intent-Source License (OISL)](legal/INTENT-SOURCE-TERM-SHEET.md) — freely usable in commercial products, source proprietary, contributions via [Intent Relay](legal/ENGINE-LICENSE.md).
