import { openInMemory } from 'arcflow'

const db = openInMemory()

// Create nodes — MERGE is idempotent; use name as the unique key
db.batchMutate([
  "MERGE (n:Person {name: 'Alice'}) ON CREATE SET n.age = 30",
  "MERGE (n:Person {name: 'Bob'}) ON CREATE SET n.age = 25",
  "MERGE (n:Person {name: 'Charlie'}) ON CREATE SET n.age = 35",
])

// Create relationships — MATCH the existing nodes, then MERGE the edge
db.batchMutate([
  "MATCH (a:Person {name: 'Alice'}) MATCH (b:Person {name: 'Bob'}) MERGE (a)-[:KNOWS {since: 2020}]->(b)",
  "MATCH (a:Person {name: 'Bob'}) MATCH (b:Person {name: 'Charlie'}) MERGE (a)-[:KNOWS {since: 2021}]->(b)",
  "MATCH (a:Person {name: 'Alice'}) MATCH (b:Person {name: 'Charlie'}) MERGE (a)-[:KNOWS {since: 2019}]->(b)",
])

// Query the graph
const friends = db.query("MATCH (p:Person)-[:KNOWS]->(friend:Person) RETURN p.name, friend.name ORDER BY p.name")

console.log('Friends:')
for (const row of friends.rows) {
  console.log(`  ${row.get('p.name')} knows ${row.get('friend.name')}`)
}

// Run a graph algorithm — no setup, no projection
const pr = db.query("CALL algo.pageRank()")

console.log('\nPageRank:')
for (const row of pr.rows) {
  console.log(`  ${row.get('name')}: ${row.get('rank')}`)
}

// Graph stats
const stats = db.stats()
console.log(`\nGraph: ${stats.nodes} nodes, ${stats.relationships} relationships`)

db.close()
