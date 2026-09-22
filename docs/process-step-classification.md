---
type: research
status: active
source_of_truth_for:
  - process-step-classification-boundary
read_when:
  - process-function-vocabulary-work
  - canonical-model-change
  - interoperability-work
update_when:
  - canonical-model-change
  - dexpi-model-change
---

# Process-Step Classification Boundary (Issue #31)

> This document is the primary deliverable of Issue #31, an **evidence-first
> canonical-model decision slice**. It is not documentation of a delivered
> capability and it authorizes no implementation.
>
> Question under investigation:
>
> ```text
> Does canonical DeepPlant need a second process-step classification concept
> in addition to ProcessStep.function?
> ```
>
> **Answer (Outcome A): no.** The recurring DEXPI `Method` properties do not
> expose one reusable canonical engineering concept. They are seven different
> enumeration types across nine properties whose semantics are heterogeneous and
> function-specific. Many values have direct or close counterparts in DEXPI's
> physical `Plant.ProcessEquipment` taxonomy, while others describe mechanisms,
> principles, or non-answers. `ProcessStep.function` therefore remains the only
> canonical step-classification axis, and no canonical field is added. §10
> records the exact decision, §8 the rejected candidate shapes, and §9 the
> rejected shortcuts.
>
> The decision is deliberately made on engineering grounds, not on adapter
> convenience: preserving more DEXPI content is explicitly *not* a sufficient
> reason to grow the canonical model (§7.3).

## 1. Problem

Issue #22 established one blocker and reported that it is not class-local:

```text
DEXPI ProcessStep subclasses may carry a required, non-derivable Method
→ DeepPlant ProcessStep.function is not sufficient to preserve it
```

`ExchangingThermalEnergy` cannot be mapped because, among other things,
`Method: HeatExchangeMethod` is `1..1`. Issue #22 recorded that this blocker is
**model-level and shared with the rest of the DEXPI ProcessStep family** rather
than specific to thermal steps
([dexpi-exchanging-thermal-energy-evidence.md](dexpi-exchanging-thermal-energy-evidence.md)).
Issue #31 was created to answer that model-level half — and only that half —
before any new canonical field is designed.

The specific question is whether these properties represent one reusable
DeepPlant engineering concept sitting next to `ProcessStep.function`:

```text
ProcessStep.function            = WHAT process function is performed
possible second concept         = HOW / by what process principle / variant
                                  is that function performed?
```

The task does not assume the second concept exists, does not assume that its
name is `method`, and does not assume that all DEXPI properties named `Method`
share one meaning. This document determines that from the pinned official DEXPI
model.

## 2. Current DeepPlant semantics

`ProcessStep` is the canonical process-domain object
(`src/deepplant/model.py`):

```text
ProcessStep
├── id
├── function      open, non-empty string (ADR-0009)
├── name
└── ProcessPort[]
```

`function` is the engineering process function performed by the step. ADR-0009
fixes its boundary, and this slice does **not** weaken it:

```text
ProcessStep.function
=  canonical engineering function
!= equipment class
!= physical realization
!= presentation role
!= DEXPI class identifier
```

Two further properties of the current implementation matter for this decision:

1. **The vocabulary is deliberately open.** Any non-empty string is legal;
   `unspecified` is legal and means the step exists but its function is not yet
   specified. No closed Python `Enum`, no function taxonomy, and no subclass
   hierarchy exists (ADR-0009 decisions 1 and 3).
2. **Presentation is resolved outside the model.** The renderer owns a private
   default policy (`src/deepplant/render.py`): `source→source`, `sink→sink`,
   `mixing→mixing`, `splitting_material→splitting`, `pumping→pump`,
   `heat_exchange→heat_exchanger`, plus per-call `symbol_role_overrides`. Symbol
   role is never stored in `ProcessStep`.

Documented canonical functions today: `source`, `sink`, `mixing`,
`splitting_material`, `pumping`, `heat_exchange`, `unspecified` (plus any other
non-empty string).

## 3. Evidence sources

Policy applied: *stable release exists → target the latest stable release; a
beta/RC newer than stable is inspected but is not made the production target
unless strongly justified.* This is the same policy and the same pin used by
[dexpi-process-spike.md](dexpi-process-spike.md),
[dexpi-plant-pid-spike.md](dexpi-plant-pid-spike.md), and
[dexpi-exchanging-thermal-energy-evidence.md](dexpi-exchanging-thermal-energy-evidence.md).
**No re-pinning was performed**, because no repository evidence shows the pin
has changed.

| Fact | Value |
|---|---|
| Targeted DEXPI version | **2.0.0** (DEXPI Specification 2.0.0) |
| Targeted tag | `V2.0.0` |
| Tag object id (annotated tag target) | `dc74c370645651b4a4f691c79723710657472c6d` |
| Release commit used by the DeepPlant pin | `260c81c51039789a6148a98af4c6caf23f87a3e2` |
| Release date | 2025-10-10 |
| Official source URL | https://gitlab.com/dexpi/Specification |
| Licence | CC BY 4.0 |
| Inspection date | **2026-09-22** |
| Checked-out revision of the inspected tree | `260c81c51039789a6148a98af4c6caf23f87a3e2` (verified locally) |
| DeepPlant evidence baseline | branch `research/issue-31-process-step-classification`, created from `origin/main` |

The tag-object-versus-release-commit distinction is the same one recorded in
[dexpi-exchanging-thermal-energy-evidence.md](dexpi-exchanging-thermal-energy-evidence.md)
§1; both identifiers are recorded rather than silently substituting one for the
other. The shallow clone used for this inspection resolved to exactly
`260c81c51039789a6148a98af4c6caf23f87a3e2`.

### 3.1 Official source paths inspected

All DEXPI semantic claims below come from these official `V2.0.0` paths:

| Path | Role in this analysis |
|---|---|
| `src/model/Process/Process/Process.py` | authoritative definition of every `ProcessStep` subclass, every `Method` property, and `ProcessStepDetail` (4328 lines) |
| `src/model/Process/Enumerations/process_enumerations.ods` | authoritative enumeration workbook: literal names per enumeration |
| `src/model/Process/Enumerations/Enumerations.py` | shows the Process enumerations are generated at build time from the `.ods` workbook |
| `src/model/Plant/ProcessEquipment/ProcessEquipment.py` | authoritative physical-realization / equipment-technology vocabulary used to test the `Method` values |
| `src/model/Process/Process.py` | Process package definition |

