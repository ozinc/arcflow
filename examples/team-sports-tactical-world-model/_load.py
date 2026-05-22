"""
Synthesized fixture for the Team-Sports Tactical World Model cookbook.

Generates 5 minutes of 5 Hz tracking for 17 entities (8 attackers, 8
defenders, 1 ball) on a 105 m × 68 m field. The motion model is a
deterministic seeded random walk centred on role-appropriate baseline
positions (defenders deeper, forwards higher, etc.) with three tactical
events deliberately planted in time:

    EVENT_PRESS_START    = frame  450  (3:00)
        Defenders converge on the ball after a turnover.
    EVENT_LINE_BREAK     = frame  900  (6:00)
        Attacker plays the ball >15 m past the highest defender.
        (Note: total frames = 5 min × 5 Hz = 1500; event indices are
         compressed into a single fixture so all three appear.)
    EVENT_COUNTER_ORIGIN = frame 1200  (8:00 equivalent)
        Possession flips; ball travels >20 m and crosses half-way.

Three confidence tiers are written on every fact:
    observed  — Position nodes from the tracking stream         (0.95)
    inferred  — derived events from rule-based detectors         (0.80)
    predicted — coach-intent pressing plans + LLM commentary     (0.45-0.65)

Field origin is (0, 0) at the centre; attackers attack +y, defenders
defend -y. The half-way line is y = 0.
"""

import math
import random

from arcflow import ArcFlow

FIELD_LENGTH = 105.0
FIELD_WIDTH  = 68.0
FRAMES = 1500   # 5 min × 5 Hz
HZ = 5

EVENT_PRESS_START    = 450
EVENT_LINE_BREAK     = 900
EVENT_COUNTER_ORIGIN = 1200

# 8 attackers + 8 defenders + 1 ball. Roles drive baseline positions.
ATTACKERS = [
    ("A01", "FWD",  -10.0, +30.0),
    ("A02", "FWD",   +0.0, +32.0),
    ("A03", "FWD",  +10.0, +30.0),
    ("A04", "MID",  -20.0, +10.0),
    ("A05", "MID",   +0.0, +12.0),
    ("A06", "MID",  +20.0, +10.0),
    ("A07", "DEF",   -8.0, -10.0),
    ("A08", "DEF",   +8.0, -10.0),
]
DEFENDERS = [
    ("D01", "DEF", -15.0, -20.0),
    ("D02", "DEF",  -5.0, -22.0),
    ("D03", "DEF",  +5.0, -22.0),
    ("D04", "DEF", +15.0, -20.0),
    ("D05", "MID", -12.0,  -5.0),
    ("D06", "MID",  +0.0,  -3.0),
    ("D07", "MID", +12.0,  -5.0),
    ("D08", "FWD",  +0.0, +15.0),
]


