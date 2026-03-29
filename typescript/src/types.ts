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
}

/** Sync configuration for bidirectional replication. */
export interface SyncConfig {
	/** Sync endpoint URL. */
	url: string
	/** Authentication token. */
	token: string
}
