// @arcflow/react — shared types (I-INIT-0048)

import type { QueryResult, QueryParams, SubscriptionRow, DeltaEvent } from 'arcflow'

/** Result state returned by `useQuery`. */
export interface UseQueryResult {
	/** Query result rows, or `null` while loading / on error. */
	data: QueryResult | null
	/** True during the initial load and on every re-fetch. */
	loading: boolean
	/** Error message if the query threw, otherwise `null`. */
	error: string | null
}

/** Result state returned by `useLiveQuery`. */
export interface UseLiveQueryState {
	/** Current rows from the live subscription. `null` until first delivery. */
	rows: SubscriptionRow[] | null
	/** True until the first snapshot is delivered. */
	loading: boolean
	/** Error message if subscription setup failed, otherwise `null`. */
	error: string | null
}

export type { QueryParams, QueryResult, SubscriptionRow, DeltaEvent }
