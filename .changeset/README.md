# Changesets

This project uses [changesets](https://github.com/changesets/changesets) for versioning.

To add a changeset:

```bash
cd typescript
npx changeset
```

This will prompt you for:
1. Which packages changed
2. Semver bump type (patch/minor/major)
3. A summary of the change

Changesets are committed as markdown files in `.changeset/` and consumed during release.
