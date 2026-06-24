---
id: doc-gap-matrix
type: backlog
title: "arcflow-core public surface → docs coverage gap matrix"
status: active
created: 2026-06-24
source: systematic 3-agent deep dive of arcflow-core vs arcflow-docs (iter 26)
note: feeds MISSION-doc-alignment Arm B; drain top-down, 1 cluster/iteration; verify signatures in source before writing (anti-vaporware)
---

# Doc gap matrix — undocumented / wrong arcflow-core capabilities

Priority order = correctness-impact first (wrong > missing-flagship > thin), then breadth.

## P0 — ACTIVELY WRONG (docs mislead; fix first)

- **`arcflow.spatial.*` documented as scalar FUNCTIONS but shipped as CALL PROCEDURES** with
  different args. `docs/guides/scale-patterns.mdx:85-87`. Real (verify in `spatial_primitives.rs`):
  - `CALL arcflow.spatial.cone_intersection(point_label, position_property, cone_apex, cone_axis, half_angle_rad, max_distance) YIELD nodeId, distance, angle_rad`
  - `CALL arcflow.spatial.kth_nearest_with_velocity(point_label, position_property, query_point, query_velocity, k, time_horizon, max_distance) YIELD nodeId, predicted_distance`
  - `CALL arcflow.spatial.occlusion_area(occluder_label, position_property, viewpoint, direction, max_distance, half_angle_rad) YIELD occluder_count, nearest_distance`
  - `CALL arcflow.spatial.dbscan(label, locationKey, epsilon, minPoints) YIELD nodeId, clusterId, backend` (`call_procedure_dispatch.rs:7191`)
- **`arcflow.moransI` wrong arg order** in `docs/concepts/layers/algorithm-library.mdx:30` — engine needs
  `(label, coords_property, value_property, k, confidence_weighted)`, coords BEFORE value.

## P1 — MISSING flagship analytics (no YIELD anywhere) — `stats_procs.rs` / `stats_procs_spatial.rs`
chiSquare, mannWhitneyU, kolmogorovSmirnov, biasDetection, moransI, localMoransI, getisOrdGStar,
ripleysK, localOutlierFactor. Full signatures captured (Agent A) — verify, then add a proper
statistics reference (AGENTS.md + docs/algorithms or a stats page).

## P1 — worldcypher STATEMENTS section structural gap
`docs/worldcypher/statements/` has only the 5 ISO DML statements. EVERY ArcFlow extension statement
is absent there: CREATE LIVE VIEW / PROGRAM / TRIGGER / REACTIVE SKILL / SKILL / SEMANTIC CONSTRAINT /
TOPIC / WINDOW / DECAY POLICY, REFINE EDGE, REPROCESS EDGES, EVOLVE SKILL, SUBSCRIBE/PUBLISH, FOREACH,
ASOF JOIN, VIRTUAL FROM PARTITION, DROP-* variants, REFRESH FULLTEXT INDEX, SESSION SET/RESET,
START TRANSACTION/ISOLATION. Build out the statements section from the parser (`api.rs` dispatch +
`parser/statements/*.rs`).

### MISSING statements (parsed+dispatched, zero docs)
EVOLVE SKILL (`api.rs:847`); CREATE WINDOW SIZE/STEP/KIND (`ddl.rs:1335`); CREATE DECAY POLICY HALF_LIFE
(`ddl.rs:1500`); ALTER LABEL SET DECAY POLICY (`ddl.rs:1574`); CREATE TOPIC (`ddl.rs:1306`); FOREACH
(`live_statements.rs:386`); SUBSCRIBE TO / PUBLISH TO (`live_statements.rs:451/482`); REFRESH FULLTEXT
INDEX (`api.rs:698`).

## P2 — THIN procedures (named, no usable signature)
- `arcflow.trajectory.*` 5 placeholders in AGENTS.md:669 (full sigs in `trajectory_proc.rs`).
- `arcflow.lag.by_topic` args+YIELD (DONE iter20: topic/head_seq/count_consumers/max_lag/mean_lag/total_lag).
- `db.*` introspection (~30) absent from AGENTS.md SSoT — temporal/observation/plane/store/index/vector/
  GPU/live families (signatures captured Agent A).
- Functions MISSING: confidence aggregates AVG_CONF/SUM_CONF/COUNT_CONF/MIN_CONF/MAX_CONF
  (`conf_agg_fns.rs`); PERCENTILECONT; spatial geometry fns arcflow.area/contains/intersects/
  convexHull/length (`return_list.rs:1083`).
- Data types THIN: CRS literals (Cartesian/Wgs84/LocalFlat), Vector3d/Extent/LineString/Polygon construction.
- EXT catalog THIN: durable workflows (VERIFY — no dispatch arm found; possible vaporware),
  ASOF JOIN, evidence algebra (REFINE EDGE), graph-embedding algos (node2vec/struc2vec/graphSAGE),
  relationship skills clause grammar.

