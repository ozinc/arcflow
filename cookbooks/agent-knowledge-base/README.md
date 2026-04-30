# Agent Knowledge Base via Confidence-Scored GraphRAG

**What you'll build:** An LLM agent's working knowledge base — documents,
extracted entities, and entity-to-entity relations — stored in ArcFlow
with per-extraction confidence scores. Retrieval queries filter by
confidence so the agent ignores low-quality extractions.

**Audience:** python, agent

**Runtime:** ~30 seconds

**ArcFlow version:** 1.6.6

## Run

```bash
uv sync
uv run python 00-make-sample.py            # synthesizes data/corpus.json
uv run python 02-load.py
uv run python 03-confidence-retrieval.py
```

`01-graphrag-design.md` and `04-agent-flow.md` are reading-only steps.

## What this recipe demonstrates

1. **GraphRAG schema** — `Document`, `Entity`, `Mention`, `Relation` are
   all first-class nodes. Mentions and Relations carry extraction
   confidence; queries can filter or weight by it.
2. **Confidence-thresholded retrieval** — agents use a single tunable
   knob (`min_confidence`) to trade recall for precision when answering
   factual questions.
3. **Multi-hop entity traversal** — "drugs that target a gene associated
   with disease X" is one MATCH chain, not three SQL joins.
4. **Provenance recovery** — every retrieved fact links back to the
   document that contributed it, so the agent can cite sources.

## Data

`data/corpus.json` — 18 fictional biotech-paper abstracts mentioning
drugs, diseases, and genes. 13 unique entities (4 drugs, 5 diseases,
4 genes), 40 mentions, 24 relations. Mentions and relations carry
pre-computed extraction confidence in `[0, 1]`. Synthesized; the corpus
has no real-world clinical claims. ~13 KB.

## What this recipe is NOT

- Not a way to extract entities or relations from text. The corpus is
  pre-extracted. Production pipelines plug in spaCy / GLiNER / an LLM
  before this recipe's load step.
- Not a benchmark of retrieval quality. The corpus is small and
  synthetic; the lesson is the schema and the query patterns, not
  domain accuracy.

## Notes

- Pinned to ArcFlow 1.6.6 (see `meta.toml.manifest_pin`).
- Install command sourced from
  [`<InstallMatrix />`](https://oz.com/docs/installation) — do not hand-roll.
