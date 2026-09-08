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

This file distinguishes two levels:

- **Current Implementation Roadmap** — the actionable near-term plan that
  decides the next PR. It preserves completed work and the current state.
- **Directional Capability Roadmap** — long-term product context: capability
  progression and dependencies, not a delivery calendar, a fixed build order, or
  an implementation authorization.

This file contains no dates, estimates, release promises, fixed sequence
commitments, or completion percentages. GitHub Issues remain the place for
executable tasks.

## Current Implementation Roadmap

DeepPlant ships the project foundation plus four semantic vertical slices:

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
- standalone process-domain model: `ProcessModel` owning `ProcessStep[]` with
  `ProcessPort[]`, plus `ProcessStream[]` over `ProcessRef(step, port)`
  endpoints; structural rules S1–S4; independently constructible and valid in
  Python
- root/loadable process-model integration: `PlantModel.process: ProcessModel |
  None`; a YAML `process` section with `steps`/`streams` loads through the
  existing `load_plant` boundary into the typed submodel; missing `process` and
  `process: null` mean no authored process model, while `process: {}` is an
  explicitly empty `ProcessModel`; S1–S4 remain owned by `ProcessModel` and
  no cross-layer mappings or validation exist
- canonical YAML save / semantic round-trip: `save_plant()` serializes a
  `PlantModel` through Pydantic (`exclude_none`) into canonical, deterministic
  YAML that the existing `load_plant()` reads back as a semantically equal
  model; `process: None` is omitted while an explicitly empty `ProcessModel`
  stays present; formatting, comments, and quoting are not preserved

`Connection` is currently a directed semantic topological relationship from
`source` to `target`; it remains topology only and is not yet a pipe, process
stream, signal, cable, or physical line. Work proceeds as small vertical
changes with executable tests. `PlantModel` owns zero or one `ProcessModel`
under `process`; the loader populates it from YAML and `save_plant()` writes
canonical YAML that `load_plant()` reads back into a semantically equal model.
Round-trip is semantic (`load(save(model)) == model`), not byte-preserving.
Process and physical graphs stay independently valid: process step/port ids
never imply equipment, and no cross-layer rules exist yet.

### Completed

| Item | Notes |
|---|---|
| Define `PlantModel` | Root container and composition of the model |
| Define `Plant` | Plant identity: `id`, `name` |
| Define `Equipment` | Engineering objects: `id`, `type`, `name`, owned `Port[]`; no fixed taxonomy yet |
| Define `Port` | Typed connection points owned by equipment; id local to the owning equipment |
| Define `PortRef` | Structured endpoint reference: `component` + `port` |
| Define `Connection` | Directed semantic topology only: `source`/`target` as `PortRef(component, port)`; not a pipe/stream/signal/physical line yet |
| Reference validation | Connections resolve to existing equipment and owned ports; referential integrity only |
| YAML load | YAML as serialization, validated via Pydantic into the domain model |
| Semantic validation (structural) | Non-empty ids; unknown fields rejected; unique equipment ids; unique port ids per equipment |
| First executable example | `examples/minimal-process/plant.yaml` runs through the CLI |
| Decide process-model container | ADR-0005 accepted (C1): `PlantModel` remains the overall aggregate; one independently valid `ProcessModel` owns the process graph and the S1–S4 validation boundary |
| Define `ProcessModel` | Standalone process-domain container owning `ProcessStep[]` and `ProcessStream[]`; step and stream ids are separate namespaces (S1); not yet part of `PlantModel` |
| Define `ProcessStep` / `ProcessPort` | Process steps with `id`, open non-empty `type`, `name`, owned `ProcessPort[]`; process-port ids local to the owning step (S2) |
| Define `ProcessRef` / `ProcessStream` | `ProcessRef(step, port)` endpoints; binary directed `ProcessStream` with `id`, optional `name`; no flow/designation/physical semantics |
| Process structural validation | S1 duplicate step/stream ids rejected; S3 endpoints resolve to process steps and owned process ports; S4 identical source/target endpoints rejected; cycles/recycle/mixing/splitting structurally allowed; no dependency on `Equipment`/`Port`/`Connection` |
| Integrate `ProcessModel` into the root/loadable model | `PlantModel.process: ProcessModel \| None`; YAML `process` section (`steps`, `streams`) loads through the existing loader; missing `process` and `process: null` load as no process model, `process: {}` as an empty one; S1–S4 stay on the process-domain models; process and physical ids remain separate namespaces; root/YAML shape recorded in ADR-0006 |
| YAML save / semantic round-trip | Canonical `save_plant()` through Pydantic `model_dump(exclude_none=True)` + PyYAML (`sort_keys=False`, `allow_unicode=True`); `load_plant(save_plant(model)) == model`; `None` optionals omitted; `process: None` omitted; explicit empty `ProcessModel` preserved; deterministic field order; UTF-8 with a trailing newline; comments/formatting not preserved; no domain-model changes; no CLI save/format command |