## P2 — SDK / binding / daemon
- **TS/napi (largest):** sync/mesh family (~24 methods MISSING), workspace family (MISSING), live-view
  poll/list/status/template (THIN), algo methods (confidence_page_rank/impact_subgraph/etc. MISSING),
  diagnostics (spans/telemetry MISSING). `bindings/typescript/src/lib.rs`.
- **WASM:** entire API undocumented (init/execute/execute_in/workspace lifecycle/snapshot — 12 fns,
  `crates/arcflow-wasm/src/lib.rs`).
- **Python:** `arcflow.sharded` (ArcflowSharded/ShardHandle + SHARDED_* error enum) THIN; `TYPE_*` result
  type-tag constants + `QueryResult.column_type()` MISSING; `arcflow.algo` helper THIN.
- **Daemon:** `daemon.rpcCatalog` MISSING; tick-based `window.register/feed/drop/list` THIN; `group.*`
  consumer-group family THIN; fix method-count (spec says 59/49; real = 61).
- **C ABI:** 74 exported, ~12 documented (Arrow/live-view/pubsub/llm/sharded/graphblas families) — mostly
  mitigated by Python/TS wrappers; low priority.

## DO-NOT-DOCUMENT (engine-internal / not customer-facing — verify intent)
`db.competitorMatrix` (marketing matrix); `arcflow.contributor.*` (repo contributor tooling);
`db.proofGates`/`db.proofArtifacts` (CI/proof-harness). `CREATE WORKFLOW` — verify it actually parses
before documenting (catalog claims it; no dispatch arm found).

## Progress
- **2026-06-24 (iter 26)** P0 DONE: corrected scale-patterns.mdx (arcflow.spatial.* shown as CALL procs
  with real sigs, was scalar fns) + algorithm-library.mdx (moransI/localMoransI/getisOrdGStar arg order
  fixed: coords_property before value_property). P1 DONE: added full verified Statistical & spatial-analytics
  procedure reference to AGENTS.md (9 stats + 4 spatial procs w/ YIELD). Verified vs spatial_primitives.rs +
  stats_procs.rs + stats_procs_spatial.rs. NEXT: worldcypher statements section (extension DDL) + trajectory.* sigs.
