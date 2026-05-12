# Algo-Trading World Model

> **Your alpha lives in models. Your evidence lives here.**
>
> The persistent, queryable, replayable operational world model your
> LLM-driven trading agent reads, writes, and remembers from — the
> integration stack elite quant shops spend $10M+ building, shipped as a
> library and runnable on your laptop in three minutes.

**Audience:** quant developers · ML engineers · LLM-agent builders
**Runtime:** under 3 minutes total
**Pins:** `oz-arcflow==1.6.7`

---

## The state of the art, and the gap it leaves

The X discourse in May 2026 converged on the same insight every elite
quant shop has lived by for years:

> Math and data are table stakes. **Systems-mastery is the actual moat.**

The "black magic" of the top 0.1% — Jane Street, Citadel Securities,
Hudson River Trading, Renaissance — isn't a clever indicator or a magic
feature. It's the integrated *stack* underneath every strategy:

- Petabyte-scale tick history that is queryable as of any past moment
- Derived signals that maintain themselves as new ticks arrive
- Confidence and provenance tracked on every fact, propagated through
  every operator
- A backtest that is mathematically equivalent to the live system,
  because both run the same operator plan against the same persistent
  store

That stack used to require a fifty-person infrastructure team and tens
of millions of dollars in custom engineering. Everyone else either
chases decaying technical-analysis edges in spreadsheets, or wires
together five silos (vector DB · SQL/timeseries · message bus ·
scheduler · audit log) and pays the drift tax forever — every divergence
between batch and live a fresh debugging tax.

**This cookbook is the bootstrap version of that stack** — three
patterns deep, on a single laptop, in 180 seconds.

---

## The world-model framing

OZ distinguishes two distinct things that today share the name
"world model" (see [/concepts/world-model](/concepts/world-model)):

| Layer | Examples | Role |
|---|---|---|
| **Foundation models** | Claude, GPT, Gemini | Generate alpha hypotheses, narrate news, classify sentiment, write code |
| **Neural world models** | DreamerV3, Sora, world-foundation models | Simulate possible futures given an action — generative, ephemeral output |
| **Operational world model** | **ArcFlow** | Persist every tick, signal, decision, and revision with confidence + temporal index; serve `AS OF seq N` replay; maintain cascading queries |

For an algo-trading agent the mapping is direct. Your LLM proposes
strategies. Your predictive models (HMM regime classifier, OBI
predictor, LSTM forward forecast) translate market state into signals.
**ArcFlow records what actually happened**, with three epistemic states
that come back exactly as written:

- **observed** — trades from the tape, fundamentals filings, the agent's
  own decisions. `_confidence ≥ 0.95`.
- **inferred** — derived from observed facts via your own pipelines.
  Rolling stats, cross-sectional ranks, sector aggregations. `_confidence
  0.70–0.85`.
- **predicted** — model emissions. LLM-tagged news sentiment, HMM regime
  beliefs, ML forward forecasts. `_confidence 0.30–0.70`.

The trading agent isn't just *reading* a world model. It **writes its
own decisions back into it**. When you `AS OF seq` replay six weeks
later, you don't just see "what was the market doing" — you see "what
did I know, what did I think, and what did I decide", together,
deterministically, bit-for-bit. That single property is the audit trail
every regulator wants AND the dataset every causal-inference model wants.
They are the same dataset.

---

## What this recipe ships

### Step 1 — Persistent memory · `AS OF seq` replay

```python
# WAL seq 1: the agent decides
db.execute("CREATE (t:TradeDecision {ticker:'ENGY-02', action:'BUY', ...})")

# WAL seqs 2, 3: the fundamentals restatement
db.execute("MATCH ... SET f.eps = 2.10")
db.execute("MATCH ... SET f.revision = 'restated-day-35'")

# Six weeks later, the auditor asks: what did the agent see at decision time?
db.execute(
    "MATCH (s:Symbol {ticker:'ENGY-02'})-[:HAS_FUNDAMENTAL]->(f) "
    "AS OF seq $s RETURN f.eps, f.revision",
    params={"s": 1},
)
# → original eps, original revision. Bit-for-bit what the agent saw.
```

