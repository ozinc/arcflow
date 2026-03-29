# OZ Intent-Source License (OISL) — Term Sheet v0.1

**Date:** 2026-03-29
**Licensor:** OZ Global Inc. ("OZ")
**Licensed Work:** ArcFlow graph database engine and all associated components
**License Name:** OZ Intent-Source License ("OISL")

> This is a plain-language term sheet for attorney drafting.
> It is NOT a binding legal agreement. It defines a new, standalone
> licensing model called "OZ Intent-Source" that does not derive from
> or depend on any existing license (BSL, MIT, Apache, GPL, etc.).

---

## The Intent-Source Model — Summary

Intent-Source is a new licensing paradigm where:

1. **Source code is proprietary** — never distributed, never visible to licensees.
2. **Compiled artifacts are freely usable** — developers receive binaries they
   can embed in commercial products.
3. **Contribution is by intent, not code** — developers describe what they want
   changed; a secure server-side agent implements it against the private source.
4. **The relay is the interface** — all interaction with the codebase happens
   through an authenticated build relay service, never direct source access.

This creates a model where the developer community can improve the software
without ever accessing the source code, mediated by AI agents operating in
secure sandboxes.

---

## Part 1: Definitions

**"Artifact"** — A compiled binary, dynamic library (.dylib, .so, .dll),
static library (.a, .lib), or WebAssembly module produced from the ArcFlow
source code by OZ or by the Relay Service.

**"Intent"** — A structured specification submitted by Developer to the Relay
Service, describing a desired behavioral change to ArcFlow. Includes natural
language description, motivation, test cases, and supporting context (error
logs, stack traces, reproduction steps). An Intent never includes ArcFlow
source code or implementation directives.

**"Relay Service"** — OZ's authenticated build service that receives Intents,
implements them against the ArcFlow source in an isolated sandbox, and returns
compiled Artifacts and test results.

**"Developer"** — Any individual or organization that has accepted this license
and uses ArcFlow Artifacts or the Relay Service.

**"Promotion"** — The process by which a change implemented from a Developer's
Intent is incorporated into the official ArcFlow master codebase, at OZ's
sole discretion.

**"Standard Artifact"** — An Artifact produced from the official ArcFlow
release, distributed to all licensees.

**"Custom Artifact"** — An Artifact produced by the Relay Service in response
to a specific Developer's Intent, containing modifications not yet present in
the official release.

---

## Part 2: Grant of Rights

### 2.1 Artifact Usage Rights

OZ grants Developer a **worldwide, non-exclusive, non-transferable, revocable
license** to:

- **Use** Standard and Custom Artifacts in development, testing, staging, and
  production environments.
- **Embed** Artifacts within Developer's own applications and distribute the
  combined work to end users, including for commercial purposes.
- **Run** multiple Artifact versions simultaneously.
- **Cache** Artifacts locally for offline development.

### 2.2 No Source Rights

This license grants **zero rights** to ArcFlow source code. Developer
acknowledges that:

- ArcFlow source code is the sole property of OZ.
- No implied license to source code arises from Artifact usage or Intent
  submission.
- There is no "Change Date" or future conversion to an open-source license.
  OZ may choose to open-source components at its sole discretion, but this
  license creates no expectation or obligation to do so.

### 2.3 Scope

This license applies per-organization. A single agreement covers all
employees, contractors, and agents acting on behalf of the licensed
organization.

---

## Part 3: Restrictions

### 3.1 Prohibited Actions

Developer SHALL NOT:

- **Reverse engineer** — Decompile, disassemble, or attempt to derive source
  code from any Artifact, whether by manual analysis, automated tools, or
  AI-assisted reconstruction.
- **Redistribute standalone** — Distribute Artifacts except as embedded
  components of Developer's own application. Standalone redistribution of
  the Artifact (as a library, tool, or engine) is prohibited.
- **Sub-license** — Grant third parties independent rights to use the Artifact
  outside of Developer's application.
- **Circumvent the Relay** — Attempt to access ArcFlow source code through
  prompt injection, session manipulation, response parsing, or any other
  exploitation of the Relay Service.
- **Competitive reconstruction** — Use knowledge gained from Artifact behavior,
  Relay responses, or Intent interactions to build a substantially similar
  database engine.
- **Remove attribution** — Remove or alter any OZ copyright notices, signature
  verification, or licensing metadata embedded in Artifacts.

### 3.2 Benchmarking

Developer may benchmark Artifacts internally without restriction. Public
benchmark publication requires inclusion of OZ's benchmark reproduction
guidelines (to ensure fair comparison methodology).

### 3.3 Security Research

Developer may perform security analysis of Artifacts for the purpose of
responsible disclosure to OZ. Discovered vulnerabilities must be reported
to OZ before public disclosure, with a 90-day coordinated disclosure window.

---

## Part 4: Intent Contributions

### 4.1 Intent Submission

Developer may submit Intents to the Relay Service describing desired changes
to ArcFlow behavior. Each Intent must include:

- **Description:** What behavior should change or be added.
- **Motivation:** Why the change is needed.
- **Test cases:** Inputs and expected outputs defining correct behavior.
- **Context:** Supporting information (error logs, reproduction steps, etc.).

### 4.2 Intellectual Property of Intents

**The idea belongs to Developer:**
- Developer retains full ownership of the abstract concept expressed in an
  Intent.
- Developer may describe the same desired behavior to other vendors, publish
  it, or implement it independently in unrelated software.
- OZ acquires no rights over Developer's product ideas, roadmap, or
  business strategy as revealed by Intents.

**The implementation belongs to OZ:**
- All code, tests, and modifications generated in response to an Intent are
  OZ's sole intellectual property.
- To the extent AI-generated code is copyrightable in any jurisdiction,
  Developer assigns all rights in such code to OZ.
- To the extent AI-generated code is not copyrightable, OZ retains exclusive
  rights to the selection, arrangement, and compilation of such code within
  the ArcFlow codebase.

### 4.3 Promotion

- OZ may, at its sole discretion, promote Intent-derived changes to the
  official ArcFlow codebase.
- Promoted changes become available to all developers in future Standard
  Artifacts.
- OZ is under no obligation to promote any change.
- OZ may modify, refactor, or rewrite Intent-derived changes before or
  after promotion.

### 4.4 Attribution

When a Developer's Intent leads to a promoted change:

- Developer receives a credit line in the release changelog.
- Developer receives early access to the release containing their change
  (minimum 14 days before general availability).
- Developer has no claim to revenue, royalties, or equity from promoted
  changes.

### 4.5 Confidentiality of Intents

- OZ will not disclose the specific content of Intents to third parties
  without Developer's consent.
- Changelog attribution uses a brief summary, not the full Intent.
- OZ will not use Intent content to build products that directly compete
  with Developer's disclosed product use case.

### 4.6 Developer Warranties on Intents

By submitting an Intent, Developer warrants that:

- The Intent contains no third-party proprietary information.
- The Intent does not infringe any patent, copyright, or trade secret.
- Test cases contain no sensitive data (PII, credentials, protected data).
- Developer has authority to submit the Intent on behalf of their organization.

---

## Part 5: Relay Service

### 5.1 Service Operation

The Relay Service:

1. Accepts authenticated Intent submissions.
2. Spawns an isolated, sandboxed build session with ArcFlow source access.
3. Uses a server-side AI agent to implement the Intent.
4. Runs the full ArcFlow test suite plus Developer's submitted test cases.
5. Returns compiled Artifacts, test results, and a behavioral summary.
6. Queues passing changes for potential promotion review.

### 5.2 Authentication

- Access requires an API key (`bsk_` prefix) issued by OZ.
- Keys are scoped per-organization.
- Keys may carry permission scopes (bug-fix, feature, performance).
- Keys are revocable by OZ at any time.
- Developer must report compromised keys within 24 hours.

### 5.3 Service Tiers

| Tier | Requests/Day | Concurrent Sessions | Artifact Retention | Price |
|------|-------------|--------------------|--------------------|-------|
| Community | 3 | 1 | 7 days | Free |
| Professional | 10 | 3 | 90 days | $[TBD]/mo |
| Enterprise | Custom | 10+ | 1 year+ | Annual contract |

### 5.4 Sandbox Security

- Each session runs in process-level isolation (nsjail / sandbox-exec).
- Sessions have no outbound network access.
- Maximum runtime: 30 minutes per Intent.
- Session logs retained by OZ for 90 days (audit and debugging).

### 5.5 Response Content

