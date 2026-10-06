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

### Implemented baseline

DeepPlant currently ships the project foundation plus semantic vertical slices:
the physical/plant model (equipment-owned ports, identified directed
connections, reference validation), the physical piping-realization layer
(ADR-0011), the standalone process-domain model with canonical
`ProcessStep.function` semantics (ADR-0009), YAML load/save into typed Pydantic
models, the `deepplant validate` command, the `basic` process symbol-pack
contract, a headless read-only process renderer, a narrow DEXPI 2.0.0 Process
adapter, and the runnable, read-only Process/PFD editor slice
(the `src/deepplant/editor/` application boundary plus the `apps/editor/` SPA,
launched with `deepplant ui <path>`). The editor ships as a self-contained
graphical application on Windows and Linux: `deepplant-editor` opens a native
desktop window with an embedded webview rendering the same `apps/editor/` SPA,
and since Issue #97 it launches directly into that ordinary shared workspace with
`active project = none` rather than a native start page
(PR #92 established the distribution foundation; Issue #93, merged through PR #95,
delivered the native desktop host). The editor HTTP transport is an optional `deepplant[editor]` extra
and the native host an optional `deepplant[desktop]` extra, so the semantic Core
stays installable without either.

Current implementation facts are owned by the contracts and the architecture
boundary map, not by this brief:

- [docs/dev/architecture/index.md](../docs/dev/architecture/index.md) — what exists and its module
  boundaries;
- [docs/contracts/index.md](../docs/contracts/index.md) — current model, format,
  CLI, renderer, and adapter obligations;
- [docs/dev/planning/roadmap.md](../docs/dev/planning/roadmap.md) — current state, operational priority,
  and unresolved evidence gates.

### Current initiative

**Engineering Editor MVP** is the current product initiative: a local-first,
standalone editor that lets process and piping engineers interactively author a
bounded PFD and P&ID subset — with bidirectional YAML editing — while the semantic
model remains authoritative. Its definition is in
[docs/dev/planning/product.md](../docs/dev/planning/product.md), and it is pursued
through the product milestones in
[docs/dev/planning/roadmap.md](../docs/dev/planning/roadmap.md).

