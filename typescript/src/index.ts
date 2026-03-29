// ArcFlow TypeScript SDK
// Ergonomic, typed wrapper over the raw napi-rs arcflow-core binding.
// Replaces direct Runtime/Session usage with a clean db.query()/db.mutate() API.

import { type QueryResult as RawQueryResult, Runtime, type Session } from 'arcflow-core'
import { ArcflowError } from './errors'
import type {
	ArcflowDB,
	GraphStats,
	MutationResult,
	QueryParams,
	QueryResult,
	TypedRow,
} from './types'

export { ArcflowError } from './errors'
export type { ErrorCategory } from './errors'
export type {
	ArcflowDB,
	QueryParams,
	QueryResult,
	MutationResult,
	TypedRow,
	GraphStats,
} from './types'

/** Open a persistent graph database at the given directory. */
export function open(dataDir: string): ArcflowDB {
	return new ArcflowDBImpl(dataDir)
}

/** Open an in-memory graph database (ideal for testing). */
export function openInMemory(): ArcflowDB {
	return new ArcflowDBImpl(null)
}

// ---------------------------------------------------------------------------
// Internal: TypedRow implementation
// ---------------------------------------------------------------------------

function parseTypedValue(raw: string): string | number | boolean | null {
	if (raw === '' || raw === 'null') return null
	if (raw === 'true') return true
	if (raw === 'false') return false
	const asInt = Number.parseInt(raw, 10)
	if (String(asInt) === raw) return asInt
	const asFloat = Number.parseFloat(raw)
	if (!Number.isNaN(asFloat) && String(asFloat) === raw) return asFloat
	// Strip surrounding quotes if present
	if (raw.length >= 2 && raw.startsWith('"') && raw.endsWith('"')) {
		return raw.slice(1, -1)
	}
	return raw
}

function createTypedRow(columns: string[], rawValues: string[]): TypedRow {
	const colIndex = new Map<string, number>()
	for (let i = 0; i < columns.length; i++) {
		colIndex.set(columns[i], i)
		// Also index by short name (after last '.') for "n.name" → "name" access
		const dot = columns[i].lastIndexOf('.')
		if (dot >= 0) {
			const short = columns[i].slice(dot + 1)
			if (!colIndex.has(short)) colIndex.set(short, i)
		}
	}

	return {
		get(column: string): string | number | boolean | null {
			const idx = colIndex.get(column)
			if (idx === undefined) return null
			return parseTypedValue(rawValues[idx])
		},
		toObject(): Record<string, string | number | boolean | null> {
			const obj: Record<string, string | number | boolean | null> = {}
			for (let i = 0; i < columns.length; i++) {
				obj[columns[i]] = parseTypedValue(rawValues[i])
			}
			return obj
		},
	}
}

// ---------------------------------------------------------------------------
// Internal: coerce QueryParams to Record<string, string>
// ---------------------------------------------------------------------------

function coerceParams(params: QueryParams): Record<string, string> {
	const out: Record<string, string> = {}
	for (const [k, v] of Object.entries(params)) {
		out[k] = v === null ? 'null' : String(v)
	}
	return out
}

// ---------------------------------------------------------------------------
// Internal: build QueryResult from raw napi result
// ---------------------------------------------------------------------------

function buildQueryResult(raw: RawQueryResult, startMs: number): QueryResult {
	const columns = raw.columnsList
	const rows: TypedRow[] = []
	for (let r = 0; r < raw.rowCount; r++) {
		const values: string[] = []
		for (let c = 0; c < raw.columnCount; c++) {
			values.push(raw.get(r, c) ?? '')
		}
		rows.push(createTypedRow(columns, values))
	}
	return {
		columns,
		rows,
		rowCount: raw.rowCount,
		computeMs: Date.now() - startMs,
	}
}

function buildMutationResult(raw: RawQueryResult, startMs: number): MutationResult {
	const base = buildQueryResult(raw, startMs)
	// The engine doesn't currently return mutation stats per-query,
	// so we provide the structure with zeros. Future engine versions
	// will populate these from the execution plan.
	return {
		...base,
		nodesCreated: 0,
		nodesDeleted: 0,
		relationshipsCreated: 0,
		relationshipsDeleted: 0,
		propertiesSet: 0,
	}
}

// ---------------------------------------------------------------------------
// ArcflowDB implementation
// ---------------------------------------------------------------------------

class ArcflowDBImpl implements ArcflowDB {
	private runtime: Runtime
	private session: Session
	private closed = false

	constructor(dataDir: string | null) {
		this.runtime = new Runtime(dataDir)
		this.session = this.runtime.session()
	}

	version(): string {
		return this.runtime.version()
	}

	query(cypher: string, params?: QueryParams): QueryResult {
		this.ensureOpen()
		const start = Date.now()
		try {
			const raw = params
				? this.session.executeWithParams(cypher, coerceParams(params))
				: this.session.execute(cypher)
			return buildQueryResult(raw, start)
		} catch (err) {
			throw ArcflowError.fromNapiError(err)
		}
	}

	mutate(cypher: string, params?: QueryParams): MutationResult {
		this.ensureOpen()
		const start = Date.now()
		try {
			const raw = params
				? this.session.executeWithParams(cypher, coerceParams(params))
				: this.session.execute(cypher)
			return buildMutationResult(raw, start)
		} catch (err) {
			throw ArcflowError.fromNapiError(err)
		}
	}

	batchMutate(queries: string[]): number {
		this.ensureOpen()
		try {
			return this.session.batchMutate(queries)
		} catch (err) {
			throw ArcflowError.fromNapiError(err)
		}
	}

	isHealthy(): boolean {
		if (this.closed) return false
		try {
			this.session.execute('CALL db.version')
			return true
		} catch {
			return false
		}
	}

	stats(): GraphStats {
		this.ensureOpen()
		try {
			const r = this.session.execute('CALL db.stats')
			if (r.rowCount > 0) {
				const cols = r.columnsList
				const nodeIdx = cols.indexOf('nodes')
				const relIdx = cols.indexOf('relationships')
				const idxIdx = cols.indexOf('indexes')
				return {
					nodes: nodeIdx >= 0 ? Number.parseInt(r.get(0, nodeIdx) ?? '0', 10) : 0,
					relationships: relIdx >= 0 ? Number.parseInt(r.get(0, relIdx) ?? '0', 10) : 0,
					indexes: idxIdx >= 0 ? Number.parseInt(r.get(0, idxIdx) ?? '0', 10) : 0,
				}
			}
			return { nodes: 0, relationships: 0, indexes: 0 }
		} catch {
			return { nodes: 0, relationships: 0, indexes: 0 }
		}
	}

	close(): void {
		this.closed = true
		// Runtime/Session are cleaned up by GC since napi-rs handles Drop.
		// For persistent databases, the WAL is flushed on drop.
	}

	private ensureOpen(): void {
		if (this.closed) {
			throw new ArcflowError('DB_CLOSED', 'Database has been closed')
		}
	}
}
