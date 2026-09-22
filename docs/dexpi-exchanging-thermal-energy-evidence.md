---
type: spike-report
status: active
source_of_truth_for:
  - dexpi-2-exchanging-thermal-energy-mapping-evidence
read_when:
  - interoperability-work
  - dexpi-version-pinning
  - process-function-vocabulary-work
  - adapter-boundary-work
update_when:
  - dexpi-model-change
  - canonical-model-change
  - adapter-change
---

# DEXPI 2.x `ExchangingThermalEnergy` Semantic Mapping Evidence (Issue #22)

> This document is the primary analysis deliverable of Issue #22, an
> **evidence-first interoperability slice**. It is not documentation of a
> delivered mapping, and it authorizes no implementation by itself.
>
> Question under investigation: can DEXPI `ExchangingThermalEnergy` be mapped
> honestly to canonical DeepPlant `ProcessStep(function="heat_exchange")`, and
> can import, export, and semantic round-trip be claimed?
>
> **Answer: no mapping is claimed today.** The class-level engineering function
> does correspond to canonical `heat_exchange` as a *process function* (both are
> process-function statements, not equipment, not symbols, and not physical
> realization), but the canonical model cannot carry the semantics the DEXPI
> class requires. `ExchangingThermalEnergy` therefore stays **explicitly
> unsupported** for import, export, and semantic round-trip. Canonical
> `heat_exchange` stays DeepPlant-native and is **not** claimed to equal the
> DEXPI class.
>
> The exact gap is recorded in §6, the smallest justified model change is
> proposed — and deliberately **not authorized** — in §7, and the executable
> guardrails that ship with this slice are in §8.
>
> This document deliberately does not force the "existing model is sufficient"
> outcome. A DEXPI class name, a heat-exchanger symbol, and the existing
> DeepPlant `function="heat_exchange"` value are three different things, and
> none of them proves semantic equivalence.

## 1. Targeted DEXPI release (pinned)

Policy applied: *stable release exists → target the latest stable release;
beta/RC newer than stable → inspect but do not make the production target unless
strongly justified.* This is the same policy and the same pin already used by
[dexpi-process-spike.md](dexpi-process-spike.md) and
[dexpi-plant-pid-spike.md](dexpi-plant-pid-spike.md); no re-pinning is performed.

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
| DeepPlant evidence baseline | branch `research/issue-22-exchanging-thermal-energy`, created from `origin/main` |

### Tag object versus release commit

The official GitLab tags API reports `V2.0.0` as a tag whose `target` is
`dc74c370645651b4a4f691c79723710657472c6d`, while the annotated tag's own commit
object is `260c81c51039789a6148a98af4c6caf23f87a3e2` ("Merge branch
'spec_2.0.0-rc2' into 'master'", authored 2025-10-10; release
`DEXPI Specification 2.0.0`, `upcoming_release: false`). DeepPlant's existing
adapter constant, fixture attribution record, and both earlier spike documents
use `260c81c…`. This document keeps that established revision and records the
distinction rather than silently substituting one identifier for the other,
because the two are not interchangeable as provenance statements.

### Version state on the inspection date

- The latest stable tagged 2.x release is still `V2.0.0`; the tags API returns
  `V2.0.0`, `V1.4.0`, `V1.3.0`, `1.2`.
- DEXPI 2.0.1 is still not released. The official DEXPI August 2026 update
  (2026-08-25) states that 2.0.1 "is being prepared" and "particularly addresses
  corrections and clarifications in the Process Model". The Process-model
  clarification risk recorded by the earlier spikes therefore still applies to
  every finding below.

### Sources inspected

1. `https://gitlab.com/dexpi/Specification` — releases/tags API (version state
   and tag/commit provenance) and the `V2.0.0` tree.
2. `src/model/Process/Process/Process.py` — the authoritative Process model
   definition: `ExchangingThermalEnergy`, `ProcessStep`, `Port` and its concrete
   subclasses, `ProcessConnection`, `Stream`, `EnergyFlow` and subclasses.
3. `src/model/Process/Process.py` — the Process model/package entry
   (`ProcessModel` composition properties; model URI
   `https://data.dexpi.org/models/2.0.0/Process.xml`).
