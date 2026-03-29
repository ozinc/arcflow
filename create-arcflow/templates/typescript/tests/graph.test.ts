import { describe, it, expect } from 'vitest'
import { openInMemory } from 'arcflow'

describe('graph operations', () => {
  it('creates and queries nodes', () => {
    const db = openInMemory()
    db.mutate(`CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'})`)

    const result = db.query(`MATCH (p:Person) RETURN p.name ORDER BY p.name`)
    expect(result.rowCount).toBe(2)
    expect(result.rows[0].get('p.name')).toBe('Alice')
    expect(result.rows[1].get('p.name')).toBe('Bob')
  })

  it('runs graph algorithms', () => {
    const db = openInMemory()
    db.mutate(`
      CREATE (a:Node {name: 'A'})-[:LINK]->(b:Node {name: 'B'})
      CREATE (b)-[:LINK]->(c:Node {name: 'C'})
      CREATE (c)-[:LINK]->(a)
    `)

    const result = db.query(`
      CALL algo.pageRank()
      YIELD node, score
      RETURN node.name, score
    `)
    expect(result.rowCount).toBe(3)
  })

  it('supports parameterized queries', () => {
    const db = openInMemory()
    db.mutate(`CREATE (p:Person {name: 'Alice', age: 30})`)

    const result = db.query(
      `MATCH (p:Person) WHERE p.name = $name RETURN p.age`,
      { name: 'Alice' }
    )
    expect(result.rows[0].get('p.age')).toBe(30)
  })
})
