"""
Synthesized loader: a small spatiotemporal world model with multi-source
identity, observed + predicted facts, and known disagreement, designed to
exercise the three tactical query patterns in this cookbook.

Shape:
- Two groups (alpha, beta), 11 entities each — generic team-tracking shape.
- One play, 60 frames @ 60 Hz (1 second of tracking).
- Each entity is observed by two sources: `tracker_a` and `tracker_b`,
  with deliberate confidence drift on a subset of entities to show
  disagreement detection.
- Each entity has a multi-namespace identity profile (id_a, id_b, id_c)
  with deliberate cross-source overlap and ambiguity for ER.
- A small set of `predicted` facts represents downstream model outputs.
"""

import random
from arcflow import ArcFlow

random.seed(7)


def make_db(data_dir: str | None = None):
    """Construct the world model. data_dir=None → in-memory; pass a path
    for AS OF replay across sessions (the WAL only lives on persistent
    instances).
    """
    db = ArcFlow(data_dir) if data_dir else ArcFlow()

    # --- 1. Entities (alpha/beta groups, 22 total) ---
    # FIXME(arcflow-core#12): Python None in bulk_create_nodes props
    #   misaligns subsequent rows' property values (silent corruption).
    #   Workaround: use sentinel "" for missing and filter with `= ''`
    #   in queries instead of IS NULL. Remove this workaround once
    #   arcflow-core#12 ships.
    entities = []
    for group in ("alpha", "beta"):
        for n in range(11):
            entities.append((["Entity"], {
                "entity_key": f"{group}-{n:02d}",
                "group": group,
                # multi-namespace identifiers — deliberate cross-source ambiguity
                "id_a": f"a-{group}-{n}",
                "id_b": f"b-{group}-{n}" if n < 9 else "",   # source-b loses last 2 per group
                "id_c": f"c-{group}-{n}" if n != 5 else f"c-{group}-other",  # one collision
            }))
    entity_ids = db.bulk_create_nodes(entities)
    by_key = {entities[i][1]["entity_key"]: nid for i, nid in enumerate(entity_ids)}

    # --- 2. Sources (tracker_a, tracker_b) ---
    source_ids = db.bulk_create_nodes([
        (["Source"], {"name": "tracker_a", "kind": "primary"}),
        (["Source"], {"name": "tracker_b", "kind": "audit"}),
    ])
    src_a, src_b = source_ids[0], source_ids[1]

    # --- 3. Frames (60 @ 60 Hz) + IN_PLAY → Play ---
    play_id = db.bulk_create_nodes([(["Play"], {"name": "play_001", "duration_s": 1.0})])[0]

    frame_specs = []
    for fi in range(60):
        frame_specs.append((["Frame"], {
            "frame_idx": fi,
            "play_id": "play_001",
            "ts_ms": fi * 16,  # 60 Hz tick
            "event": "ball_snap" if fi == 5 else ("decision_point" if fi == 30 else ""),
        }))
    frame_node_ids = db.bulk_create_nodes(frame_specs)
    fi_to_node = {i: nid for i, nid in enumerate(frame_node_ids)}

    db.bulk_create_relationships(
        "IN_PLAY",
        [(fnid, play_id, {}) for fnid in frame_node_ids],
    )

    # --- 4. OBSERVED_AT edges — both sources observe each entity each frame ---
    # Deliberate confidence drift: entities alpha-03 and beta-07 get tracker_b
    # confidence dropping from 0.95 → 0.45 over the play.
    drift_keys = {"alpha-03", "beta-07"}

    observed_a = []
    observed_b = []
    for fi in range(60):
        frame_node = fi_to_node[fi]
        for ent_spec, ent_node in zip(entities, entity_ids):
            key = ent_spec[1]["entity_key"]
            group = ent_spec[1]["group"]
            n = int(key.split("-")[1])
            # rough position: entities arranged in two lines, drifting downfield
            x = 50.0 + (5.0 if group == "beta" else -5.0) + (fi * 0.1)
            y = 5.0 + n * 4.0 + random.uniform(-0.3, 0.3)
            base_conf = 0.95
            # tracker_a is steady at 0.95
            observed_a.append((ent_node, frame_node, {
                "x": round(x + random.uniform(-0.2, 0.2), 3),
                "y": round(y, 3),
                "_confidence": base_conf,
                "_observation_class": "observed",
                "source": "tracker_a",
            }))
            # tracker_b drifts on selected entities
            if key in drift_keys:
                conf_b = round(0.95 - (fi / 60.0) * 0.50, 3)
            else:
                conf_b = 0.95
            observed_b.append((ent_node, frame_node, {
                "x": round(x + random.uniform(-0.4, 0.4), 3),
                "y": round(y + random.uniform(-0.2, 0.2), 3),
                "_confidence": conf_b,
                "_observation_class": "observed",
                "source": "tracker_b",
            }))
    db.bulk_create_relationships("OBSERVED_AT", observed_a)
    db.bulk_create_relationships("OBSERVED_AT", observed_b)

    # --- 5. Predicted facts — a downstream model emits 10 future-frame predictions ---
    # These land in the same graph as observed facts, distinguished by
    # _observation_class. Pattern: neural world model output integrated
    # alongside ground truth for unified queries.
    predicted = []
    # Predict where alpha-00 will be at frame 70 (10 frames into the future)
    future_frame = db.bulk_create_nodes([(["Frame"], {
        "frame_idx": 70,
        "play_id": "play_001",
        "ts_ms": 70 * 16,
        "event": "predicted_horizon",
    })])[0]
    db.bulk_create_relationships("IN_PLAY", [(future_frame, play_id, {})])

    for n in range(11):
        predicted.append((by_key[f"alpha-{n:02d}"], future_frame, {
            "x": round(57.0 + n * 0.1, 3),
            "y": round(5.0 + n * 4.0, 3),
            "_confidence": 0.62,
            "_observation_class": "predicted",
            "source": "trajectory_model_v3",
        }))
    db.bulk_create_relationships("OBSERVED_AT", predicted)

    # --- 6. Stats ---
    stats = {}
    for label, q in [
        ("entities", "MATCH (e:Entity) RETURN count(*) AS n"),
        ("frames", "MATCH (f:Frame) RETURN count(*) AS n"),
        ("plays", "MATCH (p:Play) RETURN count(*) AS n"),
        ("observed", "MATCH ()-[r:OBSERVED_AT]->() WHERE r._observation_class = 'observed' RETURN count(r) AS n"),
        ("predicted", "MATCH ()-[r:OBSERVED_AT]->() WHERE r._observation_class = 'predicted' RETURN count(r) AS n"),
    ]:
        rows = list(db.execute(q))
        stats[label] = int(rows[0]["n"])
    return db, stats


if __name__ == "__main__":
    db, stats = make_db()
    print("Loaded:")
    for k, v in stats.items():
        print(f"  {k:12s}  {v:,}")
    db.close()
