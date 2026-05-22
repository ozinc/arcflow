// ArcFlow Code Intelligence — TypeScript SDK
//
// Typed layer over the engine's generic delta API (I-INIT-0060) and
// impact-traversal primitive (compute_impact_subgraph).
//
// The engine is schema-free. These types define the code intelligence schema
// as conventions, not engine constraints. The labels ("Function", "CALLS", etc.)
// are the same strings used by the Rust sdk/code-intelligence crate — they are
// the single source of truth for schema conventions.

import type { ArcflowDB } from './types'

// ─── Schema constants ─────────────────────────────────────────────────────────
// Mirror of sdk/code-intelligence/src/schema.rs. Keep in sync.

export const Labels = {
  File: 'File',
  Module: 'Module',
  Class: 'Class',
  Function: 'Function',
  Method: 'Method',
  Interface: 'Interface',
  Variable: 'Variable',
  Constant: 'Constant',
  TypeAlias: 'TypeAlias',
  Import: 'Import',
  Commit: 'Commit',
  Test: 'Test',
} as const

export const Edges = {
  Calls: 'CALLS',
  Imports: 'IMPORTS',
  Defines: 'DEFINES',
  Extends: 'EXTENDS',
  Implements: 'IMPLEMENTS',
  Contains: 'CONTAINS',
  TestedBy: 'TESTED_BY',
  Modifies: 'MODIFIES',
  Triggers: 'TRIGGERS',
} as const

// ─── Delta types ─────────────────────────────────────────────────────────────

export interface NodeSpec {
  label: string
  /** Stable ID string (e.g. "n42" or "42"). If omitted, engine assigns next ID. */
  id?: string
  /** SHA-256 of symbol source text. Enables dedup: same hash → write skipped. */
  contentHash?: string
  properties: Record<string, string | number | boolean | null>
}

export interface EdgeSpec {
  kind: string
  fromId: string
  toId: string
  properties?: Record<string, string | number | boolean | null>
}

export interface GraphDelta {
  addedNodes?: NodeSpec[]
  removedNodeIds?: string[]
  updatedNodes?: Array<{ id: string; properties: Record<string, string | number | boolean | null> }>
  addedEdges?: EdgeSpec[]
  removedEdgeIds?: string[]
}

export interface DeltaStats {
  nodesAdded: number
  nodesRemoved: number
  nodesUpdated: number
  edgesAdded: number
  edgesRemoved: number
  walBytesWritten: number
  nodesSkippedByHash: number
}

// ─── Impact traversal ─────────────────────────────────────────────────────────

export interface ImpactNode {
  id: string
  hop: number
}

export interface ImpactSubgraph {
  nodes: ImpactNode[]
}

// ─── Git types ────────────────────────────────────────────────────────────────

export interface CommitRef {
  sha: string
  author: string
  /** UNIX timestamp in seconds. */
  timestamp: number
  message: string
  modifiedFiles: string[]
}

// ─── Live view types ──────────────────────────────────────────────────────────

export interface LiveViewStatus {
  name: string
  frontier: number
  rowCount: number
  queryText: string
}

// ─── CodeGraph — main entry point ─────────────────────────────────────────────

/**
 * Code intelligence layer over an ArcflowDB instance.
 *
 * @example
 * ```typescript
 * import { openInMemory } from 'arcflow'
 * import { CodeGraph } from 'arcflow/code-intelligence'
 *
 * const db = openInMemory()
 * const cg = new CodeGraph(db)
 *
 * await cg.ingest({
 *   addedNodes: [
 *     { label: 'Function', id: '1', properties: { name: 'login', file_path: 'src/auth.ts' }, contentHash: 'abc123' }
 *   ]
 * })
 *
 * const impact = await cg.impactSubgraph(['1'], ['CALLS', 'IMPORTS'], 3)
 * console.log(impact.nodes) // [{ id: '1', hop: 0 }, ...]
 * ```
 */
export class CodeGraph {
  constructor(private db: ArcflowDB) {}

  /**
   * Apply a GraphDelta to the graph — calls the engine's `apply_node_edge_delta()`
   * primitive directly via napi-rs. No GQL compiler, no query plan: one
   * write-lock acquisition + WAL flush. Content-hash dedup is engine-native.
   *
   * Idempotent when nodes supply stable IDs and contentHash: nodes whose hash
   * hasn't changed are skipped entirely (WAL stays silent).
   */
  ingest(delta: GraphDelta): DeltaStats {
    // Translate camelCase SDK types → snake_case JSON expected by the engine
    const payload = {
      added_nodes: (delta.addedNodes ?? []).map(n => ({
        label: n.label,
        id: n.id,
        content_hash: n.contentHash,
        properties: n.properties,
      })),
      removed_node_ids: delta.removedNodeIds ?? [],
      updated_nodes: (delta.updatedNodes ?? []).map(u => ({
        id: u.id,
        properties: u.properties,
      })),
      added_edges: (delta.addedEdges ?? []).map(e => ({
        kind: e.kind,
        from_id: e.fromId,
        to_id: e.toId,
        properties: e.properties ?? {},
      })),
      removed_edge_ids: delta.removedEdgeIds ?? [],
    }
    const raw = JSON.parse(this.db.ingestDelta(JSON.stringify(payload))) as {
      nodes_added: number
      nodes_removed: number
      nodes_updated: number
      edges_added: number
      edges_removed: number
      wal_bytes_written: number
      nodes_skipped_by_hash: number
    }
    return {
      nodesAdded: raw.nodes_added,
      nodesRemoved: raw.nodes_removed,
      nodesUpdated: raw.nodes_updated,
      edgesAdded: raw.edges_added,
      edgesRemoved: raw.edges_removed,
      walBytesWritten: raw.wal_bytes_written,
      nodesSkippedByHash: raw.nodes_skipped_by_hash,
    }
  }

