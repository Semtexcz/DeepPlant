# ADR-0012: `ProcessStep` Has Exactly One Classification Axis

> Status: Accepted
> Date: 2026-09-22

## Context

Issue #22 established a recurring model-level blocker and reported that it was
not class-local: DEXPI `ProcessStep` subclasses may carry a **required,
non-derivable** `Method` property, and `ProcessStep.function` alone cannot
preserve it
([docs/dexpi-exchanging-thermal-energy-evidence.md](../dexpi-exchanging-thermal-energy-evidence.md)).
Issue #31 was created to decide — before any new canonical field was designed —
whether those `Method` properties expose one reusable canonical engineering
concept beside `ProcessStep.function`:

```text
ProcessStep.function      = WHAT process function is performed
possible second concept   = HOW / by what process principle / variant?
```

The investigation is documented in
[docs/process-step-classification.md](../process-step-classification.md), based
on the pinned official DEXPI Specification 2.0.0 (`V2.0.0`, release commit
`260c81c51039789a6148a98af4c6caf23f87a3e2`, dated 2025-10-10, inspected
2026-09-22). It found that:

- `Method` exists only in the DEXPI Process model, as **nine** property
  declarations across **seven** different enumeration types, with multiplicities
  of both `1..1` and `0..1`;
- the enumeration domains are not one semantic dimension — inside single enums,
  mechanism/principle labels (`CentrifugalMotion`, `PositiveDisplacement`),
  equipment-class names (`Fan`, `Blower`, `Ejector`, `Eductor`) and non-answers
  (`Unspecified`, `CustomMethod`, `Generic`) are mixed;
- many literal names have direct or close counterparts in `Plant.ProcessEquipment`
  classes in the same release (`PlateHeatExchanger`, `SpiralHeatExchanger`,
  `TubularHeatExchanger`, `CentrifugalPump`, `AxialCompressor`, `GasTurbine`,
  `AlternatingCurrentMotor`, `Tank`, …), demonstrating semantic overlap with
  physical realization rather than exact semantic identity for every literal;
- DEXPI expresses mixing distinctions by subclassing (`RotaryMixing`,
  `StaticMixing`, with no `Mixing.Method` at all) and compression distinctions by
  a `Method` property; `ReactingChemicals.Method = PackedBed` and the
  `ProcessStepDetail` subclass `ContactingInPacking` carry related packed-bed
  semantics through different constructs, without inspected evidence of
  equivalence.

The question this ADR answers is therefore narrow and canonical:

```text
How many classification axes does canonical ProcessStep have?
```

It does **not** answer how a `ProcessStep` maps to a physical realization.

## Options

- **A — no second classification:** `ProcessStep` keeps `id`, `function`,
  `name`, `ports`; DEXPI `Method` stays adapter-unsupported where DEXPI requires
  it.
- **B — generic second classification:** one additional
  `principle`/`variant`/`method` string with a shared value namespace.
- **C — function-specific semantic details:** a function-scoped `details`
  structure.
- **D — realization-layer concept:** the subset of values that overlaps
  physical realization belongs outside `ProcessStep`, at the physical-realization
  layer; candidate D does not claim ownership of every `Method` literal.

Candidate analysis, the layer separation, the DeepPlant-authoring test, and the
rejected shortcuts are in
[docs/process-step-classification.md](../process-step-classification.md) §7–§9.
## Decision

**A is accepted**, on the following explicit terms:

1. **Canonical `ProcessStep` currently has exactly one classification axis:
   `function`.** No second canonical classification field is added, and no name
   for one is reserved.
2. **`ProcessStep.function` is unchanged.** It stays an open, non-empty string
   (ADR-0009). ADR-0009 is preserved here, not weakened.
3. **No generic second classification is justified.** The DEXPI `Method` values
   are not one reusable engineering concept: they span seven enumeration domains
   across nine properties whose value domains are heterogeneous, so no single
   value namespace could be semantically coherent (candidate B is rejected).
4. **No function-specific detail structure is introduced now.** The values are
   function-specific, which argues against a global union, but that alone does
   not make them DeepPlant process concepts. No DeepPlant-native consumer or
   authoring workflow currently justifies a function-scoped structure (candidate
   C is rejected now; only the direction is recorded).
5. **A large part of the `Method` vocabulary overlaps physical-realization /
   equipment-technology semantics, while the remainder contains function-specific
   mechanism/principle labels and non-answer values.** Taken together, the seven
   enumeration domains do not form one coherent process-level classification
   axis. Some values may later find an honest home in a physical-realization or
   function-specific model, but this ADR does not decide that ownership.
6. **No `realized_by` field, no `ProcessStep` → `Equipment` reference, and no
   Process ↔ physical realization mapping is introduced.** That layer keeps its
   own deferred status under ADR-0009 and ADR-0011.
7. **No generic semantic-extension mechanism is introduced** — no
   `attributes`/`properties`/`metadata`/`details` bag, no generic `Property`,
   `Attribute`, or `Entity`, no generic schema framework, and no
   `ProcessStepMethod` enum unioning DEXPI enumerations. Unknown or
   unrepresentable semantic content continues to fail explicitly rather than
   being absorbed.
8. **Adapter round-trip convenience is not a justification for canonical model
   growth.** The `Method` properties stay adapter-unsupported where DEXPI
   requires them, and a required-but-unrepresentable value keeps raising a named
   error rather than being silently dropped or synthesized.
