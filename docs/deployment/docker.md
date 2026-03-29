# Deployment: Docker

Run ArcFlow in Docker — zero build tools, 30 seconds to first query.

## Quick start

```bash
docker run -p 7687:7687 -p 8080:8080 ghcr.io/oz-global/arcflow:latest
```

## docker-compose

```yaml
services:
  arcflow:
    image: ghcr.io/oz-global/arcflow:latest
    ports:
      - "7687:7687"
      - "8080:8080"
    volumes:
      - arcflow-data:/data
    environment:
      - ARCFLOW_DATA_DIR=/data
      - ARCFLOW_LOG_LEVEL=info

volumes:
  arcflow-data:
```

```bash
docker compose up -d
```

## Connect from SDK

```typescript
import { open } from 'arcflow'

// In-process (recommended for same-machine apps)
const db = open('./data/graph')

// Or connect to Docker instance via HTTP (coming soon)
```

## Data persistence

Mount a volume to `/data` to persist graph data across container restarts:

```bash
docker run -v ./my-data:/data ghcr.io/oz-global/arcflow:latest
```

## Image details

- **Base:** scratch (no OS, minimal attack surface)
- **Binary:** statically linked, <20MB
- **Architecture:** `linux/amd64`, `linux/arm64`

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `ARCFLOW_DATA_DIR` | `/data` | Data directory |
| `ARCFLOW_LOG_LEVEL` | `info` | Log level (debug, info, warn, error) |
| `ARCFLOW_METAL_FORCE_UNAVAILABLE` | `false` | Disable Metal GPU |
