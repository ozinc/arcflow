# ArcFlow Documentation

## Getting Started

- [Installation](getting-started/installation.md) — npm, Docker, binary, local dev
- [Quickstart](getting-started/quickstart.md) — first query in 5 minutes
- [Project Setup](getting-started/project-setup.md) — Express, testing, monorepo, TypeScript config

## WorldCypher Language

- [Overview](worldcypher/overview.md) — clauses, patterns, extensions beyond Cypher
- [Spatial Queries](worldcypher/spatial.md) — distance, zones, spatial predicates
- [Temporal Queries](worldcypher/temporal.md) — AS OF, decay, velocity, trajectory
- [Algorithms](worldcypher/algorithms.md) — 30+ algorithms, centrality, community detection, search

## Core Concepts

- [Graph Model](core-concepts/graph-model.md) — nodes, relationships, properties
- [WorldCypher](core-concepts/worldcypher.md) — query language intro
- [Parameters](core-concepts/parameters.md) — parameterized queries
- [Results](core-concepts/results.md) — QueryResult, TypedRow, typed access
- [Persistence](core-concepts/persistence.md) — WAL, checkpoints, recovery
- [Error Handling](core-concepts/error-handling.md) — ArcflowError, categories, codes

## Tutorials

- [Knowledge Graph](tutorials/knowledge-graph.md) — entities, facts, confidence scores
- [Entity Linking](tutorials/entity-linking.md) — multi-MATCH patterns, cross-source linking
- [Vector Search](tutorials/vector-search.md) — embeddings, HNSW index, similarity search
- [Graph Algorithms](tutorials/graph-algorithms.md) — PageRank, Louvain, betweenness, centrality

## Recipes

- [CRUD](recipes/crud.md) — create, read, update, delete
- [Multi-MATCH](recipes/multi-match.md) — cross-entity joins
- [MERGE (Upsert)](recipes/merge-upsert.md) — find-or-create patterns
- [Full-Text Search](recipes/fulltext-search.md) — BM25 indexes
- [Temporal Queries](recipes/temporal-queries.md) — AS OF, decay, velocity
- [Batch Projection](recipes/batch-projection.md) — high-throughput pipeline ingestion
- [GraphRAG](recipes/graph-rag.md) — retrieval-augmented generation

## Reference

- [API](reference/api.md) — complete TypeScript SDK API
- [Compatibility Matrix](reference/compatibility.md) — all WorldCypher features and procedures
- [WorldCypher YAML](reference/worldcypher.yaml) — machine-readable compatibility data
- [Known Issues](reference/known-issues.md) — workarounds and caveats

## Deployment

- [Docker](deployment/docker.md) — docker run, docker-compose, persistence

## Use Cases

- [Knowledge Management](use-cases/knowledge-management.md) — entity extraction, linking, search
- [RAG Pipeline](use-cases/rag-pipeline.md) — vector + graph + full-text retrieval
- [Sports Analytics](use-cases/sports-analytics.md) — player tracking, formations, events
- [Behavior Graphs](use-cases/behavior-graphs.md) — game AI, robotics, autonomous agents
- [Grounded Neural Objects](use-cases/grounded-neural-objects.md) — real-time object identity, spatial tracking, camera handoff

## Sample Data

- [Fixtures](../fixtures/README.md) — ready-to-load sample datasets
