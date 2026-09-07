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

DeepPlant now ships the project foundation plus the first executable semantic
vertical slice:

- minimal domain model: `PlantModel` -> `Plant` + `list[Equipment]`
- YAML load through a small boundary into typed Pydantic models
- basic structural validation (non-empty ids, unique equipment ids within a
  model)
- a runnable example: `examples/minimal-process/plant.yaml`
- `deepplant validate <path>`

Ports, connections, and reference validation are **not** implemented yet. Work
proceeds as small vertical changes with executable tests; no item below requires
`PlantModel`, `Equipment`, `Port`, and `Connection` to land in one change.

## Completed

| Item | Notes |
|---|---|
| Define `PlantModel` | Root container and composition of the model |
| Define `Plant` | Plant identity: `id`, `name` |
| Define `Equipment` | First engineering objects: `id`, `type`, `name`; no fixed taxonomy yet |
| YAML load | YAML as serialization, validated via Pydantic into the domain model |
| Semantic validation (structural) | Non-empty `plant.id`/`equipment.id`; unique equipment ids within a model |
| First executable example | `examples/minimal-process/plant.yaml` runs through the CLI |

## Backlog (Suggested Order)

| # | Item | Note |
|---|---|---|
| 1 | Define `Port` | Typed connection points on components |
| 2 | Define `Connection` | Generic `Port -> Connection -> Port` edges |
| 3 | Reference validation | Validate that connections reference existing ports/components |
| 4 | YAML save / round-trip | `load`/`save` symmetry once the model needs persistence |
| 5 | SVG symbol specification | Deliberate symbol spec, separate from semantics |
| 6 | Basic renderer | Derive a simple PFD/P&ID-like drawing from the model |
| 7 | DEXPI adapter spike | Prove import/export feasibility on a real fragment |

## Milestones

### Milestone 1 — validated YAML load

> DeepPlant can load a small process model from YAML, validate its semantic
> structure and report invalid references through the CLI.

The structural-validation half of this milestone is done for the first slice.
The reference-validation half still requires `Port` and `Connection`.

### Milestone 2 — prototype fragment and renderer

> DeepPlant can represent a real process fragment of roughly 20–50 engineering
> objects, render it as a basic PFD/P&ID-like diagram and validate at least 10
> classes of engineering/model consistency errors.

## Next Task

Implement `Port` + `Connection` + reference validation as the next vertical
change: extend the example fragment with typed connection points on equipment
and validate that connections reference existing model objects. Keep rendering,
YAML save, and DEXPI out of that change.

## Scope Discipline

- No database, ORM, web backend, containers, or external services.
- No empty architecture trees before real code exists.
- Schema and model design come from real example fragments, not abstraction.
