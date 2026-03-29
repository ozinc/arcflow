import { openInMemory } from 'arcflow'

const db = openInMemory()

// Build a knowledge graph
db.mutate(`
  CREATE (js:Language {name: 'JavaScript', type: 'dynamic'})
  CREATE (ts:Language {name: 'TypeScript', type: 'static'})
  CREATE (rust:Language {name: 'Rust', type: 'static'})
  CREATE (react:Framework {name: 'React', category: 'frontend'})
  CREATE (next:Framework {name: 'Next.js', category: 'fullstack'})
  CREATE (arcflow:Database {name: 'ArcFlow', category: 'graph'})

  CREATE (ts)-[:SUPERSET_OF]->(js)
  CREATE (react)-[:WRITTEN_IN]->(js)
  CREATE (next)-[:BUILT_ON]->(react)
  CREATE (arcflow)-[:WRITTEN_IN]->(rust)
  CREATE (arcflow)-[:HAS_SDK {language: 'TypeScript'}]->(ts)
`)

// Traverse relationships
const result = db.query(`
  MATCH (db:Database)-[:WRITTEN_IN]->(lang:Language)
  MATCH (db)-[:HAS_SDK]->(sdk:Language)
  RETURN db.name, lang.name AS engine_lang, sdk.name AS sdk_lang
`)

console.log('Knowledge Graph:')
for (const row of result.rows) {
  console.log(`  ${row.get('db.name')} — engine: ${row.get('engine_lang')}, SDK: ${row.get('sdk_lang')}`)
}

// Find paths
const paths = db.query(`
  MATCH path = (ts:Language {name: 'TypeScript'})-[*1..3]->(target)
  RETURN target.name, length(path) AS depth
  ORDER BY depth
`)

console.log('\nReachable from TypeScript:')
for (const row of paths.rows) {
  console.log(`  ${row.get('target.name')} (depth ${row.get('depth')})`)
}

db.close()
