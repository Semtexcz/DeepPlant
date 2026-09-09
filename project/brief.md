---
type: project-brief
status: draft
source_of_truth_for:
  - current-initiative
read_when:
  - discovery
  - definition
  - feature-planning
update_when:
  - scope-change
  - durable-project-learning
---

# Project Brief

## Context

DeepPlant is the first product implementing the broader idea of **Engineering as
Code** for process plants. It will grow into a Git-native semantic engineering
platform in which a process plant is represented by a machine-readable semantic
model that can be validated, versioned, diffed, reviewed, and rendered.

This repository currently ships the project foundation plus semantic vertical
slices: the minimal domain model (`PlantModel`, `Plant`, `Equipment`), the
topology slice (`Port`, `Connection`, reference validation), the standalone
process-domain model (`ProcessModel` with `ProcessStep[]`/`ProcessStream[]`),
canonical `ProcessStep.function` engineering semantics separated from
presentation symbol roles (ADR-0009; an explicitly resolved `symbol_role`
override boundary in the renderer), YAML load/save boundaries into typed
Pydantic models, strict structural and reference validation, a `deepplant
validate` command, the `basic` process symbol-pack contract, a headless
read-only process renderer, and a narrow DEXPI 2.x Process adapter spike
(`deepplant.adapters.dexpi`; see
[docs/dexpi-process-spike.md](../docs/dexpi-process-spike.md)). The interactive
editor, full DEXPI and other vendor adapters, and P&ID rendering do **not**
exist yet.

## Problem

Process plant engineering data is scattered across drawings (PFD/P&ID), line
lists, datasheets, and documents. Engineering intent is encoded as graphics
(symbols, coordinates, routing) rather than as explicit semantic statements, so
it cannot be validated, diffed, or reused reliably. Drawings become the source
of truth by accident.

DeepPlant addresses the first step of this problem: represent a process plant as
a semantic engineering model serialized as YAML, validate its structure, and
later derive drawings and other views from the model.

## Target Users

- Process and piping engineers who author and review PFD/P&ID content.
- Engineering software integrators who need a machine-readable plant model.
- Engineering organizations that want Git-native review, CI, and validation for
  engineering deliverables.

Interactive GUI, simulation, and DEXPI consumers are future users, not bootstrap
targets.

## Desired Outcome

A validated, versionable semantic model of a process plant where CLI tools,
renderers, DEXPI adapters, simulation adapters, and AI agents all depend on the
model — never the reverse.

Milestone 1 so far: DeepPlant loads a small process model from YAML, reports
structural errors through the CLI, and validates `Connection` references against
equipment-owned `Port` objects.

## Main Use Case

An engineer writes a small process fragment as YAML, loads it with the DeepPlant
CLI, and receives a clear validation report for structural and reference errors
(unknown components or ports in connections).

## Scope

- In scope (done): clean, tested project foundation; durable DeepPlant
  documentation; ADRs for the core architecture principles; minimal CLI package.
- In scope (second semantic vertical slice): equipment-owned `Port` objects;
  top-level `Connection` objects over structured `PortRef(component, port)`
  endpoints; reference validation (endpoint components and ports must exist);
  strict unknown-field rejection extended to the new models; CLI reports
  equipment, port, and connection counts; runnable
  `examples/minimal-process/plant.yaml`.
- Out of scope (so far): pipes/pipelines/streams/signal semantics and their
  canonical representation, `Pipeline`, `Instrument`, full tag naming standards,
  fixed equipment taxonomy, YAML save, rendering, DEXPI, interactive editor,
  simulators, databases, ORMs, network services, and container runtimes.

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
- Long-term vision lives in `docs/product.md`; the two-level roadmap (current
  implementation vs directional capability) lives in `docs/roadmap.md`. The
  directional roadmap is product context, not implementation authorization:
  implement only the currently scoped vertical slice.

## Risks

- Designing taxonomy, tag standards, or schema fields from habit instead of from
  needed semantics. The next model growth (starting with the open
  pipes/streams representation question) must be driven by real example
  fragments.