4. `src/model/Process/Enumerations/Enumerations.py` and
   `src/model/Process/Enumerations/process_enumerations.ods` — the
   `HeatExchangeMethod` and `PortDirection` literal sets.
5. `src/model/Core/Core.py` — `Core.ConceptualObject`, `Core.ConceptualModel`,
   `Core.Role` (the role mechanism referenced by the Process port classes).
6. `src/documentation/index.rst` — repository licence statement (CC BY 4.0).

No official DEXPI **instance** file for the 2.0 Process model was found in the
authoritative repository; the only XML files upstream under `V2.0.0` are
`src/documentation/_static/DEXPI_XML_Schema.xsd` (the generic envelope schema)
and `src/documentation/_static/reference_pid.xml` (a Plant/P&ID instance). That
limitation is inherited from the earlier spikes and is not resolved here.

**Licence and provenance policy applied (ADR-0007, [standards.md](standards.md)).**
DEXPI 2.0.0 is published under CC BY 4.0, which permits use with attribution, so
the official model definitions may be inspected for this analysis. This document
reproduces only class names, property names, multiplicities, type references,
and the class's two-sentence definition — the minimum needed to make the
engineering judgement auditable. No DEXPI figures, symbol artwork, PDF text, or
substantial normative prose is copied, and no DEXPI content is vendored.

**Version-mixing policy.** Every DEXPI statement below comes from the single
pinned `V2.0.0` release. No DEXPI 1.x, Proteus-era, pyDEXPI, or 2.0.1-preview
semantics is mixed in. Where a statement is DeepPlant's own engineering
inference rather than an upstream fact, it is labelled as such.

## 2. Authoritative definition of `ExchangingThermalEnergy`

Source: `src/model/Process/Process/Process.py`, DEXPI Specification `V2.0.0`,
release commit `260c81c51039789a6148a98af4c6caf23f87a3e2`.

### 2.1 Class identity, category, and definition

```text
ExchangingThermalEnergy     CONCRETE_CLASS
superTypes                  [Process.Process.ProcessStep]   (abstract)
package                     Process.Process
```

Class description, quoted from the pinned model definition (DEXPI Specification
2.0.0, CC BY 4.0, DEXPI e.V.):

> "This process transfers thermal energy between two or more streams of
> material. This process is realized by a heat exchanger."

Three facts follow directly, and they are decisive for the mapping question:

1. **Its semantic category is `ProcessStep`.** It is a *process function* in the
   DEXPI **Process** model. It is not a `Plant`/P&ID object, not equipment, not
   piping, and not a symbol or `ShapeUsage`. This corroborates, from the
   opposite direction, the DeepPlant invariant recorded in ADR-0009: an
   engineering process function is neither an equipment type nor a presentation
   role.
2. **It is defined over "two or more streams of material".** Participation of
   multiple material flows is explicit in the definition, and their thermal
   coupling is the point of the class.
3. **"Realized by a heat exchanger" is realization language, not identity.**
   "Realized by a heat exchanger" establishes that the process statement and its
   physical realization are distinct concepts. The inspected DEXPI Process-model
   evidence does not establish physical-realization identity or cardinality here;
   DeepPlant therefore must not infer 1:1, 1:N, N:1, or N:M from this class
   definition. This again matches DeepPlant's function ≠ physical-realization
   invariant.

### 2.2 Properties owned by `ExchangingThermalEnergy`

`lower` / `upper` are the DEXPI model multiplicities; `upper=None` means
unbounded. All quantities are *qualified values* (value plus unit).

