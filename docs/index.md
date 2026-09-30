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
decision: []
evidence: []
superseded_by: null
---

# Documentation

Every entry is labelled by **authority**, so a current rule is never confused
with a decision record, an investigation, or history:

- **Current** — what exists and what must hold now.
- **Contract** — current model / API / format obligations.
- **Decision** — why a boundary exists (immutable record).
- **Evidence** — what was investigated, with outcomes.
- **Historical** — what shipped or was proposed earlier.
- **Governance** — how work, planning, quality, and standards are governed.

Documentation types, length limits, metadata, and linking rules:
[conventions.md](conventions.md).

## I need to understand DeepPlant

- **Current** — [project brief](../project/brief.md): purpose, users, scope
- **Current** — [architecture.md](architecture.md): boundary map of what exists
- **Current** — [product.md](product.md): product thesis and long-term position

## I need a current contract

- **Contract** — [contracts/index.md](contracts/index.md): plant model, process
  model, physical piping, YAML format, CLI, DEXPI Process adapter, renderer, SVG
  symbol pack

## I need to know what is next

- **Current** — [roadmap.md](roadmap.md): current state, next direction,
  unresolved evidence gaps
- **Current** — [direction.md](direction.md): long-term capability progression
  (product context, not implementation authorization)
- **Historical** — [history/implementation-slices.md](history/implementation-slices.md):
  what shipped, in order

## I need to understand why a choice was made

- **Decision** — [decisions/index.md](decisions/index.md)

## I need evidence, research, or a prototype

- **Evidence** — [research/index.md](research/index.md)

## I need governance, standards, or provenance

- **Governance** — [workflow.md](workflow.md): the change loop
- **Governance** — [planning.md](planning.md): vision → roadmap → Project →
  milestones → issues → pull requests
- **Governance** — [quality.md](quality.md): checks and test expectations
- **Governance** — [standards.md](standards.md): standards and symbol-asset
  provenance
- **Governance** — [conventions.md](conventions.md): this documentation system
- **Governance** — [AGENTS.md](../AGENTS.md): agent instructions
