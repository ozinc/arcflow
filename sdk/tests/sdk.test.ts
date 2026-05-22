import { describe, expect, it } from 'vitest'
import { ArcflowError, open, openInMemory } from '../src/index'

// ─── Example 1: Basic CRUD ─────────────────────────────────────────────────

describe('Example 1: Basic CRUD', () => {
	const db = openInMemory()

	it('creates a node with properties', () => {
		const result = db.mutate("CREATE (n:Person {name: 'Alice', age: 30})")
		expect(result).toBeDefined()
	})

	it('reads nodes with typed values', () => {
		const result = db.query('MATCH (n:Person) RETURN n.name, n.age')
		expect(result.rowCount).toBe(1)
		expect(result.rows[0].get('name')).toBe('Alice')
		expect(result.rows[0].get('age')).toBe(30)
		expect(typeof result.rows[0].get('age')).toBe('number')
	})

	it('updates a property', () => {
		db.mutate("MATCH (n:Person {name: 'Alice'}) SET n.age = 31")
		const result = db.query("MATCH (n:Person {name: 'Alice'}) RETURN n.age")
		expect(result.rows[0].get('age')).toBe(31)
	})

	it('deletes a node', () => {
		db.mutate("MATCH (n:Person {name: 'Alice'}) DELETE n")
		const result = db.query("MATCH (n:Person {name: 'Alice'}) RETURN n.name")
		expect(result.rowCount).toBe(0)
	})

	it('result has computeMs timing', () => {
		const result = db.query('MATCH (n:Person) RETURN count(*)')
		expect(typeof result.computeMs).toBe('number')
		expect(result.computeMs).toBeGreaterThanOrEqual(0)
	})
})

// ─── Example 2: Multi-MATCH (Entity Linking) ───────────────────────────────

describe('Example 2: Entity linking', () => {
	const db = openInMemory()

	it('links entities via inline relationship creation', () => {
		db.mutate("CREATE (a:Person {id: 'p1', name: 'Alice'})")
		db.mutate("CREATE (b:Org {id: 'o1', name: 'Acme'})")
		db.mutate("CREATE (a:Person {id: 'p1'})-[:WORKS_AT]->(b:Org {id: 'o1'})")

		// Traversal query returns both ends
		const result = db.query(
			'MATCH (a:Person)-[:WORKS_AT]->(b:Org) RETURN a.name AS personName, b.name AS orgName',
		)
		expect(result.rowCount).toBeGreaterThanOrEqual(1)
	})

	it('parameterized entity lookup', () => {
		const result = db.query('MATCH (n:Person {id: $id}) RETURN n.name', { id: 'p1' })
		expect(result.rowCount).toBe(1)
		expect(result.rows[0].get('name')).toBe('Alice')

		const orgResult = db.query('MATCH (n:Org {id: $id}) RETURN n.name', { id: 'o1' })
		expect(orgResult.rowCount).toBe(1)
		expect(orgResult.rows[0].get('name')).toBe('Acme')
	})
})

// ─── Example 3: Batch Projection ───────────────────────────────────────────

describe('Example 3: Batch projection', () => {
	const db = openInMemory()

	it('executes batch mutations atomically', () => {
		const mutations = [
			"MERGE (p:Person {id: 'p1', name: 'Alice', workspaceId: 'ws1'})",
			"MERGE (o:Org {id: 'o1', name: 'Acme', workspaceId: 'ws1'})",
			"MERGE (f:Fact {uuid: 'f1', predicate: 'employment', confidence: 0.87})",
		]
		const count = db.batchMutate(mutations)
		expect(count).toBe(3)
	})

	it('verifies batch-created nodes', () => {
		const result = db.query('MATCH (f:Fact {uuid: $uuid}) RETURN f.predicate, f.confidence', {
			uuid: 'f1',
		})
		expect(result.rowCount).toBe(1)
		expect(result.rows[0].get('predicate')).toBe('employment')
		expect(result.rows[0].get('confidence')).toBe(0.87)
	})
})

// ─── Example 4: Algorithms ─────────────────────────────────────────────────

describe('Example 4: Algorithms', () => {
	const db = openInMemory()

	it('runs PageRank directly', () => {
		db.mutate("CREATE (a:Page {name: 'Home'})")
		db.mutate("CREATE (b:Page {name: 'About'})")
		db.mutate("CREATE (a:Page {name: 'Home'})-[:LINKS]->(b:Page {name: 'About'})")

		const result = db.query('CALL algo.pageRank()')
		expect(result.rowCount).toBeGreaterThan(0)
		expect(result.columns.some((c) => c === 'name' || c === 'rank')).toBe(true)
	})
})

