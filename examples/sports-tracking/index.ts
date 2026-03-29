// ArcFlow SDK — Sports Tracking Example
// Track players on a pitch, compute distances, find formations.

import { openInMemory } from 'arcflow'

const db = openInMemory()

// ── Create pitch and players ──
console.log('Setting up match...')
db.batchMutate([
  "CREATE (pitch:Pitch {name: 'Wembley', width: 105, height: 68})",
  "CREATE (p1:Player {id: 'p1', name: 'Alice', team: 'home', number: 10, x: 52.3, y: 34.1, speed: 7.2})",
  "CREATE (p2:Player {id: 'p2', name: 'Bob', team: 'home', number: 7, x: 65.0, y: 20.5, speed: 4.1})",
  "CREATE (p3:Player {id: 'p3', name: 'Carol', team: 'away', number: 9, x: 48.7, y: 35.2, speed: 8.9})",
  "CREATE (p4:Player {id: 'p4', name: 'Dave', team: 'away', number: 5, x: 40.2, y: 50.1, speed: 3.5})",
  "CREATE (ball:Ball {x: 50.0, y: 33.5, speed: 12.4})",
])

// Create team relationships
db.batchMutate([
  "CREATE (p1:Player {id: 'p1'})-[:PLAYS_FOR]->(t:Team {name: 'home'})",
  "CREATE (p2:Player {id: 'p2'})-[:PLAYS_FOR]->(t:Team {name: 'home'})",
  "CREATE (p3:Player {id: 'p3'})-[:PLAYS_FOR]->(t:Team {name: 'away'})",
  "CREATE (p4:Player {id: 'p4'})-[:PLAYS_FOR]->(t:Team {name: 'away'})",
])

// ── Query: Fast players ──
console.log('\nPlayers running fast (speed > 5.0):')
const fast = db.query("MATCH (p:Player) WHERE p.speed > 5.0 RETURN p.name, p.speed ORDER BY p.speed DESC")
for (const row of fast.rows) {
  console.log(`  ${row.get('name')}: ${row.get('speed')} m/s`)
}

// ── Query: Players by team ──
console.log('\nHome team:')
const home = db.query("MATCH (p:Player) WHERE p.team = 'home' RETURN p.name, p.number")
for (const row of home.rows) {
  console.log(`  #${row.get('number')} ${row.get('name')}`)
}

// ── Query: Graph algorithms on player network ──
console.log('\nPageRank (player importance):')
const pr = db.query("CALL algo.pageRank()")
for (const row of pr.rows) {
  const name = row.get('name')
  if (name) console.log(`  ${name}: ${row.get('rank')}`)
}

// ── Stats ──
const stats = db.stats()
console.log(`\nGraph: ${stats.nodes} nodes, ${stats.relationships} relationships`)

db.close()
console.log('Done!')