9. **The values are neither presentation nor quantities.** No `Method` literal
   is a symbol role or graphical asset, so the ADR-0009 presentation boundary is
   untouched; and qualified engineering quantities remain a separate, undecided
   question.
10. **No implementation follows from this ADR.** It records a boundary, not a
    task.

## Rejected alternatives

| Alternative | Why rejected |
|---|---|
| **B — generic second classification** | The seven DEXPI enumeration domains cannot be unioned into one coherent value domain; the per-enum escape hatches (`Unspecified`, `CustomMethod`, `Generic`) would collide with each other and with the empty default; and no DeepPlant consumer or authoring workflow needs it. |
| **C — function-specific details now** | The values are function-specific, but no DeepPlant-native process concept or consumer justifies a polymorphic per-function framework now. |
| **D as an implementation** | Candidate D is a plausible future home for part of the vocabulary because many values overlap realization semantics, but it is not proven to own every literal. Implementing Process ↔ physical realization here would exceed this decision's evidence and duplicate work ADR-0009/ADR-0011 already defer. |
| `method: str \| None` because DEXPI has a property named `Method` | Copies a DEXPI property name into the canonical model on the strength of the name; no coherent value domain and no consumer. |
| Any `dict[str, Any]` semantic bag | Destroys the fail-fast semantic contract that keeps unsupported engineering data visible instead of silently meaningless. |
| Unioning the DEXPI `*Method` enums into one canonical enum | Makes DEXPI the owner of DeepPlant's canonical vocabulary and freezes an incoherent union into the model. |
| Encoding the variant inside `function` (for example `"pumping:centrifugal"`) | Collapses process semantics and realization selection into one field, weakening ADR-0009 and breaking the renderer's function → symbol-role policy. |

## Consequences

### Positive

- `ProcessStep` keeps a single honest classification axis, so a reader never has
  to decide whether a field states a process fact or an equipment choice.
- No speculative schema is added: no field without a consumer, without a
  DeepPlant-native value domain, and without an authoring workflow.
- The process model does not absorb a heterogeneous DEXPI vocabulary merely
  because its values overlap physical realization; any future ownership remains
  evidence-backed and separate from this decision.
- The recurring blocker from Issue #22 is answered durably, so the next DEXPI
  slice does not re-investigate `Method`.
- Unrepresentable DEXPI content keeps failing explicitly and by name, which
  preserves the evidence value of adapter errors.

### Negative

- DEXPI classes whose `Method` is mandatory remain unimportable and unexportable,
  and no round-trip is claimed for them. That information loss is accepted because
  DeepPlant has no honest canonical home for the heterogeneous values today.
- A future physical-realization or function-specific model may carry relevant
  values, but their ownership is deferred rather than assumed.
- Any later reversal must be evidence-backed through this ADR's Revisit-When
  list rather than by adding a field opportunistically.

## Deferred

- Qualified engineering quantities (`QualifiedValue`, units, `Duty`, `Area`,
  `Head`, `VolumeFlow`, `Pressure`, `Temperature`, mass flow, unit conversion) —
  a separate decision, and the remaining model-level blocker from Issue #22.
- Physical realization / equipment technology, and the Process ↔ physical
  realization mapping.
- `ProcessStepDetail` semantics and any step-refinement/sub-process concept.
- Function-specific semantic details, if new evidence ever justifies them.
- `StoringMaterial` storage classes (Issue #21).
- DEXPI Process subset expansion.

## Revisit When

- A DeepPlant-native (non-DEXPI) authoring need requires a *process-level*
  distinction `ProcessStep.function` cannot express, and the distinction does not
  merely restate an equipment mechanism or physical-realization choice; a
  genuine equipment-independent process principle with a DeepPlant-native
  consumer remains valid revisit evidence.
- Simulation, calculation, engineering rules, or design workflows need a
  function-specific process principle independent of equipment realization.
- The physical-realization layer is designed and new evidence establishes an
  honest home there for relevant values, or demonstrates that one cannot be
  placed there.
- Future DEXPI evidence exposes a coherent cross-cutting semantic axis — for
  example, a later release replaces the per-class `*Method` enumerations with
  one coherent, equipment-independent process-principle axis.
- `ProcessStepDetail` mapping reveals a genuine process-level refinement concept.

## Related

- [ADR-0002-semantic-model-is-the-core.md](ADR-0002-semantic-model-is-the-core.md)
- [ADR-0003-separate-semantic-and-presentation-models.md](ADR-0003-separate-semantic-and-presentation-models.md)
- [ADR-0009-separate-process-function-from-symbol-role.md](ADR-0009-separate-process-function-from-symbol-role.md)
- [ADR-0010-dexpi-plant-pid-semantic-boundary.md](ADR-0010-dexpi-plant-pid-semantic-boundary.md)
- [ADR-0011-canonical-physical-piping-realization.md](ADR-0011-canonical-physical-piping-realization.md)
- [../process-step-classification.md](../process-step-classification.md) — the
  full evidence and candidate analysis (Issue #31)
- [../dexpi-exchanging-thermal-energy-evidence.md](../dexpi-exchanging-thermal-energy-evidence.md),
  [../dexpi-process-spike.md](../dexpi-process-spike.md),
  [../architecture.md](../architecture.md), [../roadmap.md](../roadmap.md)

