// ArcFlow SDK — Typed error classes
// Parses napi error strings ("CODE: message") into structured errors.

export type ErrorCategory = 'parse' | 'validation' | 'execution' | 'integration'

const PARSE_CODES = new Set([
	'EXPECTED_KEYWORD',
	'UNEXPECTED_TOKEN',
	'INVALID_SYNTAX',
	'UNTERMINATED_STRING',
	'INVALID_NUMBER',
	'PARSE_ERROR',
])

const VALIDATION_CODES = new Set([
	'UNKNOWN_FUNCTION',
	'UNKNOWN_PROCEDURE',
	'TYPE_MISMATCH',
	'MISSING_PROPERTY',
	'INVALID_ARGUMENT',
	'SCHEMA_VIOLATION',
])

const INTEGRATION_CODES = new Set(['LOCK_POISONED', 'WAL_ERROR', 'SNAPSHOT_ERROR', 'IO_ERROR'])

function categorize(code: string): ErrorCategory {
	if (PARSE_CODES.has(code)) return 'parse'
	if (VALIDATION_CODES.has(code)) return 'validation'
	if (INTEGRATION_CODES.has(code)) return 'integration'
	return 'execution'
}

function suggest(code: string, message: string): string | undefined {
	if (code === 'EXPECTED_KEYWORD') {
		const match = message.match(/expected\s+(.+)/i)
		if (match) return `Expected ${match[1]}`
	}
	if (code === 'UNKNOWN_FUNCTION') return 'Run CALL db.help to see available functions'
	if (code === 'UNKNOWN_PROCEDURE') return 'Run CALL db.help to see available procedures'
	if (code === 'LOCK_POISONED') return 'Restart the runtime — a previous operation panicked'
	return undefined
}

/** Typed error from the ArcFlow engine. */
export class ArcflowError extends Error {
	/** Error code from the engine (e.g., "EXPECTED_KEYWORD", "LOCK_POISONED"). */
	readonly code: string
	/** Error category for programmatic handling. */
	readonly category: ErrorCategory
	/** Optional recovery hint. */
	readonly suggestion?: string

	constructor(code: string, message: string) {
		super(message)
		this.name = 'ArcflowError'
		this.code = code
		this.category = categorize(code)
		this.suggestion = suggest(code, message)
	}

	/** Parse a napi error (format "CODE: message") into an ArcflowError. */
	static fromNapiError(err: unknown): ArcflowError {
		if (err instanceof ArcflowError) return err

		const msg = err instanceof Error ? err.message : String(err)
		const colonIdx = msg.indexOf(': ')
		if (colonIdx > 0 && colonIdx < 40) {
			const code = msg.slice(0, colonIdx).trim()
			const body = msg.slice(colonIdx + 2).trim()
			// Only treat as code if it looks like an error code (ALL_CAPS or PascalCase)
			if (/^[A-Z][A-Z0-9_]+$/.test(code) || /^[A-Z][a-zA-Z]+$/.test(code)) {
				return new ArcflowError(code, body)
			}
		}
		return new ArcflowError('UNKNOWN', msg)
	}
}
