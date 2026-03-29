// ArcFlow SDK — AI Agent Example
// Build a knowledge graph that an LLM can query via the SDK.
// This pattern is the foundation for MCP integration and GraphRAG.

import { openInMemory } from 'arcflow'

const db = openInMemory()

// ── Load knowledge base ──
console.log('Loading knowledge base...')
db.batchMutate([
  // People
  "CREATE (p:Person {id: 'alice', name: 'Alice Chen', role: 'CTO', expertise: 'distributed systems'})",
  "CREATE (p:Person {id: 'bob', name: 'Bob Smith', role: 'VP Eng', expertise: 'machine learning'})",
  "CREATE (p:Person {id: 'carol', name: 'Carol Davis', role: 'Staff Eng', expertise: 'databases'})",

  // Projects
  "CREATE (proj:Project {id: 'atlas', name: 'Project Atlas', status: 'active', priority: 'high'})",
  "CREATE (proj:Project {id: 'beacon', name: 'Project Beacon', status: 'planning', priority: 'medium'})",

  // Documents
  "CREATE (d:Document {id: 'rfc1', title: 'Atlas Architecture RFC', author: 'alice', embedding: '[0.1,0.8,0.3]'})",
  "CREATE (d:Document {id: 'rfc2', title: 'Beacon Proposal', author: 'bob', embedding: '[0.7,0.2,0.6]'})",
])

// Relationships
db.batchMutate([
  "CREATE (p:Person {id: 'alice'})-[:LEADS]->(proj:Project {id: 'atlas'})",
  "CREATE (p:Person {id: 'bob'})-[:CONTRIBUTES_TO]->(proj:Project {id: 'atlas'})",
  "CREATE (p:Person {id: 'carol'})-[:LEADS]->(proj:Project {id: 'beacon'})",
  "CREATE (p:Person {id: 'alice'})-[:MENTORS]->(p2:Person {id: 'carol'})",
])

// ── Simulate agent queries ──

// "Who leads Project Atlas?"
console.log('\nAgent query: "Who leads Project Atlas?"')
const leader = db.query("MATCH (p:Person)-[:LEADS]->(proj:Project {name: 'Project Atlas'}) RETURN p.name, p.role")
for (const row of leader.rows) {
  console.log(`  ${row.get('name')} (${row.get('role')})`)
}

// "What is Alice working on?"
console.log('\nAgent query: "What is Alice working on?"')
const work = db.query("MATCH (p:Person {id: $id})-[]->(target) RETURN labels(target), target.name", { id: 'alice' })
for (const row of work.rows) {
  console.log(`  ${row.get('labels(target)')}: ${row.get('target.name')}`)
}

// "Who are the most connected people?"
console.log('\nAgent query: "Who are the most connected people?"')
const central = db.query("CALL algo.pageRank()")
for (const row of central.rows) {
  const name = row.get('name')
  if (name) console.log(`  ${name}: rank ${row.get('rank')}`)
}

// "Find documents related to architecture"
console.log('\nAgent query: "Find related documents"')
db.mutate("CREATE FULLTEXT INDEX doc_search FOR (n:Document) ON (n.title)")
const docs = db.query("CALL db.index.fulltext.queryNodes('doc_search', 'Architecture')")
for (const row of docs.rows) {
  console.log(`  ${row.get('title')} (BM25: ${row.get('score')})`)
}

// "Find communities in the org"
console.log('\nAgent query: "Find communities"')
const communities = db.query("CALL algo.louvain()")
for (const row of communities.rows) {
  const name = row.get('name')
  if (name) console.log(`  ${name} → community ${row.get('community')}`)
}

db.close()
console.log('\nDone!')
