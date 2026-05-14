# ArcFlow Binary Distribution

Pre-built binaries ship as GitHub Releases on the public `ozinc/arcflow`
repo. The [`install.sh`](./install.sh) script in this directory is the
canonical installer; it is deployed to `oz.com/install/arcflow` via the
marketing site.

## Asset naming convention

```
arcflow-{version}-{platform}-{arch}.{ext}
```

### CLI binary

| Platform | Architecture | Asset |
|---|---|---|
| macOS | Apple Silicon | `arcflow-{v}-darwin-arm64.tar.gz` |
| macOS | Intel | `arcflow-{v}-darwin-x86_64.tar.gz` |
| Linux | x64 (glibc) | `arcflow-{v}-linux-x86_64-gnu.tar.gz` |
| Linux | ARM64 (glibc) | `arcflow-{v}-linux-arm64-gnu.tar.gz` |
| Linux | x64 (musl) | `arcflow-{v}-linux-x86_64-musl.tar.gz` |
| Linux | ARM64 (musl) | `arcflow-{v}-linux-arm64-musl.tar.gz` |

Each archive contains:

```
arcflow              # CLI binary
arcflow-mcp          # MCP server binary
libarcflow.{so,dylib,dll}  # Shared library (for FFI bindings)
```

### Checksums

Every release includes `SHA256SUMS` with checksums for all assets.

## Install methods — see the matrix

The customer-facing install matrix is rendered from the engine's release
manifest:

- **Live page**: <https://oz.com/docs/installation>
- **Manifest source**: <https://github.com/ozinc/arcflow/releases/latest/download/release-matrix.json>
- **Schema**: `arcflow/schemas/release-matrix.schema.json` (`schema_version: 1`)

Every binding's install command — current shipping status, target quarter
for planned bindings, supported platforms — comes from a single source of
truth. This README does not duplicate that matrix; if you need an install
command, read the manifest.

## Why this README exists

To document the installer **script** and the **asset naming convention** —
both of which are arcflow-docs concerns. The install **matrix** itself
(what's available to install, where) is the engine domain's responsibility
via `RELEASE-MATRIX.toml`. See PAT-0042 (Release Artifact Manifest as SSoT)
in the engine repo.