</content>
- **2026-06-24 (iter 27)** Started worldcypher STATEMENTS build-out: new docs/worldcypher/statements/live-views.mdx (CREATE LIVE VIEW + WITH governance + LIVE MATCH/LIVE CALL + DROP), grammar verified vs live_statements.rs + api.rs, cross-linked to jsonrpc-v1 view.* + live-queries; latest-vocab (TRIGGER not 'reactive'). Remaining statements: PROGRAM, TRIGGER, SKILL, SEMANTIC CONSTRAINT, TOPIC, WINDOW, DECAY POLICY, REFINE EDGE, REPROCESS, EVOLVE SKILL, SUBSCRIBE/PUBLISH, FOREACH, ASOF JOIN, VIRTUAL FROM PARTITION, DROP-*, REFRESH FULLTEXT, SESSION, START TRANSACTION. Also queue: new feat(cli) autoupdate/self_update (I-INIT-RELEASE-E2E) → document in docs/cli once surface confirmed.
- **2026-06-24 (iter 28)** statements: +trigger.mdx (CREATE TRIGGER ON :Label WHEN CREATED|MODIFIED|DELETED RUN SKILL — latest vocab, replaces 'reactive skill') + create-program.mdx (CREATE PROGRAM VERSION (...) clauses: PROVIDES/CARDINALITY/REQUIRES GPU/MODEL/EXECUTOR/EVIDENCE/SKILLS/TRIGGERS + install-time admission, x-link program.spend). Verified vs program.rs. Remaining statements: SKILL, SEMANTIC CONSTRAINT, TOPIC, WINDOW, DECAY POLICY, REFINE EDGE, REPROCESS, EVOLVE SKILL, SUBSCRIBE/PUBLISH, FOREACH, ASOF JOIN, VIRTUAL FROM PARTITION, DROP-*, REFRESH FULLTEXT, SESSION, START TRANSACTION.
- **2026-06-24 (iter 29)** CREATE SKILL: enhanced docs/skills/create-skill.mdx with full grammar (FROM EMBEDDING/THRESHOLD, TIER NEURAL|LLM|WASM, INPUT VIEW, MODEL) — Arm E (enhanced existing page, no worldcypher dup). NEW feat documented: arcflow upgrade/--check (autoupdate, I-INIT-RELEASE-E2E) in docs/cli (resolves ozinc/arcflow releases, ARCFLOW_REPO mirror). Verified vs ddl.rs + self_update.rs + main.rs:241. Remaining statements: SEMANTIC CONSTRAINT, TOPIC, WINDOW, DECAY POLICY, REFINE EDGE/REPROCESS, EVOLVE SKILL, SUBSCRIBE/PUBLISH/FOREACH, ASOF JOIN, VIRTUAL FROM PARTITION, DROP-*, REFRESH FULLTEXT, SESSION, START TRANSACTION.
- **2026-06-24 (iter 30)** Constraints: enhanced docs/worldcypher/schema/constraints.mdx (Arm E, no dup) — modernized to GQL-V2 FOR...REQUIRE...IS form (Arm G: dropped old ASSERT), added IS PRIMARY KEY / IS NOT NULL, WITH GRANDFATHER_EXISTING on CAUSED_BY, and the missing SEMANTIC UNIQUE CONSTRAINT section (ON :Label(prop) WITHIN PROPERTY x THRESHOLD f). Verified vs ddl.rs:907-1247. Closes gap-matrix items: SEMANTIC CONSTRAINT, CAUSED_BY/GRANDFATHER clauses. Remaining statements: TOPIC, WINDOW, DECAY POLICY+ALTER LABEL, REFINE EDGE/REPROCESS, EVOLVE SKILL, SUBSCRIBE/PUBLISH/FOREACH, ASOF JOIN, VIRTUAL FROM PARTITION, DROP-*, REFRESH FULLTEXT, SESSION, START TRANSACTION.
- **2026-06-24 (iter 31)** +decay-policy.mdx (CREATE DECAY POLICY HALF_LIFE N [DAYS] [FLOOR_CONFIDENCE F] + ALTER LABEL SET DECAY POLICY — time-decaying confidence) +window.mdx (CREATE WINDOW SIZE/[STEP]/KIND count|sum|mean|min|max|stddev|first|last + DROP). Verified vs ddl.rs+api.rs:642/647. Arm-E finding: CREATE TOPIC/SUBSCRIBE TO/PUBLISH TO are NOT missing — already documented in docs/live-queries.mdx §Topics-and-CDC (Agent B false-positive: checked worldcypher/ only). Removed from MISSING. Remaining statements: REFINE EDGE/REPROCESS, EVOLVE SKILL, FOREACH, ASOF JOIN, VIRTUAL FROM PARTITION, DROP-* variants, REFRESH FULLTEXT, SESSION, START TRANSACTION.
- **2026-06-24 (iter 32)** +evidence-refinement.mdx (REFINE EDGE r SET confidence/observation + REPROCESS EDGES [WHERE confidence<N], evidence-algebra mutation surface) + EVOLVE SKILL added to docs/skills/index.mdx lifecycle (auto-version+re-evaluate). Verified vs program.rs:664/dml.rs:1424/api.rs:847. Note: generated reference/extensions/{evidence-algebra,asof-join}.mdx are catalog stubs (do-not-hand-edit) — hand-written homes added in worldcypher/skills. Remaining statements: ASOF JOIN, FOREACH, VIRTUAL FROM PARTITION, DROP-* variants, REFRESH FULLTEXT, SESSION SET/RESET, START TRANSACTION.
- **2026-06-24 (iter 33)** +query-syntax/asof-join.mdx (ASOF [LEFT] JOIN (b:Label) ON eq AND a.time>=b.time — temporal most-recent-prior join) +composition/foreach.mdx (FOREACH (x IN list | mutations) — write-side counterpart to UNWIND). Verified vs ddl.rs:1621 + live_statements.rs:384. Generated reference/extensions/asof-join.mdx stub left as-is (do-not-hand-edit). Remaining statements: CREATE NODE LABEL VIRTUAL FROM PARTITION, DROP-* variants, REFRESH FULLTEXT INDEX, SESSION SET/RESET, START TRANSACTION/ISOLATION.
- **2026-06-24 (iter 34)** +worldcypher/statements/create-node-label.mdx (CREATE NODE LABEL typed owned + VIRTUAL FROM PARTITION 'lake://...' with {var} placeholders + predicate pushdown). Verified vs schema_ddl.rs. ARM-G FLAG: docs/migrations/v0.7-to-v0.8-lakehouse-fastpath.mdx is a pre-launch v0.7->v0.8 migration guide (greenfield = no migration audience) yet holds canonical lakehouse prose — queue for Arm-G/E sweep: relocate the lakehouse fast-path content to a capability page + retire the migration framing. Remaining statements tail: REFRESH FULLTEXT INDEX, SESSION SET/RESET, START TRANSACTION/ISOLATION (query-control; can be one combined page). Then trajectory/db.*/functions/SDK clusters.
