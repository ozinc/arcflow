//! Step 03 (Rust) — confidence-thresholded retrieval + provenance walk.
//!
//! Mirrors `03-confidence-retrieval.py` end-to-end: same four queries
//! (entities-in-doc, treats-disease, drug-target-disease-chain,
//! provenance-for-claim), same `min_confidence` semantics. Reaches the
//! Rust-only surface in step 5: `arcflow_sdk::provenance_chain(&db,
//! node_id)` walks the DERIVED_FROM / SOURCE / EXTRACTED_FROM chain up
//! to depth 10 in one call, returning `(node_id, label, confidence,
//! depth)` — useful for the agent's "show me the trail" tool call.

use agent_knowledge_base::load;
use anyhow::Result;
use std::path::PathBuf;

const MIN_CONFIDENCE: f64 = 0.85;

fn main() -> Result<()> {
    let mut path = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    path.pop();
    path.push("data");
    path.push("corpus.json");
    let (db, _corpus) = load(&path)?;

    // ---- q1: entities mentioned in document D03 ----------------------
    println!("[q1] Entities mentioned in document D03 (confidence >= {MIN_CONFIDENCE}):");
    let q1 = format!(
        "MATCH (d:Document {{doc_id: 'D03'}})-[:HAS]->(m:Mention)-[:OF]->(e:Entity) \
         WHERE m.confidence >= {MIN_CONFIDENCE} \
         RETURN e.name AS entity, e.type AS type, m.confidence AS conf \
         ORDER BY m.confidence DESC"
    );
    for row in db.execute(&q1)?.rows {
        println!(
            "    {:>14}  ({:>8})  conf={}",
            row.get("entity").cloned().unwrap_or_default(),
            row.get("type").cloned().unwrap_or_default(),
            row.get("conf").cloned().unwrap_or_default(),
        );
    }

    // ---- q2: drugs that TREAT hypertension ---------------------------
    println!("\n[q2] Drugs that TREAT hypertension (confidence >= {MIN_CONFIDENCE}):");
    let q2 = format!(
        "MATCH (disease:Entity {{name: 'hypertension'}})<-[:TAIL]- \
               (r:Relation)<-[:HEAD]-(drug:Entity) \
         WHERE r.predicate = 'TREATS' AND r.confidence >= {MIN_CONFIDENCE} \
         RETURN drug.name AS drug, r.confidence AS conf \
         ORDER BY r.confidence DESC"
    );
    let result = db.execute(&q2)?;
    if result.rows.is_empty() {
        println!("    (no relations met the threshold)");
    }
    for row in result.rows {
        println!(
            "    {:>10}  conf={}",
            row.get("drug").cloned().unwrap_or_default(),
            row.get("conf").cloned().unwrap_or_default(),
        );
    }

    // ---- q3: drug → gene → disease chain (multi-hop GraphRAG) --------
    let drug_target_min = MIN_CONFIDENCE - 0.2;
    println!("\n[q3] Drugs that TARGET a gene ASSOCIATED_WITH hypertension");
    println!(
        "     (drug-target conf >= {drug_target_min:.2}, gene-disease conf >= {MIN_CONFIDENCE}):"
    );
    let q3 = "MATCH (disease:Entity {name: 'hypertension'})<-[:TAIL]-\
              (rg:Relation)<-[:HEAD]-(gene:Entity)<-[:TAIL]-\
              (rt:Relation)<-[:HEAD]-(drug:Entity) \
              WHERE rt.predicate = 'TARGETS' AND rg.predicate = 'ASSOCIATED_WITH' \
              RETURN drug.name AS drug, gene.name AS gene, \
                     rt.confidence AS dc, rg.confidence AS gc";
    let result = db.execute(q3)?;
    let mut seen = std::collections::HashSet::new();
    let mut any = false;
    for row in result.rows {
        let drug = row.get("drug").cloned().unwrap_or_default();
        let gene = row.get("gene").cloned().unwrap_or_default();
        let dc: f64 = row.get("dc").and_then(|s| s.parse().ok()).unwrap_or(0.0);
        let gc: f64 = row.get("gc").and_then(|s| s.parse().ok()).unwrap_or(0.0);
        if dc < drug_target_min || gc < MIN_CONFIDENCE {
            continue;
        }
        let key = (drug.clone(), gene.clone());
        if !seen.insert(key) {
            continue;
        }
        any = true;
        println!(
            "    {drug:>10} -> {gene:>6} -> hypertension  combined={:.2}",
            dc * gc,
        );
    }
    if !any {
        println!("    (no drug→gene→disease chains met the thresholds)");
    }

    // ---- q4: provenance ------------------------------------------------
    println!("\n[q4] Provenance: 'Calmovir TREATS migraine' — supporting documents:");
    let q4 = "MATCH (drug:Entity {name: 'Calmovir'})-[:HEAD]->(r:Relation)\
              -[:CITES]->(d:Document) \
              WHERE r.predicate = 'TREATS' \
              RETURN d.doc_id AS doc, d.title AS title, r.confidence AS conf \
              ORDER BY r.confidence DESC";
    for row in db.execute(q4)?.rows {
        println!(
            "    [{}] {}  (conf={})",
            row.get("doc").cloned().unwrap_or_default(),
            row.get("title").cloned().unwrap_or_default(),
            row.get("conf").cloned().unwrap_or_default(),
        );
    }

    println!("\nOK");
    Ok(())
}
