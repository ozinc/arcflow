// ArcFlow SDK — Knowledge Graph Example
// Models people, organizations, and confidence-scored facts.

import { openInMemory } from 'arcflow'

const db = openInMemory()

// ── Step 1: Create entities ──
console.log('Creating entities...')
db.batchMutate([
  "CREATE (p:Person {id: 'p1', name: 'Alice Chen', role: 'CTO', city: 'San Francisco'})",
  "CREATE (p:Person {id: 'p2', name: 'Bob Smith', role: 'VP Engineering', city: 'New York'})",
  "CREATE (p:Person {id: 'p3', name: 'Carol Davis', role: 'Data Scientist', city: 'London'})",
  "CREATE (o:Org {id: 'o1', name: 'Acme Corp', industry: 'tech', hq: 'San Francisco'})",
  "CREATE (o:Org {id: 'o2', name: 'Globex Inc', industry: 'finance', hq: 'New York'})",
])

// ── Step 2: Create relationships ──
console.log('Linking entities...')
db.batchMutate([
  "MATCH (p:Person {id: 'p1'}) MATCH (o:Org {id: 'o1'}) MERGE (p)-[:WORKS_AT {since: 2019}]->(o)",
  "MATCH (p:Person {id: 'p2'}) MATCH (o:Org {id: 'o2'}) MERGE (p)-[:WORKS_AT {since: 2021}]->(o)",
  "MATCH (a:Person {id: 'p1'}) MATCH (b:Person {id: 'p2'}) MERGE (a)-[:KNOWS {context: 'conference'}]->(b)",
])

// ── Step 3: Add facts with confidence scores ──
console.log('Creating facts...')
db.batchMutate([
  "CREATE (f:Fact {uuid: 'f1', predicate: 'advises', confidence: 0.87, source: 'press-release'})",
  "MATCH (p:Person {id: 'p1'}) MATCH (f:Fact {uuid: 'f1'}) MERGE (p)-[:SUBJECT_OF]->(f)",
  "MATCH (f:Fact {uuid: 'f1'}) MATCH (o:Org {id: 'o2'}) MERGE (f)-[:OBJECT_IS]->(o)",
])

// ── Step 4: Query the knowledge graph ──
console.log('\nAll connections for Alice:')
const connections = db.query(
  "MATCH (p:Person {id: $id})-[r]->(target) RETURN labels(target), target.name",
  { id: 'p1' }
)
for (const row of connections.rows) {
  console.log(`  -> ${row.get('target.name')} (${row.get('labels(target)')})`)
}

console.log('\nHigh-confidence facts:')
const facts = db.query(`
  MATCH (s)-[:SUBJECT_OF]->(f:Fact)-[:OBJECT_IS]->(o)
  WHERE f.confidence > 0.8
  RETURN s.name, f.predicate, o.name, f.confidence
  ORDER BY f.confidence DESC
`)
for (const row of facts.rows) {
  console.log(`  ${row.get('s.name')} --[${row.get('f.predicate')}]--> ${row.get('o.name')} (confidence: ${row.get('f.confidence')})`)
}

// ── Step 5: Graph algorithms ──
console.log('\nPageRank:')
const pr = db.query("CALL algo.pageRank()")
for (const row of pr.rows) {
  console.log(`  ${row.get('name')}: ${row.get('rank')}`)
}

const stats = db.stats()
console.log(`\nGraph: ${stats.nodes} nodes, ${stats.relationships} relationships`)

db.close()
