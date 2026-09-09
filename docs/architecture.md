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

This document separates what exists from what is only direction.

- **Current Architecture** describes implemented components and boundaries —
  the exact implemented state.
- **Directional Architecture (Principles Only)** describes durable target
  principles and future architectural direction. Some primitives referenced in
  that section may already exist; future components are not implemented unless
  explicitly stated.

## Current Architecture

The system is a Python CLI package implementing two executable semantic vertical
slices — the minimal domain model and the topology slice (`Port`, `Connection`,
reference validation): YAML file -> Pydantic validation -> typed domain model
-> `validate` CLI.

```text
tests -> CLI (src/deepplant/__main__.py) -> io.load_plant -> model
```

```text
YAML file
   ↓  PyYAML
Python data structure (dict)
   ↓  Pydantic validation
DeepPlant domain model (PlantModel -> Plant + Equipment[] + Connection[])
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

The process presentation assets ship inside the Python package as the
DeepPlant-original `basic` process symbol pack under
`src/deepplant/assets/symbols/process/basic/` — the canonical packaged asset
tree (contract: [svg-symbols.md](svg-symbols.md); decision: ADR-0008).
`ProcessStep.type` identifies a symbol role, not a globally canonical SVG
geometry; the headless renderer selects an explicitly chosen symbol pack
(currently only `basic`), whose pack-local SVG asset supplies monochrome
`currentColor` line art on the canonical `viewBox="0 0 100 100"` plus
machine-readable generic ordered `anchor-in-N` / `anchor-out-N` slots and
per-asset provenance records. The `basic` pack is non-normative
fallback/reference geometry.

The basic headless read-only process renderer (`src/deepplant/render.py`,
documented in [rendering.md](rendering.md)) renders a standalone SVG
process/PFD diagram from `ProcessModel` only: deterministic layered layout,
`ProcessStream`-incidence anchor assignment, orthogonal forward routing, and
dedicated feedback return lanes. It is pack-aware (runtime asset resolution
through `importlib.resources` from the installed package) and keeps every
layout/routing value transient — no presentation data is stored on semantic
models. The physical layer (`Equipment`, `Port`, `Connection`) is never
rendered.

Current semantic model:

```text
PlantModel
├── Plant
├── Equipment[]
│   └── Port[]
└── Connection[]
    ├── source: PortRef
    └── target: PortRef
```

- Port identity is local to the owning equipment/component. The same port id may
  exist on different equipment; a globally resolvable port endpoint is the pair
  `(component id, port id)`.
- `Connection` is currently a directed semantic topological relationship from
  `source` to `target`. Direction records which endpoint is the source and
  which is the target; it does not add flow or process-stream semantics.
- A `Connection` is not yet a pipe, process stream, signal, cable, or other
  physical engineering object. It is topology only and carries no engineering
  properties.
- The deliberate distinction is: directional topology != process-stream
  semantics. What should represent process piping / streams in the canonical
  model — a component with ports, a connection with engineering properties, or
  a separate semantic entity — remains an open modeling question that this
  iteration does not answer.

- Runnable example: `examples/minimal-process/plant.yaml`.
- `make run` executes the package module; `make test`, `make lint`,
  `make typecheck`, and `make build` verify the local package lifecycle.

No service runtime, browser runtime, container runtime, database, or external
infrastructure exists in this profile.

## Directional Architecture (Principles Only)

The semantic engineering model is the product core; everything else depends on
it:

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
  `Connection` objects (directed `source`/`target` `PortRef`s) already ship in
  the current implementation.

Integration/control-plane direction:

```text
                    DeepPlant
               canonical plant model
                       │
       ┌────────┬──────┼───────┬────────────┐
       ▼        ▼      ▼       ▼            ▼
     DEXPI    COMOS  AVEVA  simulators  calculations
                                     
                       │
                       ▼
             other engineering systems
```

DeepPlant may ultimately act as a semantic and automation layer across
heterogeneous engineering tools rather than replace them (see
[product.md](product.md)). DEXPI, COMOS, AVEVA, simulators, calculations, and
other engineering systems are peer consumers/adapters around the canonical
model, not stages below one another. Consumer-specific representation concerns
must not leak into the semantic domain model; a genuine engineering concept
discovered through DEXPI, simulation, or another integration may legitimately
cause the domain model to evolve, but an external schema shape alone must not
dictate the canonical model. This control-plane idea is analogous in spirit to
Infrastructure as Code, without claiming identical architecture.

Do not create packages for `model/`, `rendering/`, `dexpi/`, or `simulation/`
until real code needs them. A future stage in the directional roadmap is
product context, not implementation authorization (see the Anti-Roadmap in
[roadmap.md](roadmap.md)).

## Current Quality Gates

```bash
make validate-docs
make validate-agent-skills

make check
```

## Directional Extensions

Not implemented. Add any item only when a concrete requirement and an ADR
justify it:

- semantic model growth: further engineering concepts (starting with the open
  pipes/streams representation question) and the YAML save path
- rendering polish: layout/label refinement and higher-fidelity symbol
  sourcing (the SVG + anchor contract and the initial `basic` process pack
  ship under `src/deepplant/assets/symbols/process/basic/`; a basic headless
  renderer already exists in `src/deepplant/render.py`)
- DEXPI, COMOS, AVEVA, and simulator adapters
- interactive editor
- engineering rules / validation engine
- safety (HAZOP / SIS) concepts
- AI-assisted engineering workflows
- database or durable persistence
- cache, queue, broker, or background worker
- public deployment, Kubernetes, or service mesh

## Related

- [product.md](product.md)
- [roadmap.md](roadmap.md)
- [rendering.md](rendering.md)
- [svg-symbols.md](svg-symbols.md)
- [standards.md](standards.md)
- [workflow.md](workflow.md)
- [quality.md](quality.md)
- [decisions/index.md](decisions/index.md)
