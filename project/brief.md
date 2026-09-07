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

This repository currently ships the project foundation plus the first semantic
vertical slice: a minimal domain model (`PlantModel`, `Plant`, `Equipment`), a
YAML loading boundary into typed Pydantic models, structural validation, and a
`deepplant validate` command. Rendering, adapters, DEXPI, and the interactive
editor do **not** exist yet.

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

Milestone 1 so far: DeepPlant loads a small process model from YAML and reports
structural errors through the CLI. Reference validation comes with
`Port`/`Connection` in the next iteration.

## Main Use Case

The first vertical slice: an engineer writes a small process fragment as YAML,
loads it with the DeepPlant CLI, and receives a clear validation report for
structural errors. Reference errors are the next slice.

## Scope

- In scope (done): clean, tested project foundation; durable DeepPlant
  documentation; ADRs for the core architecture principles; minimal CLI package.
- In scope (first semantic vertical slice): minimal domain model (`PlantModel`,
  `Plant`, `Equipment`); YAML load boundary into typed Pydantic models;
  structural validation (non-empty ids, unique equipment ids); `deepplant
  validate <path>`; runnable `examples/minimal-process/plant.yaml`.
- Out of scope (this slice): `Port`, `Connection`, `Pipeline`, `Instrument`,
  reference validation, full tag naming standards, fixed equipment taxonomy,
  YAML save, rendering, DEXPI, interactive editor, simulators, databases, ORMs,
  network services, and container runtimes.

## Success Criteria

- `deepplant --help` and `deepplant version` work from the installed entry point.
- `deepplant validate examples/minimal-process/plant.yaml` succeeds with concise
  output reporting the plant id and equipment count.
- Invalid YAML syntax, missing files, and structurally invalid models exit
  non-zero with a clear message and no raw traceback.
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

## Risks

- Designing taxonomy, tag standards, or schema fields from habit instead of from
  needed semantics. The next model growth must be driven by real example
  fragments (`Port`, `Connection`, and references).