The canonical look-ahead-bias landmine, weaponized into a one-line
query. Decisions and evidence in the same graph, queried the same way.
The audit trail IS the dataset. Bulk ingest vs `execute()` is the
auditability boundary — cold history bypasses the WAL, decisions and
revisions enter it.

### Step 2 — Orchestrated context · the graph IS the working memory

```python
# Three context queries; one MATCH each.
SECTOR_ROLLUP    = "MATCH (b:DailyBar) WHERE b.day_idx = $day ..."
CROSS_RANK       = "MATCH (b:DailyBar) WHERE b.day_idx = $day RETURN ..., percent_rank() OVER (PARTITION BY b.sector ORDER BY b.close) ..."
LEADERS_BY_SECTOR = "MATCH (b:DailyBar) ... RETURN ..., row_number() OVER (PARTITION BY b.sector ORDER BY b.close DESC) AS rn"

# One tick mutates the graph; the same three queries re-read.
# No factor-rollup job, no message bus, no scheduler.
for tick in ticks:
    insert_bar(tick)
    rollup, ranks, leaders = (list(db.execute(q, params={"day": tick.day})) for q in (SECTOR_ROLLUP, CROSS_RANK, LEADERS_BY_SECTOR))
    feed_to_agent_prompt(rollup, ranks, leaders)
```

Window functions (`lag`, `percent_rank`, `row_number`, `OVER (PARTITION
BY … ORDER BY …)`) are full WorldCypher citizens, verified end-to-end.
The same query SHAPE works in three modes the engine guarantees are
operator-plan-equivalent:

- **Batch** — re-execute on demand (this Python recipe).
- **Subscription** — `db.subscribe(query, callback)` from the TS SDK,
  engine fires within ~20ms of any mutation.
- **Maintained `LIVE VIEW`** — `CREATE LIVE VIEW name AS …` from the
  Rust SDK, with view chaining and continuous-proof asserting batch-vs-
  live equivalence cell-by-cell.

