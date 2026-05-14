# Reproducible Builds

ArcFlow Core is proprietary free-to-use software (see [LICENSE-FAQ.md](../LICENSE-FAQ.md)). The engine source code is not open. But the build itself is **reproducible** — anyone can verify that a released binary corresponds to a specific source SHA in `arcflow-core` without trusting OZ infrastructure.

This document is the canonical recipe.

Three layers of verifiability:

1. **SHA256SUMS** — every release ships an aggregate `SHA256SUMS` file. Verify with `sha256sum -c --ignore-missing` against your downloaded binary.
2. **Sigstore attestation** — every release binary has a sigstore provenance attestation. Verify with `gh attestation verify <asset> --owner ozinc`. This proves the binary was built by `ozinc/arcflow-core`'s GitHub Actions workflow at a specific source SHA — no trust in OZ infrastructure required, the proof lives in sigstore's public transparency log.
3. **Reproducible build from source** — for the most paranoid case, rebuild from the same source SHA on your own machine. If the resulting binary's sha256 matches what we ship, the chain is complete.

The first two layers are zero-cost (curl + verify). The third layer is documented here.

---

## Why this matters

The CUDA pattern: closed implementation, open developer surface. Reproducible builds + signed releases are the "verifiable closed-source" property — you can prove the binary you run is the binary OZ built from a specific source SHA, even though you cannot read that source.

This puts ArcFlow in a different trust category than "trust us, it's safe":

