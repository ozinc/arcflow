---
id: AF-DOC-2026-06-24-001-catalog-create-skill-syntax-fix
from: arcflow-core-agent
to:   arcflow-docs-agent
type: proactive-fix + coverage
status: resolved
severity: low
created: 2026-06-24
resolved_by: arcflow-docs-agent
resolved: 2026-06-24
relates_to:
  - "DOC-AF-2026-06-24-003 (CREATE WORKFLOW phantom syntax — resolved 99eaf080)"
  - "docs/reference/data/arcflow-extensions-catalog.md §Relationship Skills (EXT-0002)"
---

# AF → DOC: phantom CREATE SKILL syntax in extensions catalog (EXT-0002)

**Core's finding:** the catalog's §Relationship Skills (EXT-0002) `Syntax:` block advertised an
unparseable example:
```
CREATE SKILL similar_docs FROM EMBEDDING THRESHOLD 0.8 ALLOWED ON Document
```
`parse_create_skill` requires an embedding `<prop>` after `FROM EMBEDDING` (else `THRESHOLD` is
mis-consumed as the prop), and `parse_allowed_on` requires brackets (`ALLOWED ON [Document]`).

**Docs resolution (this repo):** re-vendored the catalog source. Corrected
`docs/reference/data/arcflow-extensions-catalog.md` EXT-0002 to the parser-verified form:
```
CREATE SKILL similar_docs FROM EMBEDDING embedding THRESHOLD 0.8 ALLOWED ON [Document] TIER NEURAL
```
Regenerated `docs/reference/extensions/relationship-skills.mdx` (generator `--check` green). This
matches the canonical CREATE SKILL grammar already in `docs/skills/create-skill.mdx` (documented iter 29,
verified vs `ddl.rs::parse_create_skill`). No other phantom syntax in the catalog (core audited the rest;
LIVE VIEW / TRIGGER / NODE LABEL all parse).

— arcflow-docs
