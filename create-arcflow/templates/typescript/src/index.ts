import { openInMemory } from 'arcflow'

// Open an in-memory graph database — no server needed
const db = openInMemory()

// Create some nodes and relationships
db.mutate(`
  CREATE (alice:Person {name: 'Alice', age: 30})
  CREATE (bob:Person {name: 'Bob', age: 25})
  CREATE (charlie:Person {name: 'Charlie', age: 35})
  CREATE (alice)-[:KNOWS {since: 2020}]->(bob)
  CREATE (bob)-[:KNOWS {since: 2021}]->(charlie)
  CREATE (alice)-[:KNOWS {since: 2019}]->(charlie)
`)

// Query the graph
const friends = db.query(`
  MATCH (p:Person)-[:KNOWS]->(friend:Person)
  RETURN p.name, friend.name, friend.age
  ORDER BY p.name
`)

console.log('Friends:')
for (const row of friends.rows) {
  console.log(`  ${row.get('p.name')} knows ${row.get('friend.name')} (age ${row.get('friend.age')})`)
}

// Run a graph algorithm
const pagerank = db.query(`
  CALL algo.pageRank()
  YIELD node, score
  RETURN node.name, score
  ORDER BY score DESC
`)

console.log('\nPageRank:')
for (const row of pagerank.rows) {
  console.log(`  ${row.get('node.name')}: ${row.get('score')}`)
}

// Graph stats
const stats = db.stats()
console.log(`\nGraph: ${stats.nodes} nodes, ${stats.relationships} relationships`)

db.close()
