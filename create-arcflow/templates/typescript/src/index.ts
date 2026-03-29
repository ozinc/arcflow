import { openInMemory } from 'arcflow'

const db = openInMemory()

// Create nodes
db.batchMutate([
  "CREATE (alice:Person {name: 'Alice', age: 30})",
  "CREATE (bob:Person {name: 'Bob', age: 25})",
  "CREATE (charlie:Person {name: 'Charlie', age: 35})",
  "CREATE (alice:Person {name: 'Alice'})-[:KNOWS {since: 2020}]->(bob:Person {name: 'Bob'})",
  "CREATE (bob:Person {name: 'Bob'})-[:KNOWS {since: 2021}]->(charlie:Person {name: 'Charlie'})",
  "CREATE (alice:Person {name: 'Alice'})-[:KNOWS {since: 2019}]->(charlie:Person {name: 'Charlie'})",
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