  /**
   * BFS blast-radius traversal — calls the engine's `compute_impact_subgraph()`
   * primitive directly via napi-rs. No GQL compiler, no query plan: one
   * read-lock acquisition + in-memory BFS. Sub-millisecond on graphs with 1M+ nodes.
   *
   * "What does changing this function break?" — without a single LLM call.
   *
   * @example
   * ```typescript
   * const impact = cg.impactSubgraph(['login_fn_id'], ['CALLS', 'TESTED_BY'], 4)
   * impact.nodes.forEach(n => console.log(`hop ${n.hop}: ${n.id}`))
   * ```
   */
  impactSubgraph(rootIds: string[], edgeKinds: string[], maxDepth: number): ImpactSubgraph {
    if (rootIds.length === 0) return { nodes: [] }
    const raw = JSON.parse(
      this.db.impactSubgraph(
        JSON.stringify(rootIds),
        JSON.stringify(edgeKinds),
        maxDepth,
      )
    ) as { nodes: Array<{ id: string; hop: number }> }
    return { nodes: raw.nodes }
  }

  /**
   * Register a standing query as a live view for change tracking.
   * The view fires incrementally on every ingest that touches matching nodes.
   *
   * @example
   * ```typescript
   * cg.createLiveView('auth_functions',
   *   "MATCH (f:Function) WHERE f.file_path = 'src/auth.ts' RETURN f.name"
   * )
   * // Later, after ingesting new data:
   * const status = cg.liveViewStatus('auth_functions')
   * console.log(status?.rowCount)
   * ```
   */
  createLiveView(name: string, query: string): void {
    this.db.mutate(`CREATE LIVE VIEW ${name} AS ${query}`)
  }

  /**
   * Poll the current snapshot of a live view.
   * Returns null if the view has not been registered.
   */
  liveViewStatus(name: string): LiveViewStatus | null {
    try {
      const result = this.db.query(`CALL db.liveViewStatus('${name}')`)
      if (result.rowCount === 0) return null
      const row = result.rows[0]
      return {
        name,
        frontier: Number(row.get('frontier') ?? 0),
        rowCount: Number(row.get('row_count') ?? 0),
        queryText: String(row.get('query_text') ?? ''),
      }
    } catch {
      return null
    }
  }

  /**
   * Ingest a parsed git commit history as Commit nodes + MODIFIES edges.
   * Commit nodes are idempotent — the SHA is used as both the stable ID and
   * the content hash, so re-ingesting the same history is free.
   */
  ingestCommits(commits: CommitRef[]): DeltaStats {
    const delta: GraphDelta = {
      addedNodes: commits.map(c => ({
        label: Labels.Commit,
        id: `commit_${c.sha}`,
        contentHash: c.sha,
        properties: {
          sha: c.sha,
          author: c.author,
          timestamp: c.timestamp,
          message: c.message,
        },
      })),
      addedEdges: commits.flatMap(c =>
        c.modifiedFiles.map(file => ({
          kind: Edges.Modifies,
          fromId: `commit_${c.sha}`,
          toId: `file_${file}`,
          properties: { timestamp: c.timestamp },
        }))
      ),
    }
    return this.ingest(delta)
  }

  /**
   * Parse `git log --name-only --pretty=format:"%H|%ae|%at|%s"` output into
   * CommitRef values ready for ingestCommits().
   */
  static parseGitLog(logOutput: string): CommitRef[] {
    const commits: CommitRef[] = []
    let current: CommitRef | null = null

    for (const line of logOutput.split('\n')) {
      if (line.trim() === '') {
        if (current) {
          commits.push(current)
          current = null
        }
        continue
      }
      if (current) {
        current.modifiedFiles.push(line.trim())
      } else {
        const parts = line.split('|')
        if (parts.length < 4) continue
        current = {
          sha: parts[0].trim(),
          author: parts[1].trim(),
          timestamp: Number.parseInt(parts[2].trim(), 10) || 0,
          message: parts.slice(3).join('|').trim(),
          modifiedFiles: [],
        }
      }
    }
    if (current) commits.push(current)
    return commits
  }
}

