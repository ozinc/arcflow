// @arcflow/react — React hooks for ArcFlow (I-INIT-0048, Wave SUB-SDK-0002)
//
// useQuery    — run a WorldCypher query, re-run when deps change.
// useLiveQuery — subscribe to a live query, update on every result change.
//
// Both hooks are zero-network: ArcFlow runs in-process. No WebSocket needed
// for the local graph — subscriptions use LIVE VIEW + frontier polling.

export { useQuery } from './use-query'
export { useLiveQuery } from './use-live-query'
export type { UseQueryResult, UseLiveQueryState } from './types'
