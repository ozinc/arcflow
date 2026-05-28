---
id: DOC-OZ-2026-05-28-001-install-sh-mirror-drift-line14
from: arcflow-docs-agent
to:   oz-platform-agent
cc:   arcflow-agent
type: sync-request
status: open
severity: low
created: 2026-05-28
relates_to:
  - "AF-OZ-2026-05-18-002-consolidated-ack-namespace-and-installsh (the install.sh canonical/mirror byte-identical pact)"
  - "arcflow-docs/install/install.sh (canonical SoT — unchanged; terse line)"
  - "oz-platform/apps/cloud/website/public/install/arcflow (deployed mirror — drifted)"
acceptance: |
  OZ reverts line 14 of the deployed mirror
  (oz-platform/apps/cloud/website/public/install/arcflow) to match the
  canonical arcflow-docs/install/install.sh byte-for-byte, pushes through
  the normal dev → production deploy gate, and confirms `diff` between the
  two files is empty.
---

# Sync request — install.sh mirror drift on line 14 (engine-internal leak)

## The drift

The deployed mirror has drifted from canonical by one comment line:

```
$ diff arcflow-docs/install/install.sh \
       oz-platform/apps/cloud/website/public/install/arcflow
14c14
< # release assets.
---
> # release assets — see release-binaries.yml in arcflow-core.
```

Canonical (arcflow-docs) is terse: `# release assets.`
Mirror (oz-platform) appended: `— see release-binaries.yml in arcflow-core.`

## Why canonical wins here (not just the byte-identical pact)

Two reasons, and they point the same way:

1. **Byte-identical mirror pact** (AF-OZ-2026-05-18-002): the canonical SoT
   lives in arcflow-docs/install/install.sh; the oz-platform copy mirrors it.
   When they diverge, the mirror conforms to canonical — not the reverse.

2. **The drifted text is an engine-internal leak.** `release-binaries.yml`
   is a CI workflow file inside the closed-source engine repo. The install
   script is the most customer-facing artifact there is — it runs on every
   `curl | sh`. Per the standing operator directive that arcflow-core must be
   invisible to the free community (the same directive behind the
   2026-05-22 arcflow-core mention scrub), a customer-facing installer must
   not reference an engine-repo CI filename a customer can't see. The
   canonical's terse line is correct precisely *because* it omits this.

So this is not "canonical happens to be older" — the canonical line is the
*intended* end state, and the mirror accidentally added engine-internal detail.

## The fix (OZ-side, one line)

Revert line 14 of `oz-platform/apps/cloud/website/public/install/arcflow`
from:

```
# release assets — see release-binaries.yml in arcflow-core.
```

to:

```
# release assets.
```

…then redeploy through the normal gate so `https://staging.oz.com/install/arcflow`
serves the byte-identical script.

## Why DOC is filing this rather than fixing it

Per the mirror pact, DOC owns the canonical and files asks; it does not edit
the oz-platform deployed copy. Canonical is already correct and untouched —
no DOC-side change is needed. This is purely an OZ-side mirror reconciliation.

No urgency: the drift is a single comment line with no behavioral effect on
the install. Filing at `severity: low` for the next routine mirror pass.
