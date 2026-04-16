#!/usr/bin/env node
/**
 * check-schema-sync.js
 *
 * Validates that the TypeScript schema constants in
 *   typescript/src/code-intelligence.ts
 * mirror the snapshot committed at
 *   schemas/schema-snapshot.json
 *
 * The snapshot is derived from the engine's source of truth:
 *   arcflow/sdk/code-intelligence/src/schema.rs
 *
 * Protocol:
 *   - When schema.rs changes in the engine repo, update schema-snapshot.json
 *     and code-intelligence.ts in the same arcflow-docs PR.
 *   - CI runs this script to catch mismatches before merge.
 *   - Run locally: node scripts/check-schema-sync.js
 *   - Optionally diff against live schema.rs: node scripts/check-schema-sync.js --rust path/to/schema.rs
 *
 * Exit 0 = in sync. Exit 1 = mismatch (CI fails). Exit 2 = parse error.
 *
 * NOTE(invariant): The Rust file is the source of truth. This snapshot is the
 *   committed cross-repo contract. code-intelligence.ts must mirror both.
 *   Consequence: nodes ingested by the Rust layer won't be found by TypeScript
 *   queries if their label/edge strings diverge — silent data loss.
 */

import { readFileSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const root = resolve(__dirname, '..')

// ─── Parse schemas/schema-snapshot.json ──────────────────────────────────────

function loadSnapshot() {
  const p = resolve(root, 'schemas', 'schema-snapshot.json')
  try {
    const data = JSON.parse(readFileSync(p, 'utf8'))
    return {
      labels: new Set(data.labels),
      edges: new Set(data.edges),
    }
  } catch (e) {
    console.error(`ERROR: Cannot read or parse ${p}: ${e.message}`)
    process.exit(2)
  }
}

// ─── Optionally parse a live schema.rs for deeper validation ──────────────────

function parseRustSchema(schemaPath) {
  let src
  try {
    src = readFileSync(schemaPath, 'utf8')
  } catch (e) {
    console.error(`ERROR: Cannot read schema.rs at ${schemaPath}: ${e.message}`)
    process.exit(2)
  }
  const labels = new Set()
  const edges = new Set()
  const labelRe = /pub const LABEL_\w+:\s*&str\s*=\s*"([^"]+)"/g
  const edgeRe = /pub const EDGE_\w+:\s*&str\s*=\s*"([^"]+)"/g
  let m
  while ((m = labelRe.exec(src)) !== null) labels.add(m[1])
  while ((m = edgeRe.exec(src)) !== null) edges.add(m[1])
  return { labels, edges }
}

// ─── Parse typescript/src/code-intelligence.ts ───────────────────────────────

function parseTypescriptSchema() {
  const p = resolve(root, 'typescript', 'src', 'code-intelligence.ts')
  let src
  try {
    src = readFileSync(p, 'utf8')
  } catch (e) {
    console.error(`ERROR: Cannot read ${p}: ${e.message}`)
    process.exit(2)
  }

  function extractObjectValues(objectName) {
    const re = new RegExp(
      `export const ${objectName}\\s*=\\s*\\{([^}]+)\\}\\s*as const`,
      's'
    )
    const match = src.match(re)
    if (!match) {
      console.error(`ERROR: Could not find 'export const ${objectName} = { ... } as const' in code-intelligence.ts`)
      process.exit(2)
    }
    const values = new Set()
    const pairRe = /:\s*'([^']+)'/g
    let m
    while ((m = pairRe.exec(match[1])) !== null) values.add(m[1])
    return values
  }

  return {
    labels: extractObjectValues('Labels'),
    edges: extractObjectValues('Edges'),
  }
}

// ─── Compare two sets and report differences ──────────────────────────────────

function compare(sectionName, expected, actual, expectedLabel, actualLabel) {
  const missingFromActual = [...expected].filter(x => !actual.has(x))
  const extraInActual = [...actual].filter(x => !expected.has(x))

  if (missingFromActual.length === 0 && extraInActual.length === 0) {
    console.log(`  ✓ ${sectionName}: in sync (${expected.size} values)`)
    return true
  }

  if (missingFromActual.length > 0) {
    console.error(`  ✗ ${sectionName}: in ${expectedLabel} but MISSING from ${actualLabel}:`)
    missingFromActual.forEach(v => console.error(`      "${v}"`))
  }
  if (extraInActual.length > 0) {
    console.error(`  ✗ ${sectionName}: in ${actualLabel} but MISSING from ${expectedLabel}:`)
    extraInActual.forEach(v => console.error(`      "${v}"`))
  }
  return false
}

// ─── Main ─────────────────────────────────────────────────────────────────────

function main() {
  const rustSchemaArg = process.argv.includes('--rust')
    ? process.argv[process.argv.indexOf('--rust') + 1]
    : null

  const snapshot = loadSnapshot()
  const ts = parseTypescriptSchema()

  let failed = false

  console.log('\nSchema sync check — arcflow-docs')
  console.log(`  Snapshot:   schemas/schema-snapshot.json`)
  console.log(`  TypeScript: typescript/src/code-intelligence.ts`)
  if (rustSchemaArg) console.log(`  Rust:       ${rustSchemaArg}`)
  console.log()

  // Check 1: TypeScript vs snapshot
  console.log('Check 1: TypeScript mirrors snapshot')
  const ok1a = compare('Labels', snapshot.labels, ts.labels, 'snapshot', 'code-intelligence.ts')
  const ok1b = compare('Edges',  snapshot.edges,  ts.edges,  'snapshot', 'code-intelligence.ts')
  if (!ok1a || !ok1b) failed = true

  // Check 2 (optional): snapshot vs live schema.rs
  if (rustSchemaArg) {
    console.log('\nCheck 2: Snapshot mirrors schema.rs')
    const rust = parseRustSchema(rustSchemaArg)
    const ok2a = compare('Labels', rust.labels, snapshot.labels, 'schema.rs', 'snapshot')
    const ok2b = compare('Edges',  rust.edges,  snapshot.edges,  'schema.rs', 'snapshot')
    if (!ok2a || !ok2b) {
      failed = true
      console.error('\n  → Update schemas/schema-snapshot.json to match schema.rs.')
    }
  }

  console.log()
  if (failed) {
    console.error('FAIL: Schema mismatch detected.')
    console.error('      See REPO-SPLIT.md → Schema Sync section for the update protocol.')
    console.error('      Summary: schema.rs (engine) → schema-snapshot.json → code-intelligence.ts')
    process.exit(1)
  } else {
    console.log('PASS: TypeScript schema mirrors snapshot exactly.')
    if (!rustSchemaArg) {
      console.log('      (Run with --rust path/to/schema.rs to also validate the snapshot against schema.rs)')
    }
  }
}

main()
