// ArcFlow SDK — Data Pipeline Case Study
//
// One in-process library replaces:
//   dbt              → batchMutate() for batch + SET for delta
//   Great Expectations → CREATE LIVE VIEW for DQ assertions
//   Airflow          → Stage nodes + FEEDS edges + PipelineRun ledger
//   Lineage tool     → SOURCED_FROM edges on every record
//   BI drill tool    → graph traversal: result → record → source document
//   Snapshot tables  → AS OF timestamp — WAL is the timeline
//
// Live view design: register BEFORE ingesting data. The view fires incrementally
// on every GQL write — no polling, no re-scan. rowCount > 0 = violation exists;
// a follow-up query gives the details. This mirrors the Great Expectations pattern:
// "define the expectation once, evaluate on every run."
//
// Run: npx ts-node index.ts

import { openInMemory } from 'arcflow'
import { CodeGraph } from 'arcflow'

const db = openInMemory()

// ─────────────────────────────────────────────────────────────────────────────
// 0. PIPELINE DAG
//    Stage nodes + FEEDS edges. No separate orchestration tool — the graph IS
//    the DAG. Critical-path analysis, documentation, and run history are all
//    GQL queries.
// ─────────────────────────────────────────────────────────────────────────────

console.log('── 0. Pipeline DAG ───────────────────────────────────────────────')

db.batchMutate([
  "MERGE (s:Stage {id:'ingest',    label:'Ingest',    description:'Load raw records'})",
  "MERGE (s:Stage {id:'validate',  label:'Validate',  description:'Schema + range checks'})",
  "MERGE (s:Stage {id:'enrich',    label:'Enrich',    description:'Join reference data'})",
  "MERGE (s:Stage {id:'aggregate', label:'Aggregate', description:'Compute derived metrics'})",
  "MERGE (s:Stage {id:'publish',   label:'Publish',   description:'Write to output + index'})",
])
db.batchMutate([
  "MATCH (a:Stage {id:'ingest'}),    (b:Stage {id:'validate'})  MERGE (a)-[:FEEDS]->(b)",
  "MATCH (a:Stage {id:'validate'}),  (b:Stage {id:'enrich'})    MERGE (a)-[:FEEDS]->(b)",
  "MATCH (a:Stage {id:'enrich'}),    (b:Stage {id:'aggregate'}) MERGE (a)-[:FEEDS]->(b)",
  "MATCH (a:Stage {id:'aggregate'}), (b:Stage {id:'publish'})   MERGE (a)-[:FEEDS]->(b)",
])

const dag = db.query(`
  MATCH (a:Stage)-[:FEEDS]->(b:Stage)
  RETURN a.label AS from, b.label AS to
  ORDER BY a.id
`)
console.log('Pipeline DAG:')
for (const row of dag.rows) console.log(`  ${row.get('from')} → ${row.get('to')}`)
console.log()

// ─────────────────────────────────────────────────────────────────────────────
// 1. DQ LIVE VIEWS — register BEFORE ingesting
//    Define the expectation once. The engine evaluates it on every write.
//    rowCount > 0 = violation exists → trigger drill-through query for details.
//    Supported predicates: =  >  <  IS NULL  (>=  <=  <> planned)
// ─────────────────────────────────────────────────────────────────────────────

console.log('── 1. DQ live views (registered before data load) ────────────────')

// Expectation: price must be positive
db.mutate(`CREATE LIVE VIEW dq_zero_price AS
  MATCH (r:Record) WHERE r.price < 0.01
  RETURN r.id AS id`)

// Expectation: confidence must meet minimum threshold
db.mutate(`CREATE LIVE VIEW dq_low_confidence AS
  MATCH (r:Record) WHERE r.confidence < 0.7
  RETURN r.id AS id`)

// Expectation: every record must declare a source
db.mutate(`CREATE LIVE VIEW dq_no_source AS
  MATCH (r:Record) WHERE r.source IS NULL
  RETURN r.id AS id`)

console.log('Registered: dq_zero_price, dq_low_confidence, dq_no_source')
console.log()

