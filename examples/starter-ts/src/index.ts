import { openInMemory } from 'arcflow'

const db = openInMemory()

// Create people
db.mutate(`
  CREATE (alice:Person {name: 'Alice', age: 30})
  CREATE (bob:Person {name: 'Bob', age: 25})
  CREATE (charlie:Person {name: 'Charlie', age: 35})

  CREATE (alice)-[:KNOWS {since: 2020}]->(bob)
  CREATE (bob)-[:KNOWS {since: 2021}]->(charlie)
  CREATE (charlie)-[:KNOWS {since: 2019}]->(alice)
`)

// Read all people
const people = db.query(`
  MATCH (p:Person)
  RETURN p.name, p.age
  ORDER BY p.age
`)

console.log('People:')
for (const row of people.rows) {
  console.log(`  ${row.get('p.name')} (age ${row.get('p.age')})`)
}

// Traverse relationships
const friends = db.query(`
  MATCH (p:Person {name: 'Alice'})-[:KNOWS]->(friend)
  RETURN friend.name
`)

console.log('\nAlice knows:')
for (const row of friends.rows) {
  console.log(`  ${row.get('friend.name')}`)
}

// Multi-hop traversal
const friendsOfFriends = db.query(`
  MATCH (p:Person {name: 'Alice'})-[:KNOWS*2]->(fof)
  RETURN fof.name
`)

console.log('\nFriends of friends:')
for (const row of friendsOfFriends.rows) {
  console.log(`  ${row.get('fof.name')}`)
}

// Update a property
db.mutate(`
  MATCH (p:Person {name: 'Bob'})
  SET p.age = 26
`)

// Verify the update
const updated = db.query(`
  MATCH (p:Person {name: 'Bob'})
  RETURN p.name, p.age
`)

console.log('\nUpdated:')
for (const row of updated.rows) {
  console.log(`  ${row.get('p.name')} is now ${row.get('p.age')}`)
}

// Stats
const stats = db.stats()
console.log('\nDatabase stats:', stats)

db.close()
