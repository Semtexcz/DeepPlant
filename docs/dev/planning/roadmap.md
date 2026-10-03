---
type: roadmap
status: active
canonical_for:
  - current-implementation-roadmap
read_when:
  - roadmap-change
  - feature-planning
  - next-task-selection
depends_on:
  - docs/contracts/index.md
  - docs/dev/architecture/index.md
  - docs/dev/planning/index.md
decision: []
evidence: []
superseded_by: null
---

# Roadmap

> **Primary question:** What is DeepPlant's current execution-planning state?

It answers that question through three aspects:

1. **Current state** — a short summary; canonical facts live in
   [contracts/](../../contracts/index.md) and [architecture.md](../architecture/index.md).
2. **Immediate operational sequence** — the authorized next work and its order.
3. **Unresolved evidence gaps** — questions whose evidence must precede another
   executable task.

It contains no dates, estimates, release promises, fixed sequence commitments, or
completion percentages; GitHub Issues remain the place for executable tasks.
Detailed completion records live in
[history/implementation-slices.md](../history/implementation-slices.md), the
long-term capability progression in [direction.md](direction.md), and planning
governance in [planning.md](index.md). This document is the canonical source for
current operational priority and horizons; GitHub Issues own detailed scope for
concrete executable work.

## Current State

DeepPlant ships a Python CLI package (`src/deepplant/`) implementing:

- the physical/plant model and its validation contract
  ([contracts/plant-model.md](../../contracts/plant-model.md));
- the process graph ([contracts/process-model.md](../../contracts/process-model.md));
- physical piping realization over identified connections
  ([contracts/physical-piping.md](../../contracts/physical-piping.md));
- YAML load/save ([contracts/yaml-format.md](../../contracts/yaml-format.md)) and the
  `validate` CLI ([contracts/cli.md](../../contracts/cli.md));
- the basic headless read-only process renderer ([contracts/rendering.md](../../contracts/rendering.md))
  and the `basic` SVG symbol-pack contract ([dev/reference/svg-symbols.md](../reference/svg-symbols.md));
- the narrow DEXPI 2.0.0 Process adapter
  ([dev/reference/dexpi-process-adapter.md](../reference/dexpi-process-adapter.md)).

Not implemented: full DEXPI and Plant/P&ID import/export, other vendor adapters
(COMOS, AVEVA), instrumentation and signal semantics, engineering rules, P&ID
rendering, and the interactive editor. The authoritative boundary map, including
directional-but-unimplemented components, is [architecture.md](../architecture/index.md).

## Completed

Delivered slices are recorded in
[history/implementation-slices.md](../history/implementation-slices.md) and, for
evidence-heavy slices, in the linked spike/decision documents.

## Operational Roadmap

### Now

- **No executable implementation slice is selected.** Issue #39 delivered its
  evidence and durable ownership decision —
  [process-physical-realization-boundary.md](../research/process-physical-realization-boundary.md)
  and [ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md) —
  and no process ↔ physical mapping is implemented. Issue #69 delivered its UI/UX
  interaction architecture
  ([engineering-editor-ux.md](../research/engineering-editor-ux.md)), and Issue #70
  has since delivered the reuse-first frontend architecture
  ([engineering-editor-reuse-architecture.md](../research/engineering-editor-reuse-architecture.md)):
  a small, replaceable stack — Vue 3 + TypeScript + Vite, Vue Flow for the canvas
  behind a DeepPlant projection/adapter, and Reka UI primitives — with docking,
  text editing, layout/routing, and state-management libraries deferred, each with
  an adoption trigger. Issue #70 authorizes no GUI implementation, dependency, or
  directory and selects no executable slice. The candidate set is re-evaluated from
  this completed evidence at the gate below; no successor task is preselected.

### Next