def make_db(data_dir: str | None = None):
    """Build the operational tactical world model.

    data_dir=None  → in-memory.
    data_dir=path  → persistent (AS OF replay across process restarts).
    """
    rng = random.Random(31)
    db = ArcFlow(data_dir) if data_dir else ArcFlow()

    # ---- Field zones (observed reference data) -------------------------
    for zone_name, x0, y0, x1, y1 in [
        ("ATK_THIRD", -FIELD_WIDTH/2,  FIELD_LENGTH/6,   FIELD_WIDTH/2,  FIELD_LENGTH/2),
        ("MID_THIRD", -FIELD_WIDTH/2, -FIELD_LENGTH/6,   FIELD_WIDTH/2,  FIELD_LENGTH/6),
        ("DEF_THIRD", -FIELD_WIDTH/2, -FIELD_LENGTH/2,   FIELD_WIDTH/2, -FIELD_LENGTH/6),
    ]:
        db.execute(
            f"CREATE (:Zone {{name: '{zone_name}', "
            f"x0: {x0:.2f}, y0: {y0:.2f}, x1: {x1:.2f}, y1: {y1:.2f}, "
            f"_observation_class: 'observed', _confidence: 1.0, "
            f"_source: 'pitch_geometry_v1'}})"
        )

    # ---- Players (observed) --------------------------------------------
    player_specs = []
    for (pid, role, bx, by) in ATTACKERS:
        player_specs.append((["Player"], {
            "player_id": pid, "team": "attacking", "role": role,
            "baseline_x": bx, "baseline_y": by,
            "_observation_class": "observed", "_confidence": 1.0,
            "_source": "roster_v1",
        }))
    for (pid, role, bx, by) in DEFENDERS:
        player_specs.append((["Player"], {
            "player_id": pid, "team": "defending", "role": role,
            "baseline_x": bx, "baseline_y": by,
            "_observation_class": "observed", "_confidence": 1.0,
            "_source": "roster_v1",
        }))
    player_nodes = db.bulk_create_nodes(player_specs)
    by_pid = {player_specs[i][1]["player_id"]: nid
              for i, nid in enumerate(player_nodes)}

    # ---- Ball (observed) -----------------------------------------------
    ball_nodes = db.bulk_create_nodes([(["Ball"], {
        "ball_id": "BALL",
        "_observation_class": "observed", "_confidence": 1.0,
        "_source": "tracker_v1",
    })])
    ball_id = ball_nodes[0]

    # ---- Frame-by-frame positions --------------------------------------
    # Deterministic motion with planted tactical events. The frame numbers
    # match the constants at the top so step 02 can compute the same
    # patterns and step 03 can replay AS OF those seqs.
    pos_specs = []
    pos_edges = []  # (player_or_ball_id, position_node_index)
    ball_x, ball_y = 0.0, 0.0
    ball_team = "attacking"  # possession

    for frame in range(FRAMES):
        # Ball position: drift + planted events
        if frame == EVENT_PRESS_START:
            # Turnover — defenders take possession near defending half
            ball_x, ball_y = -3.0, -8.0
            ball_team = "defending"
        elif frame == EVENT_LINE_BREAK - 5:
            # Line-break setup: ball deep with attackers
            ball_x, ball_y = 0.0, 5.0
            ball_team = "attacking"
        elif frame == EVENT_LINE_BREAK:
            # Long forward pass: ball jumps +20m
            ball_y += 22.0
        elif frame == EVENT_COUNTER_ORIGIN:
            # Turnover then surge: ball flips possession, moves forward
            ball_x, ball_y = -5.0, -15.0
            ball_team = "defending"
        elif frame == EVENT_COUNTER_ORIGIN + 8:
            # 1.6 s later: ball has travelled across half-way
            ball_x, ball_y = -3.0, +10.0
        else:
            ball_x += rng.uniform(-0.4, 0.4)
            ball_y += rng.uniform(-0.6, 0.6)
            ball_x = max(-FIELD_WIDTH/2 + 1, min(FIELD_WIDTH/2 - 1, ball_x))
            ball_y = max(-FIELD_LENGTH/2 + 1, min(FIELD_LENGTH/2 - 1, ball_y))

        pos_specs.append((["Position"], {
            "entity": "BALL", "frame": frame,
            "x": round(ball_x, 3), "y": round(ball_y, 3),
            "team_possession": ball_team,
            "_observation_class": "observed", "_confidence": 0.95,
            "_source": "tracker_v1",
        }))
        pos_edges.append((ball_id, len(pos_specs) - 1))

        # Player positions: drift around baseline + press event
        for (pid, role, bx, by) in ATTACKERS + DEFENDERS:
            x = bx + rng.uniform(-1.5, 1.5)
            y = by + rng.uniform(-1.5, 1.5)
            # Press event: defenders converge on the ball
            if EVENT_PRESS_START <= frame < EVENT_PRESS_START + 12 \
               and pid.startswith("D") and role in {"DEF", "MID"}:
                # Lerp 60% toward ball position over 12 frames (~2.4s)
                t = (frame - EVENT_PRESS_START + 1) / 12.0
                x = bx + t * (ball_x - bx) * 0.7 + rng.uniform(-0.3, 0.3)
                y = by + t * (ball_y - by) * 0.7 + rng.uniform(-0.3, 0.3)
            pos_specs.append((["Position"], {
                "entity": pid, "frame": frame,
                "x": round(x, 3), "y": round(y, 3),
                "_observation_class": "observed", "_confidence": 0.95,
                "_source": "tracker_v1",
            }))
            pos_edges.append((by_pid[pid], len(pos_specs) - 1))

    position_nodes = db.bulk_create_nodes(pos_specs)
    db.bulk_create_relationships(
        "POSITION_AT",
        [(entity_id, position_nodes[idx], {})
         for entity_id, idx in pos_edges],
    )

    # ---- Predicted coach-intent: pressing trigger plan -----------------
    # Coach declared at half-time: "press hard when ball enters DEF_THIRD"
    # — predicted, mid confidence.
    db.execute(
        "CREATE (:CoachIntent {"
        "intent_id: 'press_def_third', "
        "trigger: 'ball_in_def_third', "
        "action: 'collapse_3_defenders_within_5m', "
        "_observation_class: 'predicted', _confidence: 0.65, "
        "_source: 'coach_plan_v1'"
        "})"
    )

    # ---- Predicted LLM commentary tags ---------------------------------
    commentary = [
        (EVENT_PRESS_START + 3,    "intense pressing trigger",        0.55),
        (EVENT_LINE_BREAK + 1,     "line-breaking pass",              0.70),
        (EVENT_COUNTER_ORIGIN + 5, "counter-attack origin",           0.60),
        (300,                       "tempo build-up",                  0.40),
        (750,                       "tactical retreat",                0.45),
    ]
    for frame, tag, conf in commentary:
        db.execute(
            "CREATE (:CommentaryTag {"
            f"frame: {frame}, tag: '{tag}', "
            f"_observation_class: 'predicted', _confidence: {conf}, "
            f"_source: 'commentary_llm_v1'"
            "})"
        )

    return db, by_pid, ball_id


def stats(db):
    out = {}
    for label, q in [
        ("zones",       "MATCH (z:Zone)          RETURN count(*) AS n"),
        ("players",     "MATCH (p:Player)        RETURN count(*) AS n"),
        ("balls",       "MATCH (b:Ball)          RETURN count(*) AS n"),
        ("positions",   "MATCH (p:Position)      RETURN count(*) AS n"),
        ("coach",       "MATCH (c:CoachIntent)   RETURN count(*) AS n"),
        ("commentary",  "MATCH (c:CommentaryTag) RETURN count(*) AS n"),
    ]:
        rows = list(db.execute(q))
        out[label] = int(rows[0]["n"])
    return out


if __name__ == "__main__":
    db, _, _ = make_db()
    print("operational tactical world model loaded:")
    for k, v in stats(db).items():
        print(f"  {k:12s}  {v:,}")
    db.close()
