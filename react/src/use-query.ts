// useQuery — run a WorldCypher query, re-run when deps change (I-INIT-0048).
//
// Executes synchronously via the in-process engine (no network).
// Re-runs whenever the `deps` array changes (React.useEffect semantics).

import { useEffect, useState } from 'react'
import type { ArcflowDB, QueryParams } from 'arcflow'
import type { UseQueryResult } from './types'

/**
 * Execute a WorldCypher query and return the result.
 *
 * The query re-runs whenever `deps` changes. If `db` is `null` or `undefined`,
 * the hook stays in the `loading` state until a db is provided.
 *
 * @param db      ArcFlow database instance (from `open()` or `openInMemory()`).
 * @param query   WorldCypher MATCH/CALL query string.
 * @param params  Optional query parameters (same as `db.query()` params).
 * @param deps    Optional dependency array — re-runs when any dep changes.
 *                If omitted, runs once on mount.
 *
 * @example
 * const { data, loading, error } = useQuery(db, 'MATCH (n:Person) RETURN n.name', undefined, [filter])
 */
export function useQuery(
	db: ArcflowDB | null | undefined,
	query: string,
	params?: QueryParams,
	deps?: readonly unknown[],
): UseQueryResult {
	const [state, setState] = useState<UseQueryResult>({
		data: null,
		loading: true,
		error: null,
	})

	// Stable serialized params key to detect changes without reference equality.
	const paramsKey = params ? JSON.stringify(params) : ''

	useEffect(() => {
		if (!db) return

		setState(s => ({ ...s, loading: true, error: null }))

		try {
			const result = db.query(query, params)
			setState({ data: result, loading: false, error: null })
		} catch (err) {
			const msg = err instanceof Error ? err.message : String(err)
			setState({ data: null, loading: false, error: msg })
		}
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [db, query, paramsKey, ...(deps ?? [])])

	return state
}
