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
  - docs/architecture.md
  - docs/planning.md
decision: []
evidence: []
superseded_by: null
---

# Roadmap

> **Primary question:** What is DeepPlant's current execution-planning state?

It answers that question through three aspects:

1. **Current state** — a short summary; canonical facts live in
   [contracts/](contracts/index.md) and [architecture.md](architecture.md).
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
- the basic headless read-only process renderer ([rendering.md](rendering.md))
  and the `basic` SVG symbol-pack contract ([svg-symbols.md](svg-symbols.md));
- the narrow DEXPI 2.0.0 Process adapter
  ([contracts/dexpi-process-adapter.md](contracts/dexpi-process-adapter.md)).

Not implemented: full DEXPI and Plant/P&ID import/export, other vendor adapters
(COMOS, AVEVA), instrumentation and signal semantics, engineering rules, P&ID
rendering, and the interactive editor. The authoritative boundary map, including
directional-but-unimplemented components, is [architecture.md](architecture.md).

## Completed

Delivered slices are recorded in
[history/implementation-slices.md](history/implementation-slices.md) and, for
evidence-heavy slices, in the linked spike/decision documents.

## Next Directions

### Operational sequence

```text
#32 → re-evaluate the next direction from new evidence
```

- **Issue #20 is delivered:** the auditable DEXPI 2.0.0 supported-subset and
  semantic round-trip contract is published in
  [contracts/dexpi-process-adapter.md](contracts/dexpi-process-adapter.md)
  (compatibility matrix, closed support-state vocabulary, per-direction claims,
  and an explicit loss model).
- **Issue #32 is now the sole Now item:** decide the semantic boundary for
  qualified engineering quantities.
- **No third executable task is promoted yet.** Re-evaluate after Issue #32 from
  the new evidence it produces.

Issue #21 is closed. Its `StoringMaterial` topic remains deferred
strategic/evidence context in the historical and decision records, not an open or
Ready executable Issue.

The canonical operational sequence is maintained here; superseded planning
proposals do not define a competing sequence.

### Planning context

Issue #20 delivered the DEXPI Process subset and its semantic round-trip
contract, which names the remaining unsupported concepts without widening the
subset. Issue #32 is next because qualified engineering quantities remain the
separate unresolved model boundary identified by the DEXPI evidence; the
contract's `investigated / unsupported` rows keep that gap explicit. The current
contracts and ADR-0012 do not authorize a third slice: DEXPI `Method` vocabulary
is heterogeneous. The future process ↔ physical-realization layer may become the
home for the subset of `Method` semantics that overlap
physical-realization/equipment-technology semantics; ADR-0012 does not assign the
whole vocabulary there.

### Active milestone

**DEXPI Interoperability v0.1** is the current milestone; Issue #20 completes its
scope. After #20 merges, Issue #32 becomes the sole Now item (`#32 → re-evaluate
the next direction from new evidence`); it is **not** automatically part of this
milestone, and no successor milestone is created or assigned. See
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