### Backlog (Suggested Order)

The process fragment is documented in
[process-fragment-prototype.md](process-fragment-prototype.md). ADR-0005 is
accepted: `PlantModel` remains the overall aggregate while one independently
valid `ProcessModel` owns the process graph and defines the S1–S4
reference-validation boundary. The root/loadable integration and the canonical
YAML save/round-trip are implemented (see Completed):
`PlantModel.process: ProcessModel | None`, YAML loading of the `process`
section (ADR-0006), and a deterministic `save_plant()` whose output
`load_plant()` reads back into a semantically equal model. The next task is
the first row below.

| # | Item | Note |
|---|---|---|
| 1 | SVG symbol specification | Deliberate symbol/geometry/layout spec, separate from semantics (ADR-0003); prerequisite for the renderer |
| 2 | Basic renderer | Derive a simple PFD/P&ID-like drawing from the model using the symbol spec |
| 3 | DEXPI adapter spike | Prove import/export feasibility on a real fragment |

### Milestones

### Milestone 1 — validated YAML load

> DeepPlant can load a small process model from YAML, validate its semantic
> structure and report invalid references through the CLI.

Complete: structural validation and reference validation ship in the first two
slices.

### Milestone 2 — prototype fragment and renderer

> DeepPlant can represent a real process fragment of roughly 20–50 engineering
> objects, render it as a basic PFD/P&ID-like diagram and validate at least 10
> classes of engineering/model consistency errors.

### Next Task

The next task is the SVG symbol specification (first backlog row above).
Rendering is deliberately not started directly after YAML save: the roadmap and
architecture keep presentation strictly separate from semantics (ADR-0003), and
a renderer slice needs explicit symbol, geometry, port-anchoring, and layout
semantics before any drawing code is evidence-producing. The symbol
specification is the smallest next deliverable on that path; the subsequent
basic renderer slice (second backlog row) will consume it and derive a simple
PFD/P&ID-like drawing from an existing example. Canonical `save_plant()` now
gives those slices a deterministic authoring surface (`load` -> edit in Python
-> `save`), but no renderer or CLI save/format command ships in this PR.
Multiplicity beyond zero-or-one `ProcessModel` per plant remains deferred
(ADR-0005).

### Scope Discipline

- No database, ORM, web backend, containers, or external services.
- No empty architecture trees before real code exists.
- Schema and model design come from real example fragments, not abstraction.
- `Connection` is topology only; do not attach pipe/stream/signal engineering
  semantics until a real requirement justifies them.

## Directional Capability Roadmap

The stages below describe where DeepPlant may ultimately go. They are
**directional**: hypotheses about capability progression and dependencies, not
dates, release promises, commitments, or a guaranteed build order. A stage is
implemented only when its text says so; its presence never authorizes building
its architecture today (see the Anti-Roadmap at the end of this file).

The overall direction in one picture:

```text
Semantic plant model
        ↓
Topology and relationships
        ↓
Process streams / piping semantics
        ↓
PFD / P&ID rendering
        ↓
Interactive engineering editor
        ↓
Git diff / CI / engineering review
        ↓
Standards and DEXPI interoperability
        ↓
Engineering validation and rules
        ↓
Simulation and calculation adapters
        ↓
Safety / HAZOP / SIS workflows
        ↓
Multi-discipline engineering
        ↓
AI-assisted engineering workflows
```