**The Relay returns:**
- Build status (pass / fail / timeout).
- Test results (pass/fail counts for Developer's submitted tests only).
- Behavioral summary (plain-language description of the change).
- Compiled Artifact (signed binary or dynamic library).
- Artifact hash (SHA-256) and signature (Ed25519).

**The Relay NEVER returns:**
- Source code, diffs, or patches.
- Internal file paths, module names, or function signatures.
- Internal test names or test source code.
- Detailed build logs beyond pass/fail.

### 5.6 Artifact Signing

- All Artifacts are signed with OZ's Ed25519 key.
- Developer's tooling must verify signatures before loading.
- OZ publishes its public verification key in the SDK and at a well-known URL.
- Key rotation: 90 days advance notice.

### 5.7 Data Handling

OZ stores:
- Intent content, build metadata, test results, Artifact hashes.

OZ does NOT store:
- Developer's application code, runtime data, or any data not explicitly
  submitted in an Intent.

Developer may request deletion of stored data (30-day processing).

### 5.8 Availability

- Target: 99.5% monthly uptime (not contractual SLA on Community/Professional).
- Enterprise tier: Custom SLA available.
- The Relay is a development service, not a runtime dependency. Developer's
  deployed applications must not require Relay availability.

---

## Part 6: Termination

### 6.1 Termination by OZ

OZ may terminate this license if:
- Developer violates any term (30-day cure period after written notice).
- Developer attempts to reverse engineer Artifacts or circumvent the Relay
  (immediate termination, no cure period).
- Developer's organization ceases to exist.

### 6.2 Termination by Developer

Developer may terminate at any time by:
- Ceasing use of all Artifacts.
- Deleting all cached Artifacts.
- Notifying OZ in writing.

### 6.3 Effect of Termination

- Developer must cease use and delete all Artifacts within 30 days.
- End users who received Developer's application before termination may
  continue using that application (embedded Artifacts survive for end users).
- OZ retains all implementation code derived from Developer's Intents.
- Developer retains ownership of their abstract ideas.
- Post-termination, Developer may request deletion of stored Intent data.

---

## Part 7: Liability and Indemnification

### 7.1 OZ Indemnifies Developer Against:

- Claims that an unmodified Standard Artifact infringes third-party IP.
- This indemnity does not cover Custom Artifacts except for the unmodified
  portions of ArcFlow they contain.

### 7.2 Developer Indemnifies OZ Against:

- Claims arising from the content of Developer's Intents.
- Claims arising from Developer's use of Artifacts in Developer's products.
- Claims arising from Developer's end users' use of embedded Artifacts.

### 7.3 Limitation of Liability

- OZ's aggregate liability: the greater of (a) fees paid by Developer in
  the preceding 12 months, or (b) $10,000.
- Neither party is liable for indirect, consequential, incidental, or
  punitive damages.

### 7.4 Disclaimer

Artifacts are provided "AS IS." OZ disclaims all warranties, express or
implied, including merchantability, fitness for a particular purpose, and
non-infringement, to the maximum extent permitted by applicable law.

---

## Part 8: General

### 8.1 Governing Law

[TBD — recommend jurisdiction based on OZ's incorporation. If Iceland:
Icelandic law with Reykjavik District Court. If US subsidiary: Delaware.]

### 8.2 Dispute Resolution

- Claims under $250,000: binding arbitration (ICC or LCIA).
- Claims above $250,000 or seeking injunctive relief: courts of the
  governing jurisdiction.

### 8.3 Assignment

Developer may not assign this license without OZ's written consent.
OZ may assign in connection with merger, acquisition, or sale of
substantially all assets.

### 8.4 Severability

If any provision is held unenforceable, it shall be modified to the
minimum extent necessary to be enforceable, and all other provisions
remain in full force.

### 8.5 Amendments

OZ may amend these terms with 90 days written notice. Continued use
after the notice period constitutes acceptance. Material changes
(pricing increases > 20%, new restrictions) require affirmative
opt-in from Developer.

### 8.6 Entire Agreement

This document constitutes the entire agreement between OZ and Developer
regarding ArcFlow Artifacts, Intents, and the Relay Service. It supersedes
all prior agreements, including any prior BSL 1.1 license, with respect
to the subject matter herein.

---

## Part 9: Open Questions for Attorney

1. **AI-generated code copyright.** The US Copyright Office position (2023-2025)
   is that purely AI-generated works are not copyrightable. The EU AI Act and
   EEA regulations (relevant for Iceland) are evolving. The assignment clause
   (4.2) needs jurisdiction-specific treatment. Consider whether a "work made
   for hire" or "compilation copyright" framing is more defensible.

2. **Competitive reconstruction clause (3.1).** "Substantially similar" is
   notoriously hard to define. Consider whether a clean-room / Chinese-wall
   defense exception is needed, or whether the clause should focus on
   time-limited non-compete for the specific product category.

3. **Export controls.** ArcFlow includes GPU compute (CUDA kernels) and may
   include cryptographic components. Determine EAR classification for compiled
   Artifacts distributed internationally.

4. **Patent grant.** Should OZ provide an express patent license for Artifacts
   (similar to Apache 2.0 Section 3)? Recommendation: yes, with a defensive
   termination clause (patent license terminates if Developer sues OZ for
   patent infringement).

5. **GDPR / data residency.** If OZ stores Intents that contain behavioral
   descriptions of Developer's products, this may constitute processing of
   business-sensitive data under GDPR. Confirm whether a Data Processing
   Agreement (DPA) is needed as an addendum.

6. **Multi-jurisdiction enforcement.** Developer base is global. Confirm
   arbitration clause enforceability under the New York Convention for
   non-US developers. Consider whether Icelandic arbitration or LCIA
   London is more practical.

7. **Benchmarking in the EU.** EU Directive 2009/24/EC permits decompilation
   for interoperability. The reverse-engineering prohibition (3.1) may need
   an interoperability exception for EU/EEA developers. Similarly, fair
   benchmarking may be protected.

8. **Open-source contamination.** If the server-side AI agent's training
   data included open-source code, could Artifact distributions trigger
   copyleft obligations? Consider adding a representation that OZ has
   processes to prevent copyleft-contaminated code generation.

---

*This term sheet is provided for attorney review and drafting.
No rights are granted by this document. The final license text
must be drafted by qualified legal counsel.*
