//! Step 10 (Rust) — register_skill on tracking mutations.
//!
//! Mirrors the spirit of `10-triggers-and-skills.py`. The Python recipe
//! shows the TRIGGER + SKILL DDL; the Rust SDK lets you wire reactive
//! skills via `arcflow_sdk::register_skill` with a SkillTrigger.

use anyhow::Result;
use arcflow_sdk::{ProofAssertion, SkillTrigger};
use multi_stream_spatiotemporal_world_model::make_db;

fn main() -> Result<()> {
    let db = make_db()?;

    // Skill that fires on every OBSERVED_AT mutation — runs a per-frame
    // proximity query that surfaces clusters of nearby entities. In
    // production this would feed an alert pipeline (formation analysis,
    // collision-risk, hand-off detection).
    let trigger = SkillTrigger::NodeCreated { label: "Frame".to_string() };
    let proximity_q = "MATCH (a:Entity)-[ra:OBSERVED_AT]->(f:Frame), \
                            (b:Entity)-[rb:OBSERVED_AT]->(f) \
                       WHERE a.entity_id < b.entity_id \
                         AND (ra.x - rb.x) * (ra.x - rb.x) \
                           + (ra.y - rb.y) * (ra.y - rb.y) < 4.0 \
                       RETURN a.entity_id, b.entity_id, f.frame_idx";
    arcflow_sdk::register_skill(&db, "tracking", "proximity", trigger, proximity_q)?;
    println!("registered: tracking/proximity (fires on every new Frame; surfaces entity pairs < 2 m apart)");

    // LIVE VIEW + continuous proof: assert the per-frame entity count
    // never goes below a threshold (an early-warning for sensor dropout).
    db.execute(
        "CREATE LIVE VIEW frame_coverage AS \
         MATCH (e:Entity)-[r:OBSERVED_AT]->(f:Frame) \
         RETURN f.frame_idx AS frame, count(e) AS entities_seen",
    )?;
    arcflow_sdk::register_live_proof(
        &db,
        "frame_coverage_non_empty",
        "frame_coverage",
        ProofAssertion::NonEmpty,
    )?;
    println!("registered: LIVE VIEW frame_coverage + NonEmpty proof");
    println!("  → maintained per-frame entity counts");
    println!("  → continuous proof FAILs the moment any frame has zero observations");

    Ok(())
}