The map is directional, not an implementation order.

### Stage 1 — Semantic Core

Goal: represent basic engineering objects explicitly and validate their
structure. Example concepts: `Plant`, `Equipment`, `Ports`, `Connections`,
identity, references.

Relationship to today: the core primitives of Stage 1 are implemented on
`main` — `PlantModel`, `Plant`, `Equipment`, equipment-owned `Port`,
`PortRef`, directed `Connection`, reference validation, YAML load, and
strict structural validation. Implemented primitives are not the same as a
completed capability stage: the Stage 1 exit signal below has not yet been
demonstrated on a real process fragment. The open pipes / process-stream
representation question — the first item on the Current Implementation
Roadmap above — is the next semantic decision.

Exit signal:

> A small real process fragment can be represented faithfully enough to be
> useful outside the original drawing.

### Stage 2 — Process Topology

Goal: represent meaningful connectivity and distinguish different engineering
relationship concepts.

Open questions (deliberately unresolved here):

- process stream vs pipe vs generic connection
- equipment nozzles
- instrumentation connectivity
- utilities

### Stage 3 — Engineering Views

Goal: derive human-readable engineering diagrams from the semantic model.
Likely capabilities: PFD rendering, P&ID rendering, symbol library,
presentation/layout model, manual layout override. Semantic and presentation
models stay separate.

### Stage 4 — Interactive Editing

Goal: let engineers modify the semantic model graphically without making the
drawing the source of truth. Potential surfaces: PFD/P&ID editor, property
editor, symbol placement, connection editing. Directional only; it does not
justify web architecture now.

### Stage 5 — Git-native Engineering Workflow

Goal: make semantic change review a first-class engineering workflow. Potential
capabilities: semantic diff, CI validation, PR review, model consistency checks,
generated reports.

### Stage 6 — Standards and Interoperability

Goal: exchange models with established engineering ecosystems (DEXPI, COMOS,
AVEVA, and other engineering tools).

Invariant:

> External representations are adapters, not the canonical DeepPlant model.

### Stage 7 — Engineering Rules

Goal: automate deterministic engineering checks. Examples may eventually
include: reference integrity, required properties, topology consistency, company
engineering rules, and selected standards checks. No standards compliance is
claimed that is not implemented.

### Stage 8 — Simulation and Calculations

Goal: connect semantic plant data to calculation and simulation tools. Potential
targets: DWSIM, SysCAD, the CAPE-OPEN ecosystem, and specialized engineering
calculations. The canonical model must not become simulator-specific.

### Stage 9 — Process Safety

Directional only. Potential future capabilities: HAZOP support, safeguards,
SIS / SIL concepts, reliability structures, and traceability between hazards and
safeguards. Nothing here implies automated safety approval.

### Stage 10 — Multi-discipline Engineering

Potential future expansion: process, mechanical, instrumentation, control,
electrical, documents, and requirements. The generic
`Component -> Port -> Connection` direction may eventually support multiple
disciplines, but that does not justify generalizing today's code.

### Stage 11 — AI-assisted Engineering

Goal: agents operate on the same explicit semantic engineering model as
engineers. A future workflow might be:

```text
Engineer:
"Add a standby pump parallel to P-101."

Agent:
changes semantic model
        ↓
Git diff
        ↓
validation
        ↓
updated engineering views
        ↓
human review
```

AI should operate through explicit engineering models and validation rather than
silently editing opaque documents.

## Anti-Roadmap — What Must Not Be Implemented Prematurely

> The directional roadmap provides product context, not implementation
> authorization. Implement only the currently scoped vertical slice.
>
> A future stage appearing in the roadmap is not sufficient justification to
> introduce its architecture today.
>
> Do not add abstractions, dependencies, or infrastructure for future stages
> until a current vertical slice requires them.

Concrete examples:

- the simulation stage does not justify simulator interfaces now
- the editor stage does not justify web architecture now
- the multi-discipline stage does not justify generic entity hierarchies now
- the DEXPI stage does not justify DEXPI-shaped domain objects now
- the open pipes/streams representation question does not justify attaching
  pipe or process-stream semantics to `Connection` now

Think broadly about the destination. Build narrowly in the current iteration.