| Property | Kind | Type / unit type | lower | upper |
|---|---|---|---|---|
| `Area` | `COMPOSITION_PROPERTY` | `QualifiedValue[PhysicalQuantity[AreaUnit]]` | 0 | None |
| `ColdFlow` | `COMPOSITION_PROPERTY` | `QualifiedValue[PhysicalQuantity[MassFlowRateUnit]]` | 0 | None |
| `Duty` | `COMPOSITION_PROPERTY` | `QualifiedValue[PhysicalQuantity[PowerUnit]]` | 0 | None |
| `HeatTransferCoefficient` | `COMPOSITION_PROPERTY` | `QualifiedValue[PhysicalQuantity[HeatTransferCoefficientUnit]]` | 0 | None |
| `HeatTransferResistance` | `COMPOSITION_PROPERTY` | `QualifiedValue[PhysicalQuantity[HeatTransferResistanceUnit]]` | 0 | None |
| `HotFlow` | `COMPOSITION_PROPERTY` | `QualifiedValue[PhysicalQuantity[MassFlowRateUnit]]` | 0 | None |
| `Method` | `DATA_PROPERTY` | `Enumerations.HeatExchangeMethod` | **1** | **1** |
| `SkinTemperature` | `COMPOSITION_PROPERTY` | `QualifiedValue[PhysicalQuantity[TemperatureUnit]]` | 0 | None |
| `TemperatureDifference` | `COMPOSITION_PROPERTY` | `QualifiedValue[PhysicalQuantity[TemperatureUnit]]` | 0 | None |

Two findings in this table drive the decision:

- **`Method` is mandatory (`lower=1, upper=1`).** A conforming
  `ExchangingThermalEnergy` carries exactly one `HeatExchangeMethod` value. The
  literal set, read from the authoritative `process_enumerations.ods` used to
  build that enumeration, is:

  ```text
  HeatExchangeMethod = Generic | Plate | Spiral | Tubular
  ```

- **Every quantitative property is a qualified physical quantity.** `HotFlow`
  and `ColdFlow` are step-level qualified mass-flow quantities representing hot-
  and cold-side engineering values. They do not reference `ProcessPort`s and
  therefore do not identify which ports belong to the respective thermal sides.
  Nothing in this set has a canonical DeepPlant representation today.


### 2.3 Properties inherited from `ProcessStep`

`ExchangingThermalEnergy` declares no port property of its own; ports come from
the abstract parent.

| Property | Kind | Type | lower | upper |
|---|---|---|---|---|
| `Identifier` | `DATA_PROPERTY` | `String` | 1 | 1 |
| `Label` | `DATA_PROPERTY` | `Undefined \| String` | 0 | 1 |
| `Description` | `DATA_PROPERTY` | `MultiLanguageString` | 0 | 1 |
| `HierarchyLevel` | `DATA_PROPERTY` | `Undefined \| ProcessStepHierarchyLevel` | 0 | 1 |
| `Ports` | `COMPOSITION_PROPERTY` | `Port` | 0 | None |
| `SubProcessSteps` | `COMPOSITION_PROPERTY` | `ProcessStep` | 0 | None |
| `Pressure` | `COMPOSITION_PROPERTY` | `QualifiedValue[PhysicalQuantity[PressureAbsoluteUnit]]` | 0 | None |
| `Temperature` | `COMPOSITION_PROPERTY` | `QualifiedValue[PhysicalQuantity[TemperatureUnit]]` | 0 | None |
| `AmbientPressure` | `COMPOSITION_PROPERTY` | `QualifiedValue[PhysicalQuantity[PressureAbsoluteUnit]]` | 0 | None |
| `AmbientTemperature` | `COMPOSITION_PROPERTY` | `QualifiedValue[PhysicalQuantity[TemperatureUnit]]` | 0 | None |
| `ProcessStepDetails` | `COMPOSITION_PROPERTY` | `ProcessStepDetail` | 0 | None |

`ProcessStep` itself is `ABSTRACT_CLASS`, `superTypes=[Core.ConceptualObject]`,
described upstream as the parent type for all process steps in the model.
Inherited from `Core.ConceptualObject` (besides `PersistentIdentifiers`) is the
optional `PerformedRoles` reference to `Core.Role`, whose mandatory
`Core.Role.Name` is a `String`. That is DEXPI's mechanism for attaching an
engineering *role* to a step or to a port.

**Decision-relevant observation.** The thermal coupling between the
participating flows is **not** expressed by any property. It is expressed by the
existence of one step owning several material ports. There is no
`HotSide`/`ColdSide` port class and no structural reference that groups material
ports into thermal sides. `HotFlow` and `ColdFlow` are step-level quantities, not
port references. Optional `Core.Role` metadata may provide additional role
information, but it is not a structural side-grouping model.

