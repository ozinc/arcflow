# Repository Split — Single Source of Truth

Two repositories. One source of truth for each concern. Neither repo duplicates the other.
This file is **identical** in both repos and is the governing contract for all agents.

| Repo | GitHub | Visibility |
|---|---|---|
| Engine (this if reading from arcflow-core/) | `https://github.com/ozinc/arcflow-core` | Private |
| SDK + Docs (this if reading from arcflow/) | `https://github.com/ozinc/arcflow` | Public |

---

## The Wall

```
arcflow/  (CLOSED SOURCE)               arcflow-docs/  (OPEN SOURCE)
────────────────────────────            ────────────────────────────
Everything that compiles into           Everything a developer or agent
libarcflow.{so,dylib,wasm}              needs to BUILD ON top of ArcFlow

  crates/    sdk/code-intelligence/       typescript/   mcp/   react/
  kanban/    docs/ (engine-internal)      docs/         examples/
  tools/     bindings/                    AGENTS.md     llms.txt
                │                                │
                │  Release artifacts only        │
                │  (binaries, schema.rs)         │
                └────────────────────────────────┘
```

**The wall is one-directional.** arcflow produces artifacts; arcflow-docs consumes them.
arcflow-docs never pushes source back into the engine.

---

## arcflow/ — The Engine

**Owns:** everything that compiles to `libarcflow.so` / `.dylib` / WASM.

| What | Where |
|---|---|
| Graph kernel (nodes, edges, WAL, MVCC) | `crates/wc-core/` |
| Query compiler + IR | `crates/wc-query-compiler/`, `crates/wc-query-ir/` |
| Runtime (engine execution, concurrent store) | `crates/wc-runtime/` |
| Storage (async WAL, crash recovery) | `crates/wc-storage/` |
| C ABI bindings (cdylib + staticlib) | `crates/wc-ffi/` |
| MCP server binary | `crates/wc-mcp/` |
| CLI binary | `crates/wc-cli/` |
| Rust SDK (published as `arcflow` on crates.io) | `crates/wc-sdk/` |
| Schema constants — Rust source of truth | `sdk/code-intelligence/src/schema.rs` |
| Code intelligence Rust layer | `sdk/code-intelligence/` |
| GPU kernels (CUDA PTX, cuGraph dispatch) | `crates/wc-runtime/src/lib.rs` + PTX |
| Roadmap, waves, initiative DAG | `kanban/` |
| Engine benchmarks | `crates/wc-bench/`, `tools/trading-validator/` |
| Engine-internal docs (architecture, research) | `docs/` |
| Agent guide for engine contributors | `AGENTS-ENGINE.md` |

**Does NOT own:**
- TypeScript SDK source code
- MDX documentation (public guides, tutorials, reference)
- Public `AGENTS.md` (LLM / agent API reference)
- MCP npm package
- React components
- `llms.txt` / `llms-full.txt`
- Examples intended for end-users
- `sdk/typescript/`, `sdk/mcp/`, `sdk/react/`, `sdk/docs/` — these no longer exist here

---

## arcflow-docs/ — The SDK and Docs

**Owns:** everything the public sees, uses, and builds with.

| What | Where |
|---|---|
| TypeScript SDK (`arcflow` npm package) | `typescript/src/` |
| Schema constants — TypeScript mirror | `typescript/src/code-intelligence.ts` |
| MCP npm package (`arcflow-mcp`) | `mcp/` |
| React hooks library | `react/src/` |
| MDX documentation | `docs/` |
| Public AGENTS.md (LLM-optimized API reference) | `AGENTS.md` |
| `llms.txt` / `llms-full.txt` (Context7 / agent context) | `llms.txt`, `llms-full.txt` |
| Examples | `examples/` |
| Fixtures | `fixtures/` |
| Project scaffolder | `create-arcflow/` |
| Install scripts | `install/` |
| Legal (OISL license) | `legal/` |
| Docker Compose (deployment) | `docker-compose.yml` |

**Does NOT own:**
- Engine source (Rust crates)
- Rust tests
- WAL implementation
- GPU kernels or PTX
- Roadmap / wave tracking / kanban
- `sdk/code-intelligence/src/schema.rs` — source of truth lives in arcflow

---

