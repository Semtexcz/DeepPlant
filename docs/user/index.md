---
type: navigation
status: active
canonical_for:
  - user-documentation-navigation
read_when:
  - start-work
  - using-deepplant
update_when:
  - user-documentation-change
depends_on:
  - docs/index.md
  - docs/dev/workflow/conventions.md
  - docs/contracts/index.md
decision:
  - docs/dev/decisions/ADR-0015-documentation-architecture-v2-1.md
  - docs/dev/decisions/ADR-0014-documentation-architecture-v2.md
evidence: []
superseded_by: null
---

# User Documentation

For people who **use** DeepPlant rather than change its internals: authoring a
model, validating it, understanding errors, and rendering a diagram.

User guidance explains **workflows**. It does not own the exact rules. Every
technical obligation — YAML shape, field semantics, CLI behaviour, renderer API —
stays canonical in [contracts/](../contracts/index.md), and these pages link to it
instead of restating it.

## Start here

- [getting-started.md](getting-started.md) — from a checkout to a first validated
  model.

## Understand DeepPlant

- [concepts/what-is-deepplant.md](concepts/what-is-deepplant.md) — what DeepPlant
  is, what a semantic model is, and what does not exist yet.

## Common tasks

- Author a plant model as YAML:
  [how-to/author-plant-yaml.md](how-to/author-plant-yaml.md)
- Validate a model: [how-to/validate-a-model.md](how-to/validate-a-model.md)
- Diagnose validation errors:
  [how-to/diagnose-validation-errors.md](how-to/diagnose-validation-errors.md)
- Render a process diagram to SVG:
  [how-to/render-process-svg.md](how-to/render-process-svg.md)

## Reference

- [reference/index.md](reference/index.md) — routes to the exact canonical rules.
- Canonical contracts: [contracts/index.md](../contracts/index.md).

## Developer or agent?

If you are changing DeepPlant rather than using it, start from
[../dev/index.md](../dev/index.md). Only the contracts are shared between
audiences; architecture, decisions, evidence, planning, and history are
developer-owned and are not required reading to use DeepPlant.
