"""
Observed vs predicted facts in a single graph — neural-WM integration.

Pattern: ArcFlow stores every fact with an `_observation_class` of
`observed`, `inferred`, or `predicted`. Sensor readings land as observed.
Symbolic derivations land as inferred. Neural-world-model outputs land
as predicted. They coexist in the same graph and the same query, with
one extra predicate to filter by trust tier.

This recipe shows how to:
1. Pull observed facts at the present.
2. Pull predicted facts at the same horizon.
3. Compare them — what did the model get right? What drifted?
"""

from _load import make_db


def f(s):
    """Coerce a typed cell into a float; tolerate missing values."""
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def main():
    db, stats = make_db()
    print(f"Loaded: {stats}\n")

    # 1. Counts by observation class.
    print("=== Q1: Fact counts by _observation_class ===")
    for r in db.execute("""
        MATCH ()-[r:OBSERVED_AT]->()
        WITH r._observation_class AS klass, count(*) AS n
        RETURN klass, n
        ORDER BY n DESC
    """):
        print(f"  {dict(r)}")

    # 2. Predicted positions for the alpha team at the prediction horizon.
    print("\n=== Q2: Predicted positions for alpha-team @ frame 70 ===")
    for r in list(db.execute("""
        MATCH (e:Entity {group: 'alpha'})-[r:OBSERVED_AT]->(f:Frame {frame_idx: 70})
        WHERE r._observation_class = 'predicted'
        RETURN e.entity_key AS entity, r.x AS x, r.y AS y, r._confidence AS conf, r.source AS source
        ORDER BY entity
    """))[:5]:
        print(f"  {dict(r)}")

    # 3. Last observed position for the same alpha team at frame 59.
    print("\n=== Q3: Last observed positions (frame 59) for alpha-team ===")
    for r in list(db.execute("""
        MATCH (e:Entity {group: 'alpha'})-[r:OBSERVED_AT {source: 'tracker_a'}]->(f:Frame {frame_idx: 59})
        RETURN e.entity_key AS entity, r.x AS x, r.y AS y, r._confidence AS conf
        ORDER BY entity
    """))[:5]:
        print(f"  {dict(r)}")

    # 4. Drift between observed (frame 59) and predicted (frame 70) per
    #    entity — one query, observed and predicted joined via the shared
    #    entity, deltas computed in WITH.
    print("\n=== Q4: Drift between observed (frame 59) and predicted (frame 70) per entity ===")
    rows = list(db.execute("""
        MATCH (e:Entity {group: 'alpha'})-[obs:OBSERVED_AT {source: 'tracker_a'}]->(of:Frame {frame_idx: 59})
        MATCH (e)-[pred:OBSERVED_AT]->(pf:Frame {frame_idx: 70})
        WHERE pred._observation_class = 'predicted'
        WITH e.entity_key AS entity,
             obs.x AS obs_x, obs.y AS obs_y,
             pred.x AS pred_x, pred.y AS pred_y,
             (pred.x - obs.x) AS dx, (pred.y - obs.y) AS dy,
             pred._confidence AS conf
        RETURN entity, obs_x, pred_x, dx, obs_y, pred_y, dy, conf
        ORDER BY entity
    """))
    print(f"  {'entity':12s}  {'obs_x':>8s} → {'pred_x':>8s}   {'obs_y':>8s} → {'pred_y':>8s}   {'conf':>5s}")
    for r in rows[:5]:
        ox, px, oy, py, dx, dy = (f(r[k]) for k in ("obs_x", "pred_x", "obs_y", "pred_y", "dx", "dy"))
        print(f"  {r['entity']:12s}  {ox:>8.2f} → {px:>8.2f}   {oy:>8.2f} → {py:>8.2f}   {r['conf']:>5s}  (Δ {dx:+.2f}, {dy:+.2f})")

    # 5. Trust-tiered retrieval — the operational filter.
    print("\n=== Q5: Trust-tiered retrieval (operational filter) ===")
    rows = list(db.execute("""
        MATCH ()-[r:OBSERVED_AT]->()
        WHERE r._observation_class = 'observed'
        WITH r._confidence AS conf, count(*) AS n
        RETURN conf, n
        ORDER BY conf DESC
    """))
    for r in rows[:5]:
        print(f"  observed @ conf={r['conf']}: {r['n']}")

    rows = list(db.execute("""
        MATCH ()-[r:OBSERVED_AT]->()
        WHERE r._observation_class = 'predicted'
        WITH r._confidence AS conf, count(*) AS n
        RETURN conf, n
    """))
    for r in rows:
        print(f"  predicted @ conf={r['conf']}: {r['n']}")

    print("\nObservations:")
    print("  - Observed and predicted facts coexist in one graph — no parallel store.")
    print("  - Trust-tier filter is one WHERE predicate, not a separate query path.")
    print("  - Models that emit 'predicted' facts plug into existing graph queries unchanged.")
    print("  - Drift / calibration is a paired MATCH on the shared entity, deltas in WITH.")

    db.close()


if __name__ == "__main__":
    main()
