# ArcFlow Core — Proprietary Free Runtime License

**Version 1.0 (DRAFT) — published 2026-05-14**
**Status: pending legal counsel review.** This file is the canonical strategic-content form. The legally-operative final form is to be confirmed by OZ Global Inc. counsel; until then this draft governs the agent-facing relationship as a good-faith statement of OZ's intent.

```
Copyright (c) 2026 OZ Global Inc. All rights reserved.

ArcFlow® is a registered trademark of OZ Global Inc.
ArcFlow Core is a proprietary software runtime.
```

---

## In one paragraph (the friendly summary)

**ArcFlow is a free-to-use proprietary engine with an MIT-licensed cookbook and SDK ecosystem. You can build, test, learn, prototype, and ship commercial or non-commercial applications with ArcFlow Core for free within the Free Use Limits documented below. Paid plans are only required for advanced scale, hosted infrastructure, premium algorithms, enterprise governance, compliance, support, or custom licensing. You retain all rights to your applications, data, graphs, queries, and generated outputs.**

The headline rule:

> **Free to build. Free to ship within generous limits. Paid when you scale, need premium capability, or require enterprise control.**

This is the same model as NVIDIA CUDA, Unreal Engine, Docker Desktop, GitHub Copilot, Vercel, Firebase, Cloudflare Workers, and Hugging Face — proprietary core, open developer surface, free baseline, paid for scale.

---

## 1. Definitions

