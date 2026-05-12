# Agent Knowledge Base via Confidence-Scored GraphRAG

> **Calibrated uncertainty in retrieval — without the vector-index circus.**
>
> A confidence-scored GraphRAG knowledge base your LLM agent reads from
> with one tunable knob (`min_confidence`) trading recall for precision.
> Every retrieved fact carries provenance back to its source document.
> No embeddings, no vector index, no re-rank model — just the schema and
> the query patterns that elite RAG stacks converge on after they outgrow
> "vector similarity over chunks."

**Audience:** python · agent · ML engineer
**Runtime:** ~30 seconds
**Pins:** `oz-arcflow==1.6.7`

## Why this exists

Every RAG stack starts with "embed the chunks, top-k cosine, stuff into
prompt" and discovers within months that the hard part is *trust*. The
LLM cites a fact; the source disagrees; the agent gets a wrong answer
with a confident citation. Vector similarity has no opinion on whether
the chunk it returned was actually high-quality evidence.

The systems-mastery move is to **make extraction confidence first-class
in the schema** and let the agent filter on it. A drug-disease relation
extracted with `0.96` confidence from a clinical-trial paper is not the
same evidence as one extracted at `0.65` from a review article. The
agent's tunable knob is one number; the graph does the rest.

This recipe is the schema and the query patterns. Production pipelines
plug in spaCy / GLiNER / an LLM upstream of the load step — extraction
is orthogonal to retrieval, and conflating the two is the trap.

## What you'll build

1. **GraphRAG schema** — `Document`, `Entity`, `Mention`, `Relation` are
   all first-class nodes. Mentions and Relations carry extraction
   confidence; queries filter or weight by it. Provenance is an edge
   (`:Relation-[:CITES]->:Document`), not a property buried in JSON.
2. **Confidence-thresholded retrieval** — one tunable knob
   (`min_confidence`) trades recall for precision. Same query shape
   spans "high-conviction facts only" and "hypothesis-generation mode."
3. **Multi-hop entity traversal** — *"drugs that target a gene
   associated with disease X"* is one MATCH chain with two confidence
   filters, not three SQL joins with confidence smuggled through case
   expressions.
4. **Provenance recovery** — every retrieved fact links back to the
   document that contributed it. The agent's response cites D03 with
   confidence 0.96, because the graph knows.

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

## What this recipe is NOT

- **Not a way to extract entities or relations from text.** The corpus
  is pre-extracted. Production pipelines plug in spaCy / GLiNER / an
  LLM before this recipe's load step. Extraction is its own discipline.
- **Not a benchmark of retrieval quality.** The corpus is small and
  synthetic; the lesson is the schema and the query patterns, not
  domain accuracy.
- **Not vector retrieval.** The retrieval here is symbolic (entity-id
  match plus graph traversal). Vector retrieval is orthogonal —
  production stacks combine both, but it lives outside this recipe.
  ArcFlow's HNSW vector index integrates as a pre-filter ahead of the
  graph traversal; that pattern deserves its own recipe.

## Connection to the broader Evidence Model

The `confidence` property used throughout this cookbook is the
pedagogical kernel of OZ's broader Evidence Model (see
[/concepts/confidence-and-provenance](/concepts/confidence-and-provenance)).
In the full convention every node and edge also carries
`_observation_class` (one of `observed` / `inferred` / `predicted`) and
`_source`, and `PhysicalWorldModel` auto-writes them on every fact.
This cookbook deliberately uses the bare `confidence` property to keep
the pedagogy tight — the lesson is "calibrated uncertainty *as a schema
commitment*," not the specific OZ vocabulary. Once you internalise the
pattern, the full vocabulary is one rename.

## See also

- [Confidence and Provenance](/concepts/confidence-and-provenance) — the full Evidence Model deep dive
- [World Model concept](/concepts/world-model) — operational vs neural, where the agent reads ground truth from
- [Graph Patterns](/concepts/graph-patterns) — the MATCH chains used in step 3
- [Trusted RAG](/trusted-rag) — production GraphRAG architecture with vector pre-filter
- [`algo-trading-world-model`](../algo-trading-world-model/) — sibling cookbook using the same evidence-algebra in a financial context
