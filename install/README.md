# ArcFlow Binary Distribution

Pre-built binaries are hosted on Cloudflare (deployed via `wrangler`) and distributed through `arcflow.dev`.

## Asset naming convention

```
arcflow-{version}-{platform}-{arch}.{ext}
```

### CLI binary

| Platform | Architecture | Asset |
|---|---|---|
| macOS | Apple Silicon | `arcflow-{v}-darwin-arm64.tar.gz` |
| macOS | Intel | `arcflow-{v}-darwin-x64.tar.gz` |
| Linux | x64 (glibc) | `arcflow-{v}-linux-x64-gnu.tar.gz` |
| Linux | ARM64 (glibc) | `arcflow-{v}-linux-arm64-gnu.tar.gz` |
| Linux | x64 (musl) | `arcflow-{v}-linux-x64-musl.tar.gz` |
| Windows | x64 | `arcflow-{v}-win32-x64.zip` |

Each archive contains:
```
arcflow              # CLI binary
arcflow-mcp          # MCP server binary
libarcflow.{so,dylib,dll}  # Shared library (for FFI bindings)
```

### Node.js native module (npm)

| Platform | Architecture | npm package |
|---|---|---|
| macOS | Apple Silicon | `arcflow-darwin-arm64` |
| macOS | Intel | `arcflow-darwin-x64` |
| Linux | x64 (glibc) | `arcflow-linux-x64-gnu` |
| Linux | ARM64 (glibc) | `arcflow-linux-arm64-gnu` |
| Linux | x64 (musl) | `arcflow-linux-x64-musl` |
| Windows | x64 | `arcflow-win32-x64-msvc` |

These are `optionalDependencies` of the `arcflow` npm package — npm installs only the one matching your platform.

### Docker

```
ghcr.io/ozinc/arcflow:{version}
ghcr.io/ozinc/arcflow:latest
```

## Hosting

Binaries are hosted on Cloudflare R2/Pages via `wrangler`:

```
https://arcflow.dev/releases/v{version}/arcflow-{version}-{platform}-{arch}.tar.gz
https://arcflow.dev/releases/latest/arcflow-latest-{platform}-{arch}.tar.gz
https://arcflow.dev/install                    # Install script
https://arcflow.dev/install/arcflow.sh         # Same, explicit path
```

### Upload flow (from arcflow-core CI)

```bash
# Build binaries in arcflow-core
cargo build --release --target aarch64-apple-darwin

# Package
tar czf arcflow-${VERSION}-darwin-arm64.tar.gz -C target/aarch64-apple-darwin/release arcflow arcflow-mcp

# Upload to Cloudflare
wrangler r2 object put arcflow-releases/v${VERSION}/arcflow-${VERSION}-darwin-arm64.tar.gz \
  --file arcflow-${VERSION}-darwin-arm64.tar.gz

# Update latest symlink
wrangler r2 object put arcflow-releases/latest/arcflow-latest-darwin-arm64.tar.gz \
  --file arcflow-${VERSION}-darwin-arm64.tar.gz
```

### Checksums

Every release includes:
```
SHA256SUMS              # sha256 checksums for all assets
```

## Install methods

| Method | Command | Source |
|---|---|---|
| curl | `curl -fsSL https://arcflow.dev/install \| sh` | Cloudflare |
| npm | `npm install arcflow` | npm registry |
| Docker | `docker run ghcr.io/ozinc/arcflow:latest` | GHCR |
| Manual | Download from `arcflow.dev/releases/` | Cloudflare |