### 3.2 Provenance and licence policy applied

DEXPI 2.0.0 is published under CC BY 4.0, which permits use with attribution, so
the official model definitions may be inspected for this analysis (ADR-0007,
[standards.md](standards.md)). This document reproduces only class names,
property names, multiplicities, type references, enumeration literal names, and
at most the short class-definition sentence needed to make the engineering
judgement auditable. No DEXPI figures, symbol artwork, PDF text, or substantial
normative prose is copied, and no DEXPI content is vendored into this
repository.

### 3.3 What is deliberately *not* used as evidence

- **pyDEXPI naming is not semantic evidence.** No pyDEXPI class, attribute, or
  enum name justifies any claim here.
- **DEXPI 1.x / Proteus-era semantics are not mixed in.** Every statement comes
  from the single pinned `V2.0.0` release.
- **DEXPI 2.0.1 is excluded.** It is not released; the official DEXPI update
  reported it as "being prepared" with Process-model clarifications. That
  known-upcoming incompatibility risk is inherited unchanged from the earlier
  spikes.
- **Per-literal enumeration descriptions do not exist in the authoritative
  source.** The official workbook exposes `enumeration`, `literal`, `uri`,
  `label`, and `symbol` columns and carries no literal description text; the
  `label` column is empty for every enumeration inspected here. Literal
  semantics below are therefore derived from (a) the enumeration literal names
  themselves, (b) the surrounding DEXPI class definitions, and (c) the DEXPI
  `Plant` model class vocabulary. Any step beyond the literal name is labelled
  as DeepPlant inference.
- **No official DEXPI 2.0 Process *instance* file exists upstream** (the same
  limitation the earlier spikes recorded), so no instance-level literals are
  quoted from example documents.

## 4. DEXPI `Method` inventory

### 4.1 Search scope and completeness

The search was performed over the **entire** official model, not only the known
`Pumping` / `Compressing` / `ExchangingThermalEnergy` examples:

- every property declaration matching `.Method = ` in the whole
  `src/model/**` tree was enumerated;
- every property whose name is exactly `Method` was located;
- `ProcessStep` subclass relationships were resolved from `superTypes`.

Result: **`Method` exists only in the DEXPI Process model.** All nine
occurrences are in `src/model/Process/Process/Process.py`, and no `Core` or
`Plant` class declares a property named `Method`. There is therefore no
cross-model `Method` concept to reconcile.

The concrete ProcessStep class tree at `V2.0.0` has 22 direct children of the
abstract `Process.Process.ProcessStep`:

```text
ExchangingThermalEnergy   Flaring          FormingSolidMaterial
GeneratingFlow            IncreasingParticleSize
Mixing                    Packaging        ReactingChemicals
ReducingParticleSize      RemovingThermalEnergy
Separating                Source           SteeringFlow
StoringEnergy             StoringMaterial  SupplyingElectricalEnergy
SupplyingFluids           SupplyingMechanicalEnergy
SupplyingThermalEnergy    TransportingElectricalEnergy
TransportingFluids        TransportingSolids
```

Of those 22 classes (and their concrete descendants), **only nine** declare a
`Method` property, and they belong to **five** function families.

### 4.2 Inventory matrix

`lower` / `upper` are the DEXPI multiplicities; `upper=None` means unbounded.
Source: `src/model/Process/Process/Process.py`, `V2.0.0`, release commit
`260c81c…`.

| # | DEXPI ProcessStep class | `Method` type | multiplicity | enumeration literals |
|---|---|---|---|---|
| 1 | `ExchangingThermalEnergy` | `HeatExchangeMethod` | **1..1** (mandatory) | `Generic`, `Plate`, `Spiral`, `Tubular` |
| 2 | `RemovingThermalEnergy` | `HeatExchangeMethod` | **1..1** (mandatory) | `Generic`, `Plate`, `Spiral`, `Tubular` |
| 3 | `SupplyingThermalEnergy` | `Undefined \| HeatExchangeMethod` | 0..1 (optional) | `Generic`, `Plate`, `Spiral`, `Tubular` |
| 4 | `Compressing` | `CompressionMethod` | **1..1** (mandatory) | `AxialMotion`, `CentrifugalMotion`, `Unspecified`, `Ejector`, `Fan`, `ReciprocatingMotion`, `CustomMethod`, `RotaryMotion`, `Blower` |
| 5 | `Pumping` | `Undefined \| PumpingMethod` | 0..1 (optional) | `CentrifugalMotion`, `PositiveDisplacement`, `Eductor`, `RotaryMotion`, `CustomMethod`, `Unspecified` |
| 6 | `ReactingChemicals` | `ReactionProcessType` | **1..1** (mandatory) | `Tubular`, `PackedBed`, `Tank`, `FluidizedBed`, `Unspecified` |
| 7 | `DrivingByEngine` | `Undefined \| EngineDriveMethod` | 0..1 (optional) | `Unspecified`, `OttoCycle`, `Diesel`, `GasTurbine` |
| 8 | `DrivingByMotor` | `Undefined \| MotorDriveMethod` | 0..1 (optional) | `Unspecified`, `AlternatingCurrent`, `DirectCurrent`, `StepperMotor` |
| 9 | `DrivingByTurbine` | `TurbineDriveMethod` | **1..1** (mandatory) | `Unspecified`, `WindTurbine`, `WaterTurbine`, `Expander` |

Distinct `Method` property declarations: **9**. Distinct enumeration types:
**7**. The three thermal classes share one enumeration; every other class has
its own.

Only two of the nine property declarations carry an authoritative DEXPI
description at all:

- `Compressing.Method` — description `"Compression method."`
- `Pumping.Method` — no property description; the **class** description states
  that "the physical principle … can be specified by selecting a value from the
  `PumpingMethod` enumeration".

`ExchangingThermalEnergy.Method` carries no description of its own; the class
description only states that the process "is realized by a heat exchanger".

### 4.3 Per-class semantic answer

The question asked of every class was: is `Method` a *process principle*, an
*equipment technology*, a *mechanism*, an *operating mode*, a *physical
realization*, a *design variant*, an *algorithm*, or something else?

