# FEDERATION.md — Cross-repo agent coordination protocol

**Canonical copy** lives in this repo (`ozinc/arcflow-core/kanban/federation/FEDERATION.md`).
Identical mirrors exist in every federated repo. When the protocol changes,
update the canonical first; each agent mirrors to its own repo as part of
the change PR. CI fitness check (TBD) diffs the 4 copies.

---

## Federated repos + agents

| Short code | Agent | Repo | Owns |
|---|---|---|---|
| `AF` | arcflow-agent | `ozinc/arcflow-core` (private) | Engine source, release pipeline, JSON-RPC protocol contract, federation pact authority |
| `DOC` | arcflow-docs-agent | `ozinc/arcflow` (public) | Cookbook (MIT), SDK source, install scripts (SoT), MCP server, LICENSE-FAQ, ARCFLOW_FOR_AI_AGENTS, docs/protocol/jsonrpc-v1.md |
| `OZ` | oz-platform-agent | `ozinc/oz-platform` (private monorepo) | Website, engine page, install Vercel rewrite, brand/strategy/positioning, pricing page, hosted services |
| `CHK` | chetak-agent | `Alendis-SmartHorse` (private) | Alendis edge2 pipeline consumer, sharded SWMR consumer migration |

## The protocol — one folder per repo, flat .md files

Each repo carries a single `kanban/federation/` directory. Every cross-repo
message is one `.md` file inside it. **No per-counterpart subdirs, no
per-topic subdirs**. Routing lives in frontmatter; substance lives in the body.

oz-platform's existing per-topic subdirs (`kanban/federation/<topic>/`) are
compatible — they're a richer container for multi-message clusters. The
wire shape (frontmatter + body) is identical.

```
kanban/federation/
  FEDERATION.md            # this file — canonical, mirrored across all 4 repos
  AGENTS.md                # per-repo index of what's expected here
  <message-id>.md          # cross-repo messages, flat layout
  resolved/                # optional — archive subdirectory for tidy listing
  <topic>/                 # optional — for multi-message clusters
    <topic>.md
    AGENTS.md
```

## Message ID naming

```
<from>-<to>-YYYY-MM-DD-NNN

  AF-DOC-2026-05-14-001    arcflow → arcflow-docs
  DOC-AF-2026-05-14-001    arcflow-docs → arcflow
  AF-OZ-2026-05-14-001     arcflow → oz-platform
  OZ-AF-2026-05-14-001     oz-platform → arcflow
  DOC-OZ-2026-05-14-001    arcflow-docs → oz-platform
  OZ-DOC-2026-05-14-001    oz-platform → arcflow-docs
  CHK-AF-2026-05-13-007    chetak → arcflow (existing — unchanged)
  AF-CHK-2026-05-13-002    arcflow → chetak (existing — unchanged)
```

Pre-existing CHK-AF / AF-CHK naming is preserved for the chetak pact.

## Message frontmatter (required)

```yaml
---
id: AF-DOC-2026-05-14-001
from: arcflow-agent
to:   arcflow-docs-agent
type: capability-request | coord | answer | bug | question | status-ping
status: open | acknowledged | in-progress | resolved | wontfix
severity: low | medium | high | blocker
created: 2026-05-14
relates_to:
  - "commit SHA, file path, prior message ID, or external link"
acceptance: <one-line definition of what makes this resolved>
---
```

## Message body (required — this is where the value lives)

The body must include enough context for the receiving agent to act
without needing to ask follow-up questions. Per the principle:

> Substance in bodies, not folders. Folders become legacy debt;
> backgrounders stay informative across any restructure.

