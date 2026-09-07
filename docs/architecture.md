---
type: architecture
status: draft
source_of_truth_for:
  - current-architecture
read_when:
  - architecture-change
  - new-module
  - ready-for-development
update_when:
  - module-boundary-change
  - runtime-component-change
---

# Architecture

Project type: `script`. Runtime level: `shared`.
Governance: `lightweight`.

This document describes the architecture now and the durable target principles
that shape it. Nothing under "Target Architecture" is implemented yet.

## Current Architecture

The system is a Python CLI package implementing the first semantic vertical
slice: YAML file -> Pydantic validation -> typed domain model -> `validate` CLI.

```text
tests -> CLI (src/deepplant/__main__.py) -> io.load_plant -> model
```

```text
YAML file
   ↓  PyYAML
Python data structure (dict)
   ↓  Pydantic validation
DeepPlant domain model (PlantModel -> Plant + list[Equipment])
```

- Python >= 3.12, managed with `uv`.
- Runtime dependencies: Typer (CLI), Pydantic v2, PyYAML.
- Dev toolchain: pytest + pytest-cov, Ruff, Pyright (strict).
- The CLI exposes `--help`, `version`, and `validate <path>`.
- Domain model (`src/deepplant/model.py`): `PlantModel`, `Plant`, `Equipment`,
  `Port`, `PortRef`, `Connection` as Pydantic v2 models that import nothing
  consumer-specific.
- Loading boundary (`src/deepplant/io.py`): `load_plant(path) -> PlantModel`;
  every expected failure (missing file, invalid YAML, invalid model) raises
  `PlantLoadError` with a concise message, so the CLI never shows raw
  tracebacks for normal user errors.
- Structural validation: unknown fields are rejected on all semantic models;
  semantic ids (`plant.id`, `equipment.id`, `equipment.type`, `port.id`, and the
  `component`/`port` fields of a reference) must be non-empty, non-whitespace
  strings. Semantic input is fail-fast rather than permissive, so typos and
  unsupported engineering data cannot be silently discarded. Equipment ids must
  be unique within a `PlantModel`; port ids must be unique within one equipment
  item. No full tag naming standard and no fixed equipment taxonomy exist yet.
- Reference validation: every connection endpoint must resolve to existing
  equipment and to a port owned by that equipment. `component` in a reference
  resolves only to `Equipment` today; there is no generic `Component` base
  class. This enforces referential integrity only, not process-engineering
  topology rules.

Semantic topology in this iteration:

```text
Equipment
   ↓ owns
Port

Connection
├── source -> PortRef(component, port)
└── target -> PortRef(component, port)
```

- Port identity is local to its owning component. The same port id may exist on
  different equipment; a globally resolvable endpoint is the pair
  `(component id, port id)`.
- `Connection` represents semantic topology only. It is not yet a pipe, stream,
  signal, or other physical engineering object, and it carries no engineering
  properties.

- Runnable example: `examples/minimal-process/plant.yaml`.
- `make run` executes the package module; `make test`, `make lint`,
  `make typecheck`, and `make build` verify the local package lifecycle.

No service runtime, browser runtime, container runtime, database, or external
infrastructure exists in this profile.

## Target Architecture (Principles Only)

The semantic engineering model is the product core; everything else depends on it:

```text
CLI
GUI
renderers
DEXPI adapters
simulation adapters
AI agents
        ↓
semantic domain model
```

Dependency direction is inward: consumers may depend on the domain model; the
domain model depends on nothing consumer-specific. The domain model must remain
usable directly from Python and from the CLI.

Stated constraints:

- Semantic model vs presentation model: engineering semantics (`Plant`,
  `Equipment`, `Port`, `Connection`, `Pipeline`, `Instrument`, properties,
  relationships) and presentation (`sheet`, `symbol`, x/y position, rotation,
  geometry, routing, labels) are strictly separate. Drawing coordinates and SVG
  concepts never live on core engineering objects.
- YAML is a serialization format, not the domain model:

  ```text
  YAML
   ↓
  Pydantic validation / parsing
   ↓
  DeepPlant domain model
   ↓
  validation / rendering / adapters
  ```

- Connectivity uses generic `Component -> Ports -> Connections` relationships
  (e.g. `P-101.discharge -> connection -> L-101.inlet`), not hard-coded
  `pump connected to pipe` fields. Equipment-owned ports and top-level
  connections ship in the current slice.

Do not create packages for `model/`, `rendering/`, `dexpi/`, or `simulation/`
until real code needs them.

## Current Quality Gates

```bash
make validate-docs
make validate-agent-skills

make check
```

## Possible Future Extensions

Do not treat this list as implemented architecture. Add any item only when a
concrete requirement and ADR justify it:

- semantic model growth: further engineering concepts (starting with the open
  pipes/streams representation question) and the YAML save path
- rendering and the SVG symbol specification
- DEXPI and simulator adapters
- interactive editor
- database or durable persistence
- cache, queue, broker, or background worker
- public deployment, Kubernetes, or service mesh

## Related

- [product.md](product.md)
- [roadmap.md](roadmap.md)
- [workflow.md](workflow.md)
- [quality.md](quality.md)
- [decisions/index.md](decisions/index.md)