| # | Class | What the literal set actually distinguishes | Verdict |
|---|---|---|---|
| 1–3 | thermal exchange classes | exchanger **construction/geometry** (`Plate`, `Spiral`, `Tubular`) plus a `Generic` escape hatch. No physics distinction (no direct/indirect contact, no condensing/evaporating, no single/two phase). | **physical realization / construction technology** |
| 4 | `Compressing` | **mixed**: motion mechanism (`AxialMotion`, `CentrifugalMotion`, `ReciprocatingMotion`, `RotaryMotion`) **plus** the equipment class names `Ejector`, `Fan`, `Blower`, **plus** `CustomMethod` / `Unspecified` | **heterogeneous within one enum** — mechanism *and* equipment technology |
| 5 | `Pumping` | **mixed**: motion mechanism (`CentrifugalMotion`, `RotaryMotion`), a displacement principle (`PositiveDisplacement`), an equipment class name (`Eductor`), plus `CustomMethod` / `Unspecified` | **heterogeneous within one enum** — mechanism *and* principle *and* equipment technology |
| 6 | `ReactingChemicals` | reactor **arrangement / contacting geometry** (`Tubular`, `PackedBed`, `Tank`, `FluidizedBed`) plus `Unspecified` | **physical realization / construction arrangement** |
| 7 | `DrivingByEngine` | prime-mover **thermodynamic cycle / technology** (`OttoCycle`, `Diesel`, `GasTurbine`) | **equipment technology** |
| 8 | `DrivingByMotor` | motor **technology / electrical supply kind** (`AlternatingCurrent`, `DirectCurrent`, `StepperMotor`) | **equipment technology** |
| 9 | `DrivingByTurbine` | turbine **working fluid / machine kind** (`WindTurbine`, `WaterTurbine`, `Expander`) | **equipment technology** |

No `Method` value was found to be an operating mode, a design condition, an
algorithm, or a qualified engineering quantity. Every value is a *kind* label.

## 5. Semantic comparison: same property name, not the same concept

### 5.1 Hypothesis test

Hypothesis under test:

```text
DEXPI property name "Method"
≠ necessarily one shared engineering concept
```

**Result: the hypothesis holds, and it is rejected more strongly than
expected.** `Method` is not merely a set of unrelated class-local
classifications; it is not even a single *dimension* of classification.

### 5.2 Comparison table

| Class | Method enum | What distinction does it encode? | Could the value make sense outside this function? | Independent of equipment realization? | Independent of presentation? | Is it an engineering decision? | Would DeepPlant need to preserve it? |
|---|---|---|---|---|---|---|---|
| `ExchangingThermalEnergy` | `HeatExchangeMethod` | exchanger construction geometry | Partially — `Tubular` also appears in `ReactionProcessType` | **No** — DEXPI also models `PlateHeatExchanger` / `SpiralHeatExchanger` / `TubularHeatExchanger` as Plant classes | Yes (no symbol role) | Yes, but as a **realization** selection | Only at the realization layer, if that layer is ever modelled |
| `RemovingThermalEnergy` | `HeatExchangeMethod` | same | same | **No** | Yes | Yes, realization | same |
| `SupplyingThermalEnergy` | `HeatExchangeMethod` | same | same | **No** | Yes | Yes, realization | same |
| `Compressing` | `CompressionMethod` | motion mechanism **and** equipment class | No — `Fan`/`Blower` are compressor-family kinds, not general | **No** — mirrors `AxialCompressor`, `CentrifugalCompressor`, `ReciprocatingCompressor`, `RotaryCompressor`, `AirEjector`, `Fan`, `Blower` | Yes | Yes: *what performs the compression* — realization | No, not as a *process-function* concept |
| `Pumping` | `PumpingMethod` | motion mechanism + displacement principle + equipment class | No | **No** — mirrors `CentrifugalPump`, `RotaryPump`, `EjectorPump` | Yes | Yes: *what performs the lift* — realization, exactly what ADR-0009 already reserves for the physical layer | No, not as a *process-function* concept |
| `ReactingChemicals` | `ReactionProcessType` | reactor contacting arrangement | No — `Tank`/`PackedBed` are reactor-arrangement terms | **No** — mirrors `Tank`, packing/tray arrangements | Yes | Yes, realization/arrangement | No, not as a *process-function* concept |
| `DrivingByEngine` | `EngineDriveMethod` | prime-mover cycle | No | **No** — mirrors `CombustionEngine` / `GasTurbine` | Yes | Yes, equipment technology | No |
| `DrivingByMotor` | `MotorDriveMethod` | motor supply kind | No | **No** — mirrors `AlternatingCurrentMotor` / `DirectCurrentMotor` | Yes | Yes, equipment technology | No |
| `DrivingByTurbine` | `TurbineDriveMethod` | turbine machine kind | No | **No** — turbine/generator equipment family | Yes | Yes, equipment technology | No |

Every row passes the "independent of presentation" test, and every row **fails**
the "independent of equipment realization" test. That single column is the
decisive one.

### 5.3 The decisive evidence: DEXPI already models these values as physical equipment

The literal names of these enumerations are not merely *similar* to
`Plant.ProcessEquipment` class names — they are largely the **same names**, in
the same official release:

| `Method` literal | Same-named / directly corresponding `Plant.ProcessEquipment` class |
|---|---|
| `HeatExchangeMethod.Plate` | `PlateHeatExchanger` |
| `HeatExchangeMethod.Spiral` | `SpiralHeatExchanger` |
| `HeatExchangeMethod.Tubular` | `TubularHeatExchanger` |
| `CompressionMethod.AxialMotion` | `AxialCompressor` |
| `CompressionMethod.CentrifugalMotion` | `CentrifugalCompressor` |
| `CompressionMethod.ReciprocatingMotion` | `ReciprocatingCompressor` |
| `CompressionMethod.RotaryMotion` | `RotaryCompressor` |
| `CompressionMethod.Ejector` | `AirEjector` |
| `CompressionMethod.Fan` | `Fan` (`AxialFan`, `RadialFan`) |
| `CompressionMethod.Blower` | `Blower` (`AxialBlower`, `CentrifugalBlower`) |
| `PumpingMethod.CentrifugalMotion` | `CentrifugalPump` |
| `PumpingMethod.RotaryMotion` | `RotaryPump` |
| `PumpingMethod.Eductor` | `EjectorPump` |
| `MotorDriveMethod.AlternatingCurrent` | `AlternatingCurrentMotor` |
| `MotorDriveMethod.DirectCurrent` | `DirectCurrentMotor` |
| `EngineDriveMethod.GasTurbine` | `GasTurbine` |
| `ReactionProcessType.Tank` | `Tank` |
| `ReactionProcessType.PackedBed` | `ColumnPackingsArrangement` |

