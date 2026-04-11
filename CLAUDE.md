ArcFlow is an embedded graph database. Runs in browser (WASM), Node.js, Python, Rust, Docker. No server needed. Try it: https://oz.com/engine

See [AGENTS.md](AGENTS.md) for full API and WorldCypher reference.

## Comment Tag Conventions

Structured tags used across this repo and the engine repo. Treat them as
first-class context — scan for them before editing any file, address them
before closing a task.

| Tag | Meaning |
|-----|---------|
| `TODO(wave-A):` | Blocked on SDK surface wave shipping. Do not write until napi-rs bindings exist. |
| `TODO(wave-N):` | Planned for a specific numbered wave/iteration. |
| `NOTE(invariant):` | Critical constraint that must never be violated. Never remove without explicit discussion. |
| `TODO(tech-debt):` | Known issue to fix; not urgent but tracked. |
| `FIXME:` | Actively broken — higher urgency than TODO. |

### Rules

- **Never delete or ignore a `NOTE(invariant):` comment** without addressing the underlying constraint and updating the comment to explain why it changed.
- **When you resolve a TODO**, update the comment to `DONE(wave-N): [date] — [how resolved]` rather than deleting it silently.
- **Before editing any planning doc**, grep for `NOTE(invariant):` in that file and confirm your change doesn't break the constraint.
- **Do not write docs** for features tagged `TODO(wave-A):` in `planning/sdk-surface-docs.md` until the corresponding SDK-0N item in the engine repo is confirmed shipped.

### What belongs in arcflow-docs vs the engine repo

| Concern | Repo |
|---------|------|
| User-facing docs (guides, references, tutorials) | arcflow-docs |
| Machine-readable context for coding agents (AGENTS.md, llms.txt) | arcflow-docs |
| Documentation planning (what to write and when) | arcflow-docs/planning/ |
| SDK implementation planning | arcflow/planning/ |
| DSL Framework (LegalQuery / FinanceQuery) | BASAL Pro codebase — not here |
| Domain SDL (runtime type registration) | BASAL Pro codebase — not here |
