//! Shared fixture for the Team-Sports Tactical World Model Rust SDK example.
//!
//! Same fixture shape as `_load.py`: 17 entities × 1500 frames at 5 Hz on
//! a 105 m × 68 m field, with three deliberately planted tactical events
//! (pressing trigger, line-breaking pass, counter-attack origin). Every
//! fact carries `_observation_class` + `_confidence` + `_source`.

use anyhow::Result;
use arcflow_sdk::ConcurrentStore;
use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha8Rng;

pub const FRAMES: u32 = 1500;
pub const HZ: u32 = 5;
pub const EVENT_PRESS_START: u32 = 450;
pub const EVENT_LINE_BREAK: u32 = 900;
pub const EVENT_COUNTER_ORIGIN: u32 = 1200;

pub const ATTACKERS: &[(&str, &str, f64, f64)] = &[
    ("A01", "FWD", -10.0,  30.0),
    ("A02", "FWD",   0.0,  32.0),
    ("A03", "FWD",  10.0,  30.0),
    ("A04", "MID", -20.0,  10.0),
    ("A05", "MID",   0.0,  12.0),
    ("A06", "MID",  20.0,  10.0),
    ("A07", "DEF",  -8.0, -10.0),
    ("A08", "DEF",   8.0, -10.0),
];
pub const DEFENDERS: &[(&str, &str, f64, f64)] = &[
    ("D01", "DEF", -15.0, -20.0),
    ("D02", "DEF",  -5.0, -22.0),
    ("D03", "DEF",   5.0, -22.0),
    ("D04", "DEF",  15.0, -20.0),
    ("D05", "MID", -12.0,  -5.0),
    ("D06", "MID",   0.0,  -3.0),
    ("D07", "MID",  12.0,  -5.0),
    ("D08", "FWD",   0.0,  15.0),
];

pub fn make_db() -> Result<ConcurrentStore> {
    let mut rng = ChaCha8Rng::seed_from_u64(31);
    let db = arcflow_sdk::open_concurrent();

    // Field zones
    for (name, x0, y0, x1, y1) in [
        ("ATK_THIRD", -34.0,  17.5,  34.0,  52.5),
        ("MID_THIRD", -34.0, -17.5,  34.0,  17.5),
        ("DEF_THIRD", -34.0, -52.5,  34.0, -17.5),
    ] {
        db.execute(&format!(
            "CREATE (:Zone {{name: '{name}', \
                x0: {x0}, y0: {y0}, x1: {x1}, y1: {y1}, \
                _observation_class: 'observed', _confidence: 1.0, \
                _source: 'pitch_geometry_v1'}})"
        ))?;
    }

    // Players
    for (pid, role, bx, by) in ATTACKERS {
        db.execute(&format!(
            "CREATE (:Player {{player_id: '{pid}', team: 'attacking', role: '{role}', \
                baseline_x: {bx}, baseline_y: {by}, \
                _observation_class: 'observed', _confidence: 1.0, \
                _source: 'roster_v1'}})"
        ))?;
    }
    for (pid, role, bx, by) in DEFENDERS {
        db.execute(&format!(
            "CREATE (:Player {{player_id: '{pid}', team: 'defending', role: '{role}', \
                baseline_x: {bx}, baseline_y: {by}, \
                _observation_class: 'observed', _confidence: 1.0, \
                _source: 'roster_v1'}})"
        ))?;
    }

    // Ball
    db.execute(
        "CREATE (:Ball {ball_id: 'BALL', \
            _observation_class: 'observed', _confidence: 1.0, \
            _source: 'tracker_v1'})",
    )?;

    // Frame-by-frame positions
    let mut ball_x = 0.0_f64;
    let mut ball_y = 0.0_f64;
    let mut ball_team = "attacking";
    for frame in 0..FRAMES {
        // Planted events
        match frame {
            f if f == EVENT_PRESS_START => {
                ball_x = -3.0; ball_y = -8.0; ball_team = "defending";
            }
            f if f == EVENT_LINE_BREAK - 5 => {
                ball_x = 0.0; ball_y = 5.0; ball_team = "attacking";
            }
            f if f == EVENT_LINE_BREAK => {
                ball_y += 22.0;
            }
            f if f == EVENT_COUNTER_ORIGIN => {
                ball_x = -5.0; ball_y = -15.0; ball_team = "defending";
            }
            f if f == EVENT_COUNTER_ORIGIN + 8 => {
                ball_x = -3.0; ball_y = 10.0;
            }
            _ => {
                ball_x = (ball_x + rng.gen_range(-0.4..0.4)).clamp(-33.0, 33.0);
                ball_y = (ball_y + rng.gen_range(-0.6..0.6)).clamp(-51.0, 51.0);
            }
        }
        db.execute(&format!(
            "MATCH (b:Ball) \
             CREATE (b)-[:POSITION_AT]->(:Position {{ \
                entity: 'BALL', frame: {frame}, \
                x: {ball_x:.3}, y: {ball_y:.3}, team_possession: '{ball_team}', \
                _observation_class: 'observed', _confidence: 0.95, \
                _source: 'tracker_v1' \
             }})"
        ))?;

        // Player positions (concise: drift around baseline + press behaviour)
        for (pid, role, bx, by) in ATTACKERS.iter().chain(DEFENDERS.iter()) {
            let mut x: f64 = bx + rng.gen_range(-1.5..1.5);
            let mut y: f64 = by + rng.gen_range(-1.5..1.5);
            let in_press = (EVENT_PRESS_START..EVENT_PRESS_START + 12).contains(&frame);
            if in_press && pid.starts_with('D') && (*role == "DEF" || *role == "MID") {
                let t = (frame - EVENT_PRESS_START + 1) as f64 / 12.0;
                x = bx + t * (ball_x - bx) * 0.7 + rng.gen_range(-0.3..0.3);
                y = by + t * (ball_y - by) * 0.7 + rng.gen_range(-0.3..0.3);
            }
            db.execute(&format!(
                "MATCH (p:Player {{player_id: '{pid}'}}) \
                 CREATE (p)-[:POSITION_AT]->(:Position {{ \
                    entity: '{pid}', frame: {frame}, x: {x:.3}, y: {y:.3}, \
                    _observation_class: 'observed', _confidence: 0.95, \
                    _source: 'tracker_v1' \
                 }})"
            ))?;
        }
    }

    // Coach-intent + commentary
    db.execute(
        "CREATE (:CoachIntent {intent_id: 'press_def_third', \
            trigger: 'ball_in_def_third', \
            action: 'collapse_3_defenders_within_5m', \
            _observation_class: 'predicted', _confidence: 0.65, \
            _source: 'coach_plan_v1'})",
    )?;

    for (frame, tag, conf) in [
        (453,  "intense pressing trigger", 0.55),
        (901,  "line-breaking pass",       0.70),
        (1205, "counter-attack origin",    0.60),
        (300,  "tempo build-up",           0.40),
        (750,  "tactical retreat",         0.45),
    ] {
        db.execute(&format!(
            "CREATE (:CommentaryTag {{frame: {frame}, tag: '{tag}', \
                _observation_class: 'predicted', _confidence: {conf}, \
                _source: 'commentary_llm_v1'}})"
        ))?;
    }

    Ok(db)
}