Source: `src/model/Plant/ProcessEquipment/ProcessEquipment.py`, `V2.0.0`,
release commit `260c81c…`.

Many `Method` literals therefore have direct or close counterparts in the
`Plant.ProcessEquipment` taxonomy in the same DEXPI release. This is strong
evidence of **semantic overlap with physical realization / equipment technology**,
not proof that every `Method` literal has identical ownership or meaning. The
inventory remains unsuitable as one process-function classification.

### 5.4 Heterogeneity findings

**H1 — One property name, seven enumeration types.** `Method` is not one value
namespace. Any canonical field storing it would need a per-function value
domain, which is the definition of "function-specific", not "generic".

**H2 — Different multiplicities.** Five declarations are mandatory `1..1` and
four are optional `0..1`. `Method` is not even a uniform dimension of the DEXPI
Process model; some classes cannot exist without it and others may omit it.

**H3 — Inconsistent optionality encoding.** Some declarations are a bare
enumeration (`HeatExchangeMethod`), others are wrapped
`BUILTIN.Undefined | <enum>`. The same "is it filled in?" question is modelled
two different ways in one release.

**H4 — At least one enum mixes mechanism with equipment-class names.**
`CompressionMethod` contains motion principles (`AxialMotion`,
`CentrifugalMotion`, `ReciprocatingMotion`, `RotaryMotion`) *and* literal
`Plant` equipment class names (`Ejector`, `Fan`, `Blower`) *and* escape hatches
(`CustomMethod`, `Unspecified`). Even a single DEXPI enumeration is not one
semantic dimension.

**H5 — `PumpingMethod` mixes a principle with its own realizations.**
`PositiveDisplacement` is a displacement *principle*, while `CentrifugalMotion`
/ `RotaryMotion` are motion *principles* and `Eductor` is an equipment *class* —
three different levels of abstraction in one enum.

**H6 — DEXPI reaches the same distinction through two different mechanisms.**
For mixing, the "how" distinction is expressed by **subclassing**
(`Mixing → RotaryMixing`, `Mixing → StaticMixing`) with **no** `Mixing.Method`
property at all. For compression, the same kind of distinction is expressed by a
**`Method` property** (`Compressing.Method`). DEXPI is internally inconsistent
about the mechanism used to express "how".

**H7 — Related packed-bed semantics appear through more than one DEXPI
construct.** `ReactingChemicals.Method = PackedBed` and the `ProcessStepDetail`
subclass `ContactingInPacking` both carry packed-bed-related semantics through
different DEXPI constructs (§6). This demonstrates semantic overlap across
constructs, but the inspected evidence does not establish that the two
statements are semantically equivalent.

### 5.5 Consequence for the "one reusable concept" question

At least four mutually incompatible conceptual dimensions are hidden behind the
one property name:

```text
1. motion mechanism            AxialMotion / CentrifugalMotion / ReciprocatingMotion
2. displacement principle      PositiveDisplacement
3. equipment technology        Plate / Spiral / Tubular / Fan / Blower / Ejector
                               Eductor / GasTurbine / StepperMotor
                               / AlternatingCurrent / DirectCurrent
4. intentional non-answer      Unspecified / CustomMethod / Generic
```

Dimensions 1 and 2 are *mechanism*, which is a property of the machine rather
than of the process statement: a `pumping` process function is the same
engineering statement whether the physical solution is centrifugal or
reciprocating. That is exactly the realization freedom ADR-0009 already
reserved — "a pumping function may later be realized by one pump, several pumps,
an ejector, gravity, or another physical solution". Dimension 3 is equipment
technology. Dimension 4 is not a classification at all.

There is **no single semantic concept** here to name.

## 6. `ProcessStepDetail` relationship

`ProcessStepDetail` is DEXPI's neighbouring construct, and inspecting it is
required evidence: if DEXPI already has a place for step refinement, a copied
`Method` field may be the wrong home for the distinction.

### 6.1 What `ProcessStepDetail` is

From `src/model/Process/Process/Process.py`, `V2.0.0`:

```text
ProcessStepDetail            ABSTRACT_CLASS
superTypes                   [Core.ConceptualObject]        (NOT ProcessStep)
definition                   "parent type for processes that
                              cannot be run independently of
                              another process"
composed by                  ProcessStep.ProcessStepDetails  0..*
referenced by                MeasuringProcessVariable.ProcessStepDetailReference 0..1
own properties               Description 1..1, Identifier 1..1, Label 1..1,
                             Pressure 0..*, Temperature 0..*
```

Concrete subtypes at `V2.0.0`:

```text
Agitating                        (shear forces to liquids)
ContactingInPacking              (packed bed; adds packing height / stages)
ContactingOnTray                 (assembly of trays; adds tray count)
SupplyingThermalEnergyWithBurner (combustion sub-process; realized by Burner)
```

### 6.2 The four mechanisms DEXPI uses, and what each means

| Mechanism | Semantic role | Example |
|---|---|---|
| `ProcessStep` subclass | *what kind of process function* this is — a class-level process-function category | `Pumping`, `Mixing`, `ExchangingThermalEnergy` |
| `ProcessStep.Method` | a class-local *qualifier* whose meaning changes per class, and which overlaps the physical model | `Plate`, `Fan`, `Diesel` |
| `ProcessStepDetail` | a **non-independent sub-process refinement of a step** — a composed child, not a classification of its parent; may itself carry quantity data | `ContactingInPacking`, `SupplyingThermalEnergyWithBurner` |
| `Plant.ProcessEquipment` subclass | physical realization / equipment technology | `PlateHeatExchanger`, `CentrifugalPump`, `Burner` |

