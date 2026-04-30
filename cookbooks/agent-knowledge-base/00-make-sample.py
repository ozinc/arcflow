"""Synthesize the corpus JSON used by subsequent steps.

A small fictional biotech-paper corpus. Entities span three types
(Drug, Disease, Gene) and relations are typed (TREATS, TARGETS,
ASSOCIATED_WITH). Mentions and relations carry pre-computed extraction
confidence scores. Deterministic — same input → byte-equal output.

Output:
    data/corpus.json (~6 KB)

Schema:
    {
      "documents": [{"doc_id", "title", "source"}],
      "entities":  [{"entity_id", "name", "type"}],
      "mentions":  [{"mention_id", "doc_id", "entity_id", "snippet", "confidence"}],
      "relations": [{"relation_id", "head", "tail", "predicate", "confidence", "doc_id"}]
    }
"""
from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    out = Path(__file__).parent / "data" / "corpus.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    documents = [
        ("D01", "Aspartin in early-onset hypertension", "Synth Press"),
        ("D02", "GeneX5 expression and inflammation pathways", "Synth Press"),
        ("D03", "Clinical trial of Calmovir vs migraine", "TrialNet"),
        ("D04", "Aspartin off-target effects review", "Synth Press"),
        ("D05", "Hypertension and KLR2 expression", "GenoTimes"),
        ("D06", "Calmovir mechanism of action", "Synth Press"),
        ("D07", "Tretinex chemistry and oncology", "OncoBrief"),
        ("D08", "ZyloFX2 in autoimmune disease", "ImmunoNotes"),
        ("D09", "Migraine genetics: a survey", "GenoTimes"),
        ("D10", "ZyloFX2 trial — phase II", "TrialNet"),
        ("D11", "Tretinex resistance and KLR2", "OncoBrief"),
        ("D12", "Inflammation cascades and Aspartin", "ImmunoNotes"),
        ("D13", "GeneX5 knockout study", "GenoTimes"),
        ("D14", "Calmovir generic equivalence", "Synth Press"),
        ("D15", "Cardiovascular risk and KLR2", "Synth Press"),
        ("D16", "Tretinex safety profile in trials", "TrialNet"),
        ("D17", "Migraine drug pipeline 2026", "OncoBrief"),
        ("D18", "Autoimmune therapeutics — perspective", "ImmunoNotes"),
    ]

    entities = [
        # drugs
        ("E01", "Aspartin", "Drug"),
        ("E02", "Calmovir", "Drug"),
        ("E03", "Tretinex", "Drug"),
        ("E04", "ZyloFX2", "Drug"),
        # diseases
        ("E10", "hypertension", "Disease"),
        ("E11", "migraine", "Disease"),
        ("E12", "carcinoma-X", "Disease"),
        ("E13", "autoimmune-Y", "Disease"),
        ("E14", "inflammation", "Disease"),
        # genes
        ("E20", "GeneX5", "Gene"),
        ("E21", "KLR2", "Gene"),
        ("E22", "TM4", "Gene"),
        ("E23", "BRX1", "Gene"),
    ]

    # Mentions: (doc, entity, confidence). Confidence reflects NER quality.
    mentions = [
        # D01: Aspartin in hypertension
        ("D01", "E01", "Aspartin reduced systolic blood pressure", 0.96),
        ("D01", "E10", "patients with early-onset hypertension", 0.95),
        ("D01", "E14", "low-grade inflammation", 0.71),
        # D02: GeneX5 and inflammation
        ("D02", "E20", "GeneX5 expression upregulated", 0.93),
        ("D02", "E14", "inflammatory pathways", 0.84),
        # D03: Calmovir vs migraine
        ("D03", "E02", "Calmovir 50mg arm", 0.97),
        ("D03", "E11", "chronic migraine cohort", 0.94),
        # D04: Aspartin off-targets
        ("D04", "E01", "Aspartin off-target binding", 0.90),
        ("D04", "E22", "TM4 receptor", 0.62),
        # D05: hypertension and KLR2
        ("D05", "E10", "essential hypertension", 0.95),
        ("D05", "E21", "KLR2 polymorphisms", 0.91),
        # D06: Calmovir MoA
        ("D06", "E02", "Calmovir is a partial agonist", 0.96),
        ("D06", "E22", "TM4-mediated signalling", 0.74),
        # D07: Tretinex oncology
        ("D07", "E03", "Tretinex synthesis", 0.95),
        ("D07", "E12", "carcinoma-X cell lines", 0.92),
        # D08: ZyloFX2 autoimmune
        ("D08", "E04", "ZyloFX2 dosing", 0.94),
        ("D08", "E13", "refractory autoimmune-Y", 0.89),
        ("D08", "E23", "BRX1 inhibitors", 0.69),
        # D09: migraine genetics
        ("D09", "E11", "migraine etiology", 0.92),
        ("D09", "E22", "TM4 variants", 0.83),
        # D10: ZyloFX2 trial
        ("D10", "E04", "ZyloFX2 phase II", 0.97),
        ("D10", "E13", "autoimmune-Y arm", 0.95),
        # D11: Tretinex resistance
        ("D11", "E03", "Tretinex-resistant clones", 0.94),
        ("D11", "E21", "KLR2 amplification", 0.83),
        ("D11", "E12", "carcinoma-X resistance", 0.89),
        # D12: inflammation and Aspartin
        ("D12", "E01", "Aspartin reduces NLRP3", 0.91),
        ("D12", "E14", "chronic inflammation", 0.86),
        # D13: GeneX5 knockout
        ("D13", "E20", "GeneX5 knockout model", 0.95),
        ("D13", "E14", "inflammatory phenotype", 0.79),
        # D14: Calmovir generic
        ("D14", "E02", "generic Calmovir", 0.93),
        ("D14", "E11", "migraine prophylaxis", 0.89),
        # D15: cardiovascular and KLR2
        ("D15", "E10", "cardiovascular hypertension", 0.94),
        ("D15", "E21", "KLR2 expression", 0.92),
        # D16: Tretinex safety
        ("D16", "E03", "Tretinex tolerability", 0.91),
        ("D16", "E12", "carcinoma-X cohort", 0.86),
        # D17: migraine pipeline
        ("D17", "E11", "migraine drug landscape", 0.90),
        ("D17", "E02", "Calmovir as anchor", 0.83),
        # D18: autoimmune therapeutics
        ("D18", "E13", "autoimmune-Y biologics", 0.91),
        ("D18", "E04", "ZyloFX2 positioning", 0.88),
        ("D18", "E23", "BRX1 axis", 0.66),
    ]

    # Relations: (head_entity, tail_entity, predicate, confidence, doc_id).
    relations = [
        # Aspartin TREATS hypertension — strong (D01) + supporting (D12, weaker)
        ("E01", "E10", "TREATS", 0.94, "D01"),
        ("E01", "E14", "TREATS", 0.78, "D12"),
        # Calmovir TREATS migraine — multiple
        ("E02", "E11", "TREATS", 0.96, "D03"),
        ("E02", "E11", "TREATS", 0.88, "D14"),
        ("E02", "E11", "TREATS", 0.77, "D17"),
        # Tretinex TREATS carcinoma-X
        ("E03", "E12", "TREATS", 0.93, "D07"),
        ("E03", "E12", "TREATS", 0.83, "D16"),
        # ZyloFX2 TREATS autoimmune-Y
        ("E04", "E13", "TREATS", 0.95, "D08"),
        ("E04", "E13", "TREATS", 0.92, "D10"),
        ("E04", "E13", "TREATS", 0.85, "D18"),
        # Drug TARGETS Gene
        ("E01", "E22", "TARGETS", 0.61, "D04"),
        ("E02", "E22", "TARGETS", 0.74, "D06"),
        ("E03", "E21", "TARGETS", 0.79, "D11"),
        ("E04", "E23", "TARGETS", 0.66, "D08"),
        ("E04", "E23", "TARGETS", 0.69, "D18"),
        # Gene ASSOCIATED_WITH Disease
        ("E20", "E14", "ASSOCIATED_WITH", 0.86, "D02"),
        ("E20", "E14", "ASSOCIATED_WITH", 0.81, "D13"),
        ("E21", "E10", "ASSOCIATED_WITH", 0.91, "D05"),
        ("E21", "E10", "ASSOCIATED_WITH", 0.92, "D15"),
        ("E21", "E12", "ASSOCIATED_WITH", 0.83, "D11"),
        ("E22", "E11", "ASSOCIATED_WITH", 0.81, "D09"),
        ("E22", "E11", "ASSOCIATED_WITH", 0.74, "D06"),
        ("E23", "E13", "ASSOCIATED_WITH", 0.69, "D08"),
        ("E23", "E13", "ASSOCIATED_WITH", 0.66, "D18"),
    ]

    payload = {
        "documents": [
            {"doc_id": d, "title": t, "source": s} for d, t, s in documents
        ],
        "entities": [
            {"entity_id": e, "name": n, "type": k} for e, n, k in entities
        ],
        "mentions": [
            {
                "mention_id": f"M{i:04d}",
                "doc_id": d,
                "entity_id": e,
                "snippet": s,
                "confidence": c,
            }
            for i, (d, e, s, c) in enumerate(mentions, start=1)
        ],
        "relations": [
            {
                "relation_id": f"R{i:04d}",
                "head": h,
                "tail": t,
                "predicate": p,
                "confidence": c,
                "doc_id": d,
            }
            for i, (h, t, p, c, d) in enumerate(relations, start=1)
        ],
    }

    out.write_text(json.dumps(payload, indent=2))
    size_kb = out.stat().st_size / 1024
    print(
        f"wrote {out} "
        f"({len(documents)} docs, {len(entities)} entities, "
        f"{len(mentions)} mentions, {len(relations)} relations, "
        f"{size_kb:.1f} KB)"
    )


if __name__ == "__main__":
    main()
