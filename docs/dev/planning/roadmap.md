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
  a framework-independent editor application
  (`src/deepplant/editor/application.py`) with a thin, loopback-only FastAPI/Uvicorn
  boundary (`src/deepplant/editor/api.py`), the `deepplant ui <path>` launcher,
  and a Vue 3 + TypeScript + Vite + Vue Flow SPA under `apps/editor/` that serves
  pan, zoom, fit view, single selection, a read-only semantic Inspector, and the
  current validation status.

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

- [#80 — Engineering Editor: frontend engineering contract and quality gates](https://github.com/Semtexcz/DeepPlant/issues/80)
  is the next authorized executable slice.

  #75 delivered the first runnable read-only Process/PFD slice and #79 hardened
  its foundation (the editor application layout and the FastAPI/Uvicorn boundary),
  producing no new product capability and no evidence that changes the sequence.
  The smallest next evidence-producing slice is therefore the frontend
  engineering contract and quality gates, which the later refactor (#81) and
  browser E2E (#82) depend on:

  ```text
  #75 read-only Process/PFD slice delivered
          ↓
  #79 application layout + FastAPI boundary hardening   (delivered)
          ↓
  #80 frontend engineering contract + quality gates      (selected)
          ↓
  #81 frontend refactor + component/integration tests
          ↓
  #82 browser end-to-end tests
          ↓
  re-evaluate the next product capability
  ```

  No semantic-editing, presentation-persistence, P&ID, or process ↔ physical
  realization slice is selected or promoted.

- No other slice is currently selected. #81 and #82 are dependency-ordered
  follow-ups, not parallel `Now` work (see **Next**).

### Next

- [#81 — Engineering Editor: frontend refactor and component/integration tests](https://github.com/Semtexcz/DeepPlant/issues/81),
  after #80 delivers the frontend engineering contract and quality gates.
- [#82 — Engineering Editor: browser end-to-end tests](https://github.com/Semtexcz/DeepPlant/issues/82),
  after #81.
- Re-evaluate the next product capability only after #80–#82, from the evidence
  those slices produce.

  Do not mechanically promote semantic editing, presentation persistence, P&ID,
  or another backlog item. Re-evaluation criteria include:

  - whether the projection/view boundary is strong enough to authorize the first
    semantic-editing slice;
  - whether the first mutation slice needs the minimum application-command
    machinery Issue #69 describes, and where undo/redo belongs;
  - whether presentation state (positions, per-step overrides) now needs its own
    explicit, non-semantic home;
  - what the editor's packaging story must be, given the SPA assets are still
    read from the checkout.

  The re-evaluation outcome is deliberately not decided here, and no successor
  Issue is created.

### Re-evaluation Gate

The previous re-evaluation gate was executed after #39, #69, and #70 were
delivered.

Outcome:
[#75 — Engineering Editor: first interactive Process/PFD vertical slice](https://github.com/Semtexcz/DeepPlant/issues/75)
was selected as the smallest executable slice and is delivered.

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

The re-evaluation from the #75 implementation evidence identified that the
delivered read-only slice needed foundation hardening before more product
functionality was layered on it. Its outcome selected
[#79 — Bug: Engineering Editor architecture is inconsistent with the existing
DeepPlant application structure](https://github.com/Semtexcz/DeepPlant/issues/79)
as the next executable slice, followed by the dependency-ordered
frontend-engineering work #80 → #81 → #82.

The next re-evaluation gate opens only after #82. Its outcome is deliberately
not decided here, and no successor Issue is created (see **Next**).

### Completed Context

- **Issue #79 is delivered (foundation hardening):** the Engineering Editor
  architecture now matches the repository structure. The browser editor is an
  explicit standalone application under `apps/editor/` instead of an
  unclassified root-level `frontend/` tree, and the custom `http.server` editor
  adapter was replaced by a thin FastAPI application factory
  (`create_editor_api`) served by Uvicorn on loopback only. Engineering behaviour
  stayed in `EditorApplication` and below it — now factored into the
  framework-independent `src/deepplant/editor/application.py` with the transport
  in `src/deepplant/editor/api.py` — so the semantic core and the CLI
  remain usable without the GUI, and no editor capability was added. See
  [history/implementation-slices.md](../history/implementation-slices.md) and
  [architecture.md](../architecture/index.md#engineering-editor-slice-implemented).
- **Issue #75 is delivered:** the first runnable, read-only Process/PFD editor
  slice shipped — a DeepPlant-owned Process/PFD projection
  (`src/deepplant/editor/projection.py`), a loopback-only local application
  boundary (`src/deepplant/editor/app.py`, later split into the
  framework-independent `src/deepplant/editor/application.py` and the
  FastAPI/Uvicorn `src/deepplant/editor/api.py` in Issue #79), the
  `deepplant ui <path>` launcher, and a Vue 3 +
  TypeScript + Vite + Vue Flow SPA under `apps/editor/`. It is read-only
  (pan/zoom/fit/selection/Inspector/validation status) and delivered no semantic
  editing, presentation persistence, undo/redo, P&ID rendering, or process ↔
  physical realization. See
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
  selected standalone SPA vertical slice authorizes it. #75 introduced exactly one
  and #79 corrected it: an explicit FastAPI application factory run by Uvicorn,
  loopback-only, read-only, and single-user. It is not a hosted, authenticated,
  production, containerized, or database-backed service surface, and it adds no
  WebSockets, authentication, background jobs, or persistence infrastructure.
- No empty architecture trees, application directories, or GUI dependencies
  before a current executable slice requires them. The only application tree is
  `apps/editor/`, which Issue #79 created by relocating the delivered SPA.
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
- GUI implementation, editor application structure, and GUI dependencies are
  authorized only within the explicitly selected Engineering Editor slices. The
  current hardening sequence is #79 (delivered: application layout + FastAPI
  boundary) → #80 (frontend engineering contract + quality gates) → #81
  (frontend refactor + component/integration tests) → #82 (browser E2E); that
  sequence does not authorize semantic editing, presentation persistence, a
  GUI redesign, P&ID, or broader Engineering Editor infrastructure
- the multi-discipline stage does not justify generic entity hierarchies now
- the DEXPI stage does not justify DEXPI-shaped domain objects now
- the physical-piping realization question and the separate process ↔ physical
  realization question do not justify attaching pipe or process-stream semantics
  to `Connection` now — and the decided piping layer (ADR-0011) honours that by
  referencing identified connections instead of widening `Connection`

Think broadly about the destination. Build narrowly in the current iteration.
