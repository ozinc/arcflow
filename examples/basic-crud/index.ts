// ArcFlow SDK — Basic CRUD Example
// Run: npx ts-node index.ts (or compile with tsc first)

import { openInMemory } from 'arcflow'

const db = openInMemory()

// ── Create ──
console.log('Creating nodes...')
db.mutate("CREATE (n:Person {name: 'Alice', age: 30, email: 'alice@example.com'})")
db.mutate("CREATE (n:Person {name: 'Bob', age: 35, email: 'bob@example.com'})")
db.mutate("CREATE (n:Company {name: 'Acme', industry: 'tech'})")

// Create a relationship
db.mutate("MATCH (a:Person {name: 'Alice'}) MATCH (c:Company {name: 'Acme'}) MERGE (a)-[:WORKS_AT]->(c)")

// ── Read ──
console.log('\nReading all people:')
const people = db.query("MATCH (n:Person) RETURN n.name, n.age ORDER BY n.name")
for (const row of people.rows) {
  console.log(`  ${row.get('name')} (age ${row.get('age')})`)
}

// Read with parameters
console.log('\nFind Alice:')
const alice = db.query("MATCH (n:Person {name: $name}) RETURN n.name, n.age, n.email", {
  name: 'Alice',
})
console.log(`  ${alice.rows[0].toObject()}`)

// Read with traversal
console.log('\nWho works at Acme?')
const employees = db.query("MATCH (p:Person)-[:WORKS_AT]->(c:Company {name: 'Acme'}) RETURN p.name")
for (const row of employees.rows) {
  console.log(`  ${row.get('name')}`)
}

// ── Update ──
console.log('\nUpdating Alice age...')
db.mutate("MATCH (n:Person {name: 'Alice'}) SET n.age = 31")
const updated = db.query("MATCH (n:Person {name: 'Alice'}) RETURN n.age")
console.log(`  Alice is now ${updated.rows[0].get('age')}`)

// ── Delete ──
console.log('\nDeleting Bob...')
db.mutate("MATCH (n:Person {name: 'Bob'}) DELETE n")
const remaining = db.query("MATCH (n:Person) RETURN count(*) AS total")
console.log(`  ${remaining.rows[0].get('total')} person(s) remaining`)

// ── Stats ──
const stats = db.stats()
console.log(`\nGraph stats: ${stats.nodes} nodes, ${stats.relationships} relationships`)

db.close()
console.log('\nDone!')
