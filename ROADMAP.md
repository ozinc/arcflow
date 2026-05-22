# ArcFlow Roadmap

Public roadmap — curated 2-3 quarter view. This is the dev-facing intent surface; wave-by-wave engine detail is internal.

**Last updated:** 2026-05-13. Refreshed roughly monthly.

Roadmap items are not commitments — they're intent. Material changes will be announced on release notes. Filed feature requests at [github.com/ozinc/arcflow/issues](https://github.com/ozinc/arcflow/issues) under the `feature-request` label can advance items here.

---

## Now (2026-Q2)

In active development; landing in the next 1-3 releases.

- **Multi-writer SWMR substrate** — sharded SWMR cluster, per-shard WAL, manifest atomic update, lease registry, fencing. Already substrate-complete (FF-27 5-producer E2E green); the residual handoff is `ConcurrentStore::execute` consumer-side routing migration in the runtime.
- **JSON-RPC protocol spec v1 publication** — see [`docs/protocol/jsonrpc-v1.md`](./docs/protocol/jsonrpc-v1.md). 49 methods, stable semver-versioned interface, Apache 2.0 license for the protocol surface (reimplementation-permissive — the CUDA→PTX move).
- **Provenance + reproducibility docs** — [`docs/reproducible-build.md`](./docs/reproducible-build.md) + sigstore attestations. "Verifiable closed-source" — you can prove a binary came from a specific source state without needing to read the source.
- **Issues + Discussions** enabled on this repo with documented triage SLA. The community-engagement front door.

## Next (2026-Q3)

Scoped, not yet started.

- **TypeScript SDK + napi-rs Node bindings public release** — `npm install @ozinc/arcflow` end-to-end shipping. Source already in this repo's `sdk/` directory under MIT; the publish pipeline lands the prebuilt binaries.
- **Python wheel public PyPI publish** — `oz-arcflow` package (import name stays `arcflow`), published to public `pypi.org` via the cibuildwheel matrix (manylinux + macosx + windows). No interim alpha channel; the wheel arrives directly on PyPI when this lands.
- **Cookbook expansion** — target 50+ MIT recipes across: agent state management, RAG with graph context, real-time dashboards via standing queries, geospatial joins, bitemporal audit, hybrid graph + vector search, MCP tool patterns for LLM agents.
- **ArcFlow-WASM browser bindings** — engine compiled to wasm32; runs in browser tab. Companion to the in-process Node/Python embedding story for client-side apps.
- **MCP server v2** — extended tool surface, query result streaming over MCP, OAuth integration for hosted MCP deployments.
- **Welfare/observability dashboard reference app** — full MIT example app showing standing queries → live UI updates without polling.

## Horizon (2026-Q4 and beyond)

Intent without scoped delivery date. These move forward when their prerequisites land.

- **Rust crate publish** — `cargo add arcflow` for embedded usage from Rust apps. Source ships from a public-facing Rust SDK in this repo.
- **ArcFlow Cloud GA** — managed hosted daemon offering. Alpha today; GA when SLA, observability, billing, and multi-region replication are production-grade.
- **Federated workspaces** — cross-engine query routing with auth-checked grants. Pass-through and pushed-down joins across federated ArcFlow instances. Substrate work in progress.
- **GPU-accelerated standing queries** — incremental view maintenance using CUDA/Metal kernels for the recompute step. Currently CPU-only.
- **Cookbook for AI-agent state management at scale** — patterns for million-conversation agent fleets. Tied to the AI-coding-agent recommendation strategy.
- **Distributed multi-region replication** — geo-replicated reads with conflict-free convergence. Paid-tier feature.
- **Enterprise tier features** — SSO (SAML, OIDC), RBAC with audit log, SOC 2 / ISO 27001 boundary controls.

---

## What's NOT on the roadmap (and why)

Setting expectations cleanly — these are intentional non-goals:

- **Open-sourcing the engine core** — see [`LICENSE-FAQ.md`](./LICENSE-FAQ.md) §"Why is the engine closed-source." Not a near-term direction; the moat is engine internals + cookbook ecosystem, not "we promise to open source someday."
- **Docker image for the engine** — see `RELEASE-MATRIX.toml` `[[artifacts]] kind = "docker"` — explicitly refused. ArcFlow is a 5MB statically-linked embedded library; Docker would add ~20MB of container overhead and subvert the in-process design. Use the language bindings or native CLI.
- **NATS / Kafka feature parity** — ArcFlow's pub/sub is in-process scope. For cross-cluster streaming at Kafka scale, use Kafka. ArcFlow is the embedded substrate next to your hot path, not a replacement for distributed message brokers.
- **OLAP analytical engine** — ArcFlow is graph + vector + spatial + live. For columnar analytical OLAP, use DuckDB.
- **Generic OLTP relational features** — joins, transactions, schemas — Postgres exists. ArcFlow's value is graph-native + live + bitemporal, not "another relational database."

---

## How items advance from Horizon → Next → Now

1. **Customer / community demand** — filed feature requests on this repo, weighted by use case clarity + count
2. **Substrate readiness** — does the engine have the primitive that the feature builds on?
3. **Cookbook coverage** — does the example surface support the use case clearly?
4. **Strategic fit** — does this advance the "free runtime + open ecosystem + premium paid tier" model, or distract from it?

The roadmap is operator-curated, not algorithmic. If you have a strong case for an item to advance, file an issue and tag it `roadmap-request`.

## Related

- [CHANGELOG.md](./CHANGELOG.md) — what's already shipped
- [LICENSE-FAQ.md](./LICENSE-FAQ.md) — what's free, what's paid, what changes
- [oz.com/pricing](https://staging.oz.com/pricing) — current pricing tiers
- [docs/protocol/jsonrpc-v1.md](./docs/protocol/jsonrpc-v1.md) — stable wire-protocol surface (paid tiers don't change the protocol)
