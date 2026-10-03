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

- **#39 — Model: decide process ↔ physical realization boundary.** Decide the
  `ProcessStep` ↔ equipment and `ProcessStream` ↔ piping-realization boundary,
  including the mapping shape and cardinality, as evidence and a durable decision
  where justified.

Issue #39 is especially important before the PFD ↔ P&ID realization workflow
becomes stable, but it does not block a pure Process/PFD UI slice.

### Next

- **#69 — Define minimalist UI/UX architecture for the DeepPlant Engineering
  Editor.**
- **#70 — Evaluate and define reuse-first GUI architecture for DeepPlant.**

No implementation sequence is preselected between #69 and #70. They define and
evaluate the minimal UI/UX and reuse-first architecture needed for the MVP;
they do not authorize frontend implementation, dependencies, or directories.

### Afterwards — Re-evaluate from Evidence

After #39, #69, and #70 provide their evidence and decisions, re-evaluate the
roadmap to select the smallest executable GUI vertical slice. Do not create
speculative implementation Issues before that re-evaluation. Select from the
actual repository state, those Issues' conclusions, accepted ADRs, and a
realistic executable example—not by mechanically promoting a backlog row.

### Completed Context

- **Issue #68 is delivered:** the Engineering Editor MVP v0.1 is bounded in
  [product.md](product.md), including the PFD/P&ID subsets, semantic
  source-of-truth interaction direction, user journey, non-goals, and Issue
  #39 relationship. It authorizes no GUI implementation.
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
