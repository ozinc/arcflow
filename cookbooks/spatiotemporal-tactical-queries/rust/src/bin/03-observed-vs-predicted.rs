//! Step 03 (Rust) — observed-vs-predicted fusion and calibration analysis.

use anyhow::Result;
use spatiotemporal_tactical_queries::make_db;

fn main() -> Result<()> {
    let db = make_db()?;

    println!("=== Trust-tier filter: only observed facts ===");
    let q = "MATCH (e:Entity)-[r:OBSERVED_AT]->(f:Frame {frame_idx: 30}) \
             WHERE r._observation_class = 'observed' AND r._confidence >= 0.9 \
             RETURN e.entity_id AS id, r.source AS source, r.x AS x, r.y AS y \
             ORDER BY e.entity_id LIMIT 8";
    for row in db.execute(q)?.rows {
        println!("  {row:?}");
    }

    println!("\n=== Predicted facts (trajectory model, future frame 80) ===");
    let q = "MATCH (e:Entity)-[p:PREDICTED_AT]->(f:Frame {frame_idx: 80}) \
             RETURN e.entity_id AS id, p.x AS x, p.y AS y, p._confidence AS conf \
             ORDER BY e.entity_id";
    for row in db.execute(q)?.rows {
        println!("  {row:?}");
    }

    println!("\n=== Calibration: observed at frame 30 alongside predicted at frame 80 ===");
    // The same entity carries both edges; one MATCH joins them.
    let q = "MATCH (e:Entity)-[obs:OBSERVED_AT {source: 'A'}]->(:Frame {frame_idx: 30}), \
                   (e)-[pred:PREDICTED_AT]->(:Frame {frame_idx: 80}) \
             RETURN e.entity_id AS id, obs.x AS obs_x, pred.x AS pred_x, \
                    pred.x - obs.x AS expected_dx \
             ORDER BY e.entity_id";
    for row in db.execute(q)?.rows {
        println!("  {row:?}");
    }

    Ok(())
}