Recommended sections (skip what's not applicable):

```markdown
# <Short, action-oriented title>

## Why this matters

Why now, what's blocked or unblocked, who feels the impact.

## What's being asked

The actionable request — concrete, scoped. Code paths if relevant.

## Backgrounder (traces, prior context, links)

- Commit SHAs that motivated this
- File paths the receiving agent should read first
- Prior federation messages this builds on
- Any decisions already made + the reasoning

## Acceptance

What "done" looks like. Specific. Verifiable.

## What I'm doing in the meantime (optional)

Bridge work, fallbacks, parallel paths.

## Timeline (optional)

Date-stamped events as the thread evolves.
```

When closing, append a `## Resolution` section noting the commit SHA(s)
or operator action(s) that closed it. Then flip frontmatter `status: open
→ resolved`. Optionally `git mv` to `resolved/`.

## The wire protocol

1. **Authoring** — agent writes the message in its OWN repo's
   `kanban/federation/<id>.md`. Commits it.
2. **Mirroring** — same agent copies the message to the recipient's
   `kanban/federation/<id>.md` (in the recipient's working tree). Commits
   from the recipient's repo. Both copies live in git history of both
   repos — durable, audit-traceable.
3. **Receiving** — at session start, agent runs:
   ```sh
   ls kanban/federation/*.md 2>/dev/null
   grep -l "to: <my-agent-name>" kanban/federation/*.md 2>/dev/null
   grep -l "status: open" kanban/federation/*.md 2>/dev/null
   ```
   Triages, acknowledges (flips frontmatter `status: open → acknowledged`),
   works.
4. **Updating status** — agent flips frontmatter in their copy. If the
   recipient updates their copy, the sender's stays open until they
   manually mirror the update. The git history of both copies is the
   audit trail.
5. **Resolving** — agent appends `## Resolution`, flips
   `status: open → resolved`, optionally moves to `resolved/`. Counterpart
   sees the closure on next poll and can mirror the resolution to their
   own copy.

## What this is NOT

- **Not synchronous.** Agents poll. Messages can sit for hours or days
  before pickup. Build in slack.
- **Not for engine-internal refactors.** Those stay in
  `kanban/waves/` or equivalent per-repo project tracking.
- **Not authoritative for code.** Code lives in commits + PRs. A message
  about a bug is the trigger + close-out signal, not a substitute for
  the bug-fix commit.
- **Not silent.** Every message has frontmatter making the from/to/status
  greppable. No "implicit messages" via TODO comments without a paired
  federation note. (See cross-repo annotation tags below.)

## Cross-repo annotation tags

In-code markers for "I owe this to a counterpart" or "the counterpart
owes this to me." Always paired with a federation message ID so the
in-code marker and the bus file stay linked.

| Tag | Lives in | Scanned by |
|---|---|---|
| `TODO(arcflow-needs):` | DOC / OZ / CHK source | AF scans |
| `TODO(docs-needs):` | AF / OZ source | DOC scans |
| `TODO(oz-platform-needs):` | AF / DOC source | OZ scans |
| `TODO(chetak-needs):` | AF source | CHK scans (existing) |
| `TODO(arcflow-bug):` | DOC / OZ / CHK source | AF scans (existing — chetak shape) |

Example:

```rust
// TODO(docs-needs): publish JSON-RPC spec for cypher.execute method
//   Federation: AF-DOC-2026-05-14-001
//   Reason: shipped 2026-05-13 (commit 21e0eada); SDK consumers need the spec
//   Success: docs/protocol/jsonrpc-v1.md §Cypher includes the new arm
```

When the counterpart resolves the message, the original agent rewrites
the tag to `DONE(docs-needs): YYYY-MM-DD — <resolution>` per the
existing CLAUDE.md annotation convention, or removes it if the
surrounding code is now self-evident.

## Read-on-start checklist (every agent, every session)

```sh
# Confirm protocol unchanged (compare against canonical)
diff kanban/federation/FEDERATION.md ../arcflow-core/kanban/federation/FEDERATION.md

# Any messages for me?
ls kanban/federation/*.md 2>/dev/null

# Specifically: any open ones to my agent name?
grep -l "to: <my-agent-name>" kanban/federation/*.md 2>/dev/null \
    | xargs -I{} grep -l "status: open" {} 2>/dev/null

# Any cross-repo TODOs I scan for? (per the annotation tags table above)
grep -rn "TODO(<my-agent-short-name>-needs):" ../<counterpart-repo>/

# Any of mine that the counterpart resolved? (close my outstanding TODOs)
grep -rn "DONE(<counterpart-short-name>-needs):" .
```

## Trade-off (kept honest)

This protocol assumes all federated repos sit on one machine OR are
cross-clone-accessible. Once any of these moves apart, swap the
filesystem channel for a shared git repo (or any markdown-friendly
surface) — the message schema doesn't change. The wire shape
(frontmatter + body) is portable.

## Pointers

- `REPO-SPLIT.md` — engine vs docs split (arcflow-core ↔ arcflow-docs)
- `CLAUDE.md` — annotation tag conventions; federation tags extend this
- Each repo's `kanban/federation/AGENTS.md` — per-repo index

## Timeline

- **2026-04** — Original 2-way pact (arcflow-core ↔ chetak) authored.
  inbox/outbox/resolved subdir layout, CHK-AF/AF-CHK ID naming.
- **2026-05-13** — Federation surface expands to 3+ agents during the
  GitHub Releases pivot + strategic content push. 5-whys analysis
  picks flat single-folder layout over per-counterpart mailboxes or
  per-topic subdirs. Existing chetak pact's structural artifacts
  (kanban/federation/{inbox,outbox,resolved}/) preserved for backward
  compat; new work uses flat layout.
- **2026-05-14** — This unified protocol published; canonical copy
  here, mirrors in arcflow-docs + oz-platform + (Alendis-SmartHorse
  if/when chetak-agent picks it up). oz-platform's existing per-topic
  subdirs continue to work — the wire shape (frontmatter + body) is
  the contract, not the directory layout.