Delivered so far (the Foundation milestone): the read-only Process/PFD editor
(Issue #75), launched with `deepplant ui <path>`; the canonical frontend
engineering contract and quality gates (#80 → #81 → #82); independent DeepPlant
Core and standalone Windows/Linux distribution (Issue #85: the PR #92
distribution foundation and the Issue #93 native desktop host, merged through PR
#95); and the empty shared Editor workspace with `active project = none`
(Issue #97).

Not yet implemented: professional application-shell UX, semantic editing,
bidirectional YAML editing, presentation persistence, and P&ID authoring. The
UI/UX interaction architecture (Issue #69,
[docs/dev/research/engineering-editor-ux.md](../docs/dev/research/engineering-editor-ux.md)),
the reuse-first frontend architecture (Issue #70,
[docs/dev/research/engineering-editor-reuse-architecture.md](../docs/dev/research/engineering-editor-reuse-architecture.md)),
and the design-to-code workflow (PR #96,
[docs/dev/frontend/design-to-code.md](../docs/dev/frontend/design-to-code.md)) are
delivered as evidence/governance to be applied.

The active milestone is owned by
[docs/dev/planning/roadmap.md](../docs/dev/planning/roadmap.md); the next
implementation Issue is selected during ordinary refinement without a planning
gate ([planning/index.md](../docs/dev/planning/index.md)).

### Deferred / out-of-scope capabilities

The MVP excludes full instrumentation and signal semantics, broader piping detail
(property breaks, pipe-piece identity, components, nozzles/nodes, detailed
numbering, qualified quantities, insulation, tracing, slope, and test circuits),
simulation, 3D, complete DEXPI and other vendor adapters, HAZOP/SIS, cloud or
collaboration services, and all EPC disciplines. These are capability context or
future evidence questions, not current implementation authorization.

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

The Engineering Editor MVP makes process and piping engineers interactive
editor users; the interactive authoring capability is a product target, not an
implemented capability. Simulation and broader DEXPI consumers remain outside
this MVP.

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

### Implemented baseline

- Clean, tested project foundation; durable DeepPlant documentation; ADRs for the
  core architecture principles; minimal CLI package.
- Equipment-owned `Port` objects; top-level `Connection` objects over structured
  `PortRef(component, port)` endpoints; reference validation; strict unknown-field
  rejection; CLI counts; and runnable `examples/minimal-process/plant.yaml`.
- The ADR-0011 physical piping-realization slice: required non-empty
  plant-unique `Connection.id`; optional `PlantModel.piping` owning
  `PipingLine` → `PipingSegment` → `PipingRealization`; closed `kind: pipe |
  direct` vocabulary; structural rules C1 and P1–P5; YAML semantic round-trip;
  and focused examples/tests.

### Current initiative

Engineering Editor MVP is a local-first, standalone editor for
semantic-model-first, file-based, Git-native interactive authoring of a
deliberately bounded PFD and P&ID subset, with bidirectional YAML editing.
Semantic, presentation/layout, and frontend-framework state must remain
separate. The MVP must not assume manual YAML editing for its core workflow. The
first executable slice (Issue #75) is delivered as a **read-only** Process/PFD
editor; semantic editing, bidirectional YAML editing, presentation persistence,
and P&ID authoring are still unimplemented. The MVP is pursued through the
product milestones in
[docs/dev/planning/roadmap.md](../docs/dev/planning/roadmap.md).

### Deferred / out-of-scope capabilities

- Full instrumentation, control loops, and signal semantics.
- Broader physical piping detail, including mid-connection property breaks,
  canonical pipe/pipe-piece identity, piping components, nozzles/nodes, detailed
  numbering, qualified quantities, insulation, tracing, slope, and test circuits.
- Simulation, 3D, complete DEXPI and other vendor adapters, HAZOP/SIS, cloud
  hosting, authentication, databases, collaboration, and all EPC disciplines.
- An implemented process ↔ physical realization mapping: ADR-0016 decides the
  future cross-layer ownership boundary, but no schema or runtime mapping exists.

## Success Criteria

### Implemented baseline / existing success criteria

- `deepplant --help` and `deepplant version` work from the installed entry point.
- `deepplant validate examples/minimal-process/plant.yaml` succeeds with concise
  output reporting the plant id, equipment count, port count, and connection
  count.
- Invalid YAML syntax, missing files, structurally invalid models, and invalid
  connection references exit non-zero with a clear message and no raw traceback.
- `make check` and `make build` pass.
- The documentation states the semantic-model-first architecture and the ADRs
  record the core decisions.

### Current initiative success criteria

- A local-first interactive editor supports the bounded MVP PFD and P&ID
  authoring workflow without requiring manual YAML editing for the core path.
- The semantic model remains authoritative while PFD and P&ID stay bounded views
  over their distinct semantic layers.
- Validation is available from the editor workflow.
- Semantic and presentation state persist separately and save/reload without loss
  of semantic intent or presentation state.
- The MVP remains file-based and Git-native without requiring hosted services.

## Constraints and Assumptions

- The semantic engineering model is the product core; everything else depends on it.
- YAML is a serialization format, not the domain model.
- Presentation and rendering data stay separate from engineering semantics.
- Domain objects remain usable from Python and CLI without a GUI.
- Keep the dependency set minimal (Typer, Pydantic v2, PyYAML, pytest toolchain).
  FastAPI and Uvicorn are confined to the optional `deepplant[editor]` extra and
  must never become base dependencies again; the native desktop host
  (PySide6/Qt WebEngine) is confined to the optional `deepplant[desktop]` extra
  and the uv `desktop` group, which is never part of `make setup`/`make check`;
  PyInstaller, Inno Setup, and `appimagetool` are build-time-only and must never
  become runtime dependencies (Issue #85).
- Do not create empty architecture directories before real code exists.
- Planning authority is repository-led and milestone-driven: `VISION.md` →
  `docs/dev/planning/strategy.md` → `docs/dev/planning/product.md` →
  `docs/dev/planning/roadmap.md` → GitHub Issues → Pull Requests. The roadmap
  owns the product milestones and the single active outcome; `direction.md` owns
  long-term capability progression (context, not authorization); the relevant
  GitHub Issue owns concrete executable scope. Creating an Issue does not
  authorize implementation, and the next Issue is selected without a planning
  gate (`docs/dev/planning/index.md`). GitHub Project may visualize derived
  groupings but is a non-canonical projection. Documentation authority,
  audience, atomicity, and metadata conventions live in
  `docs/dev/workflow/conventions.md`; the documentation migration inventory
  lives in `docs/dev/workflow/documentation-migration.md`. Milestone material is
  product context, not implementation authorization: implement only the
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

