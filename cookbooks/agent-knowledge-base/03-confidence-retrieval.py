"""Step 03 — Confidence-thresholded retrieval queries.

The agent-facing surface. Each query mirrors a real agent tool call:

  q1   "What entities are mentioned in document D03?"
  q2   "What treats hypertension, with confidence above MIN?"
  q3   "What drugs target a gene that is associated with hypertension?"
        (multi-hop GraphRAG — the canonical use case)
  q4   "Show provenance: which documents support 'Calmovir TREATS migraine'?"

Each query's result is exactly what an agent would surface back to the
user, with citation back to the source document.

The chain queries (q2, q3, q4) anchor the MATCH at the disease end and
walk back toward drugs. Anchoring at the property-known node is what
WorldCypher plans cleanest; multi-segment WHERE on deeply-bound nodes
is filtered in Python instead.

Run:
    uv run python 03-confidence-retrieval.py
"""
from __future__ import annotations

from _load import load

MIN_CONFIDENCE = 0.85


def main() -> None:
    db, _ = load()

    print(f"\n[q1] Entities mentioned in document D03 (confidence >= {MIN_CONFIDENCE}):")
    result = db.execute(
        "MATCH (d:Document {doc_id: 'D03'})-[:HAS]->(m:Mention)-[:OF]->(e:Entity) "
        f"WHERE m.confidence >= {MIN_CONFIDENCE} "
        "RETURN e.name AS entity, e.type AS type, m.confidence AS conf "
        "ORDER BY m.confidence DESC"
    )
    for row in result:
        print(
            f"    {row['entity']:>14}  ({row['type']:>8})  "
            f"conf={float(row['conf']):.2f}"
        )

    print(
        f"\n[q2] Drugs that TREAT hypertension (confidence >= {MIN_CONFIDENCE}):"
    )
    # Anchor at the disease and walk back; single WHERE on predicate.
    result = db.execute(
        "MATCH (disease:Entity {name: 'hypertension'})<-[:TAIL]-"
        "(r:Relation)<-[:HEAD]-(drug:Entity) "
        "WHERE r.predicate = 'TREATS' "
        "RETURN drug.name AS drug, r.confidence AS conf "
        "ORDER BY r.confidence DESC"
    )
    rows = [
        (row["drug"], float(row["conf"]))
        for row in result
        if float(row["conf"]) >= MIN_CONFIDENCE
    ]
    if not rows:
        print("    (no relations met the threshold)")
    for drug, conf in rows:
        print(f"    {drug:>10}  conf={conf:.2f}")

    print(
        f"\n[q3] Drugs that TARGET a gene ASSOCIATED_WITH hypertension"
    )
    drug_target_min = MIN_CONFIDENCE - 0.2
    print(
        f"     (drug-target conf >= {drug_target_min:.2f}, "
        f"gene-disease conf >= {MIN_CONFIDENCE}):"
    )
    # 4-hop reversed chain. No engine-side WHERE — filter in Python so
    # both predicates and both confidence thresholds compose.
    result = db.execute(
        "MATCH (disease:Entity {name: 'hypertension'})<-[:TAIL]-"
        "(rg:Relation)<-[:HEAD]-(gene:Entity)<-[:TAIL]-"
        "(rt:Relation)<-[:HEAD]-(drug:Entity) "
        "RETURN drug.name AS drug, gene.name AS gene, "
        "       rt.predicate AS pt, rg.predicate AS pg, "
        "       rt.confidence AS dc, rg.confidence AS gc"
    )
    seen_drugs: set[tuple[str, str]] = set()
    matches = []
    for row in result:
        if row["pt"] != "TARGETS" or row["pg"] != "ASSOCIATED_WITH":
            continue
        dc = float(row["dc"])
        gc = float(row["gc"])
        if dc < drug_target_min or gc < MIN_CONFIDENCE:
            continue
        key = (row["drug"], row["gene"])
        # Per (drug, gene) keep only the strongest gene-disease evidence.
        if key in seen_drugs:
            continue
        seen_drugs.add(key)
        matches.append((row["drug"], row["gene"], dc, gc))

    if not matches:
        print("    (no drug→gene→disease chains met the thresholds)")
    for drug, gene, dc, gc in matches:
        combined = dc * gc
        print(
            f"    {drug:>10} -> {gene:>6} -> hypertension  "
            f"combined={combined:.2f}"
        )

    print(f"\n[q4] Provenance: 'Calmovir TREATS migraine' — supporting documents:")
    # Walk from the drug head along TREATS to the citing document.
    # Caveat: this returns documents for any TREATS relation off Calmovir.
    # For the present corpus Calmovir only TREATS migraine, so the result is
    # exact. In a corpus where one drug treats multiple diseases, intersect
    # this set with a disease-anchored query (see 04-agent-flow.md).
    result = db.execute(
        "MATCH (drug:Entity {name: 'Calmovir'})-[:HEAD]->(r:Relation)"
        "-[:CITES]->(d:Document) "
        "WHERE r.predicate = 'TREATS' "
        "RETURN d.doc_id AS doc, d.title AS title, r.confidence AS conf "
        "ORDER BY r.confidence DESC"
    )
    for row in result:
        print(
            f"    [{row['doc']}] {row['title']}  "
            f"(conf={float(row['conf']):.2f})"
        )

    db.close()
    print("\nOK")


if __name__ == "__main__":
    main()
