// ArcFlow SDK — Vector Search Example
// Create embeddings, build a vector index, search by similarity.

import { openInMemory } from 'arcflow'

const db = openInMemory()

// ── Create documents with embeddings ──
console.log('Creating documents with embeddings...')
const docs = [
  { title: 'Introduction to AI', embedding: [0.1, 0.9, 0.3, 0.2, 0.5] },
  { title: 'Machine Learning Basics', embedding: [0.15, 0.85, 0.35, 0.25, 0.48] },
  { title: 'Database Systems', embedding: [0.8, 0.1, 0.05, 0.02, 0.03] },
  { title: 'Neural Networks', embedding: [0.12, 0.88, 0.32, 0.22, 0.51] },
  { title: 'SQL Optimization', embedding: [0.75, 0.15, 0.08, 0.05, 0.07] },
]

for (const doc of docs) {
  db.mutate(`CREATE (d:Document {title: '${doc.title}', embedding: '${JSON.stringify(doc.embedding)}'})`)
}

// ── Create vector index ──
console.log('Creating vector index...')
db.mutate("CREATE VECTOR INDEX doc_search FOR (n:Document) ON (n.embedding) OPTIONS {dimensions: 5, similarity: 'cosine'}")

// ── Search by similarity ──
const queryVector = [0.13, 0.87, 0.33, 0.23, 0.49]  // Closest to "Neural Networks"
console.log('\nSearching for documents similar to query vector...')
const results = db.query(
  "CALL algo.vectorSearch('doc_search', $vector, 3)",
  { vector: JSON.stringify(queryVector) }
)

console.log('Top 3 results:')
for (const row of results.rows) {
  console.log(`  ${row.get('title')} (score: ${row.get('score')})`)
}

// ── Full-text search alternative ──
console.log('\nFull-text search:')
db.mutate("CREATE FULLTEXT INDEX doc_text FOR (n:Document) ON (n.title)")
const textResults = db.query("CALL db.index.fulltext.queryNodes('doc_text', 'machine learning')")
for (const row of textResults.rows) {
  console.log(`  ${row.get('title')} (BM25 score: ${row.get('score')})`)
}

db.close()
console.log('\nDone!')