## What Crosses the Wall

Exactly three artifacts cross from arcflow → arcflow-docs:

**① Pre-built binaries / native addon**
```
arcflow/crates/wc-ffi  →  libarcflow.{so,dylib,dll}
                       →  arcflow.node (napi-rs addon)
                       →  arcflow.wasm
Delivery: GitHub Release artifacts, downloaded by arcflow-docs install scripts
```

**② Schema constants (manually synced, CI-checked)**
```
arcflow/sdk/code-intelligence/src/schema.rs  →  (PR sync)
→  arcflow-docs/typescript/src/code-intelligence.ts
Protocol: any PR that changes schema.rs must include a matching PR in arcflow-docs
CI: arcflow-docs/.github/workflows/ci.yml runs scripts/check-schema-sync.js
```

**③ Rust SDK docs**
```
arcflow/crates/wc-sdk/  →  cargo doc  →  docs.rs/arcflow
Referenced from arcflow-docs/docs/ with a link — never duplicated
```

Nothing else crosses. No TypeScript source in arcflow. No MDX docs in arcflow.

---

## Sync Rules

**Schema constants are the ONLY shared artifact.**

The code intelligence label/edge strings (`"Function"`, `"CALLS"`, etc.) must match:
- `arcflow/sdk/code-intelligence/src/schema.rs` ← **source of truth**
- `arcflow-docs/typescript/src/code-intelligence.ts` ← mirror

Rules:
1. Any PR in arcflow that changes `schema.rs` **must** have a matching PR in arcflow-docs.
2. The arcflow-docs CI check (`scripts/check-schema-sync.js`) validates label/edge names match.
3. No automated sync — human review at PR time, CI as safety net.

**API surface is owned by arcflow-docs.** When the engine adds a new primitive, the
TypeScript wrapper and documentation go to arcflow-docs. Engine Rust tests are
authoritative; TypeScript tests test the TypeScript layer.

**`AGENTS.md` is the canonical public API reference.** It lives in arcflow-docs.
LLMs, coding agents, and Context7 consume it. Engine internals (WAL format, PTX kernels,
standing query implementation) are not documented there — they go in `AGENTS-ENGINE.md`.

---

## What Goes Where — Decision Table

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
| Schema constant change (Rust) | ✓ (`sdk/code-intelligence/src/schema.rs`) | ✓ (sync to TS) |
| Benchmark results | ✓ (`kanban/`, `docs/benchmarks/`) | |
| Migration guide from Neo4j | | ✓ |
| Pricing / licensing | | ✓ |
| Engine architecture docs | ✓ (`docs/architecture/`) | |
| React components | | ✓ (`react/`) |
| Examples for end-users | | ✓ (`examples/`) |
| Engine integration test examples | ✓ (`examples/`) | |

---

## Hard Rules for Coding Agents

These rules are **non-negotiable**. Violating them creates drift that takes hours to untangle.

```
RULE 1 (Engine Boundary):
  If it's Rust and compiles into the binary → arcflow only.
  Never create Rust engine source in arcflow-docs.

RULE 2 (Docs Boundary):
  If it's TypeScript, MDX, or a developer-facing document → arcflow-docs only.
  Never create TypeScript SDK source or MDX docs in arcflow.

RULE 3 (Schema Sync):
  Schema constants are defined in Rust (arcflow/sdk/code-intelligence/src/schema.rs).
  The TypeScript mirror (arcflow-docs/typescript/src/code-intelligence.ts) must match.
  When one changes, both must change in the same release cycle.

RULE 4 (Artifact Crossing):
  The C ABI header, pre-built binaries, and Rust SDK docs (docs.rs) are the only
  artifacts that cross from arcflow to arcflow-docs.
  Everything else is a logical reference, never a copy.

RULE 5 (No Duplication):
  If a file exists in both repos with the same name/purpose, that is a violation.
  The correct action is to delete the copy from the repo that doesn't own it.
  REPO-SPLIT.md itself is the one intentional exception — it lives in both as the governing contract.
```

---

## Governance

This file lives in both repos at their root. Both copies must be identical.
When updating this file, update both repos in the same PR cycle.

Last updated: 2026-04-16 — post-cleanup, arcflow/sdk/ reduced to code-intelligence/ only.