Two conclusions follow directly, and both matter for DeepPlant:

1. **`ProcessStepDetail` is not a second classification axis on one step.** It
   is a *composition child* with lower bound `0` and unbounded upper bound, and
   its own definition says such a process "cannot be run independently of
   another process". It answers "which sub-processes make up this step", not
   "which variant of this function is this".
2. **`Method` is not `ProcessStepDetail` either.** `Method` is single-valued
   (`0..1` or `1..1`) and is a class-local qualifier of the step;
   `ProcessStepDetail` is a collection of children. H7 shows related packed-bed
   semantics through both constructs, without establishing equivalence, which is
   further evidence that `Method` is not a carefully factored reusable concept.

### 6.3 `HierarchyLevel`: a third, separate DEXPI axis

DEXPI also declares `ProcessStep.HierarchyLevel: ProcessStepHierarchyLevel`
(`0..1`) with literals `ProcessTrain`, `Process`, `ProcessSection`,
`UnitOperation`, `SupportFunction`, `ControlFunction`, `SafetyFunction`,
`ElementaryFunction`.

This is a *level-in-the-functional-breakdown* axis, distinct from both the class
identity and `Method`. Its existence is supporting evidence: where DEXPI wants
an explicit cross-cutting process-model classification, it can introduce its own
named property with its own enumeration rather than rely on the generic name
`Method`. That observation does not formally rule out another cross-cutting
concept, but the inspected heterogeneous `Method` inventory does not expose one.

### 6.4 What this slice does *not* do

`ProcessStepDetail` is **not mapped** here. DeepPlant has no step hierarchy, and
the existing adapter already rejects nested `ProcessStep` (`SubProcessSteps`)
explicitly for that reason. Whether DeepPlant ever needs a
step-refinement/sub-process concept is a separate question with its own evidence
requirement, and it is recorded as deferred work (§12).

## 7. Canonical-model requirements

### 7.1 Separating the five semantic layers

For every candidate classification this slice distinguishes:

```text
1. process function
2. process-function variant / principle
3. physical realization / equipment technology
4. operating / design parameter
5. presentation
```

Worked against the DEXPI values:

```text
function              = pumping
mechanism / principle = CentrifugalMotion / PositiveDisplacement
                                  → function-specific labels tightly associated
                                    with realization technology; this slice does
                                    not assign each one categorically to layer 3
physical realization  = CentrifugalPump                            → layer 3
parameters            = Head, VolumeFlow, ShaftPower, Efficiency    → layer 4
presentation          = pump symbol                                → layer 5
```

```text
function              = heat_exchange
Method                = Generic / Plate / Spiral / Tubular
```