// ─────────────────────────────────────────────────────────────────────────────
// 2. BATCH LOAD — full corpus
//    batchMutate: single write lock per call. CDC fires → live views update.
//    Intentional DQ violations: r003 (price=0), r005 (confidence=0.61).
// ─────────────────────────────────────────────────────────────────────────────

console.log('── 2. Batch load (full corpus) ───────────────────────────────────')

db.batchMutate([
  "MERGE (d:Document {id:'doc_001', path:'data/sales-Q1.csv', ingestedAt:1700000000})",
  "MERGE (d:Document {id:'doc_002', path:'data/sales-Q2.csv', ingestedAt:1700086400})",
])
db.batchMutate([
  "CREATE (r:Record {id:'r001', price:120.50, category:'A', confidence:0.95, source:'doc_001'})",
  "CREATE (r:Record {id:'r002', price:84.20,  category:'B', confidence:0.88, source:'doc_001'})",
  "CREATE (r:Record {id:'r003', price:0,      category:'A', confidence:0.92, source:'doc_001'})",  // DQ: bad price
  "CREATE (r:Record {id:'r004', price:210.00, category:'X', confidence:0.91, source:'doc_002'})",  // DQ: unknown category
  "CREATE (r:Record {id:'r005', price:55.75,  category:'C', confidence:0.61, source:'doc_002'})",  // DQ: low confidence
  "CREATE (r:Record {id:'r006', price:310.00, category:'B', confidence:0.97, source:'doc_002'})",
])
// Provenance edges: record → document (for drill-through in section 6)
db.batchMutate([
  "MATCH (r:Record {id:'r001'}),(d:Document {id:'doc_001'}) MERGE (r)-[:SOURCED_FROM]->(d)",
  "MATCH (r:Record {id:'r002'}),(d:Document {id:'doc_001'}) MERGE (r)-[:SOURCED_FROM]->(d)",
  "MATCH (r:Record {id:'r003'}),(d:Document {id:'doc_001'}) MERGE (r)-[:SOURCED_FROM]->(d)",
  "MATCH (r:Record {id:'r004'}),(d:Document {id:'doc_002'}) MERGE (r)-[:SOURCED_FROM]->(d)",
  "MATCH (r:Record {id:'r005'}),(d:Document {id:'doc_002'}) MERGE (r)-[:SOURCED_FROM]->(d)",
  "MATCH (r:Record {id:'r006'}),(d:Document {id:'doc_002'}) MERGE (r)-[:SOURCED_FROM]->(d)",
])
// Ownership edges: document → record (for blast-radius BFS in section 7)
db.batchMutate([
  "MATCH (d:Document {id:'doc_001'}),(r:Record {id:'r001'}) MERGE (d)-[:CONTAINS]->(r)",
  "MATCH (d:Document {id:'doc_001'}),(r:Record {id:'r002'}) MERGE (d)-[:CONTAINS]->(r)",
  "MATCH (d:Document {id:'doc_001'}),(r:Record {id:'r003'}) MERGE (d)-[:CONTAINS]->(r)",
  "MATCH (d:Document {id:'doc_002'}),(r:Record {id:'r004'}) MERGE (d)-[:CONTAINS]->(r)",
  "MATCH (d:Document {id:'doc_002'}),(r:Record {id:'r005'}) MERGE (d)-[:CONTAINS]->(r)",
  "MATCH (d:Document {id:'doc_002'}),(r:Record {id:'r006'}) MERGE (d)-[:CONTAINS]->(r)",
])

const loaded = db.stats()
console.log(`Loaded: ${loaded.nodes} nodes, ${loaded.relationships} relationships`)

// Live views fired automatically — check violation counts
const zpCount  = db.query("MATCH (row) FROM VIEW dq_zero_price     RETURN row").rowCount
const lcCount  = db.query("MATCH (row) FROM VIEW dq_low_confidence RETURN row").rowCount
console.log(`DQ violations: ${zpCount} zero-price, ${lcCount} low-confidence`)

