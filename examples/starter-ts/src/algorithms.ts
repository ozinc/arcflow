import { openInMemory } from 'arcflow'

const db = openInMemory()

// Create a social network
db.mutate(`
  CREATE (a:Person {name: 'Alice'})
  CREATE (b:Person {name: 'Bob'})
  CREATE (c:Person {name: 'Charlie'})
  CREATE (d:Person {name: 'Diana'})
  CREATE (e:Person {name: 'Eve'})

  CREATE (a)-[:FOLLOWS]->(b)
  CREATE (a)-[:FOLLOWS]->(c)
  CREATE (b)-[:FOLLOWS]->(c)
  CREATE (c)-[:FOLLOWS]->(d)
  CREATE (d)-[:FOLLOWS]->(e)
  CREATE (e)-[:FOLLOWS]->(a)
`)

// PageRank — who's most influential?
const pr = db.query(`
  CALL algo.pageRank()
  YIELD node, score
  RETURN node.name, round(score, 4) AS rank
  ORDER BY score DESC
`)

console.log('PageRank (influence):')
for (const row of pr.rows) {
  console.log(`  ${row.get('node.name')}: ${row.get('rank')}`)
}

// Community detection
const communities = db.query(`
  CALL algo.louvain()
  YIELD node, community
  RETURN node.name, community
  ORDER BY community, node.name
`)

console.log('\nCommunities:')
for (const row of communities.rows) {
  console.log(`  ${row.get('node.name')} → community ${row.get('community')}`)
}

db.close()
