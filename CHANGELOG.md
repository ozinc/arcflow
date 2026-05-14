# Changelog

User-facing summary of ArcFlow releases. Each entry corresponds to a tag on this repo (`v*`) with binaries on the [Releases page](https://github.com/ozinc/arcflow/releases).

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

For an engine-internal commit-grade changelog (wave numbering, dossier links), see the private `arcflow-core` repo. This file is the curated public-facing version.

---

## [Unreleased]

Will be cut as `v1.6.27` once the GitHub Releases pipeline is fully wired (per `release-binaries.yml` in arcflow-core; cross-repo PAT minting in progress).

### Added

- **19 new JSON-RPC daemon methods** for cross-process consumers. The daemon's wire surface grows from 30 to 49 unique methods. New families:
  - `snapshot.now` — coherent per-topic watermark snapshot for fusion reads
  - `pattern.*` (6 methods) — NATS-style wildcard topic subscriptions (`subscribe`, `register_consumer`, `drop_consumer`, `topics_matching`, `list_subscriptions`, `list_consumers`). WAL-journaled; future topics auto-bind.
  - Request-reply (6 methods) — `request`, `reply`, `poll_reply`, `cancel_request`, `sweep_expired_requests`, `pending_requests`. Engine-allocated `_correlation_id` + per-request reply topic.
  - `stream_fn.*` (5 methods) — Lag(n), Lead(n), Delta scalar streaming derivatives. Computational state (not WAL-journaled); re-feed from source topic after restart.
  - `cypher.execute` — generic Cypher execution over the wire. Unlocks every `CALL algo.*` procedure. Architectural pivot: daemon goes from "pub/sub broker + structured topic ops" to "in-process graph query engine over UDS."
- **Sharded SWMR substrate** for multi-writer deployments. Per-shard WAL with manifest atomic update, lease registry, fencing (INV-15 STALE_LEASE_TOKEN), causal closure, vshard routing, merged-view reader, delta merger. FF-27 5-producer E2E green. PyO3-style ctypes binding for Python consumers (`bindings/python/arcflow.py` with `ArcflowSharded` + `ShardHandle` classes; fork-after-open detection via OpenPid).
- **`algo.fusion.weighted_centroid` CALL procedure** — weighted centroid + variance + total weight from labeled nodes with position + confidence properties. Direct in-engine alternative to TS-side DLT triangulation.
- **Public binaries on GitHub Releases** — release authority moved from R2 to `github.com/ozinc/arcflow/releases`. Every release ships `SHA256SUMS` + sigstore provenance attestation. Verify with `gh attestation verify <asset> --owner ozinc`.
- **`LICENSE-CORE.md` — formal Proprietary Free Runtime License v1.0 (DRAFT)** for the ArcFlow Core binary runtime. Encodes the 8 strategic clauses: commercial use allowed within Free Use Limits, no license contamination, user ownership of data / graphs / queries / outputs, MIT-cookbook explicit, paid tier boundary (managed cloud, distributed prod, premium algorithms, enterprise governance, SLA, custom licensing), 180-day notice for material changes (anti-Unity-runtime-fee), redistribution rights, AI-coding-assistant permission. Plus standard sections: definitions, warranty disclaimer, liability cap, termination, severability, governing law. Pending OZ counsel review; in good-faith effect pending finalization.
- **`LICENSE` scope clarified** — explicit two-layer header: MIT for this repo's contents (cookbook, SDK source, install scripts, docs), Proprietary Free Runtime License for the engine binary (see `LICENSE-CORE.md`). The two licenses do not contaminate each other.
- **README "License at a glance" table** — Allowed / Paid / Not allowed scan-table near the top so first-time visitors (and LLMs) classify the licensing model without scrolling.

### Changed

- `engine.version` in `RELEASE-MATRIX.toml` is now enforced equal to the latest reachable git tag via a CI fitness gate (`scripts/check-engine-version-vs-tag.sh`). Prevents the manifest-vs-reality drift incident of 2026-05-13.
- Install script (`install.sh`) now fetches from `github.com/ozinc/arcflow/releases/latest/download/...` instead of R2.

### Removed

- Cloudflare R2 as the binary distribution surface (binaries only — R2 still hosts the install script via Vercel rewrite from oz-platform). One less surface to credential, audit, and pay for.
- `NOTE(chetak-limitation)` annotation on the SWMR data_dir-scope writer rule — flipped to `DONE(chetak D-EDGE-14.A)` now that both substrate gates (runtime per-shard routing + Python FFI) are cleared.

---

## [1.6.5] — 2026-03-28

### Added

- Initial public GitHub Release on this repo. Linux x86_64 tarball attached. Prior internal releases tracked in `arcflow-core` (private) only.

---

## Earlier internal releases (curated)

These were tracked privately in `arcflow-core/CHANGELOG.md` (commit-level wave numbering) but did not produce public release artifacts. Summarized here for context:

### GPU acceleration milestone (2026-03)

- 17 CUDA kernels — PageRank (2.4x), vector distance (4.2x), BFS frontier (3.5x), triangle counting (19.8x), Louvain (29.6x)
- CUDA graph capture pipeline — record kernel sequences into replayable graphs (+1.2x)
- Auto-routes CPU vs GPU based on workload + backend availability
- 630 engine tests across the GPU pipeline

### MCP integration (2026-02)

- MCP server reference implementation (`crates/arcflow-mcp/` in engine source; `mcp/` in this repo) — exposes ArcFlow's query surface as MCP tools for LLM tool calling

### Bitemporal + standing queries (2026-01)

- Bitemporal AS OF queries — system-time + valid-time axes; immutable history
- Standing queries — incremental view maintenance over Cypher queries; subscribe to result deltas

### Vector index (2025-12)

- HNSW vector similarity, integrated with graph nodes
- Quantization tiers (full precision, scalar-quantized, product-quantized)
- Hybrid graph-vector queries

### Spatial index (2025-11)

- H3 cell encoding for geospatial sharding
- R-tree for bounding-box queries
- Spatial join procedures

---

## Release cadence

- **Patch versions** (v1.6.x → v1.6.x+1) — engine fixes, minor capability additions. Roughly weekly during alpha.
- **Minor versions** (v1.6 → v1.7) — significant capability surface changes. Roughly monthly.
- **Major versions** (v1 → v2) — backward-incompatible wire-protocol changes. Rare; tied to JSON-RPC protocol spec major-version bumps (see `docs/protocol/jsonrpc-v1.md`).

Released versions stay supported under their original license terms (per [LICENSE-FAQ.md](./LICENSE-FAQ.md) §"What happens if ArcFlow's licensing terms change").

## How to track new releases

- **Watch this repo** — GitHub will notify on new releases
- **Atom feed**: https://github.com/ozinc/arcflow/releases.atom
- **JSON API**: https://api.github.com/repos/ozinc/arcflow/releases/latest
- **Machine-readable manifest**: every release attaches `release-matrix.json` as an asset; consume from `https://github.com/ozinc/arcflow/releases/latest/download/release-matrix.json`
