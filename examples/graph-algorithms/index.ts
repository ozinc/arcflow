// ArcFlow SDK — Graph Algorithms Example
// Run algorithms directly — no projection setup needed.

import { openInMemory } from '@arcflow/sdk'

const db = openInMemory()

// ── Build a social network ──
console.log('Building social network...')
db.batchMutate([
  "CREATE (a:Person {name: 'Alice', department: 'engineering'})",
  "CREATE (b:Person {name: 'Bob', department: 'engineering'})",
  "CREATE (c:Person {name: 'Carol', department: 'marketing'})",
  "CREATE (d:Person {name: 'Dave', department: 'marketing'})",
  "CREATE (e:Person {name: 'Eve', department: 'sales'})",
])

db.batchMutate([
  "MATCH (a:Person {name: 'Alice'}) MATCH (b:Person {name: 'Bob'}) MERGE (a)-[:KNOWS]->(b)",
  "MATCH (b:Person {name: 'Bob'}) MATCH (a:Person {name: 'Alice'}) MERGE (b)-[:KNOWS]->(a)",
  "MATCH (a:Person {name: 'Alice'}) MATCH (c:Person {name: 'Carol'}) MERGE (a)-[:KNOWS]->(c)",
  "MATCH (c:Person {name: 'Carol'}) MATCH (d:Person {name: 'Dave'}) MERGE (c)-[:KNOWS]->(d)",
  "MATCH (d:Person {name: 'Dave'}) MATCH (c:Person {name: 'Carol'}) MERGE (d)-[:KNOWS]->(c)",
  "MATCH (b:Person {name: 'Bob'}) MATCH (e:Person {name: 'Eve'}) MERGE (b)-[:KNOWS]->(e)",
  "MATCH (e:Person {name: 'Eve'}) MATCH (d:Person {name: 'Dave'}) MERGE (e)-[:KNOWS]->(d)",
])

// ── PageRank ──
console.log('\nPageRank (who is most important?):')
const pr = db.query("CALL algo.pageRank()")
for (const row of pr.rows) {
  console.log(`  ${row.get('name')}: ${row.get('rank')}`)
}

// ── Community Detection ──
console.log('\nLouvain communities:')
const communities = db.query("CALL algo.louvain()")
for (const row of communities.rows) {
  console.log(`  ${row.get('name')} -> community ${row.get('community')}`)
}

// ── Betweenness Centrality ──
console.log('\nBetweenness centrality (who bridges communities?):')
const betweenness = db.query("CALL algo.betweenness()")
for (const row of betweenness.rows) {
  console.log(`  ${row.get('name')}: ${row.get('score')}`)
}

// ── Graph Properties ──
console.log('\nGraph properties:')
const triangles = db.query("CALL algo.triangleCount()")
console.log(`  Triangles: ${triangles.rows[0]?.get('count') ?? 'N/A'}`)

const density = db.query("CALL algo.density()")
console.log(`  Density: ${density.rows[0]?.get('density') ?? 'N/A'}`)

// ── Connected Components ──
console.log('\nConnected components:')
const components = db.query("CALL algo.connectedComponents()")
for (const row of components.rows) {
  console.log(`  ${row.get('name')} -> component ${row.get('component')}`)
}

db.close()
console.log('\nDone!')