## 3. Surrounding model context the mapping depends on

### 3.1 `Port` and its concrete subclasses

```text
Port                      ABSTRACT_CLASS, superTypes=[Core.ConceptualObject]
  EnergyPort              CONCRETE_CLASS, superTypes=[Port]
    ElectricalEnergyPort  CONCRETE_CLASS, superTypes=[EnergyPort]
    MechanicalEnergyPort  CONCRETE_CLASS, superTypes=[EnergyPort]
    ThermalEnergyPort     CONCRETE_CLASS, superTypes=[EnergyPort]
  InformationPort         CONCRETE_CLASS, superTypes=[Port]
  MaterialPort            CONCRETE_CLASS, superTypes=[Port]
```

Upstream description of `Port` (quoted, DEXPI Specification 2.0.0, CC BY 4.0):

> "A port represents a transfer of material, energy or information into or out
> of a process step. It provides the anchor point for connecting two process
> steps to each other."

`Port` properties:

| Property | Kind | Type | lower | upper |
|---|---|---|---|---|
| `Identifier` | `DATA_PROPERTY` | `String` | 1 | 1 |
| `NominalDirection` | `DATA_PROPERTY` | `Enumerations.PortDirection` | 1 | 1 |
| `Description` | `DATA_PROPERTY` | `MultiLanguageString` | 0 | 1 |
| `SubReference` | `COMPOSITION_PROPERTY` | `Port` | 0 | None |
| `ConnectorReference` | `REFERENCE_PROPERTY` | `ProcessConnection` | 1 | 1 (upstream `TODO check multiplicities`) |
| `SuperReference` | `REFERENCE_PROPERTY` | `Port` | 0 | 1 |

`PortDirection` literals (from `process_enumerations.ods`):

```text
PortDirection = Inlet | Outlet
```

`NominalDirection` is **mandatory on every port**. That is the same fact the
already-shipped DEXPI Process adapter relies on when it refuses to export a port
that has no incident stream.

Three concrete port classes matter for thermal mapping:

- `MaterialPort` — models "the transfer of material, of whatever form, into or
  out of a ProcessStep object", used for the flow of solids, liquids and gases.
  It carries an optional `MaterialTemplateReference`. Its description lists
  non-normative suggested `Core.Role` names (for example `Feed`, `Product`,
  `Inlet`, `Outlet`, `VapourInlet`, `LiquidOutlet`) that a modeller *may* use to
  name which service a port carries.
- `ThermalEnergyPort` — "exchanges heat or thermal energy between processes",
  with suggested role names `Input` and `Output`.
- `EnergyPort` — the general energy port of unspecified form, described upstream
  as abstract in practice.

### 3.2 Connections: `ProcessConnection` and the flow subclasses

```text
ProcessConnection         ABSTRACT_CLASS, superTypes=[Core.ConceptualObject]
  Stream                  CONCRETE_CLASS             (material flow)
  EnergyFlow              CONCRETE_CLASS
    ElectricalEnergyFlow  CONCRETE_CLASS
    MechanicalEnergyFlow  CONCRETE_CLASS
    ThermalEnergyFlow     CONCRETE_CLASS
  InformationFlow         CONCRETE_CLASS
```

`ProcessConnection` owns `Identifier` (1..1), `Label` (1..1),
`Description` (0..1) and the reference properties `Source` (1..1) and `Target`
(1..1), both typed `Port`. `EnergyFlow` adds an optional `Duty` (`PowerUnit`);
`ThermalEnergyFlow` adds an optional `Temperature`.

So a **thermal utility connection is a first-class DEXPI object**: a
`ThermalEnergyFlow` between `ThermalEnergyPort` objects, carrying `Duty` and
`Temperature`. It is not a material `Stream`, and it is not an attribute of the
exchanging step.

### 3.3 Related thermal step classes (context only)

