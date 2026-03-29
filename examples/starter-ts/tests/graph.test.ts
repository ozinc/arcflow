import { openInMemory } from 'arcflow'
import { describe, it, expect } from 'vitest'

describe('graph', () => {
  it('creates and queries nodes', () => {
    const db = openInMemory()
    db.mutate(`CREATE (a:Person {name: 'Alice'})`)
    const result = db.query(`MATCH (p:Person) RETURN p.name`)
    expect(result.rows[0].get('p.name')).toBe('Alice')
  })

  it('creates relationships and traverses', () => {
    const db = openInMemory()
    db.mutate(`
      CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'})
    `)
    const result = db.query(`
      MATCH (p:Person {name: 'Alice'})-[:KNOWS]->(friend)
      RETURN friend.name
    `)
    expect(result.rows[0].get('friend.name')).toBe('Bob')
  })

  it('updates properties', () => {
    const db = openInMemory()
    db.mutate(`CREATE (a:Person {name: 'Alice', age: 30})`)
    db.mutate(`MATCH (p:Person {name: 'Alice'}) SET p.age = 31`)
    const result = db.query(`MATCH (p:Person {name: 'Alice'}) RETURN p.age`)
    expect(result.rows[0].get('p.age')).toBe(31)
  })

  it('deletes nodes', () => {
    const db = openInMemory()
    db.mutate(`CREATE (a:Person {name: 'Alice'})`)
    db.mutate(`MATCH (p:Person {name: 'Alice'}) DELETE p`)
    const result = db.query(`MATCH (p:Person) RETURN count(p) AS total`)
    expect(result.rows[0].get('total')).toBe(0)
  })

  it('reports stats', () => {
    const db = openInMemory()
    db.mutate(`CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'})`)
    const stats = db.stats()
    expect(stats.nodes).toBe(2)
    expect(stats.relationships).toBe(1)
  })
})