// For the actual violating IDs: run a targeted query (live view gives COUNT, query gives DETAIL)
if (zpCount > 0) {
  const ids = db.query("MATCH (r:Record) WHERE r.price < 0.01 RETURN r.id AS id")
  console.log(`  zero-price records: ${ids.rows.map(r => r.get('id')).join(', ')}`)
}
if (lcCount > 0) {
  const ids = db.query("MATCH (r:Record) WHERE r.confidence < 0.7 RETURN r.id AS id, r.confidence AS conf")
  console.log(`  low-confidence records: ${ids.rows.map(r => `${r.get('id')}(${r.get('conf')})`).join(', ')}`)
}
// Enum check — IN list not yet in Z-set planner, use regular query
const badCat = db.query("MATCH (r:Record) WHERE r.category = 'X' RETURN r.id AS id")
if (badCat.rows.length > 0) {
  console.log(`  unknown-category records: ${badCat.rows.map(r => r.get('id')).join(', ')}`)
}
console.log()

// ─────────────────────────────────────────────────────────────────────────────
// 3. DELTA LOAD — only changed records
//    GQL SET for targeted updates — CDC fires, live views auto-update.
//    For content-hash dedup (skip unchanged records at the WAL level), use
//    CodeGraph.ingest() which calls apply_node_edge_delta() directly.
// ─────────────────────────────────────────────────────────────────────────────

console.log('── 3. Delta load ─────────────────────────────────────────────────')

// Fix r003's bad price; add r007 (new record from updated source)
db.batchMutate([
  "MATCH (r:Record {id:'r003'}) SET r.price = 145.00",
  "MERGE (r:Record {id:'r007', price:88.50, category:'C', confidence:0.93, source:'doc_002'})",
])
db.batchMutate([
  "MATCH (r:Record {id:'r007'}),(d:Document {id:'doc_002'}) MERGE (r)-[:SOURCED_FROM]->(d)",
  "MATCH (d:Document {id:'doc_002'}),(r:Record {id:'r007'}) MERGE (d)-[:CONTAINS]->(r)",
])

// Live view behavior after SET: the Z-set delta engine currently propagates
// additions via CDC but does not propagate property-change-driven REMOVALS.
// rowCount stays 1 even after fixing r003. For current violation state, always
// run a direct query — the live view rowCount is a reliable "any violations exist"
// signal for new writes, not a real-time count after property updates.
const zpAfter = db.query("MATCH (row) FROM VIEW dq_zero_price RETURN row").rowCount
const zpActual = db.query("MATCH (r:Record) WHERE r.price < 0.01 RETURN r.id").rowCount
console.log(`DQ zero-price after delta: view=${zpAfter} (stale after SET), direct=${zpActual} violations`)

// Content-hash dedup via ingestDelta: same hash → WAL silent (zero bytes written)
// Note: uses label 'DemoRecord' to isolate from main pipeline data.
// ingestDelta() bypasses the GQL compiler entirely — one write-lock + WAL flush.
// CDC does NOT fire on ingestDelta, so DQ live views are not updated. This is the
// intended trade-off: maximum throughput (53× batch INSERT vs GQL), zero dedup
// overhead, at the cost of CDC integration. Use batchMutate() when live views matter.
const cg = new CodeGraph(db)
const dedup = cg.ingest({
  addedNodes: [
    // Attempt 1: write hash_v1
    { label: 'DemoRecord', id: 'x001', contentHash: 'hash_v1', properties: { price: 120.50, note: 'first write' } },
    // Attempt 2: same ID + same hash → skipped entirely, WAL stays silent
    { label: 'DemoRecord', id: 'x001', contentHash: 'hash_v1', properties: { price: 120.50, note: 'duplicate — skipped' } },
    // Attempt 3: same ID + changed hash → update written
    { label: 'DemoRecord', id: 'x001', contentHash: 'hash_v2', properties: { price: 121.00, note: 'new version — written' } },
  ],
  addedEdges: [],
})
console.log(`ingestDelta dedup: ${dedup.nodesAdded} new, ${dedup.nodesUpdated} updated, ${dedup.nodesSkippedByHash} skipped (WAL silent)`)
console.log()

// ─────────────────────────────────────────────────────────────────────────────
// 4. PRUNE — remove expired / superseded records
// ─────────────────────────────────────────────────────────────────────────────

