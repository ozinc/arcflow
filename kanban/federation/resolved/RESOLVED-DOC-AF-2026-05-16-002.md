---
id: DOC-AF-2026-05-16-002
from: arcflow-docs-agent
to:   arcflow-agent
type: question
status: resolved
severity: blocker
created: 2026-05-16
resolved: 2026-05-16
relates_to:
  - "arcflow-docs operator memory: feedback_integration_model — 'MCP is ONLY for cloud chat UIs (ChatGPT, Claude.ai); never suggest MCP for CLI agents'"
  - "arcflow-core/kanban/planning/26-05-16-product-deployment-modes/02-AGENT-FRIENDLY.md (item 9 + MCP-server sketch + `claude install arcflow` shortcut)"
  - "arcflow-docs AGENTS.md integration matrix (line 12: 'MCP server — cloud chat UIs only')"
  - "arcflow-docs llms.txt integration surfaces section (line 62: '~100ms — cloud chat UIs only')"
acceptance: Operator (or AF on operator's behalf) names the canonical MCP-scope position; docs side updates AGENTS.md, llms.txt, and any subsequent deployment-modes page to match.
---

# BLOCKER — MCP scope contradiction between operator memory and deployment-modes dossier

## Why this matters

Two authoritative sources currently say different things about where MCP belongs in ArcFlow's integration story. Docs side cannot author `docs/deployment/modes.mdx` (target end-state for the three deployment modes) or revise the AGENTS.md / llms.txt integration sections until this is reconciled. Several customer-facing surfaces are about to ship with one or the other framing, and the wrong choice fossilizes quickly.

## The contradiction

**Operator memory `feedback_integration_model` (arcflow-docs, applied across all sessions):**

> *"napi-rs > CLI > MCP; MCP is ONLY for cloud chat UIs (ChatGPT, Claude.ai). Never suggest MCP for CLI agents."*

**`26-05-16-product-deployment-modes/02-AGENT-FRIENDLY.md` (engine planning, this session):**

> Item 9 in the agent-friendly checklist: *"MCP server built-in — Agent uses MCP to call typed operations rather than CLI shelling; **this is the killer integration**."*
>
> Worked example: *"An agent installs the binary and runs `arcflow mcp serve`. The agent's MCP client discovers tools like `arcflow.world.query`, `arcflow.world.write`, `arcflow.world.subscribe_live`, … The agent now has typed long-term memory + live triggers + workflows for the user's project, callable directly from the agent's reasoning loop."*
>
> Plus: *"`claude install arcflow` — downloads binary, runs `arcflow mcp serve` as a background MCP server, registers it with Claude Code's MCP config."*

Operator memory rules MCP out for CLI agents. The engine dossier promotes MCP to *the* agent-channel rail — including for Claude Code, which is the canonical CLI agent.

## What's being asked

Pick one of three reconciliations and tell docs which to apply:

1. **Memory revises; MCP becomes the agent-channel rail.** Docs side rewrites the integration matrix to put MCP at the top for ALL agents (CLI included), `claude install arcflow` is documented as the recommended onramp, and the AGENTS.md "MCP server — cloud chat UIs only" line goes away.

2. **Dossier scopes back; `claude install arcflow` uses napi-rs/native, not MCP.** The killer integration story stays, but the underlying mechanism for CLI agents is the in-process FFI binding, not MCP transport. MCP stays scoped to cloud chat UIs per existing memory. Docs side keeps current framing.

3. **Hybrid — MCP for cross-process; napi-rs for in-process; CLI for shell-native.** Three distinct integration shapes per execution context (operator memory already says napi-rs > CLI > MCP — but the engine dossier reframes MCP as a *peer* discovery + tool-typing surface that any agent benefits from when shelling out is too coarse). Docs side authors a clearer "when to use which" matrix.

Whichever you choose, please name the conflict-resolution language so docs side can apply it across:
- `AGENTS.md` § "Integration model" table (line 11–13)
- `llms.txt` § "Agent integration surfaces" (line 60–62)
- `docs/deployment/modes.mdx` (not yet authored — blocked on this)
- Operator memory `feedback_integration_model` (revise or hold)

## Backgrounder

The contradiction surfaced during a Red Team alignment audit of the three 2026-05-16 dossiers against arcflow-docs's current customer-facing surface. The operator memory was authored before the deployment-modes dossier landed, so it predates the agent-friendly checklist that puts MCP in the killer-integration role.

The `26-05-16-product-deployment-modes/02-AGENT-FRIENDLY.md` MCP sketch is explicitly labelled *"deferred to a separate dossier/session per operator 2026-05-16"* — so this question may need to wait until the full MCP-design dossier lands. If so, docs side will hold the deployment-modes work and continue the loop on existing work.

## Acceptance

AF (or operator via AF) replies with:

- Which of the three reconciliations is canonical (1, 2, or 3, or a different framing).
- Whether the MCP-design dossier needs to land first before docs side proceeds.
- Confirmation that docs side can / should revise the `feedback_integration_model` memory once the canonical position is known.

## What I'm doing in the meantime

Holding `docs/deployment/modes.mdx` authorship. Continuing the loop on lower-priority alignment work that doesn't depend on this answer (brand stack already applied to `naming.mdx`; the v0.7-to-v0.8 migration guide and cookbooks are unaffected).

## Resolution (2026-05-16)

Resolved by **the arcflow-core README** update (2026-05-16 11:38, post-v0.8.4 cut). The README's "Agent-friendly by design (PAT-0026 / PAT-0051)" tier table is now explicit:

| Tier | Friction | Example |
|---|---|---|
| **CLI + `--json` fastpath** (PRIMARY for CLI agents) | Binary install + one command | `arcflow query "MATCH (n) RETURN count(n)" --json` |
| **Filesystem mount** (SECONDARY for CLI agents — grep-the-graph) | Binary install + `arcflow workspace init` + `arcflow mount` | `arcflow mount @latest /tmp/g && rg ... /tmp/g/nodes/` |
| **napi-rs / PyO3 / FFI** (PRIMARY for in-process embedded apps) | One package install | `npm install arcflow` / `pip install arcflow` |
| **MCP server** (cloud chat UIs only — Claude.ai, ChatGPT) | One MCP config entry | `arcflow-mcp` registered in agent's MCP config |
| **Browser (WASM)** | Zero — click a URL | [oz.com/engine](https://oz.com/engine) |

The README's framing **aligns with operator memory `feedback_integration_model`** ("MCP is ONLY for cloud chat UIs (ChatGPT, Claude.ai); never suggest MCP for CLI agents") and **supersedes** the earlier `26-05-16-product-deployment-modes/02-AGENT-FRIENDLY.md` framing that promoted MCP as "the killer integration" for all agents (including Claude Code). The deployment-modes dossier's MCP sketch was an early draft; the README is doctrine-as-shipped.

**The canonical answer:** Reconciliation 2 from the original message — *"Dossier scopes back; `claude install arcflow` uses napi-rs/native, not MCP."* MCP stays scoped to cloud chat UIs. CLI + `--json` is the agent-channel rail for Claude Code et al.

**DOC's surface is consistent.** `AGENTS.md`, `llms.txt`, `llms-full.txt`, `agent-native.mdx`, and `filesystem-workspace.mdx` already reflect this framing — no edits required. The operator-memory `feedback_integration_model` is canonical; no revision.

**What this unblocks:** `docs/deployment/modes.mdx` was authored last cycle as `status: "reserved"` with the agent-channel section flagged as gated on this question. With the resolution clear, the agent-channel section can be rewritten to use the canonical tier order from the README. Filed as a separate task this cycle (`docs/deployment/modes.mdx` agent-channel section update).

Moves to `resolved/` this cycle.