The same model also defines `RemovingThermalEnergy` and `SupplyingThermalEnergy`
families — for example `Cooling`, whose description says it reduces enthalpy
"through heat exchange with the environment or a cooling medium" and explicitly
points to `ExchangingThermalEnergy`, "which can be used to model the same
process in cases where the cooling medium system is defined". This is evidence
that in DEXPI **whether the utility side is modelled is a modelling choice**,
and that the material-side function can be stated without it. It is not evidence
that the classes are interchangeable in DeepPlant, and none of them is mapped.

## 4. The Issue #22 question list, answered

Every answer below is traceable to §2/§3 (verified from the pinned official
model) or is explicitly labelled as DeepPlant engineering inference.

| Question | Answer | Basis |
|---|---|---|
| What superclass / semantic category does it belong to? | Concrete subclass of the abstract `Process.Process.ProcessStep` in the DEXPI **Process** model. A process function, not equipment, not piping, not presentation. | §2.1 |
| What does the class mean in engineering terms? | A step that transfers thermal energy between two or more material streams, physically realized by a heat exchanger. | §2.1 |
| What ports or connection concepts does it own? | No port property of its own; it owns `Ports[0..*]` through `ProcessStep`. Ports are `MaterialPort` / `EnergyPort` (`ThermalEnergyPort`, …) / `InformationPort`. Ports are connected by `ProcessConnection` subclasses via `Source`/`Target`. | §2.3, §3.1, §3.2 |
| How are thermal sides represented? | There is no structural `HotSide`/`ColdSide` port class or inlet/outlet pairing relation. `HotFlow` and `ColdFlow` are step-level qualified mass-flow quantities, not port references. Optional `Core.Role` metadata may add role information, but the inspected model does not structurally group ports into thermal sides. | §2.2, §2.3 |
| Is material flow represented through the object itself? | No. Material flow is represented by `MaterialPort` children joined by `Stream` connections. The step owns ports and properties, not flow objects. | §2.3, §3.2 |
| Is energy transfer represented explicitly? | Yes, and separately from material flow: `ThermalEnergyFlow` between `ThermalEnergyPort` objects carries `Duty` and `Temperature`. The step itself can additionally carry `Duty`. | §2.2, §3.2 |
| Is one object necessarily one physical heat exchanger? | The Process-model evidence establishes that `ExchangingThermalEnergy` is a `ProcessStep` and refers separately to physical realization by a heat exchanger. It does not establish realization identity or cardinality, so DeepPlant must not infer 1:1, 1:N, N:1, or N:M. | §2.1 |
| Can one object represent a process function independent of equipment? | Yes. It lives in the Process model, which is independent of the Plant/P&ID model. | §2.1 |
| Are hot/cold sides distinguished? | Hot/cold engineering quantities exist through `HotFlow` / `ColdFlow`, but the material ports themselves are not structurally grouped into hot and cold sides. Optional `Core.Role` metadata may add role information. | §2.2, §2.3 |
| Are inlet/outlet roles explicit or derived? | **Explicit and mandatory.** `Port.NominalDirection: PortDirection` with literals `Inlet` / `Outlet` is `1..1` on every port. | §3.1 |
| Is thermal coupling represented? | Yes, but only implicitly, by the *existence* of one step owning several material ports. No property or reference states that port A couples to port B. | §2.3 |
| Can multiple material streams participate? | Yes, explicitly: "two or more streams of material". `ProcessStep.Ports` is `0..*`. | §2.1, §2.3 |
| Can a utility participate? | Yes. If an explicit thermal-energy connection is modelled, DEXPI has distinct `ThermalEnergyPort` / `ThermalEnergyFlow` semantics for it. Such an energy flow is not a material `Stream`. The inspected evidence does not make an explicit utility connection mandatory for every `ExchangingThermalEnergy`. | §3.1, §3.2, §3.3 |
| Is the class equipment-neutral? | Yes. Nothing about the class identifies physical equipment; the physics of the exchange is carried by qualified engineering quantities (area, duty, coefficients, ΔT, side mass flows). | §2.2 |
| Is a mandatory engineering value required? | Yes — `Method: HeatExchangeMethod` is `1..1`. Literals: `Generic`, `Plate`, `Spiral`, `Tubular`. | §2.2 |

## 5. Mapping assessment: what corresponds and what does not

### 5.1 The one correspondence that is honest

