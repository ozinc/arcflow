# ArcFlow Documentation

All docs are `.mdx` files with YAML frontmatter. The sidebar and ordering are defined in [`_config.json`](_config.json).

The website at `arcflow.dev/docs` fetches these files from GitHub at build time.

## Adding or editing docs

1. Edit `.mdx` files in this directory
2. Add frontmatter: `title`, `description`, `section`, `status`
3. Add to `_config.json` if it's a new page
4. Push to `main` — website revalidates automatically

## Structure

```
docs/
├── _config.json                 # Sidebar sections + ordering (website consumes this)
├── get-started.mdx              # Landing page
├── quickstart.mdx               # 5-minute quickstart
├── installation.mdx             # All install methods
├── project-setup.mdx            # Express, testing, monorepo
├── concepts/                    # Core concepts
│   ├── graph-model.mdx
│   ├── worldcypher.mdx
│   ├── parameters.mdx
│   ├── results.mdx
│   ├── persistence.mdx
│   └── error-handling.mdx
├── worldcypher/                 # Query language reference
│   ├── index.mdx                # Overview (renders at /docs/worldcypher)
│   ├── spatial.mdx
│   ├── temporal.mdx
│   └── algorithms.mdx
├── tutorials/                   # Step-by-step guides
├── recipes/                     # Copy-paste patterns
├── use-cases/                   # Real-world applications
├── reference/                   # API, compatibility, known issues
│   ├── api.mdx
│   ├── compatibility.mdx
│   ├── known-issues.mdx
│   └── worldcypher.yaml         # Machine-readable compatibility data
└── deployment/                  # Docker, cloud
```

## Frontmatter format

```yaml
---
title: "Page Title"
description: "One-line description"
section: "get-started"           # Must match a section id in _config.json
status: "stable"                 # stable | beta | deprecated
---
```

## URL mapping

`docs/{slug}.mdx` → `arcflow.dev/docs/{slug}`
`docs/concepts/graph-model.mdx` → `arcflow.dev/docs/concepts/graph-model`
`docs/worldcypher/index.mdx` → `arcflow.dev/docs/worldcypher`