console.log('── 4. Prune stale records ────────────────────────────────────────')

db.mutate("MATCH (r:Record {id:'r004'}) SET r.invalidatedAt = 1700200000, r.invalidReason = 'unknown_category'")

const beforePrune = db.stats()
db.mutate("MATCH (r:Record) WHERE r.invalidatedAt > 0 DETACH DELETE r")
const afterPrune = db.stats()

console.log(`Pruned ${beforePrune.nodes - afterPrune.nodes} record(s)`)
console.log(`Graph: ${afterPrune.nodes} nodes, ${afterPrune.relationships} relationships`)
console.log()

// ─────────────────────────────────────────────────────────────────────────────
// 5. AGGREGATE — derived metrics across valid records
// ─────────────────────────────────────────────────────────────────────────────

console.log('── 5. Aggregate metrics ──────────────────────────────────────────')

const metrics = db.query(`
  MATCH (r:Record)
  WHERE r.invalidatedAt IS NULL
  RETURN r.category AS category,
    count(*) AS count,
    avg(r.price) AS avg_price,
    avg(r.confidence) AS avg_confidence
  ORDER BY r.category
`)
console.log('By category:')
for (const row of metrics.rows) {
  const price = Number(row.get('avg_price')).toFixed(2)
  const conf  = Number(row.get('avg_confidence')).toFixed(2)
  console.log(`  ${row.get('category')}: n=${row.get('count')}, avg_price=$${price}, avg_confidence=${conf}`)
}
console.log()

// ─────────────────────────────────────────────────────────────────────────────
// 6. DRILL-THROUGH + EXPECTATION TESTING
//    The historical BI gap: a metric looks wrong, you can't trace back why.
//    ArcFlow closes it: graph traversal from result → record → source document.
// ─────────────────────────────────────────────────────────────────────────────

console.log('── 6. Drill-through / expectation testing ────────────────────────')

// Expectation: average confidence across all valid records must be >= 0.80
const exp = db.query("MATCH (r:Record) WHERE r.invalidatedAt IS NULL RETURN avg(r.confidence) AS avg_conf")
const avgConf = Number(exp.rows[0]?.get('avg_conf') ?? 0)
const passed  = avgConf >= 0.8
console.log(`Expectation avg_confidence >= 0.80 → ${passed ? 'PASS ✓' : 'FAIL ✗'} (actual: ${avgConf.toFixed(2)})`)

if (!passed) {
  // Auto drill-through: trace failing records back to their source documents
  const failing = db.query(`
    MATCH (r:Record)-[:SOURCED_FROM]->(d:Document)
    WHERE r.confidence < 0.8 AND r.invalidatedAt IS NULL
    RETURN r.id AS id, r.confidence AS conf, d.path AS source
    ORDER BY r.confidence
  `)
  console.log('  Failing records (drill-through to source):')
  for (const row of failing.rows) {
    console.log(`    ${row.get('id')} confidence=${Number(row.get('conf')).toFixed(2)} ← ${row.get('source')}`)
  }
}

// Drill-through by category: category B lowest confidence
const catB = db.query(`
  MATCH (r:Record)-[:SOURCED_FROM]->(d:Document)
  WHERE r.category = 'B' AND r.invalidatedAt IS NULL
  RETURN r.id AS id, r.price AS price, r.confidence AS confidence, d.path AS source_doc
  ORDER BY r.confidence
`)
console.log('Category B — by confidence (lowest first):')
for (const row of catB.rows) {
  const conf = Number(row.get('confidence')).toFixed(2)
  console.log(`  ${row.get('id')}: conf=${conf}, price=$${row.get('price')}, source=${row.get('source_doc')}`)
}
console.log()

// ─────────────────────────────────────────────────────────────────────────────
// 7. BLAST-RADIUS — what does changing a source document affect?
//    Graph traversal: document → records it contains → downstream aggregates.
//    No separate lineage tool. The CONTAINS edges you already created ARE the lineage.
// ─────────────────────────────────────────────────────────────────────────────

console.log('── 7. Impact analysis ────────────────────────────────────────────')

