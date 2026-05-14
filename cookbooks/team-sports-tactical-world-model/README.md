# Team-Sports Tactical World Model

> **Advanced tactical pattern detection — pressing triggers, line-breaking
> passes, defensive compression, counter-attack origins — as graph + spatial
> queries against an operational world model that holds every player, every
> frame, every confidence.**

**Audience:** python · sports-analytics · ML engineer · agent builder
**Runtime:** under 3 minutes total
**Pins:** `oz-arcflow==0.7.1`

## The four hard problems this addresses

Advanced team-sports tactical analysis is one of the most demanding
spatial-temporal-multi-entity problems anyone tackles outside autonomous
driving. The default stack — tracking provider gives you XY positions,
your team writes a Python notebook, a coach asks a question, somebody
spends a week — ships four integration-tax failures the moment you try
to answer non-trivial tactical questions in time to influence the next
match:

1. **Spatial-temporal pattern matching at scale.** A tactical event
   ("pressing trigger") is defined by joint conditions across multiple
   entities over a time window — *3+ defenders within 5 m of the ball
   within 2 s of a turnover*. Naive Python at 25 Hz × 22 players × 90
   minutes = 3 M frames × ~500 pairwise distance checks per frame =
   hours of compute for one question. Pre-computed pattern caches go
   stale by next match; the analyst is always one model version behind.

2. **Tactical replay at frame resolution.** *"What did the defensive
   shape look like the moment the breakaway started?"* Standard sports
   analytics platforms store derived statistics (xG, possession %, pass
   completion) — not the full spatial state. To replay the moment, you
   re-run optical tracking from video. The system you wanted in 30 s is
   a video-processing job an hour later.

3. **Multi-source tactical fusion.** Tracking is observed (high
   confidence, occasionally occluded). Coach-prescribed pressing-trigger
   plans are predicted (mid confidence, drift across the match).
   LLM-emitted commentary tags ("counter-attack starting") are predicted
   at low confidence with high recall. Stitching these three sources
   into one tactical alert means a JOIN chain across four schemas, each
   with its own confidence column, each silently mistyped when someone
   refactors. The analyst trusts the LLM tag as if it were observed
   because the trust tier was lost in the JOIN.

4. **Live tactical alerts during a match.** "Alert when the pressing
   trigger conditions are met" should fire within frame-time of the
   conditions being met. Recomputing per-frame in Python doesn't keep
   up; pre-computing a tactical-event timeline before the match
   doesn't react to in-match adjustments. The coach gets the alert at
   half-time.

Each one is solvable in isolation with enough engineering. Solving all
four against one persistent, queryable, replayable world model is what
this recipe is for.

## What you'll build

A small operational world model holding 5 minutes of 5 Hz tracking data
for 17 entities (8 attackers + 8 defenders + 1 ball), with three
tactical events deliberately planted: a coordinated press, a
line-breaking pass, and a counter-attack origin. Then the three
patterns this graph shape makes one-query-each:

1. **`01-tactical-world-model.py`** — load the substrate. Field zones
   as labeled nodes, players with role + jersey, frame-by-frame
   `Position` nodes, every fact tagged with `_observation_class` +
   `_confidence` + `_source`. The shape is the same the substrate
   flagship `multi-stream-spatiotemporal-world-model` builds at 60 Hz —
   smaller here for cookbook scale.

2. **`02-pattern-detection.py`** — express tactical events as graph +
   spatial queries:
   - **Pressing detection** — count of defenders within `R` metres of
     the ball, over a sliding `T`-second window after a turnover.
     Window-function aggregation; one query.
   - **Line-breaking pass** — ball moves more than `D` metres past the
     highest defensive line within `T` seconds. Spatial predicate
     joined to the time delta.
   - **Defensive compression** — convex-hull area of the back five
     shrinks below threshold over `T` seconds. Spatial aggregation
     within a time window.
   - **Counter-attack origin** — turnover + ball travels more than
     `D` metres within `T` seconds + crosses the half-way line.
     Three predicates, one MATCH.

3. **`03-tactical-replay-and-fusion.py`** — `AS OF seq` reconstruction
   of each tactical event: what was the formation, who was open, who
   covered. Then fuse tracking-observed positions with predicted
   coach-intent (pressing-trigger plans) and predicted LLM commentary
   tags — same MATCH shape over three confidence tiers, the same
   evidence-algebra pattern as the algo-trading recipe applied to
   tactics instead of signals.

## Run

```bash
uv sync
uv run python 01-tactical-world-model.py
uv run python 02-pattern-detection.py
uv run python 03-tactical-replay-and-fusion.py
```

`_load.py` is the shared fixture: 17 entities × 1500 frames at 5 Hz with
deterministic motion + 3 planted tactical events. Synthesized; no
real-world matches. Loads in under a second.

## Capabilities exercised

| Capability | What it does for tactics |
|---|---|
| `point({x, y})` spatial primitives + distance / nearest-neighbour | Pressing-trigger distance counts, defensive-line max-y queries |
| Window functions (`lag` · `row_number`) with `OVER (PARTITION BY entity ORDER BY frame)` | Frame-to-frame deltas (velocity, separation rate, hull-area change) |
| `AS OF seq` temporal replay with snapshot isolation | Frame-resolution reconstruction of formation at the moment an event fired |
| `_observation_class` + `_confidence` first-class on every fact | Tracking observed / coach-intent predicted / LLM-tagged predicted, fused in one MATCH |
| `CREATE LIVE VIEW` + `register_skill` (Rust today) | Live tactical alerts as standing queries — frame-time, no polling |

## Rust SDK alongside

The `rust/` subfolder ships the same recipe via the Rust SDK, including
the live-alert pattern (`register_skill` firing on the pressing-trigger
condition) that Python can't reach today.

## See also

- [`multi-stream-spatiotemporal-world-model`](../multi-stream-spatiotemporal-world-model/) — the 60 Hz substrate this recipe builds on (full multi-stream / coordinate-frame / LIVE / triggers flagship)
- [`spatiotemporal-tactical-queries`](../spatiotemporal-tactical-queries/) — `AS OF` counterfactuals + confidence-weighted entity resolution
- [`algo-trading-world-model`](../algo-trading-world-model/) — the same evidence-algebra pattern applied to financial signals