- **Re-evaluate the roadmap and select the smallest executable vertical slice.**
  The evidence prerequisites (#39, #69, and #70) are complete. The next planning
  action is to re-evaluate the current repository state and select the smallest
  executable vertical slice. This is a planning step, not an implementation slice:
  it preselects nothing, creates no Issue by itself, and adds no dependency or
  directory.

### Re-evaluation Gate

The evidence prerequisites for the re-evaluation gate are now complete (#39, #69,
and #70 delivered). The next planning action is to re-evaluate the current
repository state and select the smallest executable vertical slice. This gate is
**ready**; the re-evaluation itself is not performed by Issue #70. Do not create
speculative implementation Issues before that re-evaluation, and do not
mechanically promote an existing backlog row. Select from the actual repository
state, those Issues' conclusions, accepted ADRs, unresolved evidence gaps, a
realistic executable example, and a concrete DeepPlant-native consumer. Quantity
implementation, DEXPI 2.0.1, port kinds, PFD/P&ID GUI, rules, and semantic diff
remain unpromoted.

### Completed Context

- **Issue #68 is delivered:** the Engineering Editor MVP v0.1 is bounded in
  [product.md](product.md), including the PFD/P&ID subsets, semantic
  source-of-truth interaction direction, user journey, non-goals, and Issue
  #39 relationship. It authorizes no GUI implementation.
- **Issue #69 delivered design/evidence:** the minimalist Engineering Editor
  UI/UX interaction architecture is recorded in
  [research/engineering-editor-ux.md](../research/engineering-editor-ux.md)
  (canvas-dominant minimum permanent chrome, one command direction, four
  separated state kinds, engineering-concept explorer, PFD/P&ID editor views,
  cardinality-neutral related-object navigation, shared command surface, and the
  MVP/later/not-now UX matrix). It creates no ADR and authorizes no GUI
  implementation, dependency, or `frontend/` directory.
- **Issue #70 delivered design/evidence:** the reuse-first Engineering Editor
  frontend architecture is recorded in
  [research/engineering-editor-reuse-architecture.md](../research/engineering-editor-reuse-architecture.md).
  It selects a small replaceable stack (Vue 3 + TypeScript + Vite foundation; Vue
  Flow as the preferred canvas candidate behind a DeepPlant projection/adapter;
  Reka UI primitives) and defers/rejects docking (Dockview), text editing (Monaco),
  layout/routing (ELK/elkjs), a state manager (Pinia), general utilities (VueUse),
  and the shadcn-vue / X6 / Cytoscape.js alternatives, each with a recorded
  adoption trigger. It keeps semantic/presentation/framework state separated,
  places undo/redo at the application-command boundary, reuses the existing
  renderer and SVG symbol contract, creates no ADR, and authorizes no GUI
  implementation, dependency, or `frontend/` directory.
- **Issue #39 delivered decision/evidence:** the process ↔ physical realization
  ownership boundary is decided by
  [process-physical-realization-boundary.md](../research/process-physical-realization-boundary.md)
  and [ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md);
  no implementation slice or successor is selected.
- **Issue #20 is delivered:** the auditable DEXPI 2.0.0 supported-subset and
  semantic round-trip contract is published in
  [dev/reference/dexpi-process-adapter.md](../reference/dexpi-process-adapter.md).
- **Issue #32 delivered decision/evidence:** the separate qualified-engineering
  quantity boundary is decided in
  [research/qualified-engineering-quantities.md](../research/qualified-engineering-quantities.md)
  and [ADR-0013](../decisions/ADR-0013-qualified-engineering-quantity-boundary.md).
- **Issue #21 is closed:** its `StoringMaterial` topic remains historical or
  deferred strategic/evidence context, not an open executable Issue.

### Scope Discipline

- No hosted/cloud backend, authentication, database, ORM, collaboration
  service, containers, or production server infrastructure before a concrete
  requirement justifies them.
- A minimal local application/transport/API boundary required by the selected
  standalone SPA vertical slice may be introduced when that executable slice
  authorizes it; no framework is selected here.
- No empty architecture trees, frontend directories, or GUI dependencies before
  a current executable slice requires them.
- No full instrumentation, simulation, 3D, complete DEXPI, HAZOP/SIS, or all
  EPC disciplines in the Engineering Editor MVP v0.1.
- Semantic state remains distinct from presentation/layout state and
  frontend-framework state; YAML remains serialization, not the domain model.
- `Connection` is topology only; do not attach pipe/stream/signal engineering
  semantics until a real requirement justifies them.

## Directional Capability Roadmap

The long-term capability progression (stages, goals, dependencies, and their
deliberately open questions) is recorded in [direction.md](direction.md). It is
product context, not implementation authorization; the anti-roadmap below
governs what may be built now.

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
- the Engineering Editor MVP direction does not justify GUI implementation,
  dependencies, or frontend structure before its scoped executable slice
- the multi-discipline stage does not justify generic entity hierarchies now
- the DEXPI stage does not justify DEXPI-shaped domain objects now
- the physical-piping realization question and the separate process ↔ physical
  realization question do not justify attaching pipe or process-stream semantics
  to `Connection` now — and the decided piping layer (ADR-0011) honours that by
  referencing identified connections instead of widening `Connection`

Think broadly about the destination. Build narrowly in the current iteration.
