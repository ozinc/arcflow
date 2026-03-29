// ArcFlow MCP Server
// Lets AI agents query a graph database directly — no code generation needed.
//
// Usage:
//   npx arcflow-mcp                    # in-memory
//   npx arcflow-mcp --data-dir ./mydb  # persistent
//
// 5 tools:
//   get_schema      — labels, rel types, properties, indexes, stats
//   get_capabilities — algorithms, procedures, functions
//   read_query      — read-only WorldCypher (rejects mutations)
//   write_query     — mutating WorldCypher (explicit opt-in)
//   graph_rag       — trusted GraphRAG pipeline

import { Server } from '@modelcontextprotocol/sdk/server/index.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js'
import { Runtime, Session } from 'arcflow-core'

// ---------------------------------------------------------------------------
// Parse CLI args
// ---------------------------------------------------------------------------

const args = process.argv.slice(2)
const dataDirIdx = args.indexOf('--data-dir')
const dataDir = dataDirIdx >= 0 ? args[dataDirIdx + 1] ?? null : null

// ---------------------------------------------------------------------------
// ArcFlow engine (in-process, no server needed)
// ---------------------------------------------------------------------------

const runtime = new Runtime(dataDir)
const session = runtime.session()

function executeQuery(cypher: string): { columns: string[]; rows: Record<string, string>[]; rowCount: number } {
  const result = session.execute(cypher)
  const columns = result.columnsList
  const rows: Record<string, string>[] = []
  for (let r = 0; r < result.rowCount; r++) {
    const row: Record<string, string> = {}
    for (let c = 0; c < result.columnCount; c++) {
      row[columns[c]] = result.get(r, c) ?? ''
    }
    rows.push(row)
  }
  return { columns, rows, rowCount: result.rowCount }
}

function executeTyped(cypher: string): string {
  const result = session.execute(cypher)
  return result.toJson()
}

// ---------------------------------------------------------------------------
// Tool implementations
// ---------------------------------------------------------------------------

function getSchema(): string {
  const parts: string[] = []

  try {
    const labels = executeQuery('CALL db.labels')
    parts.push(`Labels: ${labels.rows.map(r => r.label).join(', ') || '(none)'}`)
  } catch { parts.push('Labels: (unavailable)') }

  try {
    const types = executeQuery('CALL db.types')
    parts.push(`Relationship types: ${types.rows.map(r => r.type).join(', ') || '(none)'}`)
  } catch { parts.push('Relationship types: (unavailable)') }

  try {
    const keys = executeQuery('CALL db.keys')
    parts.push(`Property keys: ${keys.rows.map(r => r.key).join(', ') || '(none)'}`)
  } catch { parts.push('Property keys: (unavailable)') }

  try {
    const stats = executeQuery('CALL db.stats')
    if (stats.rows[0]) {
      parts.push(`Nodes: ${stats.rows[0].nodes ?? '0'}, Relationships: ${stats.rows[0].relationships ?? '0'}`)
    }
  } catch { /* ignore */ }

  try {
    const schema = executeQuery('CALL db.schema')
    if (schema.rowCount > 0) {
      parts.push('Schema detail:')
      for (const row of schema.rows) {
        parts.push(`  :${row.label} (${row.count ?? '?'} nodes) — properties: ${row.properties ?? ''}`)
      }
    }
  } catch { /* ignore */ }

  return parts.join('\n')
}

function getCapabilities(): string {
  const parts: string[] = []

  parts.push('Algorithms (CALL algo.*):')
  parts.push('  pageRank, confidencePageRank, betweenness, closeness, degreeCentrality,')
  parts.push('  louvain, leiden, communityDetection, connectedComponents,')
  parts.push('  clusteringCoefficient, nodeSimilarity, triangleCount, kCore, density, diameter,')
  parts.push('  allPairsShortestPath, nearestNodes, confidencePath,')
  parts.push('  vectorSearch(index, vector, k), similarNodes, hybridSearch,')
  parts.push('  graphRAG, graphRAGTrusted, graphRAGContext')
  parts.push('')

  parts.push('Procedures (CALL db.*):')
  try {
    const procs = executeQuery('CALL db.procedures')
    parts.push(`  ${procs.rows.map(r => r.procedure).join(', ')}`)
  } catch {
    parts.push('  stats, schema, labels, types, propertyKeys, indexes, nodeCount, help, procedures')
  }
  parts.push('')

  parts.push('Window functions:')
  parts.push('  LAG, LEAD, AVG OVER, STDDEV_POP, SUM OVER, PERCENT_RANK, ROW_NUMBER, SKEWNESS, MAX OVER')
  parts.push('')

  parts.push('Observation classes: observed, inferred, predicted')
  parts.push('')

  parts.push('Query features: MATCH, CREATE, MERGE, SET, REMOVE, DELETE, DETACH DELETE,')
  parts.push('  WITH, UNWIND, ORDER BY, LIMIT, OPTIONAL MATCH, AS OF,')
  parts.push('  CREATE VECTOR INDEX, CREATE FULLTEXT INDEX, CREATE LIVE VIEW,')
  parts.push('  LIVE MATCH, LIVE CALL, USE PARTITION, SET SESSION')

  return parts.join('\n')
}

