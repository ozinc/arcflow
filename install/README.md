# ArcFlow Binary Distribution

Pre-built binaries are distributed via [GitHub Releases](https://github.com/ozinc/arcflow/releases).

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

### Checksums

Every release includes `SHA256SUMS` with checksums for all assets.

## Install methods

| Method | Command |
|---|---|
| curl | `curl -fsSL https://github.com/ozinc/arcflow/releases/latest/download/install.sh \| sh` |
| npm | `npm install arcflow` |
| Docker | `docker run ghcr.io/ozinc/arcflow:latest` |
| Manual | Download from [Releases](https://github.com/ozinc/arcflow/releases) |
