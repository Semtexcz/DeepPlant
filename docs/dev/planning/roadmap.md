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
  ([dev/reference/dexpi-process-adapter.md](../reference/dexpi-process-adapter.md));
- the first runnable, read-only Process/PFD editor slice
  ([architecture.md](../architecture/index.md#engineering-editor-slice-implemented)):
  a DeepPlant-owned Process/PFD projection (`src/deepplant/editor/projection.py`),
  a small loopback-only local boundary (`src/deepplant/editor/app.py`), the
  `deepplant ui <path>` launcher, and a Vue 3 + TypeScript + Vite + Vue Flow SPA
  under `frontend/` that serves pan, zoom, fit view, single selection, a
  read-only semantic Inspector, and the current validation status.

Not implemented: semantic editing and any semantic mutation command, presentation
persistence, undo/redo, P&ID rendering and physical/P&ID symbols, full DEXPI and
Plant/P&ID import/export, other vendor adapters (COMOS, AVEVA), instrumentation
and signal semantics, engineering rules, and the process ↔ physical realization
mapping. The authoritative boundary map, including
directional-but-unimplemented components, is [architecture.md](../architecture/index.md).

## Completed

Delivered slices are recorded in
[history/implementation-slices.md](../history/implementation-slices.md) and, for
evidence-heavy slices, in the linked spike/decision documents.

## Operational Roadmap

### Now

- [#75 — Engineering Editor: first interactive Process/PFD vertical slice](https://github.com/Semtexcz/DeepPlant/issues/75)
  is **delivered by the current pull request**.

  What shipped is exactly the smallest runnable browser-based Process/PFD viewer
  over the existing DeepPlant Python semantic core and the realistic process
  fragment:

  ```text
  ProcessModel
      ↓
  DeepPlant-owned Process/PFD projection
      ↓
  replaceable frontend adapter
      ↓
  Vue Flow interactive canvas
  ```

  It is read-only: pan / zoom / fit / single selection / semantic Inspector /
  current validation status. It delivered no P&ID rendering, semantic editing,
  presentation persistence, undo/redo, process ↔ physical realization
  implementation, or broader frontend infrastructure. See
  [history/implementation-slices.md](../history/implementation-slices.md).

- No other slice is currently selected. The next action is the re-evaluation
  recorded under **Next**.

### Next

- Re-evaluate from the implementation evidence delivered by #75.

  Do not mechanically promote semantic editing, presentation persistence, P&ID,
  or another backlog item. Use the delivered slice to decide the next smallest
  slice, especially:

  - whether the projection/view boundary is strong enough to authorize the first
    semantic-editing slice;
  - whether the first mutation slice needs the minimum application-command
    machinery Issue #69 describes, and where undo/redo belongs;
  - whether presentation state (positions, per-step overrides) now needs its own
    explicit, non-semantic home;
  - what the editor's packaging/deployment story must be, given that the SPA
    assets are currently read from the checkout.

  The re-evaluation outcome is not decided by this PR, and no successor Issue is
  created here.

### Re-evaluation Gate

The previous re-evaluation gate was executed after #39, #69, and #70 were
delivered.

Outcome:
[#75 — Engineering Editor: first interactive Process/PFD vertical slice](https://github.com/Semtexcz/DeepPlant/issues/75)
was selected as the smallest executable slice, and is delivered by the current PR.

Process/PFD had the strongest complete executable substrate:

- `ProcessModel`
- structural validation
- realistic process example
- deterministic headless renderer
- Process/PFD SVG symbol/anchor contract
- completed UX architecture (Issue #69,
  [engineering-editor-ux.md](../research/engineering-editor-ux.md))
- completed reuse-first GUI architecture (Issue #70,
  [engineering-editor-reuse-architecture.md](../research/engineering-editor-reuse-architecture.md))

The physical/P&ID side does not yet have an equivalent physical presentation /
symbol contract, so the first GUI slice remains Process/PFD-only.

The process ↔ physical realization boundary evidence that preceded this gate is
[process-physical-realization-boundary.md](../research/process-physical-realization-boundary.md)
and [ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md).
Quantity implementation, DEXPI 2.0.1, port kinds, physical/P&ID GUI,
rules, and semantic diff remain unpromoted. No successor is preselected; selection follows
from the current repository state and the delivered evidence, not from a backlog
row.

A new re-evaluation is now required from the #75 implementation evidence; its
outcome is deliberately not decided here (see **Next**).

### Completed Context

- **Issue #75 is delivered:** the first runnable, read-only Process/PFD editor
  slice shipped — a DeepPlant-owned Process/PFD projection
  (`src/deepplant/editor/projection.py`), a small loopback-only local
  application boundary (`src/deepplant/editor/app.py`), the
  `deepplant ui <path>` launcher, and a Vue 3 + TypeScript + Vite + Vue Flow SPA
  under `frontend/`. It is read-only (pan/zoom/fit/selection/Inspector/validation
  status) and delivered no semantic editing, presentation persistence, undo/redo,
  P&ID rendering, or process ↔ physical realization. See
  [history/implementation-slices.md](../history/implementation-slices.md).
- **Issue #68 is delivered:** the Engineering Editor MVP v0.1 is bounded in
  [product.md](product.md), including the PFD/P&ID subsets, semantic
  source-of-truth interaction direction, user journey, non-goals, and Issue
  #39 relationship. It authorized no GUI implementation; the first GUI slice was
  later authorized by Issue #75.
- **Issue #69 delivered design/evidence:** the minimalist Engineering Editor
  UI/UX interaction architecture is recorded in
  [research/engineering-editor-ux.md](../research/engineering-editor-ux.md)
  (canvas-dominant minimum permanent chrome, one command direction, four
  separated state kinds, engineering-concept explorer, PFD/P&ID editor views,
  cardinality-neutral related-object navigation, shared command surface, and the
  MVP/later/not-now UX matrix). It created no ADR and authorized no GUI
  implementation, dependency, or `frontend/` directory; Issue #75 later
  introduced them within its own narrow scope.
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
  renderer and SVG symbol contract, created no ADR, and authorized no GUI
  implementation, dependency, or `frontend/` directory; Issue #75 later
  introduced those within its own narrow, read-only scope.
- **Issue #39 delivered decision/evidence:** the process ↔ physical realization
  ownership boundary is decided by
  [process-physical-realization-boundary.md](../research/process-physical-realization-boundary.md)
  and [ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md);
  no process ↔ physical realization implementation slice or successor is
  selected.
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
- A minimal local application/transport/API boundary is introduced only when the
  selected standalone SPA vertical slice authorizes it. #75 introduced exactly
  one: Python standard library `http.server`, loopback-only, read-only and
  replaceable, with **no new Python runtime dependency**. It is not a hosted,
  authenticated, or production service surface.
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
- GUI implementation, frontend structure, and dependencies are authorized only
  within the explicit scope of Issue #75, the currently selected executable
  slice; Issue #75 does not authorize broader Engineering Editor infrastructure
- the multi-discipline stage does not justify generic entity hierarchies now
- the DEXPI stage does not justify DEXPI-shaped domain objects now
- the physical-piping realization question and the separate process ↔ physical
  realization question do not justify attaching pipe or process-stream semantics
  to `Connection` now — and the decided piping layer (ADR-0011) honours that by
  referencing identified connections instead of widening `Connection`

Think broadly about the destination. Build narrowly in the current iteration.
