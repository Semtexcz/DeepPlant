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

The system is a Python CLI package implementing the semantic domain model
(`PlantModel`, `Plant`/`Equipment` with owned `Port`s, identified `Connection`
reference topology, the optional physical piping-realization submodel
`PipingModel` with `PipingLine` → `PipingSegment` → `PipingRealization`, and
the standalone process-domain model `ProcessModel` with
`ProcessStep[]`/`ProcessPort[]`/`ProcessStream[]`), a YAML loading/saving
boundary into typed Pydantic models, a `validate` CLI, the packaged `basic`
process symbol pack, a headless read-only process renderer, and a narrow DEXPI
2.x Process adapter:

```text
tests -> CLI (src/deepplant/__main__.py) -> io.load_plant -> model
```

```text
YAML file
   ↓  PyYAML
Python data structure (dict)
   ↓  Pydantic validation
DeepPlant domain model (PlantModel -> Plant + Equipment[] + Connection[] + PipingModel?)
```

- Python >= 3.12, managed with `uv`.
- Runtime dependencies: Typer (CLI), Pydantic v2, PyYAML.
- Dev toolchain: pytest + pytest-cov, Ruff, Pyright (strict).
- The CLI exposes `--help`, `version`, and `validate <path>`.
- Domain model (`src/deepplant/model.py`): `PlantModel`, `Plant`, `Equipment`,
  `Port`, `PortRef`, `Connection`, `PipingModel`, `PipingLine`,
  `PipingSegment`, `PipingRealization` as Pydantic v2 models that import nothing
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
- Physical piping realization (ADR-0011): `Connection` carries a required,
  non-empty, plant-unique `id` and nothing else — identity only, documented as
  a pre-1.0 breaking change to authored YAML (C1). `PlantModel.piping` is an
  optional `PipingModel` owning `PipingLine` → `PipingSegment` →
  `PipingRealization`; a realization references one `Connection` by id and
  states the closed first-slice `kind` vocabulary `pipe | direct` (default
  `pipe`, unknown values are validation errors). Structural rules P1–P5 ship:
  unique line ids, segment ids unique within the owning line, resolvable
  connection references, at most one realization per connection across the whole
  piping model, and non-empty segments. Segment/line numbers stay optional human
  designations and are never canonical identity, and no DN/piping-class/
  fluid-code values are required or typed. This first slice supports segment
  boundaries only where they coincide with existing `Connection` boundaries;
  mid-connection property breaks (DEXPI `PropertyBreak`), a canonical `Pipe`
  class, `PipingComponent`, `Nozzle`/`PipingNode`, instrumentation, and
  process ↔ physical realization remain unimplemented.

The process presentation assets ship inside the Python package as the
DeepPlant-original `basic` process symbol pack under
`src/deepplant/assets/symbols/process/basic/` — the canonical packaged asset
tree (contract: [svg-symbols.md](svg-symbols.md); decision: ADR-0008).
`ProcessStep.function` is canonical engineering semantics (ADR-0009); a
*presentation symbol role* is resolved at the rendering boundary from the
function by the renderer's default presentation policy or by an explicit
per-step `symbol_role_overrides` entry, and is never stored in the semantic
model. The headless renderer selects an explicitly chosen symbol pack
(currently only `basic`), whose pack-local SVG asset supplies monochrome
`currentColor` line art on the canonical `viewBox="0 0 100 100"` plus
machine-readable generic ordered `anchor-in-N` / `anchor-out-N` slots and
per-asset provenance records. The `basic` pack is non-normative
fallback/reference geometry.

The presentation chain is therefore four distinct concepts
([svg-symbols.md](svg-symbols.md), ADR-0009):

```text
ProcessStep.function
        ↓  default presentation policy (or explicit per-step override)
symbol role
        ↓  selected symbol pack
pack-local SVG asset
        ↓
geometry + ordered anchors
```

The realistic fragment demonstrates the boundary: `PS-vessel` declares
`function: unspecified` (semantic honesty) and is still drawn with the
`vessel` basic symbol through an explicit presentation override supplied only
to `render_process_svg` (see
[examples/realistic-process-fragment/README.md](../examples/realistic-process-fragment/README.md)).

The basic headless read-only process renderer (`src/deepplant/render.py`,
documented in [rendering.md](rendering.md)) renders a standalone SVG
process/PFD diagram from `ProcessModel` only: deterministic layered layout,
`ProcessStream`-incidence anchor assignment, orthogonal forward routing, and
dedicated feedback return lanes. It is pack-aware (runtime asset resolution
through `importlib.resources` from the installed package) and keeps every
layout/routing value transient — no presentation data is stored on semantic
models. The physical layer (`Equipment`, `Port`, `Connection`) is never
rendered.

The interoperability adapter (`src/deepplant/adapters/dexpi.py`, spike report:
[dexpi-process-spike.md](dexpi-process-spike.md)) is a narrow DEXPI **2.0
Process** boundary pinned to the official stable tag `V2.0.0`. Its import
preflight requires the exact pinned 2.0.0 Core/Process model URIs and globally
unique XML `Object@id` values, then maps an explicit material subset of DEXPI
Process XML (Source/Sink/Mixing/SplittingMaterial/Pumping with `MaterialPort`s
and material `Stream`s) into the canonical `ProcessModel`; declared
`ConnectorReference` values are validated when present and unsupported populated
content fails closed. The exporter serializes the deliberately symmetric
canonical subset back as DEXPI-native XML for that supported structural subset
(`source`, `sink`, `mixing`, `splitting_material`, and material-port-only
`pumping` — ADR-0009 made the canonical `function` vocabulary an engineering
classification, which unblocked the previously rejected reverse `pumping`).
DEXPI is an adapter: `deepplant.model` imports nothing adapter-specific, no
canonical field was added for the adapter, and
EnergyFlow/InformationFlow/Plant/P&ID content is rejected explicitly rather
than silently collapsed. No generic adapter framework exists.

