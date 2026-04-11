# Security Policy

## Reporting a vulnerability

If you discover a security vulnerability, please report it responsibly:

**Email:** security@oz.com

Do not open a public issue for security vulnerabilities.

## Supported versions

| Version | Supported |
|---|---|
| latest | Yes |
| < latest | Best effort |

## Scope

The ArcFlow SDK is a TypeScript wrapper that communicates with the ArcFlow engine via in-process native bindings. Security considerations include:

- **Query injection** — Always use parameterized queries (`$param`). The SDK substitutes parameters before compilation, preventing injection.
- **Data directory access** — `open(path)` accesses the filesystem. Validate paths in your application.
- **Native binary** — The `arcflow-core` package contains a pre-built native binary. Verify package integrity via npm provenance.