**DeepPlant engineering inference, not a DEXPI claim.** At the level of *what
kind of thing it is*, the two statements agree:

```text
DEXPI ExchangingThermalEnergy                    = a process function
DeepPlant ProcessStep(function="heat_exchange")  = a process function
```

Both are process-function statements. Both are explicitly *not* equipment, *not*
a symbol or presentation role, and *not* physical realization. A DEXPI
`ExchangingThermalEnergy` is therefore a legitimate reason for a DeepPlant
`ProcessStep` to carry `function="heat_exchange"`, and the existing canonical
value does not need to be reinterpreted or replaced.

That is the only correspondence supportable today, and it is a statement about
the *function category*, not about representable content.

### 5.2 What canonical DeepPlant cannot carry

Because §2 shows the class's semantics are substantially larger than "a step
that exchanges heat", the deficit is not cosmetic. Every line below is a fact
about the canonical model, not about the adapter:

```text
DEXPI                                 canonical DeepPlant today
identifier                            id                                (OK)
label                                 name                              (OK)
material ports                        ProcessPort[]                     (OK; port kind is lost)
NominalDirection (mandatory)          not stored; derived from stream incidence
Method (mandatory)                    no field
HotFlow / ColdFlow                    no field
Duty / Area / coefficients / dT       no field; no quantity-and-unit model at all
thermal side (ThermalEnergyPort)      no port kind; ProcessPort is material-only semantics
thermal utility connection            no connection kind; ProcessStream is material semantics
hot/cold side identity per port       no port role/side field
"one step couples N flows"            representable only as "a step with N material ports"
```

DeepPlant declines to store the last item's *statement* deliberately:
`ProcessPort` is a named connection point with no role, and direction is derived
from `ProcessStream` incidence (ADR-0009, [process-topology.md](process-topology.md)).
That design is defensible and is not the problem. The problem is that DEXPI uses
a mandatory `Method` plus hot/cold-side quantities to state things DeepPlant has
no place to put.

## 6. The exact gap, and the import / export / round-trip verdicts

### 6.1 The exact gap

```text
G1  Mandatory classification with no canonical home.
    ExchangingThermalEnergy.Method is 1..1 (HeatExchangeMethod:
    Generic | Plate | Spiral | Tubular). DeepPlant has no field for it.
    Import would silently drop a required semantic statement; export would
    have to invent a value. Neither is acceptable under the adapter's
    fail-closed invariant.

G2  Coupled multi-stream semantics have no canonical grouping statement.
    DEXPI defines ExchangingThermalEnergy as transferring thermal energy between
    two or more material streams.

    DeepPlant can represent one ProcessStep with several ProcessPorts and
    ProcessStreams, but it has no canonical statement grouping those ports into
    the participating thermal sides.

    DEXPI HotFlow and ColdFlow are step-level qualified mass-flow quantities,
    not port references, so they do not resolve this structural grouping gap.

    Optional Core.Role metadata may carry role information, but the inspected
    model does not define a structural hot-side / cold-side grouping relation.

G3  No port kind.
    Ports are typed in DEXPI (MaterialPort vs ThermalEnergyPort vs ...).
    ProcessPort is a single material-flow-semantics type with no kind field.

G4  No energy-flow connection kind.
    If an explicit thermal-energy / utility connection is modelled, DEXPI
    represents it using ThermalEnergyPort and ThermalEnergyFlow rather than a
    material Stream. DeepPlant's ProcessStream has material semantics, so
    ThermalEnergyFlow must not be collapsed into ProcessStream.

G5  No engineering-quantity representation.
    Duty, Area, HotFlow, ColdFlow, HeatTransferCoefficient,
    HeatTransferResistance, SkinTemperature and TemperatureDifference are all
    qualified physical quantities. DeepPlant has no quantity/unit value model.

G6  Explicit port direction is not stored.
    Port.NominalDirection is mandatory in DEXPI; DeepPlant derives direction
    from ProcessStream incidence. This gap is shared with every DEXPI
    ProcessStep class and is already handled by the adapter's incidence
    consistency check, so it is not specific to thermal mapping — but it does
    mean a *round-trip* can only be claimed for models whose direction is
    derivable.
```