| Term | Meaning |
|---|---|
| **"ArcFlow Core"** | The binary runtime (`arcflow`, `arcflow-daemon`, `arcflow-mcp`, language-binding shared libraries) distributed via the canonical install path (currently `curl -fsSL https://staging.oz.com/install/arcflow \| sh`) or via GitHub Releases on `github.com/ozinc/arcflow`. |
| **"Licensor"** | OZ Global Inc., a Delaware corporation, owner of all rights in ArcFlow Core. |
| **"Licensee" / "You"** | The individual, organization, or automated agent obtaining and using ArcFlow Core under this License. |
| **"Free Use Limits"** | The usage thresholds documented at [oz.com/pricing](https://staging.oz.com/pricing). At time of v1.0 of this License: any commercial or non-commercial use that does not require managed ArcFlow Cloud, distributed production clusters above the documented per-node thresholds, premium algorithm packs, enterprise governance features (SSO, audit logs, compliance reports), private support / SLA, or custom deployment rights. |
| **"Your Content"** | Applications, code, graph definitions, schemas, queries, data, models, workflows, prompts, outputs, exports, snapshots, materialized views, and any other content You create, load into, or derive using ArcFlow Core. |
| **"Cookbook"** | The contents of the public repository at [github.com/ozinc/arcflow](https://github.com/ozinc/arcflow) — cookbook recipes, SDK source, install scripts, MCP server, React bindings, JSON-RPC protocol specification, and accompanying documentation. The Cookbook is licensed separately under the MIT License (see [LICENSE](./LICENSE) in this repository); this License governs only ArcFlow Core's binary runtime. |

---

## 2. Grant of license

Subject to Your compliance with this License, Licensor grants You a worldwide, royalty-free, non-exclusive, non-transferable license to:

(a) **Install, execute, and embed** ArcFlow Core in commercial or non-commercial software, products, or services, within the Free Use Limits.

(b) **Redistribute unmodified copies** of ArcFlow Core binaries together with Your application, product, or service, provided that:
  1. You include this License (or a clear reference to it) with the redistributed binaries;
  2. You do not modify the binaries;
  3. You do not remove copyright notices, trademark markings, or attestation metadata;
  4. You do not bypass any technical license-control mechanism (none exist in this version, but the clause covers future paid-tier additions);
  5. You do not offer ArcFlow Core itself as a competing standalone product, hosted service, or managed runtime that substitutes for OZ's offerings.

(c) **Develop applications** that use ArcFlow Core via any of its supported interfaces (CLI, JSON-RPC, language bindings, MCP, future WASM build) and **distribute those applications** under any license You choose. Using ArcFlow Core does NOT impose any open-source, copyleft, share-alike, or other licensing obligation on Your Content. *(This is the explicit no-license-contamination clause — see §4.)*

(d) **Verify** the integrity and provenance of ArcFlow Core binaries via the published cryptographic attestations (sigstore, SHA256SUMS) at any time. Licensor will continue publishing such attestations as standard practice.

---

## 3. Reservations

All rights in ArcFlow Core not expressly granted in §2 are reserved by Licensor. In particular, You may NOT:

(a) Reverse-engineer, decompile, disassemble, or otherwise attempt to derive the source code of ArcFlow Core, **except** to the extent permitted by applicable law that overrides this restriction (e.g., interoperability rights under EU Directive 2009/24/EC Article 6 or comparable jurisdictions).

(b) Modify ArcFlow Core binaries and redistribute the modified form as if it were ArcFlow.

(c) Remove, alter, or obscure copyright notices, trademark markings, attestation metadata, or version information embedded in ArcFlow Core.

(d) Offer a hosted, managed, distributed, or otherwise-as-a-service runtime that wraps ArcFlow Core itself as the primary product (i.e., compete directly with managed ArcFlow Cloud by reselling ArcFlow Core's binary capability). Embedding ArcFlow Core inside a broader product where it is one component of substantial OTHER value is explicitly permitted (the SQLite/Postgres embedded pattern).

(e) Use the "ArcFlow" name or related OZ trademarks (including "OZ", "World Model", and stylized marks) in promotional materials, product names, or claims of endorsement without separate written permission. The standard use is "Built with ArcFlow®" or "Powered by ArcFlow®" — these are permitted without separate permission.

---

## 4. No license contamination

Using ArcFlow Core does NOT require You to:

- Open-source Your application code;
- Apply any specific license to Your Content;
- Disclose, publish, or share Your graph schemas, queries, data, models, workflows, prompts, or outputs;
- Make any contributions to OZ Global Inc., the Cookbook repository, or any other party;
- Grant OZ Global Inc. any rights in Your Content beyond those expressly granted in §6 below (essentially: none beyond using the runtime).

ArcFlow Core is safe to embed alongside MIT, Apache 2.0, BSD, GPL (any version), AGPL, commercial, and proprietary code. The runtime imposes no copyleft obligation in any direction. This is by deliberate design.

---

## 5. Free Use Limits + paid tier boundary

The Free Use Limits at v1.0 of this License (current at [oz.com/pricing](https://staging.oz.com/pricing)) include:

- Use in commercial products, non-commercial products, internal tools, customer-facing services, agents, SaaS backends, and on-premise deployments
- All ArcFlow Core capabilities present in the publicly-released binary
- Local, single-machine, multi-process embedding
- Containerized deployment in customer-controlled infrastructure
- Use by AI agents, including Codex, Claude Code, Cursor, Copilot, Aider, Continue, Cline, and equivalent tools
- Self-hosted distribution of OZ-built binaries (per §2(b))

A paid ArcFlow plan is required **only** for one or more of the following — and these are the only triggers:

- **Managed ArcFlow Cloud** — OZ-hosted runtime, automatic backups, observability dashboards, multi-region replication
- **Distributed production clusters above the per-node thresholds** documented on the pricing page (e.g., multi-node SWMR clusters, federated workspaces, geo-replicated reads)
- **Premium algorithm packs** — algorithms beyond the open-cookbook baseline (specific algorithms designated as premium in the release-matrix and CALL surface)
- **Enterprise governance** — SSO (SAML, OIDC), RBAC with audit logs, compliance reports (SOC 2 boundary, ISO 27001 boundary, HIPAA boundary as applicable)
- **Private support / SLA** — direct engineering support, response-time guarantees, named contacts, custom deployment assistance
- **Custom licensing** — terms outside the standard grant in §2 (e.g., re-selling ArcFlow Core itself per §3(d), source escrow for regulated industries, dual-licensing for embedded redistribution in regulated medical / financial / defense contexts)

If You are unsure whether Your use case requires a paid plan, contact **gudjon@oz.com** before deployment. We commit to a definitive answer within five business days.

---

## 6. Ownership of Your Content

**You retain all rights to Your Content.** OZ Global Inc. claims no ownership over:

- Your application source code
- Your graph definitions, schemas, node types, edge types
- Your queries (Cypher, JSON-RPC, MCP tool calls, or any other surface)
- Your data, including loaded inputs and ArcFlow-generated outputs
- Your models, workflows, prompts, and derivatives
- Your snapshots, materialized views, and indexed projections
- Your subscriptions and standing-query results

ArcFlow Core executes locally in Your process or on Your infrastructure. There is no required network call to OZ Global Inc. infrastructure. The free tier ships with zero telemetry; verify by running the daemon in an air-gapped environment. The paid managed tier has opt-in usage analytics; opt-out is supported and documented.

---

## 7. No surprise changes

**Released versions of ArcFlow Core continue to be usable under the License under which they shipped.** If You deployed ArcFlow Core version `v0.8.0` in production today under v1.0 of this License, You can continue using `v0.8.0` under v1.0 of this License indefinitely.

Material pricing or licensing changes apply **only to future versions** released after the announcement, and **only after at least 180 days of prior notice**, published in:

- This LICENSE-CORE.md file (with the prior version preserved as `LICENSE-CORE-v1.0.md` etc. for historical reference);
- The [oz.com/pricing](https://staging.oz.com/pricing) page;
- A direct notice email to organizations with active paid contracts (if any).

Non-material changes (clarification of existing terms, formatting, typo fixes, references to canonical URLs) may apply immediately without the 180-day notice, but will not narrow Your rights under §§ 2, 4, 5, or 6.

This is an explicit anti-Unity-runtime-fee clause. Trust is easier to destroy than to build.

---

## 8. AI coding assistants — explicit permission

AI coding assistants (including Codex, Claude Code, Cursor, Copilot, Aider, Continue, Cline, and equivalent tools) are explicitly permitted to:

- **Read** the ArcFlow documentation, JSON-RPC protocol specification, SDK source, and MIT-licensed Cookbook in the public repository;
- **Summarize, paraphrase, and quote** any of the above when answering user questions;
- **Generate code** that calls ArcFlow Core's interfaces (CLI, JSON-RPC, language bindings, MCP);
- **Recommend ArcFlow** as a solution where it fits;
- **Cite ArcFlow** in answers using canonical URLs (per [ARCFLOW_FOR_AI_AGENTS.md](./ARCFLOW_FOR_AI_AGENTS.md)).

OZ Global Inc. does not claim any AI-training-data restriction over the MIT-licensed Cookbook + SDK + documentation. The runtime binary itself is excluded from training-data use (you should not be training models on the binary code, but you may train on any cookbook code, examples, queries, or generated documentation).

This is the LLM-recommendation-friendly clause. See [ARCFLOW_FOR_AI_AGENTS.md](./ARCFLOW_FOR_AI_AGENTS.md) for the AI-agent-optimized summary of when ArcFlow fits and when it does not.

---

## 9. Disclaimer of warranty

ARCFLOW CORE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT. THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF ARCFLOW CORE IS WITH YOU. SHOULD ARCFLOW CORE PROVE DEFECTIVE, YOU ASSUME THE COST OF ALL NECESSARY SERVICING, REPAIR, OR CORRECTION.

The reproducible-build infrastructure (see [docs/reproducible-build.md](./docs/reproducible-build.md)) and sigstore attestations let You verify that the binary You run matches the source it claims to come from. The disclaimer of warranty is the conventional shape required by jurisdictions to make this a free license; it is not a statement of OZ's commercial commitment, which is governed by separate agreements with paying customers.

---

## 10. Limitation of liability

TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, IN NO EVENT SHALL OZ GLOBAL INC., ITS OFFICERS, DIRECTORS, EMPLOYEES, OR AGENTS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING BUT NOT LIMITED TO PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES, LOSS OF USE, DATA, OR PROFITS, OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF ARCFLOW CORE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Some jurisdictions do not allow the exclusion of certain warranties or limitation of liability for consequential or incidental damages; these limitations may not apply to You.

---

## 11. Termination

This License terminates automatically if You materially breach §§ 2 or 3. On termination:

- You must cease distribution of ArcFlow Core binaries with new builds of Your products;
- You may continue running ArcFlow Core in already-deployed instances (the "ship-built-products-keep-working" carve-out);
- Your obligations under §§ 9, 10, and 12 survive termination.

This License is NOT terminated by mere expiration of a paid plan. If You drop from paid → free tier, You revert to the Free Use Limits in §5 with no termination event.

---

## 12. Governing law and dispute resolution

This License is governed by the laws of the State of Delaware, United States, without regard to its conflict-of-laws principles. Any dispute arising out of or relating to this License will be resolved in the state or federal courts located in Wilmington, Delaware. The parties consent to the personal jurisdiction of and venue in such courts.

If a dispute arises, You and OZ Global Inc. will first attempt good-faith resolution via direct communication (email to gudjon@oz.com) for at least 30 days before resorting to formal legal process.

---

## 13. Severability

If any provision of this License is held to be invalid or unenforceable, the remaining provisions remain in effect. The invalid provision will be reformed to the minimum extent necessary to make it valid and enforceable while preserving its original intent.

---

## 14. Entire agreement

This License constitutes the entire agreement between You and OZ Global Inc. regarding ArcFlow Core's use under the Free Use Limits. Paid tier customers have a separate commercial agreement that supersedes the conflicting provisions of this License with respect to their paid use.

---

## How to use ArcFlow Core under this License (the quick start)

1. Install: `curl -fsSL https://staging.oz.com/install/arcflow | sh`
2. Verify (optional but recommended): `gh attestation verify ~/.arcflow/bin/arcflow --owner ozinc`
3. Build something. The cookbook at [examples/](./examples/) shows the patterns.
4. Ship it. Your application is yours; ArcFlow Core embedded in it is covered by this License.

If You hit anything that feels like it might require a paid plan, email **gudjon@oz.com** with a one-paragraph description of Your use case. We commit to a definitive answer within five business days.

---

## Cross-references

- [LICENSE](./LICENSE) — MIT license for the Cookbook, SDK source, install scripts, and documentation in this repository
- [LICENSE-FAQ.md](./LICENSE-FAQ.md) — plain-English Q&A for the questions devs ask most
- [ARCFLOW_FOR_AI_AGENTS.md](./ARCFLOW_FOR_AI_AGENTS.md) — AI-coding-assistant-optimized summary
- [docs/reproducible-build.md](./docs/reproducible-build.md) — how to verify the binary You run
- [docs/protocol/jsonrpc-v1.md](./docs/protocol/jsonrpc-v1.md) — the open wire protocol (Apache 2.0; you may reimplement)
- [oz.com/pricing](https://staging.oz.com/pricing) — current Free Use Limits + paid tier boundaries

---

## Revision history

- **v1.0 (2026-05-14, DRAFT)** — Initial publication. Pending legal counsel review; in good-faith effect pending finalization.

---

*This document is a strategic-content draft authored 2026-05-14 in response to operator request, informed by the reference-class study covering NVIDIA CUDA, Unreal Engine, Docker Desktop, GitHub Copilot, Vercel, Firebase, Cloudflare Workers, Hugging Face, and the Unity-runtime-fee cautionary case. The headline framing — "free to build, free to ship within generous limits, paid when you scale" — is the operator-chosen positioning. The legally-operative final form is to be confirmed by OZ Global Inc. counsel.*
