---
type: navigation
status: active
canonical_for:
  - documentation-navigation
read_when:
  - start-work
  - find-document
update_when:
  - documentation-structure-change
depends_on:
  - docs/dev/workflow/conventions.md
decision:
  - docs/decisions/ADR-0015-documentation-architecture-v2-1.md
  - docs/decisions/ADR-0014-documentation-architecture-v2.md
evidence: []
superseded_by: null
---

# Documentation

This page routes you to the smallest useful entry point. It is not the
documentation itself.

```text
I want to use DeepPlant
    → user documentation: user/index.md

I want to develop, extend, or understand DeepPlant internals
    → developer documentation: dev/index.md
```

**Audience** (who is reading) and **knowledge authority** (what kind of truth a
document owns) are deliberately separate dimensions: audience determines
navigation and, for audience-specific content, physical ownership, while authority
still answers what must hold now. The rules live in [conventions.md](dev/workflow/conventions.md); the
current structure is decided in
[ADR-0015](decisions/ADR-0015-documentation-architecture-v2-1.md) (Documentation
Architecture v2.1), refining
[ADR-0014](decisions/ADR-0014-documentation-architecture-v2.md).

The **shared documentation layer is narrow**: only genuinely cross-audience
contracts live in [contracts/](contracts/index.md). Repository-role exceptions are
a separate category: `README.md` and `VISION.md` are broad public/repository entry
documents, while `AGENTS.md` and `project/brief.md` remain developer/agent-oriented
despite their locations. `docs/index.md` is global navigation, not shared
documentation. Developer/agent material is canonical *and* developer-owned, so it
lives under `dev/`; architecture and workflow/governance have already moved and
the remaining root documents follow in bounded slices. The current → target
mapping is in
[documentation-migration.md](dev/workflow/documentation-migration.md).

## Audience entry points

- **User** — [user/index.md](user/index.md): using the CLI, authoring YAML,
  reading current model contracts.
- **Developer / agent** — [dev/index.md](dev/index.md): architecture, contracts,
  decisions, evidence, workflow, and task-to-context routing.

## Where current truth lives (authority)

Every entry is labelled by authority, so a current rule is never confused with a
decision, an investigation, or history. Cross-audience content lives in
[contracts/](contracts/index.md); developer-only canonical contracts/reference
live under `dev/reference/`; architecture and workflow/governance are now
canonical under `dev/`; the rest is canonical for its authority type and still
reaches from the `docs/` root until its own slice (see
[documentation-migration.md](dev/workflow/documentation-migration.md) for the
target owners).

- **Current** — what exists and what must hold now.
- **Contract** — current model / API / format obligations.
- **Decision** — why a boundary exists (immutable record).
- **Evidence** — what was investigated, with outcomes.
- **Historical** — what shipped or was proposed earlier.
- **Governance** — how work, planning, quality, and standards are governed.

| Need | Open |
|---|---|
| Current contract (model, YAML, CLI, renderer, DEXPI) | [contracts/index.md](contracts/index.md) |
| Current boundary map of what exists | [architecture.md](dev/architecture/index.md) |
| Project purpose, users, scope | [project brief](../project/brief.md) |
| Product thesis and non-goals | [product.md](product.md) |
| Current state and next direction | [roadmap.md](roadmap.md) |
| Long-term capability progression | [direction.md](direction.md) |
| Why a choice was made | [decisions/index.md](decisions/index.md) |
| Evidence, research, or a prototype | [research/index.md](research/index.md) |
| What shipped, in order | [history/implementation-slices.md](history/implementation-slices.md) |
| Governance (workflow, planning, quality, docs, standards) | [workflow.md](dev/workflow/index.md), [planning.md](planning.md), [quality.md](dev/workflow/quality.md), [conventions.md](dev/workflow/conventions.md), [standards.md](standards.md) |
| Agent instructions | [AGENTS.md](../AGENTS.md) |

The planned split/relocation of documents lives in
[documentation-migration.md](dev/workflow/documentation-migration.md).
