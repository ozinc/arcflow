# CLAUDE.md — arcflow-docs

ArcFlow is an embedded graph database. Runs in browser (WASM), Node.js, Python, Rust, Docker.
No server needed.

See [AGENTS.md](AGENTS.md) for the full public API and WorldCypher reference.
See [REPO-SPLIT.md](REPO-SPLIT.md) for the governing boundary contract between this repo and the engine.

---

## Repository Boundary

This repo (`arcflow-docs/`) owns the **developer surface**: SDK, docs, examples, and the
machine-readable API context for coding agents. Full governance: **`REPO-SPLIT.md`**.

| Belongs here | Belongs in arcflow (engine repo) |
|---|---|
| TypeScript SDK (`typescript/src/`) | Rust engine source (`crates/`) |
| Schema constants mirror (`typescript/src/code-intelligence.ts`) | Schema constants source of truth (`sdk/code-intelligence/src/schema.rs`) |
| MCP npm package (`mcp/`) | MCP binary (`crates/wc-mcp/`) |
| React hooks (`react/`) | GPU kernels, WAL, MVCC |
| MDX documentation (`docs/`) | Roadmap + waves (`kanban/`) |
| Public `AGENTS.md` | Engine-internal agent guide (`AGENTS-ENGINE.md`) |
| `llms.txt`, `llms-full.txt` | Engine benchmarks |
| Examples (`examples/`) | C ABI (`crates/wc-ffi/`) |

### Hard rules for coding agents

**RULE 1 — Docs/SDK Boundary:**
TypeScript, MDX, developer-facing documents → this repo only.
Never create TypeScript SDK source or MDX docs in the engine repo.

**RULE 2 — No Engine Source Here:**
Never write Rust source, edit crates, or touch WAL/GPU code in this repo.
All engine changes go in `arcflow/`.

**RULE 3 — Schema Sync (critical):**
`typescript/src/code-intelligence.ts` mirrors `arcflow/sdk/code-intelligence/src/schema.rs`.
The Rust file is the **source of truth**. The TypeScript file is the **mirror**.
Any PR that touches `code-intelligence.ts` here **must** coordinate with a corresponding
change to `schema.rs` in the engine repo (or vice versa).
CI (`scripts/check-schema-sync.js`) validates label and edge names match. Do not bypass it.

**RULE 4 — Binary comes from arcflow releases:**
The native addon (`arcflow.node`), WASM binary, and shared library come from
GitHub Release artifacts produced by the engine repo. Never build them here.
The `install/` scripts download the correct release artifact.

**RULE 5 — AGENTS.md is the canonical public API reference:**
`AGENTS.md` in this repo is what LLMs, coding agents, and Context7 consume.
Keep it up to date with every engine release. Engine internals (WAL format, PTX kernels,
Z-set implementation) do not belong in this file — they belong in `arcflow/AGENTS-ENGINE.md`.

---

## Agent Onboarding Checklist

Every new coding agent session on this repo should run through this first:

```
[ ] Read CLAUDE.md (this file) — boundary rules and conventions
[ ] Read AGENTS.md — the public API surface this repo documents
[ ] Read REPO-SPLIT.md — full boundary contract with the engine repo
[ ] Run: grep -r "FIXME:" . --include="*.ts" --include="*.mdx" | head -20
[ ] Run: grep -r "NOTE(invariant):" . --include="*.ts" --include="*.mdx"
[ ] Run: grep -r "TODO(wave-A):" . — features gated on unshipped engine SDK waves
```

**Before editing `AGENTS.md` or `llms.txt`:** confirm the engine feature is actually shipped
(not just planned). Documenting unshipped features as live breaks developer trust.

**Before editing `typescript/src/code-intelligence.ts`:** check whether `schema.rs` in the
engine repo needs a matching change, and open the PR there first.

---

## Comment Tag Conventions

Structured tags used across this repo and the engine repo. Treat them as first-class context —
scan for them before editing any file, address them before closing a PR.

| Tag | Meaning |
|-----|---------|
| `TODO(wave-N):` | Planned for a specific numbered wave or iteration |
| `TODO(wave-A):` | Blocked on engine SDK surface wave — do not write docs until engine ships |
| `TODO(tech-debt):` | Known issue to fix; tracked but not urgent |
| `TODO(refactor):` | Structural cleanup, no behavior change |
| `NOTE(invariant):` | Critical constraint that must never be violated |
| `FIXME:` | Actively broken — higher urgency than TODO |
| `HACK:` | Temporary workaround — document why and when to remove |

**Preferred multi-line format:**
```ts
// TODO(tech-debt): [one-line description]
//   Reason: [why it exists]
//   Impact: [what breaks or degrades if ignored]
//   Next: [concrete next step]
//
// NOTE(invariant): [critical assumption]
//   Consequence: [what breaks if violated]
//   Evidence: [spec / test / design note]
```

### Tag Rules

- **Never delete or ignore a `NOTE(invariant):`** without addressing the underlying constraint
  and updating the comment to `DONE(invariant): [date] — [why the constraint no longer applies]`.
- **When you resolve a TODO**, update to `DONE(wave-N): [date] — [how resolved]` rather than
  deleting silently. Historical context matters.
- **Before editing any planning doc**, `grep -r "NOTE(invariant):" planning/` and confirm your
  change doesn't break any stated constraint.
- **`TODO(wave-A):` is a gate.** Do not write user-facing documentation for a feature tagged
  `TODO(wave-A):` until the engine repo confirms that SDK wave has shipped.

---

## What Goes Where — Decision Table

| Concern | This repo | Engine repo |
|---------|:---------:|:-----------:|
| User-facing guides, tutorials, reference | ✓ | |
| Public API reference for LLMs/agents (`AGENTS.md`) | ✓ | |
| Machine-readable agent context (`llms.txt`) | ✓ | |
| TypeScript SDK implementation | ✓ | |
| Schema constants (TypeScript mirror) | ✓ | |
| MCP npm package | ✓ | |
| React components | ✓ | |
| Examples for developers | ✓ | |
| Documentation planning | ✓ `planning/` | |
| SDK implementation planning | | ✓ `planning/` |
| Engine primitive implementation | | ✓ |
| Schema constants (source of truth) | | ✓ `sdk/code-intelligence/src/schema.rs` |
| Benchmark results | | ✓ `kanban/`, `docs/benchmarks/` |
| Wave / roadmap tracking | | ✓ `kanban/` |

---

## TypeScript Conventions

- **Typed results everywhere** — use `QueryResult<T>` generics, not `any`
- **Structured errors** — use `ArcflowError` from `errors.ts`, not raw string throws
- **GIL / event loop** — async wrappers must not block the event loop; use `AsyncWorker` pattern
- **No JSON on hot path** — use Arrow C Data Interface or napi-rs typed buffers for result transfer
- **Schema constants** — always import from `code-intelligence.ts`, never hardcode label/edge strings

## Documentation Conventions

- **MDX over Markdown** — all user-facing docs use `.mdx` (MDX format for component embedding)
- **Agents first** — primary audience is coding agents (Cursor, Claude Code, Codex, Copilot);
  human readability is secondary. Structure for skimmability and grep-ability.
- **No docs for unshipped features** — only document what's in the current stable release
- **WorldCypher examples** — always include runnable query examples; prefer copy-pasteable snippets
- **Cross-references** — link to `docs.rs/arcflow` for Rust SDK API, never duplicate Rust API docs here
