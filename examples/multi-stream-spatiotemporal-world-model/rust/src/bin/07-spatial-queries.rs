//! Step 07 (Rust) — spatial KNN, radius, bbox queries.
//!
//! Mirrors `07-spatial-queries.py`. The R*-tree spatial index is over
//! edge properties (x/y on OBSERVED_AT), so per-frame snapshots query
//! in sub-millisecond regardless of how many frames the session has.

use anyhow::Result;
use multi_stream_spatiotemporal_world_model::{make_db, FRAMES};

fn main() -> Result<()> {
    let db = make_db()?;
    let snap_frame = FRAMES / 2;

    println!("=== KNN: 5 nearest entities to (60, 40) at frame {snap_frame} ===");
    let knn = format!(
        "MATCH (e:Entity)-[r:OBSERVED_AT]->(f:Frame {{frame_idx: {snap_frame}}}) \
         RETURN e.entity_id AS id, r.x AS x, r.y AS y, \
                (r.x - 60.0) * (r.x - 60.0) + (r.y - 40.0) * (r.y - 40.0) AS dist_sq \
         ORDER BY dist_sq LIMIT 5"
    );
    for row in db.execute(&knn)?.rows {
        println!("  {row:?}");
    }

    println!("\n=== RADIUS: entities within 15 m of (60, 40) at frame {snap_frame} ===");
    let rad = format!(
        "MATCH (e:Entity)-[r:OBSERVED_AT]->(f:Frame {{frame_idx: {snap_frame}}}) \
         WHERE (r.x - 60.0) * (r.x - 60.0) + (r.y - 40.0) * (r.y - 40.0) < 225 \
         RETURN e.entity_id AS id, r.x AS x, r.y AS y"
    );
    for row in db.execute(&rad)?.rows {
        println!("  {row:?}");
    }

    println!("\n=== BBOX: entities inside [40-80] × [20-60] at frame {snap_frame} ===");
    let bbox = format!(
        "MATCH (e:Entity)-[r:OBSERVED_AT]->(f:Frame {{frame_idx: {snap_frame}}}) \
         WHERE r.x >= 40 AND r.x <= 80 AND r.y >= 20 AND r.y <= 60 \
         RETURN e.entity_id AS id, e.team AS team, r.x AS x, r.y AS y \
         ORDER BY id"
    );
    for row in db.execute(&bbox)?.rows {
        println!("  {row:?}");
    }

    Ok(())
}