### 6.2 Verdicts

| Claim | Verdict | Reason |
|---|---|---|
| `ExchangingThermalEnergy` → `ProcessStep(function="heat_exchange")` as a function kind | **honest as an engineering inference**, but not asserted by any mapping | §5.1 |
| **Import** `ExchangingThermalEnergy` into canonical DeepPlant | **not claimed** | G1–G5 |
| **Export** canonical `heat_exchange` to `ExchangingThermalEnergy` | **not claimed** | G1 at minimum; export would have to invent `Method` |
| **Semantic round-trip** | **not claimed** | Neither direction is lossless; G1 alone makes round-trip false |
| Class status in the adapter | **explicitly unsupported** (fail closed, class named in the error) | existing behaviour, now pinned by executable tests (§8) |

A *partial* import that dropped `Method`, `Duty`, `HotFlow`/`ColdFlow` and the
thermal side while keeping step identity and material topology was considered and
**rejected**: it would produce a canonical model that looks semantically complete
while a required DEXPI statement had been silently discarded. That is exactly the
failure mode the adapter's fail-closed policy exists to prevent, so the honest
outcome is an explicit unsupported status rather than a convenient partial
mapping.

## 7. Smallest justified model change (proposed, **not authorized**)

This slice does not change `src/deepplant/model.py`, the adapter mapping tables,
or any example. The following is a proposal for a *future* slice, ordered so that
the smallest change that unblocks an honest mapping comes first. Nothing here is
authorized by this document, and none of it should be implemented before a
concrete requirement justifies it (AGENTS.md; ADR-0009 "Deferred").

```text
Change C-1
    A canonical place for a required, non-derivable step classification that the
    step's function does not already carry. This removes the "export must invent
    a value" half of the problem, and it is a general ProcessStep question, not a
    heat-exchanger question: DEXPI Pumping and Compressing carry a Method too.
    Recommended shape: do not add a DEXPI-shaped field; first decide which
    DeepPlant engineering statement the value represents.

Change C-2
    A canonical statement of which ports of one step participate in one coupled
    process function, i.e. a side/grouping concept for ProcessPorts (for example
    an optional side/group label plus a rule that a coupled step declares at
    least two groups). This is what separates "a step with four ports" from "a
    step exchanging heat between two streams".

Change C-3
    A canonical representation of qualified engineering quantities (value + unit)
    on steps and streams. This is the already-recorded prerequisite for any
    broader DEXPI Process work (dexpi-process-spike.md §9 item 2), and it is far
    larger than this class.

Change C-4
    A canonical energy-flow / non-material connection kind and a ProcessPort kind,
    so that a thermal utility side can be represented at all. Largest change; not
    required for a material-only thermal mapping.
```

**Ordering judgement.** C-1 alone would still leave the coupling of two material
streams unstated; C-2 alone would still force an invented `Method` on export. An
honest `ExchangingThermalEnergy` mapping therefore needs the same prerequisites as
the rest of the DEXPI ProcessStep family — **C-3 and C-1 are family-level
blockers, while C-2 is specific to coupled-flow classes such as this one.** That
is the real finding: the class is not blocked by an exotic thermal concept, it is
blocked by prerequisites the earlier spikes already recorded, plus one coupling
statement.

**Cheaper honest alternative, available today with no model change:** keep
`heat_exchange` as a canonical DeepPlant engineering function and record the DEXPI
relationship as documentation-only provenance, exactly as this document does. That
is strictly better than an invented mapping and requires nothing.

## 8. Executable guardrails shipped with this slice

Per [workflow.md](workflow.md), an executable guardrail outranks a textual rule, so
this decision is pinned by tests rather than by prose alone:

- `tests/fixtures/dexpi/2.0.0/exchanging_thermal_energy.xml` — a DeepPlant-authored
  synthetic structural negative probe shaped from the pinned DEXPI 2.0.0 model
  definition. It carries the class identifiers, mandatory `Method`, representative
  material ports, and a `ThermalEnergyPort`. It is intentionally incomplete as a
  full DEXPI Process instance: it exists only to exercise class-level fail-closed
  behavior before connection/reference resolution, not to be imported.
