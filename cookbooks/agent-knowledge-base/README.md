# Agent Knowledge Base via Confidence-Scored GraphRAG

> **Calibrated uncertainty in retrieval, expressed as a schema commitment.**

A confidence-scored GraphRAG knowledge base an LLM agent reads from
with one tunable knob (`min_confidence`) trading recall for precision.
Every retrieved fact carries provenance back to its source document.
Symbolic retrieval (entity-id match plus graph traversal) — no
embeddings, no vector index, no re-rank model. The schema and the query
patterns are the lesson; extraction is upstream.

**Audience:** python · agent · ML engineer
**Runtime:** ~30 seconds
**Pins:** `oz-arcflow==1.6.7`

## Why the schema does the work

A drug-disease relation extracted with `0.96` confidence from a
clinical-trial paper is not the same evidence as one extracted at
`0.65` from a review article. If the schema collapses both into one
edge, the agent has no way to choose between them — no matter how good
the LLM reranker downstream is. If the schema keeps extraction
confidence per-extraction, the agent filters with one number and the
graph does the rest.

This recipe makes that commitment concrete:

- `Document`, `Entity`, `Mention`, `Relation` are all first-class nodes.
- The same `(Document, Entity)` pair can be mentioned more than once
  with different snippets and confidences — each Mention is its own
  node.
- The same `(head, tail, predicate)` triple can be extracted from
  multiple documents with different confidences — each Relation is its
  own node.
- Provenance is an edge (`(:Relation)-[:CITES]->(:Document)`), not a
  property buried in a JSON blob. Every retrieved relation can be
  traced back to its source document in one hop.

## What you'll build

1. **GraphRAG schema** — four node labels, three edge types, confidence
   on Mentions and Relations.
2. **Confidence-thresholded retrieval** — same query shape spans
   "high-conviction facts only" (`min_confidence = 0.85`) and
   "hypothesis-generation mode" (`min_confidence = 0.5`).
3. **Multi-hop entity traversal** — *"drugs that target a gene
   associated with disease X"* is one MATCH chain with two confidence
   filters.
4. **Provenance recovery** — every retrieved fact links back to the
   document that contributed it. The agent's response cites the
   document with its confidence, because the graph knows.

## Run

```bash
uv sync
uv run python 00-make-sample.py       # synthesizes data/corpus.json
uv run python 02-load.py
uv run python 03-confidence-retrieval.py
```

`01-graphrag-design.md` and `04-agent-flow.md` are reading-only — the
schema rationale and the agent-tool-call mapping respectively.

## Data

`data/corpus.json` — 18 fictional biotech-paper abstracts mentioning
drugs, diseases, and genes. 13 unique entities (4 drugs, 5 diseases, 4
genes), 40 mentions, 24 relations. Mentions and relations carry
pre-computed extraction confidence in `[0, 1]`. Synthesized; no
real-world clinical claims. ~13 KB.

## Scope

This recipe is the **schema and the query patterns** — what the agent
sees and how it filters. Extraction (turning paper text into Mentions
and Relations with confidence scores) lives upstream of the load step,
plugged in via spaCy / GLiNER / an LLM. Vector retrieval (semantic
similarity over chunks) lives alongside — production stacks combine
symbolic graph traversal with vector pre-filter; this recipe is the
graph half.

## See also

- [`algo-trading-world-model`](../algo-trading-world-model/) — sibling using the same confidence-as-schema pattern in a financial context
- [`fraud-graph-traversal`](../fraud-graph-traversal/) — multi-hop entity traversal in a different domain