function readQuery(cypher: string): string {
  if (!cypher.trim()) return 'Error: empty query'

  const upper = cypher.toUpperCase()
  const mutating = ['CREATE ', 'SET ', 'DELETE ', 'REMOVE ', 'MERGE ', 'DETACH ']
    .some(kw => upper.includes(kw) || upper.startsWith(kw.trim()))

  // Allow CREATE VECTOR INDEX, CREATE FULLTEXT INDEX, CREATE LIVE VIEW in read mode
  const isIndexOrView = upper.includes('CREATE VECTOR') || upper.includes('CREATE FULLTEXT') || upper.includes('CREATE LIVE VIEW')

  if (mutating && !isIndexOrView) {
    return 'read_query rejects mutating queries (CREATE, SET, DELETE, MERGE, REMOVE). Use write_query instead.'
  }

  try {
    const result = executeQuery(cypher)
    return JSON.stringify({ columns: result.columns, row_count: result.rowCount, rows: result.rows }, null, 2)
  } catch (e) {
    return `Error: ${e instanceof Error ? e.message : String(e)}`
  }
}

function writeQuery(cypher: string): string {
  if (!cypher.trim()) return 'Error: empty query'

  try {
    const result = executeQuery(cypher)
    return JSON.stringify({ columns: result.columns, row_count: result.rowCount, rows: result.rows }, null, 2)
  } catch (e) {
    return `Error: ${e instanceof Error ? e.message : String(e)}`
  }
}

function graphRag(query: string): string {
  if (!query.trim()) return 'Error: empty query'

  try {
    const escaped = query.replace(/'/g, "\\'")
    const json = executeTyped(`CALL algo.graphRAG('${escaped}')`)
    return json
  } catch (e) {
    return `GraphRAG error: ${e instanceof Error ? e.message : String(e)}`
  }
}

// ---------------------------------------------------------------------------
// MCP Server
// ---------------------------------------------------------------------------

const server = new Server(
  { name: 'arcflow-mcp', version: '0.1.0' },
  { capabilities: { tools: {} } },
)

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'get_schema',
      description:
        'Get the graph database schema: labels, relationship types, property keys, indexes, and stats. Call this first to understand the data model before writing queries.',
      inputSchema: { type: 'object' as const, properties: {} },
    },
    {
      name: 'get_capabilities',
      description:
        'Discover available graph algorithms (PageRank, Louvain, etc.), procedures, window functions, and query features. Use this to understand what the engine can do.',
      inputSchema: { type: 'object' as const, properties: {} },
    },
    {
      name: 'read_query',
      description:
        'Execute a read-only WorldCypher query. Supports MATCH, CALL algo.*, CALL db.*. Rejects CREATE/SET/DELETE/MERGE — use write_query for those. Returns rows as JSON.',
      inputSchema: {
        type: 'object' as const,
        properties: {
          cypher: {
            type: 'string',
            description: 'WorldCypher query (read-only). Examples: MATCH (n:Person) RETURN n.name, CALL algo.pageRank(), CALL db.stats',
          },
        },
        required: ['cypher'],
      },
    },
    {
      name: 'write_query',
      description:
        'Execute a mutating WorldCypher query. Supports CREATE, SET, DELETE, MERGE, REMOVE, DETACH DELETE. Changes are immediate.',
      inputSchema: {
        type: 'object' as const,
        properties: {
          cypher: {
            type: 'string',
            description: "WorldCypher mutation. Examples: CREATE (n:Person {name: 'Alice'}), MATCH (n) SET n.age = 30",
          },
        },
        required: ['cypher'],
      },
    },
    {
      name: 'graph_rag',
      description:
        'Run the trusted GraphRAG pipeline — combines graph traversal, vector search, and confidence-weighted ranking to answer a question using the knowledge graph.',
      inputSchema: {
        type: 'object' as const,
        properties: {
          query: {
            type: 'string',
            description: 'Natural language question to answer using the knowledge graph',
          },
        },
        required: ['query'],
      },
    },
  ],
}))

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params

  let text: string
  let isError = false

  switch (name) {
    case 'get_schema':
      text = getSchema()
      break
    case 'get_capabilities':
      text = getCapabilities()
      break
    case 'read_query': {
      const cypher = (args as { cypher?: string }).cypher ?? ''
      text = readQuery(cypher)
      isError = text.startsWith('read_query rejects') || text.startsWith('Error:')
      break
    }
    case 'write_query': {
      const cypher = (args as { cypher?: string }).cypher ?? ''
      text = writeQuery(cypher)
      isError = text.startsWith('Error:')
      break
    }
    case 'graph_rag': {
      const query = (args as { query?: string }).query ?? ''
      text = graphRag(query)
      isError = text.startsWith('GraphRAG error:')
      break
    }
    default:
      text = `Unknown tool: ${name}`
      isError = true
  }

  return { content: [{ type: 'text', text }], isError }
})

// ---------------------------------------------------------------------------
// Start
// ---------------------------------------------------------------------------

async function main() {
  const transport = new StdioServerTransport()
  await server.connect(transport)

  const mode = dataDir ? `persistent (${dataDir})` : 'in-memory'
  console.error(`arcflow-mcp running (${mode})`)
}

main().catch((e) => {
  console.error('Failed to start arcflow-mcp:', e)
  process.exit(1)
})
