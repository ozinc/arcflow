// ArcFlow SDK — Batch Ingestion Example
// Pipeline pattern: ingest entities + facts in bulk using batchMutate.

import { openInMemory } from 'arcflow'

const db = openInMemory()

// Simulated pipeline data (e.g., from an NLP extraction step)
const extractedEntities = [
  { label: 'Person', id: 'p1', name: 'Alice Chen', role: 'CTO' },
  { label: 'Person', id: 'p2', name: 'Bob Smith', role: 'VP Eng' },
  { label: 'Person', id: 'p3', name: 'Carol Davis', role: 'DS' },
  { label: 'Org', id: 'o1', name: 'Acme Corp', industry: 'tech' },
  { label: 'Org', id: 'o2', name: 'Globex Inc', industry: 'finance' },
]

const extractedFacts = [
  { subject: 'p1', object: 'o1', predicate: 'employment', confidence: 0.95 },
  { subject: 'p2', object: 'o2', predicate: 'employment', confidence: 0.90 },
  { subject: 'p1', object: 'p2', predicate: 'collaboration', confidence: 0.72 },
  { subject: 'p1', object: 'o2', predicate: 'advises', confidence: 0.87 },
]

// ── Phase 1: Create entity nodes ──
console.log('Phase 1: Creating entities...')
const entityMutations = extractedEntities.map(e => {
  const props = Object.entries(e)
    .filter(([k]) => k !== 'label')
    .map(([k, v]) => `${k}: '${v}'`)
    .join(', ')
  return `MERGE (n:${e.label} {${props}})`
})
const entityCount = db.batchMutate(entityMutations)
console.log(`  Created ${entityCount} entities`)

// ── Phase 2: Create fact nodes ──
console.log('Phase 2: Creating facts...')
const factMutations = extractedFacts.map((f, i) => {
  const uuid = `fact-${f.subject}-${f.predicate}-${f.object}`
  return `MERGE (f:Fact {uuid: '${uuid}', predicate: '${f.predicate}', confidence: ${f.confidence}})`
})
db.batchMutate(factMutations)

// ── Phase 3: Link facts to entities ──
console.log('Phase 3: Linking facts...')
const linkMutations: string[] = []
for (const f of extractedFacts) {
  const uuid = `fact-${f.subject}-${f.predicate}-${f.object}`
  linkMutations.push(
    `MATCH (s {id: '${f.subject}'}) MATCH (f:Fact {uuid: '${uuid}'}) MERGE (s)-[:SUBJECT_OF]->(f)`
  )
  linkMutations.push(
    `MATCH (f:Fact {uuid: '${uuid}'}) MATCH (o {id: '${f.object}'}) MERGE (f)-[:OBJECT_IS]->(o)`
  )
}
db.batchMutate(linkMutations)

// ── Verify ──
console.log('\nVerification:')
const stats = db.stats()
console.log(`  Nodes: ${stats.nodes}`)
console.log(`  Relationships: ${stats.relationships}`)

const highConf = db.query(`
  MATCH (s)-[:SUBJECT_OF]->(f:Fact)-[:OBJECT_IS]->(o)
  WHERE f.confidence > 0.85
  RETURN s.name, f.predicate, o.name, f.confidence
  ORDER BY f.confidence DESC
`)
console.log(`\nHigh-confidence facts (>0.85):`)
for (const row of highConf.rows) {
  console.log(`  ${row.get('s.name')} --[${row.get('f.predicate')}]--> ${row.get('o.name')} (${row.get('f.confidence')})`)
}

db.close()
console.log('\nDone!')