Z-set algebra (the engine's incremental-computation substrate) is what
makes the equivalence mathematical, not aspirational. Your backtest,
your live agent, and your audit trail all run the same operator plan
against the same operational world model.

### Step 3 — Evidence-algebra fusion · one MATCH, every trust tier

```cypher
-- AGREEMENT: technical momentum + LLM sentiment, same direction
MATCH (s:Symbol)-[:EMITS]->(sig:Signal),
      (s)-[:MENTIONS]->(news:NewsSentiment)
WHERE sig.day_idx = news.day_idx
  AND sig.score * news.score > 0
RETURN s.ticker, sig.score * sig._confidence + news.score * news._confidence AS fused_score
ORDER BY fused_score DESC

-- DISAGREEMENT: same MATCH; flip the predicate
WHERE sig.day_idx = news.day_idx AND sig.score * news.score < 0

-- THREE-SOURCE: layer in HMM regime beliefs; same shape; no schema migration
MATCH (s)-[:EMITS]->(sig:Signal), (s)-[:REGIME_FOR]->(reg:RegimeBelief)
WHERE sig.day_idx = reg.day_idx AND reg.regime = 'trending' AND sig.score > 0.03

-- TRUST-TIER: only feed the LLM facts with confidence ≥ 0.6
WHERE sig._confidence >= 0.6
```

The research community is publishing papers titled "calibrated
uncertainty in neural world models." In ArcFlow's persistence layer,
calibrated uncertainty is the data model itself — every node and edge
carries `_observation_class` and `_confidence` from day one. Technical
signals at `observed`/0.95 coexist with LLM-emitted sentiment at
`predicted`/0.45 and HMM regime beliefs at `predicted`/0.65 in one
graph. The same MATCH shape spans agreement, disagreement, three-source
cross-checks, and trust-tier filters. Swapping a predicate is the entire
delta.

When the LLM tier adds a new signal source tomorrow — options-flow
detection, satellite-imagery scores, analyst-call transcript extraction —
it writes `_observation_class='predicted'` facts into the same graph.
Every existing fusion query absorbs it automatically. No schema
migration. No JOIN-chain hell.

---

## Run

```bash
uv sync
uv run python 01-persistent-memory.py         # AS OF seq replay
uv run python 02-orchestrated-live-context.py # cascading context queries
uv run python 03-confidence-weighted-fusion.py # evidence-algebra fusion
```

`_load.py` is the shared fixture: 8 symbols × 60 days OHLCV
(`observed`), fundamentals with a planted restatement landmine on
`ENGY-02` at day 35 (`observed`), 6 news-sentiment events from two
distinct LLM sources (`predicted` at 0.40–0.70), and 4 HMM regime
classifications per symbol (`predicted` at 0.55–0.75). Small enough to
load in under a second; rich enough to exercise every pattern.

---

## What's running under the hood

| Capability | Engine credential |
|---|---|
| `AS OF seq $param` — temporal replay with snapshot isolation | Persisted-WAL substrate; shipped end-to-end |
| Window functions (`lag` / `lead` / `percent_rank` / `row_number`) with `OVER (PARTITION BY … ORDER BY …)` | Parsed, lowered, and executed via the Z-set window operator |
| `_observation_class` + `_confidence` first-class on every node and edge | Day-one data-model commitment ([/concepts/world-model](/concepts/world-model)) |
| Two-tier ingest as the auditability boundary (`bulk_create_*` bypasses WAL; `execute()` enters it) | The Python binding's `bulk_create_nodes` / `bulk_create_relationships` ship at ~1M nodes/sec |
| 99.48 % cell-by-cell match against DuckDB on 15.4M real trading rows | `tools/trading-validator/` in the engine repo |
| Z-set algebra substrate — the foundation under `LIVE VIEW`, view chaining, continuous proof | Shipped in the Rust SDK today; the operator-plan equivalence is what makes batch == live |

The same engine that backs this recipe is the one a continuous-proof
flywheel validates against DuckDB at 246M cells with zero divergence on
historical rows after every delta append. The recipe runs in 3 minutes;
the engine scales to the same workload that elite shops run on
custom-built infrastructure.

---

## What this recipe doesn't (yet) show

Honest scope. The polling pattern in step 2 isn't the final form.
`CREATE LIVE VIEW`, `LIVE CALL algo.pageRank({...})`, `MATCH (row) FROM
VIEW …`, the continuous-proof flywheel, and the evidence-function
WorldCypher surface (`evidence(n)`, `observation(n)`) are shipped at the
Rust SDK level but not all Python-callable yet.

The Rust sibling cookbook —
**`algo-trading-microstructure-world-model`**, coming soon — picks up
where this one stops:

- Order book as a graph (MPID nodes ↔ Order nodes ↔ PriceLevel nodes)
- LIVE cascade for predictive OBI + iceberg detection with
  confidence-upgrade lifecycle (`predicted` → `observed` when the next
  print confirms)
- `AS OF seq` post-trade replay at microsecond resolution
- Continuous-proof asserting backtest-vs-live equivalence cell-by-cell

That's the recipe that earns the "black magic, productized" headline.
This one is the operational-world-model foundation it builds on.

---

## See also

- [World Model concept](/concepts/world-model) — operational vs neural, the full framing
- [Confidence and Provenance](/concepts/confidence-and-provenance) — `_observation_class` + `_confidence` deep dive
- [Temporal Queries](/worldcypher/temporal) — `AS OF seq` patterns across domains
- [Live Queries](/live-queries) — `CREATE LIVE VIEW`, `LIVE CALL`, view chaining
- [`multi-stream-spatiotemporal-world-model`](../multi-stream-spatiotemporal-world-model/) — sibling cookbook on the spatial side of the operational world model
- [`temporal-counterfactual-replay`](../temporal-counterfactual-replay/) — `AS OF seq` patterns across fraud, robotics, IoT
