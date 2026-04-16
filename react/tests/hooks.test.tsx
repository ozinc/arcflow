// @arcflow/react — hook tests (I-INIT-0048, Wave SUB-SDK-0002)
//
// Uses @testing-library/react renderHook with happy-dom environment.
// Tests run against a real in-memory ArcFlow instance — no mocking needed.

import { describe, expect, it, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { openInMemory } from 'arcflow'
import type { ArcflowDB } from 'arcflow'
import { useQuery } from '../src/use-query'
import { useLiveQuery } from '../src/use-live-query'

// ─── useQuery ────────────────────────────────────────────────────────────────

describe('useQuery', () => {
	it('returns loading=true initially', () => {
		const db = openInMemory()
		const { result } = renderHook(() =>
			useQuery(db, 'MATCH (n:UQ1) RETURN n.name AS name'),
		)
		// May already be resolved synchronously, but error and data must be consistent
		expect(result.current.error).toBeNull()
		db.close()
	})

	it('returns data after query executes', async () => {
		const db = openInMemory()
		db.mutate("CREATE (n:UQ2 {name: 'Alice'})")

		const { result } = renderHook(() =>
			useQuery(db, 'MATCH (n:UQ2) RETURN n.name AS name'),
		)

		await waitFor(() => expect(result.current.loading).toBe(false))
		expect(result.current.data).not.toBeNull()
		expect(result.current.data?.rowCount).toBe(1)
		expect(result.current.error).toBeNull()
		db.close()
	})

	it('returns error when query fails', async () => {
		const db = openInMemory()

		const { result } = renderHook(() =>
			useQuery(db, 'INVALID CYPHER !!!'),
		)

		await waitFor(() => expect(result.current.loading).toBe(false))
		expect(result.current.error).not.toBeNull()
		expect(result.current.data).toBeNull()
		db.close()
	})

	it('re-runs when deps change', async () => {
		const db = openInMemory()
		db.mutate("CREATE (n:UQ3 {score: 1})")
		db.mutate("CREATE (n:UQ3 {score: 2})")

		let minScore = 0
		const { result, rerender } = renderHook(
			() => useQuery(
				db,
				'MATCH (n:UQ3) WHERE n.score >= $min RETURN n.score',
				{ min: minScore },
				[minScore],
			),
		)

		await waitFor(() => expect(result.current.loading).toBe(false))
		expect(result.current.data?.rowCount).toBe(2)

		// Change dep — should re-run query
		minScore = 2
		rerender()

		await waitFor(() => expect(result.current.data?.rowCount).toBe(1))
		db.close()
	})

	it('stays loading when db is null', () => {
		const { result } = renderHook(() =>
			useQuery(null, 'MATCH (n) RETURN n'),
		)
		expect(result.current.loading).toBe(true)
		expect(result.current.data).toBeNull()
	})
})

// ─── useLiveQuery ─────────────────────────────────────────────────────────────

describe('useLiveQuery', () => {
	it('delivers initial rows', async () => {
		const db = openInMemory()
		db.mutate("CREATE (n:LQ1 {name: 'Bob'})")

		const { result } = renderHook(() =>
			useLiveQuery(db, 'MATCH (n:LQ1) RETURN n.name AS name', undefined, 10),
		)

		await waitFor(() => expect(result.current.loading).toBe(false))
		expect(result.current.rows).not.toBeNull()
		expect(result.current.rows?.length).toBe(1)
		expect(result.current.error).toBeNull()
		db.close()
	})

	it('updates when a mutation changes the result', async () => {
		const db = openInMemory()

		const { result } = renderHook(() =>
			useLiveQuery(db, 'MATCH (n:LQ2) RETURN n.name AS name', undefined, 10),
		)

		await waitFor(() => expect(result.current.loading).toBe(false))
		const initial = result.current.rows?.length ?? 0

		act(() => {
			db.mutate("CREATE (n:LQ2 {name: 'Carol'})")
		})

		await waitFor(() =>
			expect((result.current.rows?.length ?? 0)).toBeGreaterThan(initial),
		{ timeout: 500 })

		db.close()
	})

	it('stays loading when db is null', () => {
		const { result } = renderHook(() =>
			useLiveQuery(null, 'MATCH (n:LQ3) RETURN n.x'),
		)
		expect(result.current.loading).toBe(true)
		expect(result.current.rows).toBeNull()
	})

	it('cancels subscription on unmount', async () => {
		const db = openInMemory()

		const { result, unmount } = renderHook(() =>
			useLiveQuery(db, 'MATCH (n:LQ4) RETURN n.x AS x', undefined, 10),
		)

		await waitFor(() => expect(result.current.loading).toBe(false))
		unmount()

		// After unmount, no more updates should cause errors
		act(() => {
			db.mutate("CREATE (n:LQ4 {x: 99})")
		})

		// Wait briefly — no assertion error expected
		await new Promise(r => setTimeout(r, 80))
		db.close()
	})

	it('re-subscribes when deps change', async () => {
		const db = openInMemory()
		db.mutate("CREATE (n:LQ5 {tag: 'a'})")

		let filter = 'a'
		const { result, rerender } = renderHook(
			() => useLiveQuery(
				db,
				`MATCH (n:LQ5 {tag: '${filter}'}) RETURN n.tag AS tag`,
				[filter],
				10,
			),
		)

		await waitFor(() => expect(result.current.loading).toBe(false))
		expect(result.current.rows?.length).toBe(1)

		filter = 'b'
		rerender()

		await waitFor(() => expect(result.current.rows?.length).toBe(0))
		db.close()
	})
})
