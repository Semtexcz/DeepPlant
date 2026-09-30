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

This document answers three questions and nothing else:

1. **What is current?** — a short summary; canonical facts live in
   [contracts/](contracts/index.md) and [architecture.md](architecture.md).
2. **What is next?** — the immediate direction and the candidates behind it.
3. **What is still unresolved?** — open evidence gaps with their triggers.

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
- the narrow DEXPI 2.x Process adapter
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

### Backlog (Suggested Order)

The rows below are the evidence-driven candidates for the next slice. What is
already delivered, and which contract owns each result, is in
[Completed](#completed) and [contracts/](contracts/index.md); the model-level
classification question from Issue #22 was closed by ADR-0012 and the
`ExchangingThermalEnergy` sub-question by Issue #22.

| # | Item | Note |
|---|---|---|
| 1 | Expand the DEXPI Process subset (evidence-driven) | Independent alternative needing no physical-model change: re-open from fresh evidence now that ADR-0009 gave canonical engineering functions; candidates include material-port-only `pumping` reverse round-trip (proven) and `StoringMaterial` storage classes, each needing its own semantic review against a real instance before any mapping claim. **Partially advanced by Issue #22:** the `ExchangingThermalEnergy` candidate was investigated in full and resolved as an explicit documented + test-pinned unsupported status — canonical `heat_exchange` corresponds to the DEXPI class only as a process-function *kind*, and import/export/round-trip are not claimed because the blockers (`Method: HeatExchangeMethod` mandatory, coupled multi-stream semantics, no port kind, no energy-flow connection kind, no qualified-quantity model) are **model-level and shared with the rest of the DEXPI ProcessStep family** rather than specific to thermal steps; see [docs/dexpi-exchanging-thermal-energy-evidence.md](dexpi-exchanging-thermal-energy-evidence.md). **Partially advanced again by Issue #31:** the `Method` blocker was decided and is now closed as a canonical-model question — the nine DEXPI `Method` properties are heterogeneous and only partially overlap physical-realization semantics, canonical `ProcessStep` currently keeps exactly one classification axis, and the properties stay adapter-unsupported where DEXPI requires them (see Completed; [ADR-0012](decisions/ADR-0012-process-step-single-classification-axis.md)). Of the remaining blockers, `StoringMaterial` (Issue #21) is its own separate evidence slice and qualified engineering quantities are the outstanding model-level decision; neither is authorized here |
| 2 | Renderer/layout refinement (evidence-driven) | Only when a concrete diagram problem needs it: label-collision handling, row/column balancing, crossing reduction, persistent view/presentation configuration, or higher-fidelity symbol sourcing with explicit provenance; do not polish ahead of an evidence gap |

### Milestones

### Milestone 1 — validated YAML load

> DeepPlant can load a small process model from YAML, validate its semantic
> structure and report invalid references through the CLI.

Complete: structural validation and reference validation ship in the first two
slices.

### Milestone 2 — prototype fragment and renderer

> DeepPlant can represent a real process fragment of roughly 20–50 engineering
> objects, render it as a basic PFD/P&ID-like diagram and validate at least 10
> classes of engineering/model consistency errors.

Order within this milestone: the realistic process fragment is a loadable
synthetic example through the production semantic model (see Completed), the
standards/symbol-licensing governance slice (ADR-0007,
[docs/standards.md](standards.md)) governs symbol sourcing, the SVG + anchor +
initial basic symbol-pack contract (ADR-0008, [docs/svg-symbols.md](svg-symbols.md))
ships the `basic` process/PFD pack, and the basic headless read-only process
renderer now derives the standalone PFD diagram from the example
([examples/realistic-process-fragment/process.svg](../examples/realistic-process-fragment/process.svg)).
The milestone's remaining breadth (P&ID-like coverage and an engineering-rule
validation engine with several consistency-error classes) is still open. The
physical-piping specification slice
([docs/physical-piping-model.md](physical-piping-model.md), ADR-0011) is a
decision record, and its first implementation slice (Issue #26) now ships the
physical piping-realization layer: it adds representable P&ID-like structure
(lines, property-bounded segments, elementary realizations) and does **not**
claim the milestone's remaining breadth — no P&ID rendering exists, no
engineering-rule engine exists, and the piping layer's own rule set (C1, P1–P5)
is structural, not engineering.

### Next Task

The piping-realization layer (Issue #26) and the process-step classification
decision (Issue #31) are complete — see [Completed](#completed) and
[history/implementation-slices.md](history/implementation-slices.md). Their
outcomes are current contracts, not roadmap items:
[contracts/physical-piping.md](contracts/physical-piping.md) and
[contracts/process-model.md](contracts/process-model.md).

No single next task is promoted here. The next choice is deliberately left to
the later review this document's planning governance requires, because this
decision closed one model-level question without creating an implementation
obligation, and each remaining candidate is a different kind of work:

- **The remaining model-level question — qualified engineering quantities
  (C-3).** Issue #22 isolated exactly two model-level blockers: a
  required/non-derivable step classification and the absence of any canonical
  qualified-quantity representation. Issue #31 closed the first (no canonical
  field is owed). The second is untouched by that decision: DEXPI still requires
  `Duty`, `Area`, `Head`, `VolumeFlow`, `Pressure`, `Temperature`, side mass
  flows, and more as *qualified* values on the very classes examined here, and
  the canonical model still has nowhere to put value-plus-unit. This is the
  smallest remaining evidence-producing step of that pair, and it is recorded
  here as an **evidence-backed candidate**, not as an authorized task; it
  deserves its own decision Issue and must not be folded into a classification
  slice or grown into a units-library design.
- **Backlog row 1** — expand the DEXPI Process subset from fresh evidence (needs
  no physical-model change). Its `ExchangingThermalEnergy` sub-question is closed
  by Issue #22
  ([docs/dexpi-exchanging-thermal-energy-evidence.md](dexpi-exchanging-thermal-energy-evidence.md)):
  the class stays explicitly unsupported. Its `Method` blocker is closed by
  Issue #31. The remaining per-class candidate is `StoringMaterial` storage
  classes, which is its own separate slice (Issue #21) and is **not** closed by
  this decision. Neither candidate is authorized here.
- **Recorded physical-model gaps, not authorized work:** a concrete requirement
  for a property change that does not coincide with a `Connection` boundary
  (then `PropertyBreak` semantics), `1:N` parallel/as-built realization
  cardinality, a canonical `Pipe`/pipe-piece identity, and process ↔ physical
  realization — which is additionally the layer the DEXPI `Method` values belong
  to under ADR-0012. Each needs its own evidence and its own Issue per
  ADR-0011's and ADR-0012's Revisit-When lists; none is a mechanical continuation
  of this slice.
- **Backlog row 2** — renderer/layout refinement stays evidence-gated.

This follows from the current repository state: the DEXPI Plant/P&ID spike
([docs/dexpi-plant-pid-spike.md](dexpi-plant-pid-spike.md), ADR-0010) bounded
the question and kept the `Port`/`Connection` invariants, the physical-piping
specification/decision slice
([docs/physical-piping-model.md](physical-piping-model.md), ADR-0011) answered
*what is the physical piping graph?*, and the implementation slice proved the
decided shape against the realistic fragment with executable tests, so the
semantic model has met real example evidence before any rule engine, adapter, or
rendering work. The slice answered the physical side only; it did not decide how
`ProcessStep` maps to equipment or how `ProcessStream` maps to piping
realization.

The remaining physical-model work is split into two independent questions:

1. **Physical-piping realization:** pipe / segment / line / node / component
   representation. This is decided at the canonical-model level
   (`PipingLine` / `PipingSegment` / `PipingRealization` over `Port` and
   `Connection`) **and its first slice is implemented**; the deferred parts
   (mid-`Connection` property breaks, `1:N` realizations, pipe-piece identity,
   `Nozzle`/`PipingNode`) each need their own evidence and Issue.
2. **Process ↔ physical realization:** mapping between `ProcessStep` /
   `ProcessStream` and physical realization. Its shape and cardinality remain
   unresolved and must not be smuggled into the piping layer or `Connection`.

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
