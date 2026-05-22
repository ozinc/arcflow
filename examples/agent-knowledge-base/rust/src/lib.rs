//! Shared loader for the Agent Knowledge Base Rust SDK example.
//!
//! Reads the same `../data/corpus.json` fixture the Python recipe uses
//! and creates the same four-node-label schema: `Document`, `Entity`,
//! `Mention`, `Relation`. The Rust loader uses `bulk_create_*` shape
//! where possible — symbol/entity/mention nodes are bulk-created;
//! relations carry edges into the same graph the agent queries.
//!
//! Schema (same as Python `01-graphrag-design.md`):
//! ```text
//! (:Document {doc_id, title, source})
//! (:Entity   {entity_id, name, type})
//! (:Mention  {mention_id, snippet, confidence})
//! (:Relation {relation_id, predicate, confidence})
//! (:Document)-[:HAS]->(:Mention)-[:OF]->(:Entity)
//! (:Entity)-[:HEAD]->(:Relation)-[:TAIL]->(:Entity)
//! (:Relation)-[:CITES]->(:Document)
//! ```

use anyhow::{Context, Result};
use arcflow_sdk::ConcurrentStore;
use serde::Deserialize;
use std::fs;
use std::path::Path;

#[derive(Deserialize)]
pub struct Corpus {
    pub documents: Vec<Document>,
    pub entities: Vec<Entity>,
    pub mentions: Vec<Mention>,
    pub relations: Vec<Relation>,
}

#[derive(Deserialize)]
pub struct Document {
    pub doc_id: String,
    pub title: String,
    pub source: String,
}

#[derive(Deserialize)]
pub struct Entity {
    pub entity_id: String,
    pub name: String,
    #[serde(rename = "type")]
    pub kind: String,
}

#[derive(Deserialize)]
pub struct Mention {
    pub mention_id: String,
    pub doc_id: String,
    pub entity_id: String,
    pub snippet: String,
    pub confidence: f64,
}

#[derive(Deserialize)]
pub struct Relation {
    pub relation_id: String,
    pub head: String,
    pub tail: String,
    pub predicate: String,
    pub confidence: f64,
    pub doc_id: String,
}

pub fn load(corpus_path: &Path) -> Result<(ConcurrentStore, Corpus)> {
    let raw = fs::read_to_string(corpus_path)
        .with_context(|| format!("reading {}", corpus_path.display()))?;
    let corpus: Corpus = serde_json::from_str(&raw)
        .with_context(|| "parsing corpus.json")?;
    let db = arcflow_sdk::open_concurrent();

    for d in &corpus.documents {
        db.execute(&format!(
            "CREATE (:Document {{doc_id: '{}', title: {}, source: {}}})",
            d.doc_id,
            cypher_string(&d.title),
            cypher_string(&d.source),
        ))?;
    }
    for e in &corpus.entities {
        db.execute(&format!(
            "CREATE (:Entity {{entity_id: '{}', name: {}, type: '{}'}})",
            e.entity_id,
            cypher_string(&e.name),
            e.kind,
        ))?;
    }
    for m in &corpus.mentions {
        db.execute(&format!(
            "CREATE (:Mention {{mention_id: '{}', snippet: {}, confidence: {}}})",
            m.mention_id,
            cypher_string(&m.snippet),
            m.confidence,
        ))?;
        db.execute(&format!(
            "MATCH (d:Document {{doc_id: '{}'}}), (mn:Mention {{mention_id: '{}'}}) \
             CREATE (d)-[:HAS]->(mn)",
            m.doc_id, m.mention_id,
        ))?;
        db.execute(&format!(
            "MATCH (mn:Mention {{mention_id: '{}'}}), (e:Entity {{entity_id: '{}'}}) \
             CREATE (mn)-[:OF]->(e)",
            m.mention_id, m.entity_id,
        ))?;
    }
    for r in &corpus.relations {
        db.execute(&format!(
            "CREATE (:Relation {{relation_id: '{}', predicate: '{}', confidence: {}}})",
            r.relation_id, r.predicate, r.confidence,
        ))?;
        db.execute(&format!(
            "MATCH (h:Entity {{entity_id: '{}'}}), (rn:Relation {{relation_id: '{}'}}) \
             CREATE (h)-[:HEAD]->(rn)",
            r.head, r.relation_id,
        ))?;
        db.execute(&format!(
            "MATCH (rn:Relation {{relation_id: '{}'}}), (t:Entity {{entity_id: '{}'}}) \
             CREATE (rn)-[:TAIL]->(t)",
            r.relation_id, r.tail,
        ))?;
        db.execute(&format!(
            "MATCH (rn:Relation {{relation_id: '{}'}}), (d:Document {{doc_id: '{}'}}) \
             CREATE (rn)-[:CITES]->(d)",
            r.relation_id, r.doc_id,
        ))?;
    }

    Ok((db, corpus))
}

fn cypher_string(s: &str) -> String {
    // Conservative escaping; corpus.json is trusted but we still escape
    // single quotes for safety.
    format!("'{}'", s.replace('\'', "\\'"))
}
