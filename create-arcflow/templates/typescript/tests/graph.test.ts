import { describe, it, expect } from 'vitest'
import { openInMemory } from 'arcflow'

describe('graph operations', () => {
  it('creates and queries nodes', () => {
    const db = openInMemory()

    db.mutate("CREATE (a:Person {name: 'Alice'})")
    db.mutate("CREATE (b:Person {name: 'Bob'})")
    db.mutate("CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'})")

    const result = db.query("MATCH (p:Person) RETURN p.name ORDER BY p.name")
    expect(result.rowCount).toBe(2)
    expect(result.rows[0].get('name')).toBe('Alice')
    expect(result.rows[1].get('name')).toBe('Bob')

    db.close()
  })

  it('runs graph algorithms', () => {
    const db = openInMemory()

    db.batchMutate([
      "CREATE (a:Node {name: 'A'})",
      "CREATE (b:Node {name: 'B'})",
      "CREATE (c:Node {name: 'C'})",
      "CREATE (a:Node {name: 'A'})-[:LINK]->(b:Node {name: 'B'})",
      "CREATE (b:Node {name: 'B'})-[:LINK]->(c:Node {name: 'C'})",
      "CREATE (c:Node {name: 'C'})-[:LINK]->(a:Node {name: 'A'})",
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
