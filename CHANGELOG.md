# Changelog

User-facing summary of ArcFlow releases. Each entry corresponds to a tag on this repo (`v*`) with binaries on the [Releases page](https://github.com/ozinc/arcflow/releases).

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

For an engine-internal commit-grade changelog (wave numbering, dossier links), see the private `arcflow-core` repo. This file is the curated public-facing version.

---

## [0.8.0] — 2026-05-15

**Minor — World Graph substrate cut.** The eighteen-initiative
worldgraph::io v0.8 batch (I-INIT-0132..0149) closed in arcflow-core
commit `c0a7181f` (Phase-D atomic cut). Additive — no breaking changes
for v0.7.x consumers.

### Mirrored from arcflow-core v0.8.0

- **`arcflow.worldgraph` is the public substrate layer.** The
  doctrinal rename "World Store" → "World Graph" lands here. The
  top-level `arcflow_core::worldgraph::*` module is public; six
  bounded capabilities (`catalog`, `topology`, `nodes`, `wal`, `mmap`,
  `schema`, `workspace`) and the I/O substrate primitive layer (`io`)
  are reachable. Legacy crate-root modules (`mvcc`, `dense_store`,
  `column_store`, `csr`) remain as canonical re-exports — **no
  migration required** for v0.7.x-pinned consumers.
- **Virtual labels.** New DDL: `CREATE NODE LABEL <name> [(col TYPE,
  ...)] VIRTUAL FROM PARTITION '<lake-uri>'`. Rows live in a
  Lakehouse partition; the engine holds the typed schema, the catalog
  pointer, and the adjacency. The planner-side predicate-pushdown
  rewriter for `MATCH (:VirtualLabel ...)` patterns lands as a
  follow-on; until then, queries against Virtual labels return a
  typed `QueryError::VirtualLabelNotYetQueryable`.
- **Python FFI `register_virtual_partition(label, partition)`** —
  drives virtual-label registration without a Cypher round-trip.
  C ABI: `arcflow_register_virtual_partition(session, label,
  partition) -> i64 epoch`.
- **Real bytes on disk** — WAL writer + replay (length-prefixed
  CRC32-IEEE framing, torn-tail tolerance, group-commit fsync),
  streaming-stripe writer (append-only ARC1 hot-tier files,
  capacity-bounded), manifest atomic commit (`write-tmp + fsync +
  atomic_rename`; two-file protocol), Memory Governor admission gate
  (per-residency-class byte accounting against `TierBudget` caps).
- **Platform-divergent storage primitives** — `PlatformOps` trait
  with macOS (`F_FULLFSYNC`) and Linux (`fdatasync` + drive-cache
  flush) implementations; WSL2 detection surfaces degraded-atomicity
  warning at mount.
- **Frozen type vocabulary** — `oz://` brand-level URI scheme (six
  variants: workspace / snapshot / label / edge / catalog /
  partition), 9-state `ResidencyClass` + 6-tier `TierBudget` model,
  ARC1 file magic + version constants, Iceberg-shaped
  `ManifestPayload`, 5-variant `MutationOp`.

### Not yet in v0.8 (carried forward)

- Planner-side predicate-pushdown rewriter for virtual labels — Cypher
  patterns against `(:VirtualLabel ...)` will rewrite to Parquet
  predicate-pushdown when the rewriter ships.
- Heat-score eviction policy — the admission gate is in place; the
  eviction policy that complements it lands in a follow-on.
- ARC1 reader + Parquet decoder bodies — the type vocabulary and
  writer-side primitives are shipped; the corresponding readers are
  queued behind the executor wiring.
- Iceberg v3 strict reader — the v0.8 manifest reader is
  Iceberg-shaped (field names match v3 conventions), not v3-strict.

### Documentation alignment

- Six new pages landed for the AF-DOC-2026-05-15-{001,002} bundle:
  `docs/concepts/execution-models.mdx` (LIVE / TRIGGER / SKILL /
  PROGRAM vocabulary), `docs/concepts/causal-edges.mdx`
  (`:CAUSED_BY` discipline + constraint),
  `docs/concepts/adapter-discipline.mdx` (PAT-0049 humble-object for
  binding authors), `docs/concepts/time-decay.mdx`
  (`decay_with_half_life` Z-set operator),
  `docs/guides/scale-patterns.mdx` (four scale primitives), and
  `docs/architecture/worldgraph.mdx` (engine-architecture preview
  of the v0.8 substrate).
- Seven layer pages added under `docs/concepts/layers/` — one per
  engine layer (Perception Lake, World Graph, Query Engine, Live
  Surface, Event Bus, Behavior Engine, Algorithm Library).
- Cross-references closed so the new pages are reachable from
  their canonical-page siblings (live-queries, event-bus,
  behavior-graph, algorithms, worldcypher, bindings, architecture).
- `docs/reference/versioning.mdx` mirrors the workspace `0.8.0` SoT.
- All cookbook `pyproject.toml` / `meta.toml` pins bumped to
  `oz-arcflow==0.8.0`.
- Illustrative install / version examples across `docs/` and
  `LICENSE-*.md` bumped to `0.8.0`.
- `docs/reference/data/SYNC.json` engine_version → `0.8.0`.
- Conformance dashboard pages re-sync to engine `0.8.0`.

### Release content

GitHub Release v0.8.0 ships from `arcflow-core` tag
[`v0.8.0`](https://github.com/ozinc/arcflow-core/releases/tag/v0.8.0).
`cargo add arcflow-core@0.8` is available once the release workflow
lands green and crates.io publish flows through.

`install.sh` end-to-end resolves to v0.8.0. `arcflow upgrade`
detects and applies the v0.7.x → v0.8.0 upgrade path; legacy module
paths continue to work via the canonical re-export shims.

---

## [0.7.2] — 2026-05-14

**Patch wheel.** Post-v0.7.1 batch. Capability surface unchanged; bug fixes and substrate additions only.

### Mirrored from arcflow-core v0.7.2

- **MRL-AF-021 resolved** — Tier-1 residual from MRL-AF-013. Column-projection leak of `d.position` (Frame Point3d) to traversed-to `(:Player).position` string role in cross-MATCH RETURN clauses. Two compound causes fixed in `typed.rs` partial-scoped Expand mode + `eval_typed.rs` CartesianProduct re-prefixing. Preemptive sister-bug fix in `optional_expand_typed_rows`. 4 MRL regression tests + 1560 runtime tests green. project-merlin's PLAY_KNN_QUERY can now collapse to the natural TRACKED-edge form.
- **Wave K substrate** — aggregate-lowering decision substrate + EXPLAIN wire-up (PS-08).
- **Wave S substrate** — LIVE-view lifecycle state machine (PS-22).
- **Wave H exit criterion** — `live_view_commit_latency` probe lands.

### Release-publication fixes (workflow-only; applied as side-commits at the v0.7.2 tag)

- **Windows daemon matrix** — drop `arcflow-daemon` from Windows build steps (UDS-only crate doesn't compile on Windows). Windows ships `arcflow` + `arcflow-mcp` only. Same fix as v0.7.1's side-commit; arcflow-core main awaiting cherry-pick.
- **Musl `libarcflow.so` packaging** — Rust drops `cdylib` for static-musl targets (no dynamic-library output). Package step now skips libarcflow for `*-musl` platforms; linux-`*-gnu`, darwin, windows still ship the cdylib.

### Documentation alignment

- All cookbook `pyproject.toml` / `meta.toml` pins bumped to `oz-arcflow==0.7.2`.
- Illustrative install / version examples across `docs/` and `LICENSE-*.md` bumped to `0.7.2`.
- `docs/reference/data/SYNC.json` engine_version → `0.7.2`.
- Conformance dashboard pages re-sync to engine `0.7.2`.

### Release content

GitHub Release v0.7.2 ships **58 assets** (up from 30 in v0.7.1):

- `arcflow` CLI for 6 unix + 2 windows (16 assets — tarball + raw)
- `arcflow-daemon` for 6 unix (12 assets)
- `arcflow-mcp` for 6 unix + 2 windows (16 assets)
- `libarcflow.dylib` for 2 darwin + `libarcflow.so` for 2 linux-gnu + `arcflow.dll` for 2 windows (12 assets — tarball/zip + raw)
- `SHA256SUMS` + `release-matrix.json`

`install.sh` end-to-end resolves to v0.7.2 across all 6 unix + 2 windows platforms. `arcflow upgrade` correctly detects and applies the v0.7.1 → v0.7.2 upgrade path.

---

## [0.7.1] — 2026-05-14

**Alpha-state versioning.** Per operator directive, ArcFlow moves from
`1.x` (which suggested production-release semantics) to `0.x` (SemVer
convention for pre-1.0 unstable / alpha software). The previous
`v1.6.88` line is succeeded by `v0.7.1` — every fix and feature
shipped under `1.x` is present in this release. The convention reversal
makes the alpha boundary unambiguous; `v1.0.0` is now reserved for the
first production-ready release. See
[`docs/reference/versioning`](./docs/reference/versioning.mdx) for the
full bump-rule policy and [`VERSIONING.md`](https://github.com/ozinc/arcflow-core/blob/main/VERSIONING.md)
in arcflow-core for the canonical source.

### Why 1.x → 0.x

Most projects ship a `0.x` cycle, hit `1.0`, and declare "production-
ready." ArcFlow's earlier `1.x` line numbers were a labelling
convention that implied production maturity ArcFlow hasn't yet claimed.
The reversal aligns the version line with where the project actually
is: alpha (`0.x`), heading toward `1.0` when the production-readiness
criteria are met. No capability has been removed; the engine surface
is unchanged from the `v1.6.88` line. The bump-rules (patch / minor /
major / `-rc.N`) carry over verbatim and apply to the `0.x` series.

### Mirrored from arcflow-core v0.7.1

The arcflow-core release accompanying this docs cut includes (per the
upstream CHANGELOG):

- **MRL-AF-013** parser symmetrization — comma-MATCH parser fix in
  `match_return.rs`; right-side Expand now mirrors the left-side
  subplan. Closes the 0-rows / 40-50× slowdown shape filed by
  project-merlin.
- **Wave F perf landings (Apple Silicon)** — `simdgroup_matrix<float, 8, 8>`
  matmul on Apple9+, AMX caller wiring through `cblas_sgemm` for vector
  brute-force fallback, adaptive cost router decisive override across
  CUDA + Metal dispatch sites, `simd_prefix_inclusive_sum` (Apple8+),
  ResidencyScope RAII pinning hot PageRank buffers.
- **Wave H release artifacts** — `arcflow-mcp` + `libarcflow.{dylib,so,dll}`
  added to the release matrix.
- **Wave V observability** — SLO-grade LIVE-view metrics (PS-25).

### Documentation alignment

- All cookbook `pyproject.toml` / `meta.toml` pins bumped to
  `oz-arcflow==0.7.1`.
- All illustrative install examples in prose and code blocks use
  `0.7.1`.
- `docs/reference/versioning.mdx` rewritten with the convention-
  revision section and the 0.x bump rules.
- `docs/reference/data/SYNC.json`, `gql-conformance.json`, and the
  rendered conformance MDX pages re-synced to engine version `0.7.1`.
- `scripts/lint-version-literals.py` extended to also catch `0.7.x`
  literals outside SoT-bearing files.

### Deferrals (durable, dossier-tracked in arcflow-core)

- ANE in-engine model inference (out of scope per ANTI-0020; AMX
  covers the in-engine matmul case).
- `MTLIndirectCommandBuffer` GPU-driven multi-iter dispatch
  (overlapping with C06 pinning).
- `grb_mxv_metal` rewrite (needs separate benchmark dossier).

---

## [Pre-0.7.1 — 1.x line]

The entries below describe the pre-convention-reversal `1.x` line.
Capability shipped under those tags is present in `0.7.1`; only the
version-line labelling has changed.

## [Unreleased — pre-revision, superseded by 0.7.1]

Originally tracked as `v1.6.27`; superseded by the alpha-state version
line. The capability listed below shipped in arcflow-core under the
`1.6.x` series and is present in `0.7.1`.

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

- 17 CUDA kernels — PageRank, vector distance, BFS frontier, triangle counting, Louvain
- CUDA graph capture pipeline — record kernel sequences into replayable graphs
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
