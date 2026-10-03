---
type: project-brief
status: active
canonical_for:
  - current-initiative
read_when:
  - discovery
  - definition
  - feature-planning
update_when:
  - scope-change
  - durable-project-learning
depends_on: []
decision: []
evidence: []
superseded_by: null
---

# Project Brief

## Context

DeepPlant is the first product implementing the broader idea of **Engineering as
Code** for process plants. It will grow into a Git-native semantic engineering
platform in which a process plant is represented by a machine-readable semantic
model that can be validated, versioned, diffed, reviewed, and rendered.

This repository currently ships the project foundation plus semantic vertical
slices: the physical/plant model (equipment-owned ports, identified directed
connections, reference validation), the physical piping-realization layer
(ADR-0011), the standalone process-domain model with canonical
`ProcessStep.function` semantics (ADR-0009), YAML load/save into typed Pydantic
models, the `deepplant validate` command, the `basic` process symbol-pack
contract, a headless read-only process renderer, and a narrow DEXPI 2.0.0 Process
adapter. The interactive editor, full DEXPI and other vendor adapters,
instrumentation semantics, engineering rules, and P&ID rendering do **not** exist
yet.

Current implementation facts are owned by the contracts and the architecture
boundary map, not by this brief:

- [docs/dev/architecture/index.md](../docs/dev/architecture/index.md) — what exists and its module
  boundaries;
- [docs/contracts/index.md](../docs/contracts/index.md) — current model, format,
  CLI, renderer, and adapter obligations;
- [docs/dev/planning/roadmap.md](../docs/dev/planning/roadmap.md) — current state, next direction, and
  unresolved evidence gaps.

## Problem

Process plant engineering data is scattered across drawings (PFD/P&ID), line
lists, datasheets, and documents. Engineering intent is encoded as graphics
(symbols, coordinates, routing) rather than as explicit semantic statements, so
it cannot be validated, diffed, or reused reliably. Drawings become the source
of truth by accident.

DeepPlant addresses this through an explicit semantic engineering model,
serialized as YAML, that can be validated, versioned, and used to derive and
interactively edit bounded engineering views without making drawings the source
of truth.

## Target Users

- Process and piping engineers who author and review PFD/P&ID content.
- Engineering software integrators who need a machine-readable plant model.
- Engineering organizations that want Git-native review, CI, and validation for
  engineering deliverables.

The Engineering Editor MVP v0.1 makes process and piping engineers interactive
editor users now; the GUI is a product target, not an implemented capability.
Simulation and broader DEXPI consumers remain outside this MVP.

## Desired Outcome

A validated, versionable semantic model of a process plant where CLI tools,
renderers, DEXPI adapters, simulation adapters, and AI agents all depend on the
model — never the reverse.

Milestone 1 so far: DeepPlant loads a small process model from YAML, reports
structural errors through the CLI, and validates `Connection` references against
equipment-owned `Port` objects.

## Main Use Case

The current implemented use case is YAML authoring and CLI validation. The next
product use case is an engineer opening a local project, creating or editing a
bounded PFD graphically, realizing part of it physically, editing basic P&ID
equipment/piping, validating, saving semantic plus presentation state, and
reloading without loss. The GUI for this target does not exist yet.

## Scope

- In scope (done): clean, tested project foundation; durable DeepPlant
  documentation; ADRs for the core architecture principles; minimal CLI package.
- In scope (second semantic vertical slice): equipment-owned `Port` objects;
  top-level `Connection` objects over structured `PortRef(component, port)`
  endpoints; reference validation (endpoint components and ports must exist);
  strict unknown-field rejection extended to the new models; CLI reports
  equipment, port, and connection counts; runnable
  `examples/minimal-process/plant.yaml`.
- In scope (physical piping-realization slice, ADR-0011): required non-empty
  plant-unique `Connection.id`; optional `PlantModel.piping` owning
  `PipingLine` → `PipingSegment` → `PipingRealization`; closed
  `kind: pipe | direct` vocabulary defaulting to `pipe`; structural rules C1 and
  P1–P5; YAML load/save semantic round-trip; the realistic fragment's evidenced
  `P-101 → FV-101 → E-101` run realized as a pipe-realized line; focused
  synthetic coverage for `kind: direct`.
- Next product-definition scope: Engineering Editor MVP v0.1 — local-first,
  standalone, browser-based SPA launched locally; semantic-model-first,
  file-based, Git-native interactive editing over a deliberately bounded PFD and
  P&ID subset. Semantic, presentation/layout, and frontend-framework state must
  remain separate. The exact UI/UX and reuse-first GUI architecture remain the
  focused work of Issues #69 and #70; no GUI implementation exists yet.
- Out of scope for the MVP: cloud hosting, authentication, databases,
  collaboration, full instrumentation, simulation, 3D, complete DEXPI,
  HAZOP/SIS, and all EPC disciplines.
- Deferred semantic scope: mid-connection property breaks (`PropertyBreak`),
  a canonical `Pipe`/pipe-piece identity, `PipingComponent`, `Nozzle`/
  `PipingNode`, line/segment numbering standards, typed engineering quantities
  for DN/pressure/temperature, insulation/tracing/slope/test-circuit data,
  process ↔ physical realization, instrumentation and signal semantics, and
  `Pipeline`/`Instrument` as further concepts; rendering, DEXPI Plant
  import/export, interactive editor, simulators, databases, ORMs, network
  services, and container runtimes.

## Success Criteria

- `deepplant --help` and `deepplant version` work from the installed entry point.
- `deepplant validate examples/minimal-process/plant.yaml` succeeds with concise
  output reporting the plant id, equipment count, port count, and connection
  count.
- Invalid YAML syntax, missing files, structurally invalid models, and invalid
  connection references exit non-zero with a clear message and no raw traceback.
- `make check` and `make build` pass.
- The documentation states the semantic-model-first architecture and the ADRs
  record the core decisions.

## Constraints and Assumptions

- The semantic engineering model is the product core; everything else depends on it.
- YAML is a serialization format, not the domain model.
- Presentation and rendering data stay separate from engineering semantics.
- Domain objects remain usable from Python and CLI without a GUI.
- Keep the dependency set minimal (Typer, Pydantic v2, PyYAML, pytest toolchain).
- Do not create empty architecture directories before real code exists.
- Planning authority is repository-led: `VISION.md` →
  `docs/dev/planning/product.md` → `docs/dev/planning/direction.md` →
  `docs/dev/planning/roadmap.md` → GitHub Issues → Pull Requests. The roadmap
  owns current priority/horizons and sequencing; the relevant GitHub Issue owns
  concrete executable scope; GitHub Project is a non-canonical visual projection.
  Documentation authority, audience, atomicity, and metadata conventions live in
  `docs/dev/workflow/conventions.md`; the documentation migration inventory
  lives in `docs/dev/workflow/documentation-migration.md`. Directional material
  is product context, not implementation authorization: implement only the
  currently scoped vertical slice.

## Risks

- Designing taxonomy, tag standards, or schema fields from habit instead of from
  needed semantics. Model growth (the next open questions are process ↔ physical
  realization and the piping concepts ADR-0011 explicitly deferred) must be
  driven by real example fragments.
- Writing engineering values into examples to make a feature look complete. The
  realistic fragment deliberately carries no DN, piping class, fluid code, line
  number, or segment number, and it does not claim a `kind: direct` adjacency
  merely to exercise the field.

