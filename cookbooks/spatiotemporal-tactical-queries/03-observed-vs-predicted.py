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
    """Coerce typed cell to float (engine returns string today)."""
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
    #    Inline property predicate avoids the WHERE-chain quirk.
    print("\n=== Q2: Predicted positions for alpha-team @ frame 70 ===")
    pred_rows = list(db.execute("""
        MATCH (e:Entity {group: 'alpha'})-[r:OBSERVED_AT]->(f:Frame {frame_idx: 70})
        WHERE r._observation_class = 'predicted'
        RETURN e.entity_key AS entity, r.x AS x, r.y AS y, r._confidence AS conf, r.source AS source
        ORDER BY entity
    """))
    for r in pred_rows[:5]:
        print(f"  {dict(r)}")

    # 3. Last observed position for the same alpha team at frame 59.
    #    Same inline-property pattern.
    print("\n=== Q3: Last observed positions (frame 59) for alpha-team ===")
    obs_rows = list(db.execute("""
        MATCH (e:Entity {group: 'alpha'})-[r:OBSERVED_AT {source: 'tracker_a'}]->(f:Frame {frame_idx: 59})
        RETURN e.entity_key AS entity, r.x AS x, r.y AS y, r._confidence AS conf
        ORDER BY entity
    """))
    for r in obs_rows[:5]:
        print(f"  {dict(r)}")

    # 4. Compute drift in Python (engine arithmetic-in-WITH not yet supported)
    #    — but the underlying graph data is already joined: same entities,
    #    same group, surfaced through one query each. Pair them by entity_key.
    print("\n=== Q4: Drift between observed (frame 59) and predicted (frame 70) per entity ===")
    obs_by_key = {r["entity"]: r for r in obs_rows}
    print(f"  {'entity':12s}  {'obs_x':>8s} → {'pred_x':>8s}   {'obs_y':>8s} → {'pred_y':>8s}   {'pred_conf':>9s}")
    for p in pred_rows[:5]:
        ent = p["entity"]
        o = obs_by_key.get(ent)
        if not o:
            continue
        ox, py = f(o["x"]), f(p["y"])
        ox, oy = f(o["x"]), f(o["y"])
        px, py = f(p["x"]), f(p["y"])
        dx = px - ox
        dy = py - oy
        print(f"  {ent:12s}  {ox:>8.2f} → {px:>8.2f}   {oy:>8.2f} → {py:>8.2f}   {p['conf']:>9s}  (Δ {dx:+.2f}, {dy:+.2f})")

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
    print("  - Drift / calibration is a paired MATCH on the shared entity_key.")

    db.close()


if __name__ == "__main__":
    main()
