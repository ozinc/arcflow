import { describe, it, expect } from 'vitest'
import { openInMemory } from 'arcflow'

describe('graph operations', () => {
  it('creates and queries nodes', () => {
    const db = openInMemory()

    db.mutate("CREATE (a:Person {name: 'Alice'})")
    db.mutate("CREATE (b:Person {name: 'Bob'})")
    db.mutate("MATCH (a:Person {name: 'Alice'}) MATCH (b:Person {name: 'Bob'}) CREATE (a)-[:KNOWS]->(b)")

    const result = db.query("MATCH (p:Person) RETURN p.name ORDER BY p.name")
    expect(result.rowCount).toBe(2)
    expect(result.rows[0].get('p.name')).toBe('Alice')
    expect(result.rows[1].get('p.name')).toBe('Bob')

    db.close()
  })

  it('runs graph algorithms', () => {
    const db = openInMemory()

    db.batchMutate([
      "MERGE (n:Node {name: 'A'})",
      "MERGE (n:Node {name: 'B'})",
      "MERGE (n:Node {name: 'C'})",
    ])
    db.batchMutate([
      "MATCH (a:Node {name: 'A'}) MATCH (b:Node {name: 'B'}) MERGE (a)-[:LINK]->(b)",
      "MATCH (a:Node {name: 'B'}) MATCH (b:Node {name: 'C'}) MERGE (a)-[:LINK]->(b)",
      "MATCH (a:Node {name: 'C'}) MATCH (b:Node {name: 'A'}) MERGE (a)-[:LINK]->(b)",
    ])

    const result = db.query("CALL algo.pageRank()")
    expect(result.rowCount).toBeGreaterThan(0)

    db.close()
  })

  it('supports parameterized queries', () => {
    const db = openInMemory()

    db.mutate("CREATE (p:Person {name: 'Alice', age: 30})")

    const result = db.query("MATCH (p:Person {name: $name}) RETURN p.age", {
      name: 'Alice',
    })
    expect(result.rows[0].get('age')).toBe(30)

    db.close()
  })

  it('handles batch mutations', () => {
    const db = openInMemory()

    const count = db.batchMutate([
      "MERGE (a:Item {id: '1', name: 'First'})",
      "MERGE (b:Item {id: '2', name: 'Second'})",
      "MERGE (c:Item {id: '3', name: 'Third'})",
    ])
    expect(count).toBe(3)

    const result = db.query("MATCH (n:Item) RETURN count(*) AS total")
    expect(result.rows[0].get('total')).toBe(3)

    db.close()
  })
})
