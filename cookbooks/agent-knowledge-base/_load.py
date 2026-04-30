"""Shared loader used by every step that needs the graph in memory.

Schema (see 01-graphrag-design.md):
    (:Document {doc_id, title, source})
    (:Entity   {entity_id, name, type})
    (:Mention  {mention_id, snippet, confidence})
    (:Relation {relation_id, predicate, confidence})
    (:Document)-[:HAS]->(:Mention)-[:OF]->(:Entity)
    (:Entity)-[:HEAD]->(:Relation)-[:TAIL]->(:Entity)
    (:Relation)-[:CITES]->(:Document)

Mentions and Relations are first-class nodes so multiple extractions of
the same (entity, doc) pair or (head, tail, predicate) triple coexist
without colliding.
"""
from __future__ import annotations

import json
from pathlib import Path

from arcflow import ArcFlow

HERE = Path(__file__).parent
INPUT = HERE / "data" / "corpus.json"


def _esc(s: str) -> str:
    return s.replace("'", "\\'")


def load(verbose: bool = False):
    if not INPUT.exists():
        raise SystemExit(f"Missing {INPUT}. Run 00-make-sample.py first.")

    payload = json.loads(INPUT.read_text())
    db = ArcFlow()

    for d in payload["documents"]:
        db.execute(
            "CREATE (:Document {"
            f"doc_id: '{d['doc_id']}', "
            f"title: '{_esc(d['title'])}', "
            f"source: '{_esc(d['source'])}'"
            "})"
        )

    for e in payload["entities"]:
        db.execute(
            "CREATE (:Entity {"
            f"entity_id: '{e['entity_id']}', "
            f"name: '{_esc(e['name'])}', "
            f"type: '{e['type']}'"
            "})"
        )

    for m in payload["mentions"]:
        db.execute(
            "CREATE (:Mention {"
            f"mention_id: '{m['mention_id']}', "
            f"snippet: '{_esc(m['snippet'])}', "
            f"confidence: {m['confidence']}"
            "})"
        )
        db.execute(
            "MATCH (d:Document {doc_id: '" + m["doc_id"] + "'}), "
            "(mn:Mention {mention_id: '" + m["mention_id"] + "'}) "
            "CREATE (d)-[:HAS]->(mn)"
        )
        db.execute(
            "MATCH (mn:Mention {mention_id: '" + m["mention_id"] + "'}), "
            "(e:Entity {entity_id: '" + m["entity_id"] + "'}) "
            "CREATE (mn)-[:OF]->(e)"
        )

    for r in payload["relations"]:
        db.execute(
            "CREATE (:Relation {"
            f"relation_id: '{r['relation_id']}', "
            f"predicate: '{r['predicate']}', "
            f"confidence: {r['confidence']}"
            "})"
        )
        db.execute(
            "MATCH (h:Entity {entity_id: '" + r["head"] + "'}), "
            "(rn:Relation {relation_id: '" + r["relation_id"] + "'}) "
            "CREATE (h)-[:HEAD]->(rn)"
        )
        db.execute(
            "MATCH (rn:Relation {relation_id: '" + r["relation_id"] + "'}), "
            "(t:Entity {entity_id: '" + r["tail"] + "'}) "
            "CREATE (rn)-[:TAIL]->(t)"
        )
        db.execute(
            "MATCH (rn:Relation {relation_id: '" + r["relation_id"] + "'}), "
            "(d:Document {doc_id: '" + r["doc_id"] + "'}) "
            "CREATE (rn)-[:CITES]->(d)"
        )

    if verbose:
        print(
            f"loaded {len(payload['documents'])} docs, "
            f"{len(payload['entities'])} entities, "
            f"{len(payload['mentions'])} mentions, "
            f"{len(payload['relations'])} relations"
        )

    return db, payload
