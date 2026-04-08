# Repository Split — Single Source of Truth

Two repositories. One source of truth for each concern. Neither repo duplicates the other.

## arcflow/ — The Engine

**Owns:** everything that compiles to libarcflow.so / .dylib / WASM.

| What | Where |
|---|---|
| Graph kernel (nodes, edges, WAL, MVCC) | `crates/wc-core/` |
| Query compiler + IR | `crates/wc-query-compiler/`, `crates/wc-query-ir/` |
| Runtime (engine execution, concurrent store) | `crates/wc-runtime/` |
| Storage (async WAL, crash recovery) | `crates/wc-storage/` |
| C ABI bindings (cdylib + staticlib) | `crates/wc-ffi/` |
| MCP server binary | `crates/wc-mcp/` |
| CLI binary | `crates/cli/` |
| Rust SDK (published as `arcflow` crate) | `crates/wc-sdk/` |
| Code intelligence SDK (Rust layer) | `sdk/code-intelligence/` |
| GPU (CUDA kernels, cuGraph dispatch) | `crates/wc-runtime/src/lib.rs` + PTX |
| Roadmap, waves, initiative DAG | `kanban/` |
| Engine benchmarks | `crates/wc-bench/`, `tools/trading-validator/` |

**Does NOT own:**
- TypeScript SDK source
- Documentation (MDX, AGENTS.md)
- MCP npm package
- Python bindings (pending)

## arcflow-docs/ — The SDK and Docs

**Owns:** everything the public sees and uses.

| What | Where |
|---|---|
| TypeScript SDK (`arcflow` npm package) | `typescript/src/` |
| Code intelligence TypeScript layer | `typescript/src/code-intelligence.ts` |
| MCP npm package (`arcflow-mcp`) | `mcp/` |
| MDX documentation | `docs/` |
| AGENTS.md (LLM-optimized API reference) | `AGENTS.md` |
| llms.txt / llms-full.txt (Context7) | `llms.txt`, `llms-full.txt` |
| Examples and fixtures | `examples/`, `fixtures/` |
| Legal (OISL license) | `legal/` |
| Docker Compose (deployment) | `docker-compose.yml` |

**Does NOT own:**
- Engine source (Rust)
- Rust tests
- WAL implementation
- Roadmap / wave tracking

## Sync rules

**Schema constants are the only shared artifact.** The code intelligence label/edge strings (`"Function"`, `"CALLS"`, etc.) must match between:
- `arcflow/sdk/code-intelligence/src/schema.rs`
- `arcflow-docs/typescript/src/code-intelligence.ts` (the `Labels` and `Edges` objects)

Any change to one requires a matching change to the other. No automated sync — review at PR time.

**API surface is owned by arcflow-docs.** When the engine adds a new primitive (e.g. `apply_node_edge_delta`, `compute_impact_subgraph`), the TypeScript exposure and documentation go to arcflow-docs. The engine Rust tests are authoritative; TypeScript tests test the TypeScript layer.

**AGENTS.md is the canonical public API reference.** It lives in arcflow-docs and is the document that LLMs, coding agents, and Context7 consume. Engine internals (WAL format, PTX kernels, standing query implementation) are not documented here.

## What goes where — decision table

| Artifact | arcflow | arcflow-docs |
|---|:---:|:---:|
| New engine primitive (Rust) | ✓ | |
| TypeScript wrapper for new primitive | | ✓ |
| Python wrapper | | ✓ (pending) |
| New MCP tool (binary) | ✓ | |
| New MCP tool (npm package wiring) | | ✓ |
| New algorithm (e.g. Leiden) | ✓ | |
| New algorithm documentation | | ✓ |
| New WorldCypher syntax | ✓ | |
| WorldCypher reference docs | | ✓ |
| New graph schema convention | ✓ (`sdk/`) | ✓ (TS constants) |
| Benchmark results | ✓ (`kanban/`) | |
| Migration guide from Neo4j | | ✓ |
| Pricing / licensing | | ✓ |
