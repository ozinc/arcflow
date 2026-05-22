//! Step 02 (Rust) — load the corpus into ArcFlow.
//!
//! Mirrors `02-load.py`. Reads `../data/corpus.json`, builds the four-
//! label GraphRAG schema (Document / Entity / Mention / Relation), and
//! prints summary counts.

use agent_knowledge_base::load;
use anyhow::Result;
use std::path::PathBuf;

fn main() -> Result<()> {
    let mut path = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    path.pop(); // rust/ → cookbook root
    path.push("data");
    path.push("corpus.json");

    let (db, corpus) = load(&path)?;

    println!(
        "loaded {} docs, {} entities, {} mentions, {} relations",
        corpus.documents.len(),
        corpus.entities.len(),
        corpus.mentions.len(),
        corpus.relations.len(),
    );

    // Sanity check: count nodes via query — same result as the Python loader.
    for (label, q) in [
        ("Document", "MATCH (d:Document) RETURN count(*) AS n"),
        ("Entity",   "MATCH (e:Entity)   RETURN count(*) AS n"),
        ("Mention",  "MATCH (m:Mention)  RETURN count(*) AS n"),
        ("Relation", "MATCH (r:Relation) RETURN count(*) AS n"),
    ] {
        let result = db.execute(q)?;
        let n = result.rows.first()
            .and_then(|row| row.get("n"))
            .cloned()
            .unwrap_or_else(|| "0".to_string());
        println!("  {label:<10} {n}");
    }

    Ok(())
}
