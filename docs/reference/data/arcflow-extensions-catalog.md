# ArcFlow Extensions Catalog

**Version:** v1.6.0  
**Date:** 2026-04-07  
**Initiative:** I-INIT-0052 (GQL-Native Extensions)

This catalog documents ArcFlow's unique capabilities beyond ISO/IEC 39075:2024 GQL.
Each extension includes GQL compatibility notes and implementation evidence.

See also: [GQL Conformance Statement](gql-conformance-statement.md)

---

## LIVE Queries (PAT-0022)

**Syntax:**
```gql
CREATE LIVE VIEW friends AS MATCH (a:Person)-[:KNOWS]->(b) RETURN a, b
LIVE MATCH (n:Person) RETURN n.name
DROP LIVE VIEW friends
```

**GQL compatibility:** Uses standard MATCH/RETURN inside LIVE prefix. No GQL equivalent.  
**Semantics:** Incremental Z-set evaluation (PAT-0021) — batch↔delta equivalence proven.  
**Evidence:** I-INIT-0025, wave-ext-0005

---

## Triggered Write-Back Views (EXT-0005)

**Syntax:**
```gql
CREATE LIVE VIEW doc_embeddings AS
  MATCH (d:Document) WHERE d.embedding IS NULL
  SET d.embedding = arcflow.embed(d.content)
  RETURN d
```

**GQL compatibility:** MATCH/WHERE/RETURN are standard GQL; SET inside LIVE VIEW is ArcFlow extension.  
**Semantics:** Fires imperatively after each graph mutation. Enables AI-in-the-database pipelines with zero application code.  
**Evidence:** EXT-0005, write-back live views field in GraphStore

---

## Evidence Algebra (PAT-0023)

**Syntax:**
```gql
MATCH ()-[r:LINKS]->() REFINE EDGE r SET confidence = 0.9, observation = 'observed'
WHERE r._confidence > 0.8
RETURN arcflow.path_confidence(r)
```

**GQL compatibility:** No GQL equivalent. `r._confidence` uses GQL property access syntax.  
**Semantics:** Z-set retract+insert. Confidence as Z-set weight. Observation replaces prediction. Multi-hop product via `arcflow.path_confidence(r)`.  
**Evidence:** EXT-0003, PAT-0023

---

## Relationship Skills (EXT-0002)

**Syntax:**
```gql
CREATE SKILL similar_docs FROM EMBEDDING THRESHOLD 0.8 ALLOWED ON Document
CALL arcflow.processNode('Document')
CALL arcflow.skills()
```

**GQL compatibility:** CALL alias `arcflow.processNode()` available. No GQL equivalent for skill definition.  
**Semantics:** Embedding-based cosine similarity auto-linking. Creates SIMILAR edges above threshold.  
**Evidence:** EXT-0002, `ExecutionTier::Neural`

---

## AI Function Namespace (EXT-0001)

**Syntax:**
```gql
RETURN arcflow.cosine(a.embedding, b.embedding)
RETURN arcflow.embed(n.content)
CALL arcflow.similar(embedding)
CALL arcflow.graphrag('question')
```

**GQL compatibility:** GQL function call syntax. Standard return expressions.  
**Semantics:** AI functions as first-class GQL expressions. arcflow.* namespace reserved for AI/graph extensions.  
**Evidence:** EXT-0001, PAT-0031 (embed→link→recompute flywheel)

---

## Graph Embedding Algorithms (EXT-0004)

**Syntax:**
```gql
CALL algo.node2vec(128, 80, 10) YIELD nodeId, embedding
CALL algo.struc2vec(64) YIELD nodeId, embedding
CALL algo.graphSAGE(256) YIELD nodeId, embedding
```

**GQL compatibility:** CALL procedure syntax.  
**Semantics:** node2vec (biased random walk + hash projection), struc2vec (degree sequence hash), graphSAGE (2-layer mean aggregation). All L2-normalized.  
**Evidence:** EXT-0004

---

## ASOF JOIN (I-INIT-0030)

**Syntax:**
```gql
MATCH (a:Price), (b:Fundamental)
WHERE a.ts ASOF <= b.ts AND a.symbol = b.symbol
RETURN a, b
```

**GQL compatibility:** No GQL equivalent. Temporal join extends standard WHERE clause.  
**Semantics:** Latest-at-or-before timestamp join. Essential for time-series/financial data.  
**Evidence:** I-INIT-0030, trading validator (99.48% DuckDB match)

---

## Durable Workflows (PAT-0020, I-INIT-0013)

**Syntax:**
```gql
CREATE WORKFLOW approval STEP review NEXT approve STEP approve NEXT done
```

**GQL compatibility:** No GQL equivalent. Graph-native execution — workflows are subgraphs.  
**Semantics:** Steps as nodes, NEXT edges for flow. WAL-backed durability. Memoization via properties.  
**Evidence:** I-INIT-0013, PAT-0020

---

## Incremental Z-Set Engine (PAT-0021, I-INIT-0025)

**Syntax:** Used internally; all queries can be LIVE queries.  
**GQL compatibility:** Transparent to user — standard MATCH/RETURN works incrementally.  
**Semantics:** Z-set algebra for provable batch↔delta equivalence. Define once, run as batch or incremental.  
**Evidence:** I-INIT-0025, PAT-0021, wave 60-64

---

## GPU GraphBLAS (I-INIT-0026)

**Syntax:**
```gql
CALL algo.pageRank()      -- auto-dispatches to Metal/CUDA/CPU
CALL algo.leiden()        -- community detection
```

**GQL compatibility:** CALL procedure syntax. GPU dispatch is transparent.  
**Semantics:** 8 SpMV semiring kernels (f64, CAS atomics). Auto-dispatch: Metal → CUDA → Rayon CSR → HashMap.  
**Evidence:** I-INIT-0026, PAT-0033, ANTI-0019

---

## Triggers (PAT-0037, I-INIT-0035)

**Syntax:**
```gql
CREATE TRIGGER auto_tag ON :Article WHEN CREATED RUN SKILL tag_skill
```

The legacy `CREATE REACTIVE SKILL` form is retained for backward
compatibility but new code uses `CREATE TRIGGER`; the user-facing
keyword "reactive" is retired per PAT-0038.

**GQL compatibility:** No GQL equivalent.
**Semantics:** Event-driven skill execution on CDC events. Skills fire when graph conditions match.
**Evidence:** I-INIT-0035, PAT-0037, PAT-0038

---

## HNSW Vector Index (I-INIT-0019)

**Syntax:**
```gql
CALL algo.vectorSearch(embedding)
CALL algo.similarNodes('node_id')
```

**GQL compatibility:** CALL procedure syntax.  
**Semantics:** Cosine-ANN search over graph node embedding properties. HNSW index auto-maintained.  
**Evidence:** I-INIT-0019

---

## Extensions Moat (PAT-0031)

The unique ArcFlow value proposition is the **embed → store → skill → auto-link → live-recompute flywheel**:

1. Insert document
2. `CREATE LIVE VIEW` with `SET ... = arcflow.embed(...)` auto-embeds
3. Relationship skill auto-links similar documents (cosine > threshold)
4. LIVE incremental query recomputes PageRank on updated graph
5. Evidence algebra tracks confidence of each link

**No competitor (Ultipa, Neo4j, Spanner) can express this pipeline in a single graph query language.** Each step in ArcFlow is a GQL-compatible query; together they form a self-reinforcing AI loop with zero application code.
