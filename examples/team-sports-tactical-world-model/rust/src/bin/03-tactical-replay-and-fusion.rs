//! Step 3 (Rust) — Tactical AS OF replay, fusion, and live-alert.
//!
//! Mirrors `03-tactical-replay-and-fusion.py` for the replay + fusion
//! parts, AND reaches the Rust-only surface for the live-alert pattern
//! Python can't do today: `arcflow_sdk::register_skill` fires the named
//! tactical-pattern query every time a position mutation matches the
//! trigger, with no polling loop.

use anyhow::Result;
use arcflow_sdk::SkillTrigger;
use team_sports_tactical_world_model::{
    make_db, EVENT_COUNTER_ORIGIN, EVENT_LINE_BREAK, EVENT_PRESS_START,
};

fn main() -> Result<()> {
    let db = make_db()?;

    // ---- A. Tactical AS OF reconstruction -----------------------------
    println!("=== Tactical AS OF reconstruction ===");
    for (label, frame) in [
        ("pressing trigger",       EVENT_PRESS_START + 6),
        ("line-breaking pass",     EVENT_LINE_BREAK),
        ("counter-attack origin",  EVENT_COUNTER_ORIGIN + 8),
    ] {
        println!("\n--- {label} @ frame {frame} ---");
        let q = format!(
            "MATCH (b:Ball)-[:POSITION_AT]->(p:Position) \
             WHERE p.frame = {frame} \
             RETURN p.x AS x, p.y AS y, p.team_possession AS poss"
        );
        for row in db.execute(&q)?.rows {
            println!("  Ball: {row:?}");
        }
    }

    // ---- B. Register a reactive skill for live alert (Rust-only) ------
    // This is the part Python can't reach today. The skill fires every
    // time a Position node is created that matches the trigger; the named
    // query computes the pressing count and surfaces the result without
    // a polling loop.
    println!("\n=== Live tactical alert via register_skill (Rust-only) ===");
    let trigger = SkillTrigger::NodeCreated {
        label: "Position".to_string(),
    };
    let alert_q = "MATCH (b:Ball)-[:POSITION_AT]->(bp:Position), \
                         (d:Player {team: 'defending'})-[:POSITION_AT]->(dp:Position) \
                   WHERE dp.frame = bp.frame \
                     AND (dp.x - bp.x) * (dp.x - bp.x) + (dp.y - bp.y) * (dp.y - bp.y) < 36 \
                   WITH bp.frame AS frame, count(d) AS pressers \
                   WHERE pressers >= 3 \
                   RETURN frame, pressers";
    arcflow_sdk::register_skill(
        &db,
        "tactics",
        "pressing-alert",
        trigger,
        alert_q,
    )?;
    println!("  registered: tactics/pressing-alert");
    println!("  trigger:    NodeCreated label='Position'");
    println!("  fires:      when >=3 defenders within 6m of ball");
    println!("  surface:    every matching mutation surfaces the alert without polling");

    println!("\n--- What this proves ---");
    println!("  - Frame-resolution reconstruction is one MATCH per event.");
    println!("  - The live-alert pattern (register_skill) is the Rust-only surface");
    println!("    that closes the loop from 'detect the pattern' to 'fire on the");
    println!("    mutation that triggered it' — no polling, no cron, no scheduler.");

    Ok(())
}
