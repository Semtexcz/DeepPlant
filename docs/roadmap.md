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
  - docs/planning.md
decision: []
evidence: []
superseded_by: null
---

# Roadmap

> **Primary question:** What is DeepPlant's current execution-planning state?

It answers that question through three aspects:

1. **Current state** — a short summary; canonical facts live in
   [contracts/](contracts/index.md) and [architecture.md](dev/architecture/index.md).
2. **Immediate operational sequence** — the authorized next work and its order.
3. **Unresolved evidence gaps** — questions whose evidence must precede another
   executable task.

It contains no dates, estimates, release promises, fixed sequence commitments, or
completion percentages; GitHub Issues remain the place for executable tasks.
Detailed completion records live in
[history/implementation-slices.md](history/implementation-slices.md), the
long-term capability progression in [direction.md](direction.md), and planning
governance — the Vision → Architecture → Roadmap → Project → Milestones →
Issues → Pull Requests hierarchy — in [planning.md](planning.md).

## Current State

DeepPlant ships a Python CLI package (`src/deepplant/`) implementing:

- the physical/plant model and its validation contract
  ([contracts/plant-model.md](contracts/plant-model.md));
- the process graph ([contracts/process-model.md](contracts/process-model.md));
- physical piping realization over identified connections
  ([contracts/physical-piping.md](contracts/physical-piping.md));
- YAML load/save ([contracts/yaml-format.md](contracts/yaml-format.md)) and the
  `validate` CLI ([contracts/cli.md](contracts/cli.md));
- the basic headless read-only process renderer ([contracts/rendering.md](contracts/rendering.md))
  and the `basic` SVG symbol-pack contract ([dev/reference/svg-symbols.md](dev/reference/svg-symbols.md));
- the narrow DEXPI 2.0.0 Process adapter
  ([dev/reference/dexpi-process-adapter.md](dev/reference/dexpi-process-adapter.md)).

Not implemented: full DEXPI and Plant/P&ID import/export, other vendor adapters
(COMOS, AVEVA), instrumentation and signal semantics, engineering rules, P&ID
rendering, and the interactive editor. The authoritative boundary map, including
directional-but-unimplemented components, is [architecture.md](dev/architecture/index.md).

## Completed

Delivered slices are recorded in
[history/implementation-slices.md](history/implementation-slices.md) and, for
evidence-heavy slices, in the linked spike/decision documents.

## Next Directions

### Operational sequence

```text
#39 → decide the process ↔ physical realization boundary → re-evaluate from its evidence
```

- **Issue #20 is delivered:** the auditable DEXPI 2.0.0 supported-subset and
  semantic round-trip contract is published in
  [dev/reference/dexpi-process-adapter.md](dev/reference/dexpi-process-adapter.md)
  (compatibility matrix, closed support-state vocabulary, per-direction claims,
  and an explicit loss model).
- **Issue #32 delivered its decision/evidence:** the boundary is decided in
  [research/qualified-engineering-quantities.md](research/qualified-engineering-quantities.md)
  and [ADR-0013](decisions/ADR-0013-qualified-engineering-quantity-boundary.md):
  a reusable canonical quantity value owned by explicit domain properties, units
  as semantic state, no implementation.
- **Issue #39 is the sole executable `Now` item:** an evidence-first decision
  slice for the process ↔ physical realization boundary
  ([issue](https://github.com/Semtexcz/DeepPlant/issues/39),
  [selection evidence](research/next-slice-re-evaluation.md)). It adds no
  mapping, field, YAML, or validation, and ends with evidence plus an ADR only if
  a durable canonical boundary is established.
- **No successor task is preselected.** The next direction is chosen from the
  evidence Issue #39 produces.

Issue #21 is closed. Its `StoringMaterial` topic remains deferred
strategic/evidence context in the historical and decision records, not an open or
Ready executable Issue.

The canonical operational sequence is maintained here; superseded planning
proposals do not define a competing sequence.

### Planning context

Issue #20 delivered the DEXPI Process subset and its round-trip contract. Issue
#32 then decided the separate quantity boundary the DEXPI evidence identified
([ADR-0013](decisions/ADR-0013-qualified-engineering-quantity-boundary.md)) — a
decision only, no implementation; the contract's `investigated / unsupported`
rows keep the remaining gap explicit. ADR-0012 does not authorize a second
step-classification axis: DEXPI `Method` vocabulary is heterogeneous, and the
future process ↔ physical-realization layer may own only the subset overlapping
equipment-technology semantics. Issue #39 now investigates that boundary
directly, as evidence and decision only.

### Active milestone

**DEXPI Interoperability v0.1** was completed by Issue #20. Issue #32 delivered a
decision only and was not part of it, and the process ↔ physical realization
slice (Issue #39) belongs to the semantic core rather than that completed
interoperability scope, so it carries **no milestone** and no new milestone is
created for a single research Issue. See
[history/implementation-slices.md](history/implementation-slices.md); P&ID-like
coverage and engineering-rule breadth stay deferred context.

### Scope Discipline

- No database, ORM, web backend, containers, or external services.
- No empty architecture trees before real code exists.
- Schema and model design come from real example fragments, not abstraction.
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
- the editor stage does not justify web architecture now
- the multi-discipline stage does not justify generic entity hierarchies now
- the DEXPI stage does not justify DEXPI-shaped domain objects now
- the physical-piping realization question and the separate process ↔ physical
  realization question do not justify attaching pipe or process-stream semantics
  to `Connection` now — and the decided piping layer (ADR-0011) honours that by
  referencing identified connections instead of widening `Connection`

Think broadly about the destination. Build narrowly in the current iteration.