- `test_exchanging_thermal_energy_step_class_is_explicitly_unsupported` — proves
  import fails closed with the DEXPI class named and with no partial model
  returned, using a fixture that carries the class's real required semantics.
- `test_exchanging_thermal_energy_is_unsupported_without_its_properties` — proves
  the rejection is **structural**: stripping every property and port from the
  instance still fails at the class level. This distinguishes "the class has no
  canonical representation" from "one property happens to be missing from an
  allow-list", which is the difference between this finding and a merely
  property-level limitation.
- `test_export_of_unsupported_functions_fails_explicitly` (already shipped, and now
  also the export-direction guardrail for this decision) — `heat_exchange` cannot
  be exported to any DEXPI class.

Consequence: a future change that accidentally widens the DEXPI ProcessStep subset
to this class — for example by walking the DEXPI superclass chain instead of using
the explicit mapping table — breaks these tests instead of silently producing an
over-claiming model.

## 9. Dependencies and semantic-model changes

- **Dependencies added: none.** The evidence was gathered from the official DEXPI
  repository; nothing from it is vendored, and no new library, XSD tooling, or
  UML/QEA reader was introduced. `uv.lock` is unchanged.
- **Semantic-model changes: none.** `src/deepplant/model.py` is unchanged:
  `ProcessStep`, `ProcessPort`, `ProcessRef`, `ProcessStream`, and `ProcessModel`
  keep their current shapes. `ProcessStep.function = "heat_exchange"` keeps its
  current, deliberately DeepPlant-native meaning and was not reinterpreted.
- **Adapter mapping changes: none.** `_STEP_TYPE_MAP` and `_REVERSE_STEP_TYPE_MAP`
  are unchanged; `ExchangingThermalEnergy` stays out of both. Only tests and
  fixtures were added, plus this document and the cross-references/roadmap updates
  it requires.
- **Fixture provenance:** the new fixture is listed in
  `tests/fixtures/dexpi/2.0.0/ATTRIBUTION.md` with its source, licence, and
  limitation. It references DEXPI identifiers only; no DEXPI normative text,
  figure, or symbol artwork is reproduced.

## 10. Quality gates

Run on this branch before merge:

```bash
make validate-docs
make validate-agent-skills
make check        # ruff format --check, ruff check, pyright, pytest
uv build          # wheel + sdist build (uv.lock unchanged)
```

All tests run offline; the DEXPI research happened during development only.

## 11. Roadmap check

- **Completed by this slice:** the Issue #22 evidence question — whether DEXPI
  `ExchangingThermalEnergy` can be mapped honestly to canonical
  `ProcessStep(function="heat_exchange")`, and whether import, export, and semantic
  round-trip can be claimed. The answer is recorded above with its authoritative
  pinned evidence, the exact gap (G1–G6), and executable guardrails. The class
  status is now an explicit, documented, test-pinned **unsupported**, not an
  unexamined omission.
- **Not completed:** the "expand the DEXPI Process subset" backlog row. This slice
  closes its `ExchangingThermalEnergy` sub-question only; `StoringMaterial` storage
  classes, quantity representation, and the rest of the class family stay open.
- **No canonical-model, adapter-mapping, or example change was made**, so no
  milestone state changed and no other roadmap row became complete.
- **Next task:** the smallest next evidence-producing step is a *model-level*
  decision, not more per-class probing — decide whether canonical DeepPlant needs a
  place for a required, non-derivable step classification (C-1) and for qualified
  engineering quantities (C-3), which block the whole DEXPI ProcessStep family and
  not just this class. If that decision is deliberately deferred, the remaining
  candidates are the `StoringMaterial` storage-class evidence question or the
  evidence-gated renderer work. Do not mechanically promote a backlog row.
- **Why this follows from the current repository state:** the three earlier DEXPI
  slices converged on the same conclusion from different directions — non-material
  energy/information semantics (dexpi-process-spike.md §9), quantity representation
  (§9 item 2), and port direction/identity — and this slice shows that one concrete
  class fails to map for exactly those reasons plus one coupling statement. The
  evidence therefore supports a model-level decision before further per-class
  adapter work.
