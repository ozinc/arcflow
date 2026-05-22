//! Step 02 (Rust) — robotics control replay via AS OF seq.
//!
//! A robot perceives an obstacle, fires an avoid action, then the
//! perception updates. The safety reviewer asks: "what did perception
//! show when the avoid fired?"

use anyhow::Result;

fn main() -> Result<()> {
    let db = arcflow_sdk::open_concurrent();

    // seq 1: initial obstacle perception
    db.execute(
        "CREATE (:Obstacle {id: 'obs-001', x: 2.5, y: 1.1, distance_m: 0.8, \
            _observation_class: 'observed', _confidence: 0.91, \
            _source: 'lidar_v1'})",
    )?;
    println!("seq 1: obstacle obs-001 perceived at (2.5, 1.1), distance 0.8 m");

    // seq 2: robot fires avoid action based on perception at seq 1
    db.execute(
        "CREATE (:ControlAction {id: 'CA-7732', action: 'AVOID_LEFT', \
            triggered_by_obstacle: 'obs-001', \
            _observation_class: 'observed', _confidence: 1.0, \
            _source: 'controller_v1'})",
    )?;
    println!("seq 2: control action CA-7732 (AVOID_LEFT) fired");

    // seq 3: perception updates — obstacle position refined
    db.execute(
        "MATCH (o:Obstacle {id: 'obs-001'}) \
         SET o.x = 2.7, o.y = 1.2, o.distance_m = 1.0",
    )?;
    println!("seq 3: perception refined to (2.7, 1.2), distance 1.0 m");

    // Replay: what did the controller see at fire time?
    println!("\n--- Safety review: perception state at CA-7732 fire time ---");
    let q = "MATCH (o:Obstacle {id: 'obs-001'}) \
             AS OF seq 2 \
             RETURN o.x AS x, o.y AS y, o.distance_m AS d, o._confidence AS conf";
    for row in db.execute(q)?.rows {
        println!("  AS OF seq 2: {row:?}");
    }

    let q_now = "MATCH (o:Obstacle {id: 'obs-001'}) \
                 RETURN o.x AS x, o.y AS y, o.distance_m AS d";
    for row in db.execute(q_now)?.rows {
        println!("  current:    {row:?}");
    }

    println!("\n  Distance at fire time (0.8 m) justified the AVOID — within safety threshold.");
    println!("  Current distance (1.0 m) would not have triggered.");

    Ok(())
}
