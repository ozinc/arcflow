//! Step 02 (Rust) — confidence-weighted ER across multiple ID namespaces.
//!
//! Cross-source matching is one MATCH predicate; cross-source
//! disagreement detection is the same shape with a confidence filter.

use anyhow::Result;
use spatiotemporal_tactical_queries::make_db;

fn main() -> Result<()> {
    let db = make_db()?;

    println!("=== Identifier collisions across the id_a namespace ===");
    let q = "MATCH (e1:Entity), (e2:Entity) \
             WHERE e1.entity_id < e2.entity_id AND e1.id_a = e2.id_a \
             RETURN e1.entity_id AS a, e2.entity_id AS b, e1.id_a AS shared_id_a";
    for row in db.execute(q)?.rows {
        println!("  {row:?}");
    }

    println!("\n=== Cross-source spatial disagreement on alpha-00 at frame 18 ===");
    let q = "MATCH (e:Entity {entity_id: 'alpha-00'})-[r:OBSERVED_AT]->(f:Frame {frame_idx: 18}) \
             RETURN r.source AS source, r.x AS x, r.y AS y, r._confidence AS conf \
             ORDER BY r.source";
    for row in db.execute(q)?.rows {
        println!("  {row:?}");
    }

    println!("\n=== Entities missing id_c ===");
    let q = "MATCH (e:Entity) \
             WHERE e.id_c IS NULL \
             RETURN e.entity_id AS entity, e.id_a AS id_a, e.id_b AS id_b \
             ORDER BY e.entity_id";
    for row in db.execute(q)?.rows {
        println!("  {row:?}");
    }

    Ok(())
}
