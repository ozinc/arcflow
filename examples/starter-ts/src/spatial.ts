import { openInMemory } from 'arcflow'

const db = openInMemory()

// Create a spatial graph (football pitch example)
db.mutate(`
  CREATE (p1:Player {name: 'Alice', team: 'A', x: 10.0, z: 5.0})
  CREATE (p2:Player {name: 'Bob', team: 'A', x: 15.0, z: -3.0})
  CREATE (p3:Player {name: 'Charlie', team: 'B', x: -20.0, z: 10.0})
  CREATE (p4:Player {name: 'Diana', team: 'B', x: 45.0, z: 2.0})
  CREATE (ball:Ball {x: 12.0, z: 3.0})
`)

// Find players near the ball
const nearby = db.query(`
  MATCH (p:Player), (b:Ball)
  WITH p, b, sqrt((p.x - b.x)^2 + (p.z - b.z)^2) AS dist
  WHERE dist < 20.0
  RETURN p.name, p.team, round(dist, 1) AS distance
  ORDER BY dist
`)

console.log('Players near the ball:')
for (const row of nearby.rows) {
  console.log(`  ${row.get('p.name')} (${row.get('p.team')}) — ${row.get('distance')}m`)
}

db.close()
