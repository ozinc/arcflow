// ArcFlow SDK — Type definitions
// Typed, ergonomic interfaces wrapping the raw napi-rs binding.

/** Parameters for parameterized queries. Values are coerced to strings internally. */
export type QueryParams = Record<string, string | number | boolean | null>

/** A single row with typed column access. */
export interface TypedRow {
	/** Get a typed value by column name. */
	get(column: string): string | number | boolean | null
	/** Get all columns as a typed object. */
	toObject(): Record<string, string | number | boolean | null>
}

/** Result of a read query. */
export interface QueryResult {
	/** Column names in result order. */
	columns: string[]
	/** Result rows with typed accessors. */
	rows: TypedRow[]
	/** Number of rows returned. */
	rowCount: number
	/** Query execution time in milliseconds. */
	computeMs: number
}

/** Result of a mutating query, with mutation statistics. */
export interface MutationResult extends QueryResult {
	nodesCreated: number
	nodesDeleted: number
	relationshipsCreated: number
	relationshipsDeleted: number
	propertiesSet: number
}

/** Graph statistics. */
export interface GraphStats {
	nodes: number
	relationships: number
	indexes: number
}

/** The main ArcFlow database interface. */
export interface ArcflowDB {
	/** Engine version string. */
	version(): string

	/** Execute a read-only query. */
	query(cypher: string, params?: QueryParams): QueryResult

	/** Execute a mutating query. */
	mutate(cypher: string, params?: QueryParams): MutationResult

	/** Execute multiple mutations atomically. Returns count of mutations applied. */
	batchMutate(queries: string[]): number

	/** Health check — always true for in-process engine. */
	isHealthy(): boolean

	/** Graph statistics. */
	stats(): GraphStats

	/** Close the database and flush WAL. */
	close(): void

	/** Number of mutations pending sync push (0 if sync not configured). */
	syncPending(): number

	/** Graph fingerprint for sync verification. */
	fingerprint(): string

	/**
	 * Apply a batch node/edge delta directly to the engine — bypasses the
	 * Cypher compiler entirely. One write-lock + WAL flush. Sub-millisecond
	 * for typical code intelligence ingestion batches.
	 *
	 * `delta` must be a JSON string with shape documented in the napi binding.
	 * Returns a JSON string with DeltaStats (nodes_added, nodes_skipped_by_hash, …).
	 *
	 * Prefer `CodeGraph.ingest()` over calling this directly.
	 */
	ingestDelta(deltaJson: string): string

	/**
	 * BFS blast-radius traversal — bypasses the Cypher compiler.
	 * Returns a JSON string `{ nodes: [{ id, hop }] }`.
	 *
	 * Prefer `CodeGraph.impactSubgraph()` over calling this directly.
	 */
	impactSubgraph(rootIdsJson: string, edgeKindsJson: string, maxDepth: number): string

	/**
	 * Create a paginated cursor over a query result.
	 *
	 * Fetches rows page-by-page via SKIP/LIMIT internally. Ideal for large
	 * result sets that should not be loaded all at once.
	 *
	 * @param query     WorldCypher MATCH query.
	 * @param params    Optional query parameters.
	 * @param pageSize  Rows per page (default: 100, min: 1).
	 *
	 * @example
	 * const cursor = db.cursor('MATCH (n:Log) RETURN n.ts AS ts ORDER BY n.ts', undefined, 500)
	 * let page: QueryResult | null
	 * while ((page = cursor.next()) !== null) process(page.rows)
	 * cursor.close()
	 */
	cursor(query: string, params?: QueryParams, pageSize?: number): QueryCursor

	/**
	 * Subscribe to a live query. The handler fires immediately with the current
	 * result (as an add-only initial delta), then again on each mutation that
	 * changes the result.
	 *
	 * Internally creates a LIVE VIEW and polls for frontier changes. Polling is
	 * in-process — no network round-trips.
	 *
	 * @param query    WorldCypher MATCH query (RETURN clause required).
	 * @param handler  Called with `{ added, removed, current, frontier }` on each change.
	 * @param options  Optional polling configuration.
	 * @returns `LiveQuery` handle — call `cancel()` to stop.
	 *
	 * @example
	 * const sub = db.subscribe(
	 *   'MATCH (n:Person) RETURN n.name AS name, n.age AS age',
	 *   ({ added, removed }) => console.log('added', added, 'removed', removed),
	 * )
	 * // … later …
	 * sub.cancel()
	 */
	subscribe(query: string, handler: SubscriptionHandler, options?: SubscribeOptions): LiveQuery
}

/** Sync configuration for bidirectional replication. */
export interface SyncConfig {
	/** Sync endpoint URL. */
	url: string
	/** Authentication token. */
	token: string
}

// ---------------------------------------------------------------------------
// Cursor / Pagination API
// ---------------------------------------------------------------------------

/**
 * Paginated query cursor for large result sets.
 *
 * Each call to `next()` fetches the next page from the engine using SKIP/LIMIT.
 * Call `close()` when done to release resources.
 */
export interface QueryCursor {
	/** Page size this cursor was created with. */
	readonly pageSize: number
	/** Number of pages fetched so far. */
	readonly pagesFetched: number
	/** Whether the cursor is exhausted (last page returned fewer rows than pageSize). */
	readonly done: boolean
	/** Fetch the next page. Returns `null` when exhausted. */
	next(): QueryResult | null
	/** Collect all remaining pages into a single result. */
	all(): QueryResult
	/** Release the cursor. Subsequent `next()` calls return `null`. */
	close(): void
}

// ---------------------------------------------------------------------------
// Live Subscription API
// ---------------------------------------------------------------------------

/** A single row in a subscription result. Column values are typed. */
export type SubscriptionRow = Record<string, string | number | boolean | null>

/** Delta event delivered to a subscription handler. */
export interface DeltaEvent {
	/** Rows present in the new result but not the previous. */
	added: SubscriptionRow[]
	/** Rows present in the previous result but not the new. */
	removed: SubscriptionRow[]
	/** Full current result set after this delta is applied. */
	current: SubscriptionRow[]
	/** Monotonic frontier (mutation sequence) that triggered this event. */
	frontier: number
}

/** Options for `db.subscribe()`. */
export interface SubscribeOptions {
	/**
	 * How often to poll for view updates (milliseconds).
	 * Default: 50. Minimum: 10. Lower = lower latency, slightly higher CPU.
	 */
	pollIntervalMs?: number
}

/** Handler called whenever the subscribed query result changes. */
export type SubscriptionHandler = (event: DeltaEvent) => void

/** Handle returned by `db.subscribe()`. Call `cancel()` to stop the subscription. */
export interface LiveQuery {
	/** Stop the subscription and release the LIVE VIEW. */
	cancel(): void
	/** The internal view name used for this subscription. */
	readonly viewName: string
}
