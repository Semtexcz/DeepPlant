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

DeepPlant ships the project foundation plus two executable semantic vertical
slices: the minimal domain model and the first topology slice.

- minimal domain model: `PlantModel` -> `Plant` + `list[Equipment]`
- equipment-owned `Port` objects; port identity is local to the owning equipment
- top-level `Connection` edges over structured `PortRef(component, port)`
  endpoints
- reference validation: every endpoint component must resolve to existing
  equipment and its port must exist on that equipment
- YAML load through a small boundary into typed Pydantic models
- strict semantic input: unknown fields rejected, non-empty semantic ids,
  unique equipment ids, unique port ids per equipment item
- a runnable example: `examples/minimal-process/plant.yaml`
- `deepplant validate <path>` reporting plant, equipment, port, and connection
  counts

Work proceeds as small vertical changes with executable tests. The next
topology concept is deliberately reconsidered before implementation, not
auto-selected.

## Completed

| Item | Notes |
|---|---|
| Define `PlantModel` | Root container and composition of the model |
| Define `Plant` | Plant identity: `id`, `name` |
| Define `Equipment` | Engineering objects: `id`, `type`, `name`, owned `Port[]`; no fixed taxonomy yet |
| Define `Port` | Typed connection points owned by equipment; id local to the owning equipment |
| Define `Connection` | Semantic topology only: `source`/`target` as `PortRef(component, port)` |
| Reference validation | Connections resolve to existing equipment and owned ports; referential integrity only |
| YAML load | YAML as serialization, validated via Pydantic into the domain model |
| Semantic validation (structural) | Non-empty ids; unknown fields rejected; unique equipment ids; unique port ids per equipment |
| First executable example | `examples/minimal-process/plant.yaml` runs through the CLI |

## Backlog (Suggested Order)

The next step is an open architectural question, recorded for the next
iteration:

> What should represent process piping / streams in the canonical model: a
> component with ports, a connection with engineering properties, or a separate
> semantic entity?

Do not answer it from habit or because rendering needs it; answer it from a real
fragment requirement.

| # | Item | Note |
|---|---|---|
| 1 | Decide the pipes/streams representation | Open modeling question above; do not guess pipe, stream, or signal semantics yet |
| 2 | YAML save / round-trip | `load`/`save` symmetry once the model needs persistence |
| 3 | SVG symbol specification | Deliberate symbol spec, separate from semantics |
| 4 | Basic renderer | Derive a simple PFD/P&ID-like drawing from the model |
| 5 | DEXPI adapter spike | Prove import/export feasibility on a real fragment |

## Milestones

### Milestone 1 — validated YAML load

> DeepPlant can load a small process model from YAML, validate its semantic
> structure and report invalid references through the CLI.

Complete: structural validation and reference validation ship in the first two
slices.

### Milestone 2 — prototype fragment and renderer

> DeepPlant can represent a real process fragment of roughly 20–50 engineering
> objects, render it as a basic PFD/P&ID-like diagram and validate at least 10
> classes of engineering/model consistency errors.

## Next Task

Deliberately open. The next vertical change starts from the pipes/streams
representation question in the Backlog; it must not be auto-assumed to be YAML
save or rendering. Keep rendering, YAML save, and DEXPI out of that decision
unless the chosen fragment proves otherwise.

## Scope Discipline

- No database, ORM, web backend, containers, or external services.
- No empty architecture trees before real code exists.
- Schema and model design come from real example fragments, not abstraction.
- `Connection` is topology only; do not attach pipe/stream/signal engineering
  semantics until a real requirement justifies them.
