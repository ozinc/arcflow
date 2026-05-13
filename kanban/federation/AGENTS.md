---
id: kanban-federation-agents-arcflow-docs
type: agents
title: "kanban/federation/ — Cross-repo agent coordination (arcflow-docs side)"
status: active
created: "2026-05-14"
---

## Purpose

Cross-repo federation mailbox for `arcflow-docs-agent` (short code `DOC`).
Holds messages from / to other federated agents in the OZ ecosystem.

## Federated agents

| Short code | Repo | Role |
|---|---|---|
| `AF`  | `ozinc/arcflow-core`  | Engine source, release pipeline |
| `DOC` | `ozinc/arcflow` (this) | Public docs, cookbook, SDK source, install scripts |
| `OZ`  | `ozinc/oz-platform`   | Website, brand, hosted services |
| `CHK` | `Alendis-SmartHorse`  | Chetak edge2 pipeline consumer |

## Protocol

See `FEDERATION.md` in this directory (mirror of the canonical copy in
arcflow-core). Single-folder flat layout; messages are `.md` files with
frontmatter + rich-context bodies.

## What `DOC` owns

- `cookbooks/` — MIT-licensed example recipes
- `typescript/` — TypeScript SDK source (MIT)
- `mcp/` — MCP server reference (MIT)
- `react/` — React bindings (MIT)
- `install/install.sh` — canonical install script (SoT; deployed copy in
  oz-platform's `public/install/arcflow` is a verbatim mirror)
- `docs/` — public-facing documentation, including
  `docs/protocol/jsonrpc-v1.md`
- `LICENSE`, `LICENSE-FAQ.md`, `ARCFLOW_FOR_AI_AGENTS.md`,
  `CHANGELOG.md`, `ROADMAP.md`, `SECURITY.md`, `CONTRIBUTING.md`

## What `DOC` does NOT touch

- Engine source (`arcflow-core/crates/`)
- Release pipeline workflows (`arcflow-core/.github/workflows/release-*.yml`)
- Vercel deploy config (`oz-platform/apps/cloud/website/`)
- Alendis pipeline source (`Alendis-SmartHorse/apps/edge2/`)

When `DOC` work depends on changes in any of the above, it files a
federation message to the owning agent.

## On-start checklist

```sh
# 1. Confirm pact unchanged (canonical authority lives in arcflow-core)
diff kanban/federation/FEDERATION.md \
     ../arcflow-core/kanban/federation/FEDERATION.md

# 2. Inbox poll
ls kanban/federation/*.md 2>/dev/null
grep -l "to: arcflow-docs-agent" kanban/federation/*.md 2>/dev/null

# 3. Open ones to my agent
for f in $(grep -l "to: arcflow-docs-agent" kanban/federation/*.md 2>/dev/null); do
  grep -l "status: open" "$f"
done

# 4. Cross-repo TODOs addressed to me
grep -rn "TODO(docs-needs):" ../arcflow-core/ ../oz-platform/ 2>/dev/null

# 5. My TODOs that counterparts have now resolved (close them out)
grep -rn "DONE(arcflow-needs):\|DONE(oz-platform-needs):\|DONE(chetak-needs):" . 2>/dev/null
```

## Authoring an outgoing message

Write to your own `kanban/federation/<id>.md`. Then mirror to the
counterpart's `kanban/federation/<id>.md` (in their repo's working tree)
and commit from that side. Both copies live in git history of both repos
— durable audit trail.

Message ID format: `<from>-<to>-YYYY-MM-DD-NNN` (e.g.
`DOC-AF-2026-05-14-001`). Frontmatter + rich-context body per the
FEDERATION.md template.
