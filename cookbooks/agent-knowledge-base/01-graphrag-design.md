# Step 01 — GraphRAG Schema and Confidence

Goal: choose how a document corpus, its extracted entities, and the
relations between those entities live in ArcFlow before writing any
retrieval code.

## The data shape

`data/corpus.json` is a pre-extracted bundle:

- **Documents** — short paper abstracts with a title and source.
- **Entities** — drugs, diseases, genes (typed).
- **Mentions** — one per `(document, entity)` extraction, with a
  surface snippet and an NER confidence in `[0, 1]`.
- **Relations** — one per `(head_entity, tail_entity, predicate)`
  extraction, with a relation-extraction confidence in `[0, 1]` and a
  back-pointer to the document that supports it.

Production GraphRAG pipelines compute mentions and relations with a
NER + relation-extraction model (spaCy / GLiNER / an LLM). This recipe
ships a pre-extracted corpus so retrieval is the lesson, not extraction.

## The chosen schema

```cypher
(:Document {doc_id, title, source})
(:Entity   {entity_id, name, type})
(:Mention  {mention_id, snippet, confidence})
(:Relation {relation_id, predicate, confidence})

(:Document)-[:HAS]->(:Mention)-[:OF]->(:Entity)
(:Entity)-[:HEAD]->(:Relation)-[:TAIL]->(:Entity)
(:Relation)-[:CITES]->(:Document)
```

Three design choices warrant explanation.

### 1. Mentions and Relations are nodes, not edges

The same (Document, Entity) pair can be mentioned more than once with
different snippets and confidences. The same (head, tail, predicate)
triple can be extracted from multiple documents with different
confidences. Modeling each extraction as its **own node** means
multiple extractions coexist without collision and each carries its
own provenance back to the source document.

### 2. Confidence is per-extraction, not per-entity

A drug-disease relation extracted with confidence 0.96 from a clinical
trial paper is not the same evidence as one extracted at 0.65 from a
review article. An agent that needs strong claims sets `min_confidence
= 0.85` and excludes the weak extraction; an agent generating
hypotheses sets `min_confidence = 0.5` and keeps it.

The agent's tunable knob is one number. The schema does the rest.

### 3. Provenance is a CITES edge, not a property

Every retrieved relation can be traced back to its source document via
`(:Relation)-[:CITES]->(:Document)`. The agent's response can include
"according to D03, Calmovir treats migraine (confidence 0.96)" without
any extra metadata fetch.

## What we are NOT doing

- Storing extracted text *as* the entity. Entities are stable
  identifiers; text snippets live on Mentions. A query like "all docs
  mentioning Aspartin" finds Mentions and follows them.
- Collapsing multiple extractions into a single weighted edge. The
  weights matter individually for source-level explanation; collapsing
  loses provenance.
- Embedding vectors. Retrieval here is symbolic (entity-id match plus
  graph traversal). Vector retrieval is orthogonal — production stacks
  combine both, but it lives outside this recipe.

## Next

[`02-load.py`](./02-load.py) — bulk-load the corpus into ArcFlow.