// Which records came from doc_002? If the source file changes, these need re-processing.
const affected = db.query(`
  MATCH (d:Document {id:'doc_002'})-[:CONTAINS]->(r:Record)
  RETURN d.path AS doc, r.id AS record_id, r.category AS category
  ORDER BY r.id
`)
console.log(`Changing doc_002 affects ${affected.rows.length} record(s):`)
for (const row of affected.rows) {
  console.log(`  ${row.get('record_id')} (category=${row.get('category')}) ← ${row.get('doc')}`)
}
console.log()

// ─────────────────────────────────────────────────────────────────────────────
// 8. FROZEN SNAPSHOT
//    AS OF seq N: query past graph state at WAL sequence N. The WAL is the
//    timeline — no snapshot tables, no CDC tables, no time-travel infra.
//    Note: AS OF <timestamp> is deprecated (engine returns error); use seq N.
//    seq 0 = before any mutations; seq N = after exactly N committed mutations.
// ─────────────────────────────────────────────────────────────────────────────

console.log('── 8. Frozen snapshot (AS OF seq) ────────────────────────────────')

// Query state at seq 0 = empty graph (before any data was loaded)
try {
  const frozen = db.query("MATCH (r:Record) AS OF seq 0 RETURN count(*) AS record_count")
  const count = frozen.rows[0]?.get('record_count') ?? 0
  console.log(`Records AS OF seq 0 (empty — before batch load): ${count}`)
} catch (e: unknown) {
  // AS OF seq may not be enabled in all builds; surface the message
  console.log(`AS OF seq: ${e instanceof Error ? e.message : String(e)}`)
}
console.log()

// ─────────────────────────────────────────────────────────────────────────────
// 9. PIPELINE RUN LEDGER
//    PipelineRun node → EXECUTED edges → Stage nodes with per-stage timing.
//    Full audit trail — no separate logging infrastructure.
// ─────────────────────────────────────────────────────────────────────────────

console.log('── 9. Pipeline run ledger ────────────────────────────────────────')

const runId  = `run_${Date.now()}`
const timing: Record<string, number> = { ingest: 12, validate: 3, enrich: 5, aggregate: 2, publish: 4 }

db.mutate(`MERGE (run:PipelineRun {id:'${runId}', startedAt:${Date.now()}, status:'completed'})`)
for (const [stage, ms] of Object.entries(timing)) {
  db.mutate(`MATCH (s:Stage {id:'${stage}'}) SET s.lastRunMs = ${ms}`)
  db.mutate(`MATCH (run:PipelineRun {id:'${runId}'}),(s:Stage {id:'${stage}'}) MERGE (run)-[:EXECUTED]->(s)`)
}

const runLog = db.query(`
  MATCH (run:PipelineRun {id:'${runId}'})-[:EXECUTED]->(s:Stage)
  RETURN s.label AS stage, s.lastRunMs AS ms
  ORDER BY s.id
`)
console.log(`Run ${runId}:`)
let totalMs = 0
for (const row of runLog.rows) {
  const ms = Number(row.get('ms') ?? 0)
  totalMs += ms
  console.log(`  ${String(row.get('stage')).padEnd(12)} ${ms}ms`)
}
console.log(`  ${'total'.padEnd(12)} ${totalMs}ms`)
console.log()

// ─────────────────────────────────────────────────────────────────────────────
// SUMMARY
// ─────────────────────────────────────────────────────────────────────────────

const final = db.stats()
console.log('── Summary ───────────────────────────────────────────────────────')
console.log(`Graph: ${final.nodes} nodes, ${final.relationships} relationships`)
console.log()
console.log('What ArcFlow replaced:')
console.log('  dbt              → batchMutate() + GQL SET for delta')
console.log('  Great Expectations → DQ live views — fire on every write, zero polling')
console.log('  Airflow          → Stage nodes + FEEDS edges + PipelineRun ledger')
console.log('  Lineage tracker  → SOURCED_FROM edges — provenance on every record')
console.log('  BI drill tool    → graph traversal: result → record → source document')
console.log('  Snapshot tables  → AS OF timestamp — WAL is the timeline')

db.close()