The critical question was whether `Plate` / `Spiral` / `Tubular` describe a
**process principle** or a **physical exchanger realization / construction
technology**. The evidence answers it: these are **construction technology**,
because DEXPI models the same three names as the Plant equipment classes
`PlateHeatExchanger`, `SpiralHeatExchanger`, `TubularHeatExchanger` (§5.3). A
construction geometry is not a statement about the process; the process
statement ("thermal energy is transferred between two or more material
streams") is complete without it.

Concrete consequences of the layer separation:

- The inventory does not reveal one stable **layer-2** process-principle axis.
  `CentrifugalMotion` and `PositiveDisplacement` are function-specific
  mechanism/principle labels tightly associated with realization technology, but
  the inspected evidence does not establish a single canonical ownership layer
  for every such literal.
- Nothing in the inventory is a **layer-4** value. DEXPI keeps parameters
  strictly separate as qualified quantities (`Area`, `Duty`, `Head`,
  `VolumeFlow`, `Pressure`, `Temperature`, `ShaftPower`, `Efficiency`,
  `CompressionRatio`, `NumberOfStages`, …), which are explicitly out of scope
  for this slice (§12).
- Nothing in the inventory is a **layer-5** value. No literal is a symbol role,
  symbol-pack asset name, diagram coordinate, or `ShapeUsage`.
- Many literals overlap strongly with **layer-3** realization / equipment
  technology, while others are mechanism/principle labels or intentional
  non-answers (`Unspecified` / `CustomMethod` / `Generic`).

The inventory therefore does not reveal one stable layer-2 process-principle
axis or any other reusable ProcessStep classification. Its heterogeneous overlap
with realization semantics is strong evidence against automatically copying the
whole DEXPI `Method` set into `ProcessStep`, but this slice does not assign every
literal categorically to the physical-realization layer.

### 7.2 The DeepPlant-authoring test

A valid canonical field must survive this test:

```text
Would a process engineer author this concept in DeepPlant
even if DEXPI did not exist?
```

Applied honestly to the inventory, with DEXPI set aside:

| Candidate question an engineer might ask | Would it be authored as a *process-function* classification? |
|---|---|
| "Is this exchanger a plate, spiral, or tubular one?" | No — a question about the **equipment**, i.e. the physical realization |
| "Is this pump centrifugal or reciprocating?" | No — same reason; the process statement is unchanged |
| "Is this reactor a packed bed or a fluidized bed?" | No — a reactor arrangement / realization decision |
| "Is the driver a diesel engine or a gas turbine?" | No — a prime-mover technology choice |
| "Is the motor AC or DC?" | No — an electrical equipment technology choice |

The engineering value in these questions is real, and engineers do make these
decisions. But they make them while **selecting the physical solution**, which
DeepPlant's accepted boundaries already place outside `ProcessStep`
(ADR-0009: function `!=` physical realization; ADR-0011: realization is a
separate layer). None of them is an authored *process-function* statement.

So the answer is **no** for every candidate: no engineer authors a second
process-function classification here.

### 7.3 Adapter convenience is not a sufficient reason

The task is explicit: *do not add canonical semantics solely to improve adapter
round-trip.* Even if a `method` field would let more DEXPI content survive a
round-trip, that alone would not justify it. Two further reasons reinforce the
refusal:

- **A partial field would be worse than none.** Only 9 of the 22 `ProcessStep`
  children carry `Method`, and 5 of DeepPlant's 7 documented functions are
  untouched by it (§7.4). A generic canonical field would be populated for a
  minority of DEXPI classes and never for DeepPlant-native authored models.
- **The field would be write-only for DeepPlant.** Nothing in the current
  canonical model, renderer, or validation would read it. `ProcessStep.function`
  is read by the renderer's presentation policy; a second classification would
  have no consumer, which is the definition of speculative schema.

### 7.4 Implications for existing supported canonical functions

Nothing in this decision changes any existing function. The assessment per
function is:

| Canonical function | DEXPI class carrying `Method`? | Would a second classification have meaningful DeepPlant-native values? |
|---|---|---|
| `source` | No — `Source` declares no `Method` | No second classification exists to consider |
| `sink` | No — `Sink` declares no `Method` | same |
| `splitting_material` | No — `SplittingMaterial` declares no `Method` | same |
| `mixing` | No `Mixing.Method`; DEXPI expresses the variant by **subclass** (`RotaryMixing`, `StaticMixing`) | Only via DEXPI class identity, which overlaps realization rather than naming a DeepPlant classification |
| `pumping` | Yes — `Pumping.Method`, `0..1`, `PumpingMethod` | The values are machine kinds/mechanisms that substantially overlap realization; no process-function value |
| `heat_exchange` | Yes — `ExchangingThermalEnergy.Method` `1..1`, `RemovingThermalEnergy.Method` `1..1`, `SupplyingThermalEnergy.Method` `0..1`, all `HeatExchangeMethod` | The values are exchanger construction geometry that substantially overlaps realization; no process-function value |
| `unspecified` | No DEXPI counterpart | out of scope |

This confirms the "a generic canonical field is probably not justified" test: a
second classification is meaningful for only **two** of the seven documented
functions, and in both cases the candidate values substantially overlap
physical realization rather than expressing an equipment-independent process
principle.

## 8. Candidate designs compared

### 8.1 Candidate A — no canonical second classification

```text
ProcessStep
├── id
├── function
├── name
└── ports
```

DEXPI `Method` remains adapter-unsupported where it is required.

**Advantages**

- `ProcessStep.function` stays the single, honest step-classification axis
  (ADR-0009 unchanged and not weakened).
- No field is added without a consumer, a DeepPlant-native value domain, or an
  authoring workflow (§7.2, §7.3).
- The process model does not absorb a heterogeneous DEXPI vocabulary merely
  because part of it overlaps physical realization; realization stays with the
  layer ADR-0009 deferred and ADR-0011 owns, and any future ownership there
  remains evidence-backed.
- Failure remains explicit and honest: a required-but-unrepresentable DEXPI
  value still raises a named error rather than being silently dropped or
  invented, which is the behaviour the existing adapter already implements and
  the negative fixtures already pin.

**Losses (explicit)**

- DEXPI `ExchangingThermalEnergy`, `RemovingThermalEnergy`, `Compressing`,
  `ReactingChemicals`, and `DrivingByTurbine` stay unimportable/unexportable
  while `Method` is mandatory in DEXPI, because a required DEXPI fact cannot be
  represented.
- No DEXPI round-trip is claimed for those classes.
- Information loss is real for pure DEXPI interchange. This is accepted because
  the `Method` vocabulary is heterogeneous: many values substantially overlap
  physical-realization / equipment-technology semantics, while others are
  function-specific mechanism/principle labels. DeepPlant has no honest generic
  canonical home for the whole set today, so recording it in `ProcessStep`
  would misstate the process statement rather than merely store it at lower
  fidelity.

### 8.2 Candidate B — generic second classification

```text
ProcessStep
├── function
└── principle / variant / method: str | None   (name not chosen)
```

**Assessment: rejected.** One value namespace cannot be semantically coherent
across different functions here, and the failure is demonstrated, not
theoretical:

- The DEXPI evidence provides **seven** enumeration types with overlapping but
  non-identical literal sets (§4.2). A single canonical namespace would have to
  union `Plate`/`Spiral`/`Tubular` with `Fan`/`Blower`/`Ejector` with
  `PositiveDisplacement` with `OttoCycle` with `AlternatingCurrent` with
  `WindTurbine`. That union has no semantic coherence: the values do not answer
  one question.
- `Unspecified` and `CustomMethod` are per-enum escape hatches. In a shared
  namespace they would collide with each other and with the `None` default,
  making three different "not answered" states indistinguishable.
- The stated key risk — *a generic string becomes a dumping ground* — is not
  hypothetical. `CompressionMethod` already demonstrates the dumping behaviour
  inside DEXPI itself (H4).
- Even the "would an engineer author it" test fails for the union (§7.2).

### 8.3 Candidate C — function-specific semantic details

```text
ProcessStep
├── function
└── details
    └── function-specific semantic structure
```

**Assessment: rejected for now, and the evidence says the boundary is the wrong
one anyway.** The key question — *are `Method` values inherently
function-specific?* — is answered **yes** (§5.2, H1), which does argue that any
future concept must be function-scoped rather than generic. But that is not
sufficient to justify building it, because:

- Function-scoping alone does not make a value a *process* concept. Many values
  for `heat_exchange`, `pumping`, `compressing`, and `reacting_chemicals` overlap
  physical realization, while others are function-specific mechanism/principle
  labels (§5.3, §7.1). A function-specific detail structure is not justified
  without evidence that a DeepPlant-native process concept needs it.
- It requires a polymorphic detail framework (per-function schemas, per-function
  validation, discriminated unions, serialization rules) that the current
  `script`-level, `lightweight`-governance project has no requirement for, and
  the task explicitly forbids designing a generic polymorphic framework here.
- No consumer exists (§7.3), and no real DeepPlant example fragment needs it.

The **direction** is nevertheless recorded as the smallest future shape *if*
evidence ever changes: a function-scoped structure, never a global union. It is
not authorized (§12).

### 8.4 Candidate D — realization-layer concept

```text
ProcessStep ──(mapping, not a field)──> physical realization
```

**Assessment: Candidate D explains an important subset of the evidence, and it
is not a reason to add anything to `ProcessStep`.** Many `Method` values
correspond directly or approximately to equipment technology or
physical-realization choices. Candidate D is therefore a plausible future home
for part of the vocabulary, but the evidence does not prove that it owns every
literal.

Outcome A is the accepted canonical boundary now; Candidate D is a possible
future destination for relevant semantics, not an alternative implementation
selected by this ADR. The Process ↔ physical-realization implementation is
explicitly **not** done here — no `realized_by`, no `ProcessStep` → `Equipment`
reference, and no realization-layer change. It already sits in ADR-0009's and
ADR-0011's deferred lists and needs its own evidence and its own Issue.

### 8.5 Comparison summary

| Candidate | DeepPlant-native value? | Consumer exists? | Production-ready now? | Verdict |
|---|---|---|---|---|
| A — no second classification | n/a (nothing added) | n/a | yes | **selected** |
| B — generic second classification | no | no | no | rejected (incoherent union) |
| C — function-specific details | not established as a process classification | no | no | rejected now; direction recorded |
| D — realization-layer concept | plausible for part of the vocabulary | no (physical layer incomplete) | no | possible future destination; not implemented |

## 9. Rejected shortcuts

Each of the following was considered and rejected explicitly, with the reason:

| Shortcut | Why rejected |
|---|---|
| `method: str \| None` on `ProcessStep`, added because DEXPI has a property named `Method` | Copies a DEXPI property name into the canonical model on the strength of the name alone. §4.2 and §5 show the name carries at least four different meanings; the field would have no coherent value domain, no consumer, and no DeepPlant-native authoring workflow. |
| `attributes: dict[str, Any]` / `properties` / `metadata` / `details` bag to absorb unknown DEXPI semantics | Destroys the fail-fast semantic contract that makes the model usable: unknown fields are currently rejected so typos and unsupported engineering data cannot be silently discarded. A bag would make every unsupported DEXPI fact silently representable and silently meaningless. |
| `ProcessStepMethod` enum that unions the DEXPI `*Method` enums | Creates exactly the incoherent union §8.2 shows cannot be semantically coherent, and freezes a DEXPI-derived vocabulary into DeepPlant's canonical model, making DEXPI the model owner. |
| Generic `Property` / `Attribute` / `Entity` / semantic extension bag / generic schema framework | The task forbids it; it also contradicts ADR-0002 and the project rule to introduce abstractions only when justified, and no current requirement needs it. |
| Renaming or widening `ProcessStep.function` to also carry the variant (for example `"pumping:centrifugal"` or a second `function_detail` string) | Collapses two layers into one field, so the model can no longer tell a process statement from an equipment choice. That would weaken ADR-0009, which this slice must not do, and would make `function` unrenderable by the existing policy mapping. |
| Storing the DEXPI class name or XML enumeration name on the step for round-trip fidelity | Makes an external representation the canonical identity (ADR-0009 rejects `function` as a DEXPI class identifier) and would let adapter convenience drive the domain model. |
| Declaring the `Method` question "out of scope" without recording the decision | Loses the reasoning, leaves the recurring blocker unexplained, and guarantees the same investigation is repeated by the next DEXPI slice. |

## 10. Decision

**Outcome A — no generic second `ProcessStep` classification is justified.**

```text
DEXPI Method remains adapter-specific / unsupported where DEXPI requires it.
No DeepPlant field is added.
ProcessStep.function remains the only canonical step-classification axis.
```

Stated precisely, and independently of DEXPI adapter convenience:

1. **`ProcessStep` gains no second classification field**, and no name for one
   is reserved.
2. **`ProcessStep.function` is unchanged** and remains an open, non-empty
   string. ADR-0009 is preserved, not weakened.
3. **The DEXPI `Method` properties are not one reusable engineering concept.**
   They span seven heterogeneous enumeration domains across nine properties and
   mix mechanism/principle labels, equipment technology or construction, and
   non-answers (§5).
4. **Many values overlap physical realization / equipment technology, while
   others express function-specific mechanisms or principles.** This ADR does
   not assign every `Method` literal to one future layer. The heterogeneous
   inventory does not expose one reusable cross-cutting `ProcessStep`
   classification, which establishes Outcome A rather than merely defaulting to
   it.
5. **They are not presentation values.** No literal is a symbol role or graphical
   asset, so the ADR-0009 presentation boundary is untouched.
6. **They are not qualified quantities**, which stay a separate, deferred
   question (§12).
7. **The decision is durable, not tactical.** It is a canonical-model boundary
   ("canonical `ProcessStep` currently has exactly one classification axis, and
   no generic second classification is justified"), so it is recorded as
   **ADR-0012**. The seven DEXPI enumeration domains are adapter observations —
   those are recorded in this document, not in the ADR.
8. **No implementation follows.** No production-code change, no adapter change,
   no dependency change, and no runtime test is added or modified by this slice.

## 11. Adapter implications

**No adapter change is made by this slice** (`src/deepplant/adapters/dexpi.py`
is untouched). The consequences of the decision for the existing adapter are
limited to confirming its current behaviour:

1. **The supported subset is unchanged.** `Source`, `Sink`, `Mixing`,
   `SplittingMaterial`, and `Pumping` keep their current mapping to `source`,
   `sink`, `mixing`, `splitting_material`, and `pumping`. None of those five
   classes requires `Method` for the supported material-port-only subset, so
   nothing about the decision forces a change.
2. **`Pumping.Method` remains unsupported when populated.** It is optional
   (`0..1`) in DEXPI, so a populated value continues to fail explicitly rather
   than being dropped. That behaviour is correct under Outcome A: DeepPlant has
   no honest place to put it.
3. **The mandatory-`Method` classes stay explicitly unsupported** —
   `ExchangingThermalEnergy`, `RemovingThermalEnergy`, `Compressing`,
   `ReactingChemicals`, and `DrivingByTurbine`. Outcome A does not create a
   mapping for them; it explains *why* one cannot honestly exist today, which is
   the durable answer the recurring blocker needed.
4. **Diagnostics remain fail-closed and named.** A required-but-unrepresentable
   `Method` must keep raising an error that names the DEXPI class and the
   property. Silently omitting a `1..1` DEXPI property would be semantic
   invention, not import.
5. **A future revision is possible without rework.** Some values may later find
   an honest home in a physical-realization or function-specific model, through
   explicit evidence and modelling rather than a generic `ProcessStep` field.
   Candidate A therefore does not permanently foreclose DEXPI class coverage or
   a justified process-level distinction.

## 12. Deferred work

Nothing below is authorized by this document. Each item needs its own evidence
and its own Issue.

| Deferred item | Why deferred | Owner of the decision |
|---|---|---|
| **Qualified engineering quantities (C-3)** — `QualifiedValue`, units, `Duty`, `Area`, `Head`, `VolumeFlow`, `Pressure`, `Temperature`, mass flow, engineering unit conversion | Explicitly out of scope for this slice: the only question here was the classification semantic. DEXPI requires these on the same classes, so they are the remaining model-level blocker. They deserve their own decision slice and must not be solved as part of a classification slice or as a units-library design. | its own decision Issue |
| **Physical realization / equipment technology** — a plausible future home for `Plate`/`Tubular`/`Fan`/`Diesel`/`AlternatingCurrent`-style values, and the Process ↔ physical realization mapping | Requires its own evidence and its own Issue; ADR-0009 and ADR-0011 explicitly leave Process ↔ physical realization undecided. No `realized_by` field, no `ProcessStep` → `Equipment` reference, and no realization-layer change is made here. | ADR-0009 / ADR-0011 Revisit-When lists |
| **`ProcessStepDetail` mapping** — `Agitating`, `ContactingInPacking`, `ContactingOnTray`, `SupplyingThermalEnergyWithBurner`, `MeasuringProcessVariable.ProcessStepDetailReference` | Investigated here as neighbouring evidence only (§6). DeepPlant has no step hierarchy or sub-process concept, and the adapter already rejects nested `ProcessStep` for that reason. Not mapped. | a separate Issue if evidence appears |
| **Function-specific semantic details (candidate C)** | Rejected now because no DeepPlant-native process classification or consumer justifies it (§8.3). Only the *direction* is recorded: if evidence changes, the shape must be function-scoped, never a global union. | a separate decision Issue with new evidence |
| **`StoringMaterial` storage classes (Issue #21)** | Remains a separate slice. Not implemented here, not closed here, and not turned into another per-class DEXPI mapping spike. Storage semantics were not needed as evidence for the classification boundary. | Issue #21 |
| **DEXPI Process subset expansion** | Not claimed. No additional DEXPI class became supported, and no round-trip is newly claimed. | roadmap backlog, evidence-driven |

## 13. Revisit-when conditions

Reconsider a second canonical classification only if at least one of the
following becomes true, and reopen the question with **new** evidence rather
than re-reading the same enumerations:

1. **A DeepPlant-native authoring need appears.** A real, realistic DeepPlant
   example fragment — authored as YAML, with no DEXPI file in the loop — needs
   to state a *process-level* distinction that `ProcessStep.function` genuinely
   cannot express. Test applied: the distinction must not merely restate an
   equipment mechanism or physical-realization choice; a genuine
   equipment-independent process principle with a DeepPlant-native consumer
   remains valid revisit evidence.
2. **Simulation, calculation, engineering rules, or design workflows require a
   function-specific process principle independent of equipment realization.**
   This must demonstrate a DeepPlant-native consumer, not merely DEXPI naming.
3. **The physical-realization layer is designed and implemented**, and new
   evidence establishes an honest home there for relevant values or demonstrates
   that one cannot be placed there.
4. **Future DEXPI evidence exposes a coherent cross-cutting semantic axis.** For
   example, a later release could replace the per-class `*Method` enumerations
   with a coherent, equipment-independent process-principle axis.
5. **`ProcessStepDetail` semantics are mapped**, and doing so reveals a
   genuinely process-level refinement concept that `ProcessStep.function` cannot
   express and that is not physical realization.

Absent all five, canonical `ProcessStep` currently keeps exactly one
classification axis.

## 14. Quality gates and scope verification

Run on `research/issue-31-process-step-classification` before the pull request:

```bash
make validate-docs
make validate-agent-skills
make check        # ruff format --check, ruff check, pyright, pytest
uv build          # wheel + sdist build (uv.lock unchanged)
```

Scope verification for this slice:

| Expectation | Actual |
|---|---|
| production-code changes (`src/deepplant/model.py`, `io.py`, `render.py`, `adapters/dexpi.py`) | **none** |
| adapter mapping changes | **none** |
| new runtime tests | **none** |
| changed runtime tests | **none** |
| dependency changes | **none** |
| test count | **352** (unchanged from the post-PR-#30 baseline) |

All tests run offline; the DEXPI inspection happened during development only.
No DEXPI content is vendored, and the analysis used only the official `V2.0.0`
sources listed in §3.1, under CC BY 4.0 attribution.
## 15. Roadmap check

- **Completed by this slice:** the Issue #31 decision question — whether
  canonical DeepPlant needs a second process-step classification concept beside
  `ProcessStep.function`. The answer is recorded above as Outcome A with pinned
  authoritative evidence, the semantic comparison, the four candidate shapes,
  the rejected shortcuts, and an ADR. The recurring model-level blocker from
  Issue #22 is now explained and decided instead of re-inherited by the next
  DEXPI slice.
- **Not completed:** the "expand the DEXPI Process subset" backlog row. No
  additional DEXPI class became supported, no round-trip is newly claimed, and
  no runtime capability changed. The row's `ExchangingThermalEnergy` status is
  unchanged and the remaining candidates (`StoringMaterial`, quantity
  representation) stay open.
- **No canonical-model, adapter-mapping, example, or dependency change was
  made**, so no milestone state changed and no other roadmap row became
  complete.
- **Next task:** the remaining model-level half of the same Issue #22 finding —
  qualified engineering quantities (C-3). Issue #22's blockers were the
  non-derivable step classification *and* the absence of any canonical
  qualified-quantity representation; this slice closes the first and deliberately
  leaves the second untouched (§12). The classification half closing is what
  makes the quantity half the concrete next evidence-producing step rather than
  a speculative one. It is recorded as an evidence-backed candidate, not
  authorized here, and `StoringMaterial` (Issue #21) remains a separate slice.
- **Why this follows from the current repository state:** three earlier DEXPI
  slices and Issue #22 converged on the same two model-level blockers from
  different directions. This slice demonstrates that the classification half is
  not a real canonical concept — the `Method` vocabulary is heterogeneous and
  only partially overlaps physical-realization semantics — so no model growth is
  warranted there and no
  further per-class adapter probing on `Method` can produce progress. The only
  remaining model-level blocker of that pair is the quantity representation.
  Do not mechanically promote a backlog row.