Current semantic model:

```text
PlantModel
├── Plant
├── Equipment[]
│   └── Port[]
├── Connection[]
│   ├── id                canonical, plant-unique identity (C1, ADR-0011)
│   ├── source: PortRef
│   └── target: PortRef
├── PipingModel (optional; ADR-0011)
│   └── PipingLine[]
│       ├── id            canonical line identity
│       ├── line_number   optional human designation
│       ├── name
│       └── PipingSegment[]
│           ├── id                canonical identity, local to the owning line
│           ├── segment_number    optional human/external designation
│           ├── nominal_diameter  optional open string
│           ├── piping_class      optional open string
│           ├── fluid_code        optional open string
│           └── PipingRealization[]
│               ├── connection    id of one Connection in this PlantModel
│               └── kind          closed: "pipe" (default) | "direct"
└── ProcessModel (optional; ADR-0005/ADR-0006)
    ├── ProcessStep[]
    │   ├── id
    │   ├── function        engineering process function (open string, ADR-0009)
    │   ├── name
    │   └── ProcessPort[]
    └── ProcessStream[]
        ├── id
        ├── name
        ├── source: ProcessRef(step, port)
        └── target: ProcessRef(step, port)
```

- `ProcessStep.function` is the engineering process function performed by the
  step (`source`, `sink`, `mixing`, `splitting_material`, `pumping`,
  `heat_exchange`, `unspecified`, or any other non-empty string — the
  vocabulary is open). It is not an equipment class, a symbol role, a DEXPI
  class, or a physical realization (ADR-0009). `unspecified` is legal and
  means the step exists but its function is not yet specified; rendering such
  a step needs explicit presentation information and is a presentation error,
  never a semantic-model error.

- Port identity is local to the owning equipment/component. The same port id may
  exist on different equipment; a globally resolvable port endpoint is the pair
  `(component id, port id)`.
- `Connection` is a directed semantic topological relationship from `source` to
  `target` with a required canonical `id`. Direction records which endpoint is
  the source and which is the target; it does not add flow or process-stream
  semantics, and the id is identity only, not an engineering property.
- A `Connection` is not a pipe, process stream, signal, cable, or other physical
  engineering object. It is topology only and carries no engineering properties.
- The physical piping graph is expressed beside that topology, not inside it
  (ADR-0011): `PipingModel` groups realizations into `PipingLine`s and
  `PipingSegment`s and references identified `Connection`s instead of restating
  endpoints, so adjacency is authored exactly once. An unreferenced
  `Connection`, a pipe-realized realization, and a direct realization are three
  distinguishable states, and `Connection` never absorbs pipe, segment, line,
  class, fluid, or DN data.
- Process-layer directed edges are `ProcessStream`s inside the standalone
  `ProcessModel` (ADR-0005), deliberately distinct from physical `Connection`s
  and from piping realization. Piping is valid with no `ProcessModel`, and no
  process object is required to resolve into the physical layer: process ↔
  physical realization (including its cardinality) remains an unresolved
  boundary.

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

- semantic model growth: further engineering concepts (the physical piping
  realization layer now ships; the next open representation questions are
  process ↔ physical realization and the piping concepts explicitly deferred by
  ADR-0011) and the YAML save path
- rendering polish: layout/label refinement and higher-fidelity symbol
  sourcing (the SVG + anchor contract and the initial `basic` process pack
  ship under `src/deepplant/assets/symbols/process/basic/`; a basic headless
  renderer already exists in `src/deepplant/render.py`)
- broader interoperability: only a narrow DEXPI 2.0 Process adapter exists
  (this spike, `src/deepplant/adapters/dexpi.py`); full DEXPI (energy/
  information flows, Plant/P&ID, further step classes), COMOS, AVEVA, and
  simulator adapters remain future work. The DEXPI **Plant/P&ID semantic
  boundary** is now established at the evidence level, and its physical-piping
  side is implemented: `Port` remains sufficient for DeepPlant's currently
  claimed physical-topology abstraction, `Connection` remains directed topology
  only, and instrumentation plus Plant/P&ID import stay unimplemented. The
  piping realization layer ships per
  [physical-piping-model.md](physical-piping-model.md) and ADR-0011:
  `PipingLine` / `PipingSegment` / `PipingRealization` reference identified
  `Connection`s, so `Connection` keeps its property-free topology meaning and
  gained canonical identity only. Process↔physical realization remains a
  separate unresolved boundary — see
  [dexpi-plant-pid-spike.md](dexpi-plant-pid-spike.md) and ADR-0010.
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
- [dexpi-process-spike.md](dexpi-process-spike.md)
- [dexpi-plant-pid-spike.md](dexpi-plant-pid-spike.md)
- [physical-piping-model.md](physical-piping-model.md)
- [workflow.md](workflow.md)
- [quality.md](quality.md)
- [decisions/index.md](decisions/index.md)
