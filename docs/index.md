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
  - docs/conventions.md
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
still answers what must hold now. The rules live in [conventions.md](conventions.md); the
current structure is decided in
[ADR-0015](decisions/ADR-0015-documentation-architecture-v2-1.md) (Documentation
Architecture v2.1), refining
[ADR-0014](decisions/ADR-0014-documentation-architecture-v2.md).

The **shared layer is narrow**: only [contracts/](contracts/index.md) and the
repository-root documents kept for repository/project role are shared.
Developer/agent material is canonical *and* developer-owned, so it will
eventually live under `dev/`; the current → target mapping is in
[documentation-migration.md](documentation-migration.md).

## Audience entry points

- **User** — [user/index.md](user/index.md): using the CLI, authoring YAML,
  reading current model contracts.
- **Developer / agent** — [dev/index.md](dev/index.md): architecture, contracts,
  decisions, evidence, workflow, and task-to-context routing.

## Where current truth lives (authority)

Every entry is labelled by authority, so a current rule is never confused with a
decision, an investigation, or history. Shared content lives in
[contracts/](contracts/index.md); the rest is canonical for its authority type and
currently still reaches from the `docs/` root (see
[documentation-migration.md](documentation-migration.md) for the target owners).

- **Current** — what exists and what must hold now.
- **Contract** — current model / API / format obligations.
- **Decision** — why a boundary exists (immutable record).
- **Evidence** — what was investigated, with outcomes.
- **Historical** — what shipped or was proposed earlier.
- **Governance** — how work, planning, quality, and standards are governed.

| Need | Open |
|---|---|
| Current contract (model, YAML, CLI, renderer, DEXPI) | [contracts/index.md](contracts/index.md) |
| Current boundary map of what exists | [architecture.md](architecture.md) |
| Project purpose, users, scope | [project brief](../project/brief.md) |
| Product thesis and non-goals | [product.md](product.md) |
| Current state and next direction | [roadmap.md](roadmap.md) |
| Long-term capability progression | [direction.md](direction.md) |
| Why a choice was made | [decisions/index.md](decisions/index.md) |
| Evidence, research, or a prototype | [research/index.md](research/index.md) |
| What shipped, in order | [history/implementation-slices.md](history/implementation-slices.md) |
| Governance (workflow, planning, quality, docs, standards) | [workflow.md](workflow.md), [planning.md](planning.md), [quality.md](quality.md), [conventions.md](conventions.md), [standards.md](standards.md) |
| Agent instructions | [AGENTS.md](../AGENTS.md) |

The planned split/relocation of documents lives in
[documentation-migration.md](documentation-migration.md).
