# Step 04 — How an Agent Uses This

Goal: sketch the loop an LLM agent runs against the loaded knowledge
base, so the recipe's queries map cleanly onto a tool-call protocol.

## The agent's tools

A typical agent gets four ArcFlow-backed tools, each one query from
[`03-confidence-retrieval.py`](./03-confidence-retrieval.py):

```jsonc
[
  {
    "name": "kb_entities_in_doc",
    "description": "List entities mentioned in a document, filtered by min confidence.",
    "input": {"doc_id": "string", "min_confidence": "number"}
  },
  {
    "name": "kb_relations_for_disease",
    "description": "Find drugs that have a typed relation to a disease, with min confidence.",
    "input": {"disease_name": "string", "predicate": "string", "min_confidence": "number"}
  },
  {
    "name": "kb_traverse",
    "description": "Multi-hop: drug TARGETS gene ASSOCIATED_WITH disease.",
    "input": {"disease_name": "string", "min_confidence": "number"}
  },
  {
    "name": "kb_provenance",
    "description": "Cite the documents that support a (drug, predicate, disease) claim.",
    "input": {"drug_name": "string", "predicate": "string", "disease_name": "string"}
  }
]
```

Each tool maps to one ArcFlow query. The query is the contract.

## The loop

1. The user asks a question. Example: *"What drugs might help with
   hypertension, and what is the evidence?"*
2. The agent calls `kb_relations_for_disease(disease_name="hypertension",
   predicate="TREATS", min_confidence=0.85)` — gets a small candidate list.
3. For each candidate, the agent calls `kb_provenance(drug_name=...,
   predicate="TREATS", disease_name="hypertension")` to retrieve the
   citing documents.
4. The agent generates a response that names the drugs, names the
   documents, and never claims anything beyond what the citations
   support.

## Confidence as a tunable

The agent's only retrieval knob is `min_confidence`. Conservative
agents (regulatory, medical, legal) set it high and accept low recall.
Exploratory agents (hypothesis generation, brainstorming) set it lower.
The schema doesn't change between the two modes — only the threshold.

For chained queries like `kb_traverse`, multiply confidences along the
chain and threshold the product. Step 03's q3 does this.

## Why ArcFlow over a vector store

Vector retrieval surfaces *similar* documents. GraphRAG over confidence-
scored extractions surfaces *factual claims* with provenance. They
compose. A production agent typically:

1. Vector-retrieves documents most relevant to the user query.
2. Extracts entities from those documents at query time.
3. Joins extracted entities into the ArcFlow graph for confidence-scored
   reasoning across the corpus.

This recipe is just step 3 — the part that vector stores cannot do.

## Why this scales

Mentions and Relations are one node each. A 100K-document corpus with
~10 entities per document and ~5 relations per entity-pair lives in a
~6M-node graph. ArcFlow's in-process binding means the agent's tool
calls are sub-millisecond — no network round-trip to a separate graph
service.

## Next

There is no next step in this recipe. The agent's loop is the recipe.