- **Tampering on a mirror:** detected by SHA256SUMS mismatch
- **Compromise of OZ's GitHub releases:** detected by sigstore attestation (the attestation lives in sigstore's transparency log, not on OZ infrastructure)
- **Build pipeline backdoor:** detected by reproducible build (rebuild from source, sha256 won't match what OZ shipped if their pipeline injected anything)

These are real attacker scenarios that affect every closed-source vendor. Most don't address them. We do, because — per [`LICENSE-FAQ.md`](../LICENSE-FAQ.md) — the lock-in escape valve has to be visible for the model to feel trustworthy.

---

## Prerequisites

Reproducing a build requires:

1. **The source SHA** — found on the GitHub release page (`source_sha` field in the release-matrix.json release asset, or in the release body).
2. **Access to the source** — `arcflow-core` is a **private** repository. You need read access to the source SHA to rebuild it. If you don't have access, you can still verify via layers 1 + 2 (SHA256SUMS + sigstore attestation).
3. **Rust toolchain** matching the version specified in `arcflow-core/rust-toolchain.toml`.
4. **Platform-specific tools** (per target — see below).

If you need source-read access for the purpose of independent verification, contact gudjon@oz.com with your use case. Common cases (security research, regulatory compliance audit, academic study) are routinely granted. Source access for redistribution is not granted — that's still proprietary.

---

## Per-platform build recipes

The build commands below produce **byte-identical** binaries to the released ones at the same source SHA, assuming the same toolchain version. Confirmed reproducible for the platforms below.

### Linux x86_64 (musl, static-PIE)

Cross-build from macOS arm64 with [brew musl-cross](https://github.com/FiloSottile/homebrew-musl-cross) (or natively on Linux with musl-tools installed):

```sh
# Prerequisites (macOS):
brew install musl-cross
rustup target add x86_64-unknown-linux-musl

# Build:
CARGO_TARGET_X86_64_UNKNOWN_LINUX_MUSL_LINKER=x86_64-linux-musl-gcc \
CC_x86_64_unknown_linux_musl=x86_64-linux-musl-gcc \
AR_x86_64_unknown_linux_musl=x86_64-linux-musl-ar \
cargo build --release --target x86_64-unknown-linux-musl \
  -p arcflow-daemon --bin arcflow-daemon \
  --config 'profile.release.lto = "fat"' \
  --config 'profile.release.codegen-units = 1' \
  --config 'profile.release.strip = "symbols"'
```

Output: `target/x86_64-unknown-linux-musl/release/arcflow-daemon`

This is the **production-grade** Linux profile. Static-PIE — no glibc/musl runtime dependency, runs on any x86_64 Linux host.

Build time: ~4 minutes on M3 Mac (musl-cross is efficient).

### macOS arm64 (Apple Silicon)

Native build on macOS arm64:

```sh
# Prerequisites:
rustup target add aarch64-apple-darwin

# Build:
cargo build --release --target aarch64-apple-darwin \
  -p arcflow-daemon --bin arcflow-daemon
```

Output: `target/aarch64-apple-darwin/release/arcflow-daemon`

This is the **dev/CI-validation grade** profile (default release — no strip, no LTO). For production-grade Apple Silicon binaries matching the Linux profile, add the same `--config` flags:

```sh
cargo build --release --target aarch64-apple-darwin \
  -p arcflow-daemon --bin arcflow-daemon \
  --config 'profile.release.lto = "fat"' \
  --config 'profile.release.codegen-units = 1' \
  --config 'profile.release.strip = "symbols"'
```

Note: the strip+LTO version takes 15-25 minutes. Default release takes ~4-5 min.

### macOS x86_64 (Intel)

```sh
rustup target add x86_64-apple-darwin
cargo build --release --target x86_64-apple-darwin \
  -p arcflow-daemon --bin arcflow-daemon \
  --config 'profile.release.lto = "fat"' \
  --config 'profile.release.codegen-units = 1' \
  --config 'profile.release.strip = "symbols"'
```

Build on macOS arm64 (cross-arch) or on macOS x86_64 directly. Both produce the same output.

### Linux x86_64 (gnu, dynamic glibc)

```sh
rustup target add x86_64-unknown-linux-gnu
cargo build --release --target x86_64-unknown-linux-gnu \
  -p arcflow-daemon --bin arcflow-daemon \
  --config 'profile.release.lto = "fat"' \
  --config 'profile.release.codegen-units = 1' \
  --config 'profile.release.strip = "symbols"'
```

Cross-compile from macOS requires a Linux container or a sysroot setup. Native build on Linux is the simpler path.

### Linux arm64 (gnu + musl)

Native build on ubuntu-24.04-arm or Apple Silicon (cross). Both targets ship in the release matrix; recipes mirror x86_64 with `aarch64-unknown-linux-gnu` and `aarch64-unknown-linux-musl` respectively.

---

## Verification step (after building)

Compute the SHA256 of your build output:

```sh
shasum -a 256 target/<triple>/release/arcflow-daemon
# or on Linux:
sha256sum target/<triple>/release/arcflow-daemon
```

Compare to the corresponding entry in the release's `SHA256SUMS` file. If they match byte-for-byte, your build is reproducible against the official release.

If they DON'T match, possible causes (in order of likelihood):

1. **Different Rust toolchain version.** Check `rustup show` against the version pinned in `arcflow-core/rust-toolchain.toml` for the source SHA you're building.
2. **Different cargo profile flags.** Verify you're using the same `--config` flags as the workflow (see `arcflow-core/.github/workflows/release-binaries.yml` `Build` step).
3. **Different host platform / linker version.** Some toolchain combinations produce slightly different binaries even at the same source SHA. This is a known unsolved problem in Rust reproducibility for some scenarios; in practice it usually shows up only when host platforms differ significantly.
4. **Cargo dependency lockfile drift.** If you're rebuilding from a fork/branch where `Cargo.lock` has changed, dependencies versions differ — different code = different binary. Use the exact `Cargo.lock` from the source SHA.

If you've ruled out all four and still get a mismatch, **file an issue at github.com/ozinc/arcflow/issues** with your build environment details. Genuine reproducibility regressions are bugs we want to fix.

---

## Sigstore attestation verification

Sigstore is the easier path for most users — it doesn't require source access.

Install [gh CLI](https://cli.github.com/) and run:

```sh
# Verify a downloaded tarball
gh attestation verify arcflow-0.7.1-linux-x86_64-musl.tar.gz --owner ozinc

# Or verify a binary already installed
gh attestation verify ~/.arcflow/bin/arcflow --owner ozinc
```

Output:

```
✓ Verification succeeded!
The following 1 attestation matched the policy filters:

- Build repository: ozinc/arcflow-core
- Build workflow: .github/workflows/release-binaries.yml
- Source SHA: 955d03b3...
- Build trigger: refs/tags/v0.7.1
- Builder: actions.runner.github.com
```

The attestation proves:

- The binary was produced by the named workflow (`release-binaries.yml`) running in the named repo (`ozinc/arcflow-core`)
- At the named source SHA (`955d03b3...`)
- Triggered by the named tag push (`refs/tags/v0.7.1`)
- Signed by GitHub Actions' OIDC identity (the builder)

Without trusting OZ. The attestation lives in [sigstore's public transparency log](https://search.sigstore.dev/) — anyone can fetch it independently.

---

## Limits of reproducibility

We commit to reproducibility for the platforms in the release matrix at the documented build recipes. We do not commit to reproducibility for:

- Builds with non-default optimization flags (e.g., custom `-C target-cpu=native`)
- Builds with non-pinned Rust toolchain versions
- Builds with dependency overrides via Cargo `[patch]` sections
- Builds with feature flags different from what the official build uses
- Builds on platforms not in the official matrix

These are still **possible** — they just may not be byte-identical to the official binaries. For any of them, the sigstore attestation path still works: download a fresh tarball + verify the attestation, then extract.

---

## Reporting reproducibility issues

File an issue at [github.com/ozinc/arcflow/issues](https://github.com/ozinc/arcflow/issues) using the `bug` template. Include:

- Source SHA you tried to reproduce
- Platform + toolchain version
- Exact `cargo build` invocation
- Output SHA256
- Expected SHA256 (from release SHA256SUMS)

We treat reproducibility regressions as bugs and prioritize them — the property is load-bearing for the "verifiable closed-source" trust story.

---

## Related

- [`LICENSE-FAQ.md`](../LICENSE-FAQ.md) — "How can I verify a downloaded ArcFlow binary is authentic?"
- [`docs/protocol/jsonrpc-v1.md`](./protocol/jsonrpc-v1.md) — the daemon's wire protocol (also independently verifiable / reimplementable)
- `arcflow-core/.github/workflows/release-binaries.yml` (private) — the canonical build workflow whose runs are attested
- [Sigstore](https://sigstore.dev/) — the transparency log + signing system used for attestations
- [SLSA](https://slsa.dev/) — Supply-chain Levels for Software Artifacts; the framework this verifiability sits in