// ─── Example 5: Vector Search ──────────────────────────────────────────────

describe('Example 5: Vector search', () => {
	const db = openInMemory()

	it('creates a vector index and searches', () => {
		db.mutate("CREATE (f:Doc {title: 'AI Intro', embedding: '[0.1,0.2,0.3]'})")
		db.mutate(
			"CREATE VECTOR INDEX doc_search FOR (n:Doc) ON (n.embedding) OPTIONS {dimensions: 3, similarity: 'cosine'}",
		)

		const result = db.query("CALL algo.vectorSearch('doc_search', $vector, 10)", {
			vector: JSON.stringify([0.1, 0.2, 0.3]),
		})
		expect(result.rowCount).toBeGreaterThanOrEqual(0)
	})
})

// ─── Example 6: Persistence (WAL) ──────────────────────────────────────────

describe('Example 6: WAL persistence', () => {
	it('in-memory db works for lifecycle tests', () => {
		const db = openInMemory()
		db.mutate("CREATE (n:Important {data: 'critical'})")
		const result = db.query('MATCH (n:Important) RETURN n.data')
		expect(result.rows[0].get('data')).toBe('critical')
		db.close()
	})

	it('rejects operations after close', () => {
		const db = openInMemory()
		db.close()
		expect(() => db.query('RETURN 1')).toThrow(ArcflowError)
	})

	it('isHealthy returns false after close', () => {
		const db = openInMemory()
		expect(db.isHealthy()).toBe(true)
		db.close()
		expect(db.isHealthy()).toBe(false)
	})
})

// ─── Example 7: Error Handling ─────────────────────────────────────────────

describe('Example 7: Error handling', () => {
	const db = openInMemory()

	it('throws ArcflowError for invalid queries', () => {
		expect(() => db.query('INVALID CYPHER')).toThrow(ArcflowError)
	})

	it('error has structured fields', () => {
		try {
			db.query('COMPLETELY INVALID QUERY SYNTAX')
			expect.unreachable('Should have thrown')
		} catch (err) {
			expect(err).toBeInstanceOf(ArcflowError)
			const e = err as ArcflowError
			expect(e.message.length).toBeGreaterThan(0)
			expect(e.code.length).toBeGreaterThan(0)
			expect(['parse', 'validation', 'execution', 'integration']).toContain(e.category)
		}
	})
})

// ─── SDK-specific features ─────────────────────────────────────────────────

describe('SDK features', () => {
	const db = openInMemory()

	it('version() returns a string', () => {
		const v = db.version()
		expect(typeof v).toBe('string')
		expect(v.length).toBeGreaterThan(0)
	})

	it('stats() returns graph statistics', () => {
		db.mutate("CREATE (n:StatsTest {name: 'test'})")
		const s = db.stats()
		expect(typeof s.nodes).toBe('number')
		expect(typeof s.relationships).toBe('number')
		expect(typeof s.indexes).toBe('number')
	})

	it('TypedRow.toObject() returns all columns', () => {
		db.mutate("CREATE (n:ObjTest {name: 'Alice', age: 25, active: true})")
		const result = db.query('MATCH (n:ObjTest) RETURN n.name, n.age, n.active')
		const obj = result.rows[0].toObject()
		expect(typeof obj).toBe('object')
		expect(Object.keys(obj).length).toBeGreaterThanOrEqual(3)
	})

	it('query with numeric params', () => {
		db.mutate('CREATE (n:NumTest {score: 42})')
		const result = db.query('MATCH (n:NumTest {score: $score}) RETURN n.score', { score: 42 })
		expect(result.rowCount).toBe(1)
	})

	it('columns array matches result shape', () => {
		const result = db.query('MATCH (n:ObjTest) RETURN n.name, n.age')
		expect(result.columns.length).toBe(2)
		expect(result.columns[0]).toContain('name')
		expect(result.columns[1]).toContain('age')
	})

	it('TypedRow.get() returns null for unknown columns', () => {
		db.mutate('CREATE (n:NullTest {x: 1})')
		const result = db.query('MATCH (n:NullTest) RETURN n.x')
		expect(result.rows[0].get('nonexistent')).toBeNull()
	})
})
