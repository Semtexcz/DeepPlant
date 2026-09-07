---
type: roadmap
status: proposed
source_of_truth_for:
  - roadmap
read_when:
  - roadmap-change
  - feature-planning
update_when:
  - roadmap-change
---

# Roadmap

DeepPlant currently ships only the project foundation: a Python CLI package with
a `version` command, a minimal dependency set, durable documentation, ADRs, and
automated checks. Nothing in the backlog below is implemented yet. Work proceeds
as small vertical changes with executable tests.

## Backlog (Suggested Order)

| # | Item | Note |
|---|---|---|
| 1 | Define `PlantModel` | Root container and composition of the model |
| 2 | Define `Equipment` | First engineering objects |
| 3 | Define `Port` | Typed connection points on components |
| 4 | Define `Connection` | Generic `Port -> Connection -> Port` edges |
| 5 | YAML load/save | YAML as serialization, validated via Pydantic into the domain model |
| 6 | Semantic validation | Structural and reference validation on the domain model |
| 7 | First executable example | `examples/minimal-process` becomes runnable |
| 8 | SVG symbol specification | Deliberate symbol spec, separate from semantics |
| 9 | Basic renderer | Derive a simple PFD/P&ID-like drawing from the model |
| 10 | DEXPI adapter spike | Prove import/export feasibility on a real fragment |

## Milestones

### Milestone 1 — validated YAML load

> DeepPlant can load a small process model from YAML, validate its semantic
> structure and report invalid references through the CLI.

### Milestone 2 — prototype fragment and renderer

> DeepPlant can represent a real process fragment of roughly 20–50 engineering
> objects, render it as a basic PFD/P&ID-like diagram and validate at least 10
> classes of engineering/model consistency errors.

## Next Task

Design the first YAML schema deliberately, driven by example process fragments,
and implement the minimal domain model (`PlantModel`, `Equipment`, `Port`,
`Connection`) in the same vertical change so the schema is never invented in the
abstract.

## Scope Discipline

- No database, ORM, web backend, containers, or external services.
- No empty architecture trees before real code exists.
- Schema and model design come from real example fragments, not abstraction.
