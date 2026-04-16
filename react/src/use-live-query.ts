// useLiveQuery — subscribe to a live query, update on every result change (I-INIT-0048).
//
// Calls db.subscribe() under the hood. The subscription is created on mount
// (or when deps change) and cancelled on unmount / deps change. No network
// round-trips — the engine polls the LIVE VIEW frontier in-process.

import { useEffect, useRef, useState } from 'react'
import type { ArcflowDB, DeltaEvent, SubscriptionRow } from 'arcflow'
import type { UseLiveQueryState } from './types'

/**
 * Subscribe to a live WorldCypher query.
 *
 * Returns the current result rows and updates the component whenever the
 * underlying data changes. The subscription is cancelled automatically on
 * unmount or when `deps` changes.
 *
 * @param db           ArcFlow database instance.
 * @param query        WorldCypher MATCH query (RETURN clause required).
 * @param deps         Optional dependency array — re-subscribes on change.
 * @param pollIntervalMs  Polling interval in milliseconds (default 50).
 *
 * @example
 * const { rows, loading } = useLiveQuery(db, 'MATCH (n:Task) RETURN n.title AS title')
 * // rows updates automatically whenever a Task node changes
 */
export function useLiveQuery(
	db: ArcflowDB | null | undefined,
	query: string,
	deps?: readonly unknown[],
	pollIntervalMs = 50,
): UseLiveQueryState {
	const [state, setState] = useState<UseLiveQueryState>({
		rows: null,
		loading: true,
		error: null,
	})

	// Track mounted status to prevent setState after unmount.
	const mountedRef = useRef(true)
	useEffect(() => {
		mountedRef.current = true
		return () => { mountedRef.current = false }
	}, [])

	useEffect(() => {
		if (!db) return

		setState({ rows: null, loading: true, error: null })

		let cancelled = false
		let sub: { cancel(): void } | null = null

		try {
			sub = db.subscribe(
				query,
				(event: DeltaEvent) => {
					if (!mountedRef.current || cancelled) return
					setState({ rows: event.current, loading: false, error: null })
				},
				{ pollIntervalMs },
			)
		} catch (err) {
			const msg = err instanceof Error ? err.message : String(err)
			if (mountedRef.current) {
				setState({ rows: null, loading: false, error: msg })
			}
		}

		return () => {
			cancelled = true
			sub?.cancel()
		}
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [db, query, pollIntervalMs, ...(deps ?? [])])

	return state
}
