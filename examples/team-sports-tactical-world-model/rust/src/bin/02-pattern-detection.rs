//! Step 2 (Rust) — Tactical pattern detection.
//!
//! Mirrors `02-pattern-detection.py`. Four patterns: pressing detection,
//! line-breaking pass, defensive compression, counter-attack origin.
//! Each is a single graph + spatial query against the substrate from
//! step 01.

use anyhow::Result;
use team_sports_tactical_world_model::{
    make_db, EVENT_COUNTER_ORIGIN, EVENT_LINE_BREAK, EVENT_PRESS_START,
};

const PRESS_RADIUS_M: f64 = 6.0;
const PRESS_MIN_COUNT: i64 = 3;
const LINE_BREAK_MIN_M: f64 = 15.0;
const COUNTER_MIN_M: f64 = 20.0;
const COUNTER_WINDOW_FR: u32 = 15;

fn main() -> Result<()> {
    let db = make_db()?;

    // ---- Pattern 1: pressing detection --------------------------------
    println!("=== Pattern 1: pressing detection ===");
    let r2 = PRESS_RADIUS_M * PRESS_RADIUS_M;
    let q1 = format!(
        "MATCH (b:Ball)-[:POSITION_AT]->(bp:Position), \
               (d:Player {{team: 'defending'}})-[:POSITION_AT]->(dp:Position) \
         WHERE bp.frame >= {start} AND bp.frame <= {end} \
           AND dp.frame = bp.frame \
           AND (dp.x - bp.x) * (dp.x - bp.x) + (dp.y - bp.y) * (dp.y - bp.y) < {r2} \
         RETURN bp.frame AS frame, count(d) AS pressers \
         ORDER BY bp.frame",
        start = EVENT_PRESS_START - 5,
        end = EVENT_PRESS_START + 20,
    );
    let result = db.execute(&q1)?;
    let mut triggers: Vec<u32> = Vec::new();
    for row in result.rows {
        let pressers: i64 = row.get("pressers")
            .and_then(|s| s.parse().ok()).unwrap_or(0);
        let frame: u32 = row.get("frame")
            .and_then(|s| s.parse().ok()).unwrap_or(0);
        if pressers >= PRESS_MIN_COUNT {
            triggers.push(frame);
        }
    }
    println!("  pressing-trigger frames: {triggers:?}");

    // ---- Pattern 2: line-breaking pass --------------------------------
    println!("\n=== Pattern 2: line-breaking pass ===");
    let ball_jumps = db.execute(
        "MATCH (b:Ball)-[:POSITION_AT]->(p:Position) \
         RETURN p.frame AS frame, p.y AS y, \
                p.y - lag(p.y, 1) OVER (ORDER BY p.frame) AS dy \
         ORDER BY p.frame",
    )?;
    for row in ball_jumps.rows {
        let dy_raw = row.get("dy").cloned().unwrap_or_default();
        if dy_raw.is_empty() || dy_raw == "NULL" {
            continue;
        }
        let dy: f64 = dy_raw.parse().unwrap_or(0.0);
        if dy < LINE_BREAK_MIN_M {
            continue;
        }
        let frame: u32 = row.get("frame")
            .and_then(|s| s.parse().ok()).unwrap_or(0);
        println!("  frame {frame}: ball forward jump {dy:.1} m (line-break candidate)");
    }

    // ---- Pattern 3: defensive compression -----------------------------
    println!("\n=== Pattern 3: defensive compression (back-five y-spread) ===");
    let q3 = format!(
        "MATCH (d:Player {{team: 'defending', role: 'DEF'}})-[:POSITION_AT]->(p:Position) \
         WHERE p.frame >= {start} AND p.frame <= {end} \
         RETURN p.frame AS frame, \
                max(p.y) - min(p.y) AS y_spread, \
                count(d) AS n_defs \
         ORDER BY p.frame",
        start = EVENT_PRESS_START - 5,
        end = EVENT_PRESS_START + 20,
    );
    let result = db.execute(&q3)?;
    for row in result.rows {
        let n_defs: i64 = row.get("n_defs")
            .and_then(|s| s.parse().ok()).unwrap_or(0);
        if n_defs < 3 {
            continue;
        }
        let frame: u32 = row.get("frame")
            .and_then(|s| s.parse().ok()).unwrap_or(0);
        let spread: f64 = row.get("y_spread")
            .and_then(|s| s.parse().ok()).unwrap_or(0.0);
        println!("  frame {frame}: y-spread = {spread:.1} m");
    }

    // ---- Pattern 4: counter-attack origin -----------------------------
    println!("\n=== Pattern 4: counter-attack origin ===");
    let flips = db.execute(
        "MATCH (b:Ball)-[:POSITION_AT]->(p:Position) \
         RETURN p.frame AS frame, p.team_possession AS poss, \
                lag(p.team_possession, 1) OVER (ORDER BY p.frame) AS prev_poss \
         ORDER BY p.frame",
    )?;
    let mut flip_frames = Vec::new();
    for row in flips.rows {
        let prev = row.get("prev_poss").cloned().unwrap_or_default();
        let poss = row.get("poss").cloned().unwrap_or_default();
        if !prev.is_empty() && prev != "NULL" && prev != poss {
            let f: u32 = row.get("frame").and_then(|s| s.parse().ok()).unwrap_or(0);
            flip_frames.push(f);
        }
    }
    println!("  possession-flip frames: {flip_frames:?}");

    for flip in flip_frames {
        let after = flip + COUNTER_WINDOW_FR;
        let q = format!(
            "MATCH (b:Ball)-[:POSITION_AT]->(p:Position) \
             WHERE p.frame = {flip} OR p.frame = {after} \
             RETURN p.frame AS frame, p.x AS x, p.y AS y \
             ORDER BY p.frame"
        );
        let res = db.execute(&q)?;
        if res.rows.len() == 2 {
            let x0: f64 = res.rows[0].get("x").and_then(|s| s.parse().ok()).unwrap_or(0.0);
            let y0: f64 = res.rows[0].get("y").and_then(|s| s.parse().ok()).unwrap_or(0.0);
            let x1: f64 = res.rows[1].get("x").and_then(|s| s.parse().ok()).unwrap_or(0.0);
            let y1: f64 = res.rows[1].get("y").and_then(|s| s.parse().ok()).unwrap_or(0.0);
            let dist = ((x1 - x0).powi(2) + (y1 - y0).powi(2)).sqrt();
            let crossed = (y0 < 0.0 && y1 > 0.0) || (y0 > 0.0 && y1 < 0.0);
            let counter = dist >= COUNTER_MIN_M && crossed;
            println!("  flip @ {flip}: dist={dist:.1} m, crossed half-way={crossed}, counter={counter}");
        }
    }

    let _ = EVENT_LINE_BREAK;
    let _ = EVENT_COUNTER_ORIGIN;
    Ok(())
}
