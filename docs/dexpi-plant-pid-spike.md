---
type: spike-report
status: active
source_of_truth_for:
  - dexpi-2-plant-pid-semantic-boundary-evidence
read_when:
  - interoperability-work
  - dexpi-version-pinning
  - physical-model-growth
  - piping-model-work
  - nozzle-port-identity-work
update_when:
  - dexpi-model-change
  - canonical-model-change
  - adapter-change
---

# DEXPI 2.x Plant / P&ID Semantic Mapping Spike

> This document is the primary analysis deliverable of the DEXPI Plant/P&ID
> semantic-mapping spike (Issue #19), not secondary documentation. It is an
> **evidence-producing architecture spike**, not an importer implementation. Its
> purpose is to establish where the semantic boundary runs between DEXPI
> Plant/P&ID concepts and the canonical DeepPlant physical model:
>
> ```text
> DEXPI Plant / P&ID semantics
>             ↓
> what belongs in canonical DeepPlant?
>             ↓
> what belongs only in an adapter?
>             ↓
> what belongs only in presentation?
> ```
>
> The durable decisions this spike produced are recorded in
> [ADR-0010](decisions/ADR-0010-dexpi-plant-pid-semantic-boundary.md). No generic
> Plant/P&ID importer is implemented, and this document authorizes no
> implementation by itself.
>
> Follow-up status: the decision slice this document recommended (§14 item 1) has
> been delivered by Issue #24 —
> [physical-piping-model.md](physical-piping-model.md) and
> [ADR-0011](decisions/ADR-0011-canonical-physical-piping-realization.md) decide
> the canonical physical-piping shape (`PipingLine` / `PipingSegment` /
> `PipingRealization` over identified `Connection`s) without changing
> `Connection` semantics. §14 item 2 (the first piping vertical slice) is the
> next implementation candidate; item 3 remains the independent alternative. The
> DEXPI evidence recorded in this document is unchanged.

## 1. Targeted DEXPI release (pinned)

Policy applied: *stable release exists → target the latest stable release;
beta/RC newer than stable → inspect but do not make the production target unless
strongly justified.*

| Fact | Value |
|---|---|
| Targeted DEXPI version | **2.0.0** (DEXPI Specification 2.0.0) |
| Targeted tag | `V2.0.0` |
| Tag/release commit | `260c81c51039789a6148a98af4c6caf23f87a3e2` |
| Release date | 2025-10-10 |
| Official source URL | https://gitlab.com/dexpi/Specification |
| Licence | CC BY 4.0 (confirmed in the official release announcement and in the official repository `src/documentation/index.rst`) |
| Inspection date | **2026-09-21** |
| DeepPlant baseline inspected | `origin/main` = `210720408328829ddba40db7ea3c48d4b15d57e6` |

### Version state on the inspection date

- **Latest stable tagged 2.x release is still `V2.0.0`.** The official GitLab
  releases API returns exactly one 2.x release (`DEXPI Specification 2.0.0`, tag
  `V2.0.0`, `upcoming_release: false`, released 2025-10-10) and the tags API
  returns `V2.0.0`, `V1.4.0`, `V1.3.0`, `1.2`.
- **DEXPI 2.0.1 is still not released.** The official DEXPI August 2026 update
  (2026-08-25) states that 2.0.1 "is being prepared", that it "particularly
  addresses corrections and clarifications in the Process Model", and that it is
  "expected to become the recommended basis for further work with the
  specification". The official DEXPI September 2026 update (2026-09-14) contains
  no 2.0.1 release announcement and refers only to "DEXPI Specification 2.0".
  No `2.0.1`/`v2.0.1` tag or release exists on the official repository.
- Therefore the previous Process spike's pin to `V2.0.0` is **re-verified as
  still correct as of 2026-09-21**, and the primary semantic evidence for this
  spike is `V2.0.0`. No model version is mixed: every structural claim in this
  document is taken from the `V2.0.0` tag.
- **Known-upcoming risk (recorded, not worked around):** 2.0.1 is expected to
  bring **Process Model** corrections and clarifications. That risk applies to
  the Process adapter pin
  ([dexpi-process-spike.md](dexpi-process-spike.md)), not to the Plant/P&ID
  findings below, which are additionally corroborated by an official `V2.0.0`
  instance. This document should still be rechecked against 2.0.1 before any
  Plant/P&ID mapping is encoded in production code.

## 2. Evidence hierarchy and method

Evidence was collected in this order, and every conclusion below is labelled
with one of four evidence levels:

```text
confirmed by model/schema        class/property exists in the official V2.0.0 model definitions
confirmed by official instance   observed in the official V2.0.0 Plant/P&ID reference instance
inferred from specification text stated in official DEXPI documentation, not machine-verified here
hypothesis                       plausible but not evidenced; explicitly not used as a decision basis
```

Sources inspected on 2026-09-21 (all official, CC BY 4.0):

| Source | Role in this spike |
|---|---|
| `https://gitlab.com/dexpi/Specification` (project, releases API, tags API) | version/tag/commit/licence verification |
| `V2.0.0` archive, `src/model/Plant/Plant.py` | `PlantModel` composition properties |
| `V2.0.0` archive, `src/model/Plant/ProcessEquipment/ProcessEquipment.py` | physical items, nozzles, tags, chambers |
| `V2.0.0` archive, `src/model/Plant/Piping/Piping.py` | piping topology, pipes, segments, systems, components |
| `V2.0.0` archive, `src/model/Plant/Instrumentation/Instrumentation.py` | instrumentation functions, signals, sensing/actuating locations |
| `V2.0.0` archive, `src/model/Plant/PlantStructure/PlantStructure.py` | plant/system/train structure |
| `V2.0.0` archive, `src/model/Plant/Diagram/Diagram.py` | plant-layer presentation/label constructs |
| `V2.0.0` archive, `src/model/Core/Core.py` | conceptual vs graphical separation, identity, notes, roles |
| `V2.0.0` archive, `src/model/Core/Diagram/Diagram.py` | graphics primitives, shapes, shape usage |
| `V2.0.0` archive, `src/documentation/_static/reference_pid.xml` | **the official DEXPI Reference P&ID instance** |
| `V2.0.0` archive, `src/documentation/appendix/reference_pid.rst` | official statement of what that instance demonstrates |
| `V2.0.0` archive, `src/documentation/_static/DEXPI_XML_Schema.xsd` | generic XML envelope only |
| `https://dexpi.org/` news pages (2026-08-25, 2026-09-14) | version freshness |
| `https://gitlab.com/api/v4/groups/dexpi/projects` | whether other official instance sources exist |

Model definitions in this repository are not UML/XMI at `V2.0.0`: the class
model is expressed in the official generator DSL
(`MODEL`/`PACKAGE`/`ABSTRACT_CLASS`/`CONCRETE_CLASS`/`COMPOSITION_PROPERTY`/
`REFERENCE_PROPERTY`/`DATA_PROPERTY`/`ENUMERATION`) under `src/model/`.
`DEXPI_XML_Schema.xsd` (28,664 bytes) is a **generic envelope schema**: it
contains zero references to `Plant`, `Piping`, `Nozzle`, or `PlantModel` class
names. Class vocabulary therefore lives in the DSL model, and instances carry
class identity as `type` strings. **No semantic claim in this document is made
from a class name alone**: every claim below cites either a declared
supertype/property or an observed instance reference.

### Why the official instance matters

The official `V2.0.0` repository contains exactly one XML instance,
`src/documentation/_static/reference_pid.xml` (32,067 lines, 1,480,481 bytes).
It is the **Reference P&ID of the DEXPI Plant Model**, so for the Plant/P&ID
layer this spike has genuine official-instance evidence — a stronger position
than the Process spike had (no official Process instance exists). Official
`reference_pid.rst` states: "The DEXPI Reference P&ID serves to demonstrate the
features of the DEXPI Plant Model." *(inferred from specification text)*

The other official DEXPI repositories are not 2.0 Plant/P&ID instance sources:
`dexpi/TrainingTestCases` ("Lots of example PIDs, many with DEXPI reference
solutions and vendor uploads", last activity 2025-07-11) and
`dexpi/GraphicBuilder` ("GraphicBuilder Software to visualize the graphical part
of ProteusXML", last activity 2025-07-11) belong to the pre-2.0 Proteus/P&ID 1.x
era. `dexpi/dexpi-viewer` (last activity 2026-04-23) is a viewer. No official
2.0 Plant/P&ID example set beyond the Reference P&ID was found, so this spike
needed **no synthetic fixture** to support its conclusions.

## 3. DEXPI's top-level split versus DeepPlant's top-level split

*(confirmed by model/schema; Plant side additionally confirmed by official
instance)*

```text
Core.EngineeringModel
├── ConceptualModel      (engineering information, independent of graphics)
├── Diagram              (graphical representation)
└── ShapeCatalogues      (DIAGRAM.ShapeCatalogue)
```

`Core.ConceptualModel` is described in the model as "The conceptual content of
an EngineeringModel, i.e., engineering information independent from its
graphical representation."

Two conceptual models exist, and they are **separate models with separate model
URIs**:

```text
Plant/PlantModel     (uri https://data.dexpi.org/models/2.0.0/Plant.xml)
Process/ProcessModel (uri https://data.dexpi.org/models/2.0.0/Process.xml)
```

`Plant.PlantModel` is a `Core.ConceptualModel` subclass and owns exactly these
composition properties (confirmed by model/schema, `src/model/Plant/Plant.py`):

| `PlantModel` property | Element type |
|---|---|
| `TaggedPlantItems` | `Plant.ProcessEquipment.TaggedPlantItem` |
| `PipingNetworkSystems` | `Plant.Piping.PipingNetworkSystem` |
| `ProcessInstrumentationFunctions` | `Plant.Instrumentation.ProcessInstrumentationFunction` |
| `MeasuringSystems` | `Plant.Instrumentation.MeasuringSystem` |
| `ActuatingSystems` | `Plant.Instrumentation.ActuatingSystem` |
| `ActuatingElectricalSystems` | `Plant.Instrumentation.ActuatingElectricalSystem` |
| `InstrumentationLoopFunctions` | `Plant.Instrumentation.InstrumentationLoopFunction` |
| `PlantStructureItems` | `Plant.PlantStructure.PlantStructureItem` |

Two structural facts follow directly and matter for the whole spike:

1. **`PlantModel` has no generic `Connections` collection.** Physical
   connectivity lives inside the `Piping` package; instrumentation/signal
   connectivity lives inside the `Instrumentation` package. DEXPI does not have
   one universal "connection" collection at plant level.
2. **`PlantModel` does not own nozzles directly.** Nozzles are owned by their
   equipment item (`NozzleOwner.Nozzles`). There is no plant-level nozzle list.

The official instance confirms the same shape: `<Model>` → `<Object
type="Core/EngineeringModel">` → `<Components property="ConceptualModel">` →
`<Object id="PlantModel1" type="Plant/PlantModel">`. *(confirmed by official
instance)*

### Comparison with DeepPlant

| Aspect | DEXPI 2.0 Plant | DeepPlant `main` |
|---|---|---|
| Root | `EngineeringModel` = `ConceptualModel` + `Diagram` + `ShapeCatalogues` | `PlantModel` = `Plant` + `Equipment[]` + `Connection[]` + optional `ProcessModel` |
| Plant/P&ID conceptual model | `PlantModel` (separate model, separate URI) | physical/bootstrap layer (`Equipment`/`Port`/`Connection`) |
| Process conceptual model | `ProcessModel` (separate model, separate URI) | `ProcessModel` (separate submodel, ADR-0005/0006) |
| Graphics | `Core.Diagram` inside the same file | strictly separate; no presentation data in the semantic model (ADR-0003) |

The DeepPlant split (`ProcessModel` beside a physical layer) mirrors DEXPI's
separate Plant/Process models. The DeepPlant semantic/presentation split is
stricter than DEXPI's *file format*, which carries both in one document — but
not stricter than DEXPI's own *model*, which separates `ConceptualModel` from
`Diagram`.

### Process ↔ physical realization

The DEXPI `V2.0.0` evidence inspected in this spike provides **no direct**
`ProcessStep` ↔ Plant-equipment realization relationship. It also provides **no
direct** `ProcessStream` ↔ physical-piping realization relationship.

DEXPI therefore does **not** establish realization cardinality as `1:1`, `1:N`,
`N:1`, or `N:M`. Class similarity is not evidence for any of those mappings:

```text
function="pumping" != pump equipment
mixing ProcessStep != mixer vessel/equipment
ProcessStream != PipingNetworkSystem
ProcessStream != PipingNetworkSegment
```

Virtual process steps such as `mixing` and `splitting` may have no dedicated
physical-equipment object. Conversely, physical inline items need not have a
`ProcessStep`. DeepPlant must keep process↔physical realization explicit and
unresolved until a concrete engineering use case provides evidence for its shape
and cardinality. This spike does not design that mapping.

## 4. Equipment and physical-object identity

*(confirmed by model/schema unless stated otherwise)*

```text
Core.ConceptualObject                      (abstract base of all conceptual content)
└── Plant.ProcessEquipment.TaggedPlantItem  (abstract: "A fully tagged item in a plant")
    superTypes: Core.ConceptualObject, Plant.PlantStructure.TechnicalItem
    properties: TagName, TagNamePrefix, TagNameSequenceNumber, TagNameSuffix
    │
    └── Plant.ProcessEquipment.ProcessEquipment  (abstract: "An apparatus or machine")
        superTypes: ChamberOwner, NozzleOwner, TaggedPlantItem, TransmissionDriver
        │
        ├── CentrifugalPump / ReciprocatingPump / Tank / TubularHeatExchanger / ...
        └── (templates: design pressure/temperature, material of construction,
             nominal diameter, SubTagName, ...)
```

The official instance uses concrete equipment classes directly, e.g.
`type="Plant/ProcessEquipment.CentrifugalPump"`, `.ReciprocatingPump`,
`.Tank`, `.TubularHeatExchanger`, `.PlateHeatExchanger`, plus part-like objects
`.Chamber` (8), `.Impeller`, `.Displacer`, `.TubeBundle`, `.Motor` etc.
*(confirmed by official instance)*

### Answers to the equipment questions

| Question | Evidence-backed answer |
|---|---|
| What is the physical object identity? | Two-layer. **Engineering identity** is `TagName` (+ `TagNamePrefix`/`SequenceNumber`/`Suffix`), a data property on `TaggedPlantItem`; `TagName` occurs 85× in the official instance. **Serialization identity** is the XML `Object@id` (`CentrifugalPump1`, `Pipe1`, `Nozzle1`…), which is file-local reference plumbing only. |
| Is there a persistent identifier? | Yes: `Core.ConceptualObject.PersistentIdentifiers` composes `Core.PersistentIdentifier` ("A persistent context-dependent identifier"), with `Value` and a context/URI. The official Plant instance contains **0** `PersistentIdentifier` objects and **0** `property="Identifier"` data properties, so the Plant layer's observed identity practice is `TagName`-based. |
| Classification versus instance identity? | Separated. Classification is the **class** (`CentrifugalPump`) selected in the external model; instance identity is the tag. `EquipmentDescription` is a `MultiLanguageString` natural-language property (`en`/`de` variants), not an identity. |
| Which properties belong to the object? | Structure: `Chambers` (composition), `Nozzles` (composition), `Motors`, `Mounts`, `SprayNozzles`, `TransmissionSystems`, `Vents`, `DryingChambers`; engineering data via templates (design pressures/temperatures, material of construction code, nominal diameter, `SubTagName`, `EquipmentDescription`); physical quantities are `Core.PhysicalQuantities.PhysicalQuantity` with units (60 in the instance). |
| Nozzle vs "SprayNozzle"? | `Plant.ProcessEquipment.SprayNozzle` is a **separate concrete class**, not a `Nozzle` subclass. The word "nozzle" alone therefore does not identify one concept in DEXPI. |
| How does it differ from a `ProcessStep`? | Different model entirely: `ProcessStep` is in the `Process` model with `Identifier`/`Label` and ports; equipment here is a tagged physical artefact with `TagName`, chambers, nozzles, and design data. Neither is a subtype of the other; there is no direct mapping property between them. |

### Comparison with DeepPlant `Equipment`

| Aspect | DEXPI `ProcessEquipment` | DeepPlant `Equipment` |
|---|---|---|
| Identity | `TagName` (+ prefix/number/suffix), optional `PersistentIdentifiers`; XML `id` is file-local | `id`: required, non-empty, unique within the model, no naming standard defined yet |
| Classification | The DEXPI class itself (`CentrifugalPump`) | `type`: open non-empty string, no taxonomy (deliberately) |
| Human label | `EquipmentDescription` (`MultiLanguageString`) | `name: str \| None` |
| Owned connection points | `Nozzles` (composition) | `ports: list[Port]` (composition, local ids) |
| Other owned parts | `Chambers`, `Motors`, `Mounts`, `TransmissionSystems`, `Vents`, part-like objects | none |
| Engineering data | design pressure/temperature, material, nominal diameter, quantities with units | none |

**Finding E1.** DeepPlant `Equipment` (`id` + open `type` + optional `name` +
owned `Port`s) is a faithful *structural* projection of DEXPI's tagged physical
item, and deliberately weaker on two axes: (a) DeepPlant has no typed equipment
vocabulary; (b) DeepPlant stores no engineering properties yet. Neither gap is
closed by this spike, and neither is required to represent the realistic
fragment. The DEXPI evidence does **not** justify introducing an equipment
taxonomy now; it does confirm that `Equipment.type` is the right *place* for a
future classification, and that no separate "tag" concept is needed while
`Equipment.id` is the engineering identifier.

**Finding E2 (evidence gap, recorded).** DEXPI distinguishes *tag* from
*instance id*. DeepPlant deliberately has one identifier (`Equipment.id`), which
the realistic fragment uses as a tag (`P-101`). This is a lossy but honest
simplification for adapter purposes: a future importer must map `TagName` →
`Equipment.id` and must not use the file-local XML `id` as the canonical
identifier. That decision is adapter-level and already precedented by the
Process adapter's `Identifier` → `id` rule.

## 5. Nozzles and physical connection points (central question)

*(confirmed by model/schema; instance cross-check noted per claim)*

DEXPI has **three** distinct connection-point concepts in the Plant layer, not
one:

```text
Plant.ProcessEquipment.Nozzle                (concrete)
    superTypes: Core.ConceptualObject,
                Instrumentation.ActuatingElectricalLocation,
                Instrumentation.SensingLocation,
                Piping.PipingNodeOwner,
                Piping.PipingSourceItem,
                Piping.PipingTargetItem
    description: "A projecting short piece of pipe that is attached to
                  another (hollow) body."
    owned by:    NozzleOwner.Nozzles  (COMPOSITION, lower 0, upper *)
    properties:  NominalPressureNumericalValueRepresentation,
                 NominalPressureRepresentation,
                 NominalPressureStandard,
                 NominalPressureTypeRepresentation,
                 Chamber (REFERENCE to a Chamber of the same owner)
    subclasses:  AccessNozzle, InstrumentNozzle, ProcessNozzle

Piping.PipingNode                            (concrete)
    description: "A possible connection point for a PipingConnection."
    owned by:    PipingNodeOwner.Nodes (COMPOSITION, lower 0, upper *)
    properties:  nominal diameter templates
    owners:      Nozzle, PipingComponent  (both are PipingNodeOwners)

Process.Process.Port                         (Process model, other model)
    subclasses:  MaterialPort, EnergyPort, InformationPort, ThermalEnergyPort
```

Four independent structural facts follow, each of which contradicts a naive
one-concept reading:

1. **Ownership is real and compositional.** `NozzleOwner.Nozzles` is a
   composition property typed `Nozzle`, so a nozzle belongs to exactly one
   owning object. Nozzles are not free-floating, and the plant model has no flat
   nozzle collection.
2. **A nozzle is also a piping node owner.** Because `Nozzle` is a
   `PipingNodeOwner`, a nozzle owns `PipingNode` objects, and a `PipingNode` is
   the actual attach point referenced by piping connections. In the official
   instance, 19 nozzles coexist with 62 `PipingNode` objects, and every
   connection references an **item *and* a node**: `SourceItem` 50×,
   `SourceNode` 50×, `TargetItem` 50×, `TargetNode` 50×. *(confirmed by official
   instance)*
3. **A nozzle carries engineering data beyond "a name".** Nominal-pressure
   representation/standard/type and an optional `Chamber` reference are nozzle
   properties; `Nozzle.Chamber` is constrained to a chamber of the same owner.
   Nozzles are also classified by purpose into `ProcessNozzle`,
   `InstrumentNozzle`, and `AccessNozzle`.
4. **A nozzle is an instrumentation location.** `Nozzle` is both
   `SensingLocation` and `ActuatingElectricalLocation`, so instrumentation can
   reference a nozzle directly as where measurement or actuation happens.

### What the official instance actually does

The instance contains 19 `type="Plant/ProcessEquipment.Nozzle"` objects — the
**base class**, not the purpose subclasses (`ProcessNozzle` does not appear; it
only appears inside the UML illustration `Core/Diagram/example2.svg`).
*(confirmed by official instance)*

Pipes terminate at nozzles as (item, node) pairs:

```xml
<Object id="Pipe1" type="Plant/Piping.Pipe">
  <References objects="#FlowInPipeOffPageConnector1" property="SourceItem"/>
  <References objects="#PipingNode1"               property="SourceNode"/>
  <References objects="#Nozzle1"                   property="TargetItem"/>
  <References objects="#PipingNode2"               property="TargetNode"/>
</Object>

<Object id="Pipe2" type="Plant/Piping.Pipe">
  <References objects="#Nozzle2"     property="SourceItem"/>
  <References objects="#PipingNode3" property="SourceNode"/>
  <References objects="#Nozzle3"     property="TargetItem"/>
  <References objects="#PipingNode4" property="TargetNode"/>
</Object>
```

*(confirmed by official instance)*

### Comparison with DeepPlant `Port`

| Aspect | DEXPI `Nozzle` (+ its `PipingNode`s) | DeepPlant `Port` |
|---|---|---|
| Ownership | composition from the owning item (`Nozzles`), plus owned `PipingNode`s | composition from `Equipment` (`ports`), id local to the owner |
| Identity | no tag property of its own; XML `id` is file-local; addressed as owner + nozzle | `id`, unique per owning equipment; global endpoint = `(component id, port id)` |
| Directionality | none on the nozzle itself; direction lives on the piping connection (`SourceItem`/`TargetItem`) | none; direction lives on `Connection.source`/`Connection.target` |
| Classification | purpose subclasses + nominal-pressure data + optional chamber | none |
| Geometry/presentation relation | **none** on the semantic object; positions live in `Plant/Diagram.PipingNodePosition` (65 instances) and labels in `Plant/Diagram.NozzleStandardLabel` (19 instances, one per nozzle) *(confirmed by official instance)* | none (presentation stays out of the model, ADR-0003) |
| Connectivity role | is a `PipingSourceItem` and `PipingTargetItem`; owns the `PipingNode`s that connections actually attach to | referenced by `PortRef` as the connection endpoint |
| Engineering properties | nominal pressure (representation + standard), chamber | none |

**Finding N1 (the central answer).** The evidence **does not** justify adding a
`Nozzle` concept to DeepPlant now, and it **does** justify keeping `Port` as the
canonical physical connection point.

Reasoning, strictly from the evidence: the DEXPI facts that carry *work* here
are (a) a connection point is **owned** by one item, (b) it is **addressed as
(owner, point)**, and (c) connectivity references it as a **directed endpoint**.
DeepPlant `Port` already expresses exactly those three things (owner-owned,
locally identified, `PortRef(component, port)`). What DEXPI's `Nozzle` adds
beyond `Port` is:

```text
nozzle engineering data (nominal pressure, chamber)     → DeepPlant stores no engineering properties at all yet
nozzle purpose classification (process/instrument/...)  → no DeepPlant requirement or example needs it
a nozzle's own owned PipingNodes (item vs node)         → only meaningful once pipes/nodes exist (see §6–§8)
nozzle as SensingLocation / ActuatingElectricalLocation  → only meaningful once instrumentation exists (see §9)
```

Each addition is conditional on a capability DeepPlant does not have, and the
realistic fragment (`P-101.suction`, `P-101.discharge`, `FV-101.inlet`,
`FV-101.outlet`, `E-101.process_inlet`, …) is representable with `Port` alone.
Adding `Nozzle` today would model a word rather than a requirement.

**Finding N2.** The evidence proves that `Port` is currently a **collapsed
concept**: it stands for what DEXPI splits into `Nozzle` (equipment-side
connection point) and `PipingNode` (attach point, also owned by piping
components and by fittings). That collapse is acceptable *only while DeepPlant
has no piping components and no node-level connectivity*. If a real requirement
later needs (a) an attach point separate from the equipment penetration or
(b) nozzle-level engineering data, the split becomes evidence-backed. Until
then the collapse is documented, not implemented around.

**Finding N3 (rejected shortcut).** It is tempting to say "a `Port` *is* a
nozzle". The evidence contradicts strict identity: a `PipingNode` is also a
connection point and is **not** a nozzle, and nothing in DeepPlant requires the
name. The correct statement is the weaker, already-recorded one:

```text
DeepPlant Port != DEXPI Nozzle != DEXPI PipingNode != SVG anchor
```

A future Plant/P&ID adapter may map `Nozzle` → `Port` (and must then decide
explicitly what happens to `PipingNode`) as a documented, lossy adapter rule.
That is an adapter decision, not a canonical-model requirement.

**Finding N4 (unresolved port identity boundary).** `Port` is structurally
sufficient for DeepPlant's currently claimed physical-topology abstraction, but
DEXPI → DeepPlant port identity mapping remains unresolved. The official
instance demonstrates no canonical engineering tag for a `Nozzle`; its XML
`Object@id` is file-local serialization identity. `PipingNode` likewise uses
file-local XML object identity, while DeepPlant `Port` requires a non-empty local
canonical `id`. A future adapter must not casually map `Nozzle17` to
`Port.id = "Nozzle17"`, or `PipingNode42` to `Port.id = "PipingNode42"`, and
then treat that value as engineering identity.

A future adapter must instead define an evidence-backed derivation of a stable
owner-local `Port.id` — for example, an owner-local derived identifier, an
explicit adapter-generated stable id, future engineering-identifier data, or
another justified rule. This spike deliberately chooses none of them. The gap is
an unresolved adapter/canonical-boundary question, not a reason to introduce
`Nozzle` or `PipingNode` into DeepPlant now.

## 6. Physical connectivity

*(confirmed by model/schema unless stated otherwise)*

```text
Piping.PipingConnection                       (abstract)
    description: "An elementary connection between two piping items."
    SourceItem  REFERENCE → PipingSourceItem   (lower 0, upper 1)
    TargetItem  REFERENCE → PipingTargetItem   (lower 0, upper 1)
    SourceNode  REFERENCE → PipingNode         ("must belong to the SourceItem")
    TargetNode  REFERENCE → PipingNode         ("must belong to the TargetItem")
    │
    ├── Piping.Pipe                    (concrete, ALSO a Core.ConceptualObject)
    │       description: "An elementary piece of piping, i.e., not interrupted
    │                     by any item."
    └── Piping.DirectPipingConnection  (concrete)
            description: "A direct connection between two piping items, i.e. a
                          connection that is not realized by a pipe."
```

`PipingSourceItem` is documented as "An item that can be the source of a
`PipingConnection` (attribute `PipingConnection.SourceItem`) or a
`PipingNetworkSegment`"; `PipingTargetItem` is the mirror-image target role.

### Answers to the connectivity questions

| Question | Evidence-backed answer |
|---|---|
| Is DEXPI connectivity explicitly directed? | **Yes.** `SourceItem`/`TargetItem` and `SourceNode`/`TargetNode` are separate directional references, and the item roles are separate abstract classes (`PipingSourceItem` vs `PipingTargetItem`). Nozzle and `PipingComponent` are both, so direction is a property of the *connection*, not of the endpoint class. |
| What exactly are connection endpoints? | An **item + node pair**: the functional/structural item (`Nozzle`, `PipingComponent`, `PipeOffPageConnector`, …) *and* the specific `PipingNode` on that item. In the instance all four reference kinds occur exactly 50× each, so node refinement is used uniformly, not occasionally. |
| Can one physical connection span intermediate components? | **No.** `Pipe` is "an elementary piece of piping, i.e., not interrupted by any item", and its endpoints are items/nodes. Intermediate components are themselves endpoint items, so a chain is several connections. The instance shows this directly. |
| How are valves and inline equipment represented? | As `PipingComponent` objects that are both `PipingSourceItem` and `PipingTargetItem`, so they terminate one connection and start the next (see §8). |
| Is topology separate from piping-line identity? | **Yes.** A `PipingConnection` carries no line number; line identity lives on `PipingNetworkSystem` (`LineNumber`) one level up (§7). |

### Instance proof that inline components break the chain

```xml
<Object id="Pipe3" type="Plant/Piping.Pipe">
  <References objects="#Nozzle4"     property="SourceItem"/>
  <References objects="#PipingNode5" property="SourceNode"/>
  <References objects="#GlobeValve2" property="TargetItem"/>
  <References objects="#PipingNode6" property="TargetNode"/>
</Object>
<Object id="Pipe4" type="Plant/Piping.Pipe">
  <References objects="#GlobeValve2" property="SourceItem"/>
  <References objects="#PipingNode7" property="SourceNode"/>
  <References objects="#Nozzle5"     property="TargetItem"/>
  <References objects="#PipingNode8" property="TargetNode"/>
</Object>
```

A globe valve in the middle of a run is **not** crossed by one pipe: the run is
`Nozzle4 → valve` and `valve → Nozzle5`, i.e. two `Pipe` objects. *(confirmed by
official instance)*

### Comparison with DeepPlant `Connection`

| Aspect | DEXPI `PipingConnection`/`Pipe` | DeepPlant `Connection` |
|---|---|---|
| Directed? | yes (`SourceItem`/`TargetItem`) | yes (`source`/`target`) |
| Endpoints | item + node (`Nozzle`+`PipingNode`, valve+node, …) | `PortRef(component, port)` |
| Own identity | `Pipe` is a `Core.ConceptualObject` with a file-local XML `id`; `DirectPipingConnection` likewise | **none** — `Connection` has no `id` |
| Own engineering data | `Pipe` itself has none; the enclosing `PipingNetworkSegment` carries fluid code, piping class, nominal diameter, operating temperature, insulation, tracing, inclination, pressure-test circuit | **none** (deliberate) |
| Cardinality per physical run | one connection object per elementary piece; a run is many | one `Connection` per directly known adjacency; the fixture models 2 of a deliberately incomplete graph |
| Realization distinction | `Pipe` (realized by pipe) vs `DirectPipingConnection` (not realized by pipe) | none |
| Relation to line identity | nested inside a `PipingNetworkSegment` / `PipingNetworkSystem` that owns `LineNumber` | none |

**Finding C1.** The current DeepPlant invariant remains **valid** under real
P&ID semantics, with one precise correction of scope:

```text
Connection = directed semantic topology between two connection points
Connection != pipe
Connection != pipe segment
Connection != piping line / line number
Connection != process stream
Connection != signal
Connection != cable
```

DEXPI never represents "physical adjacency" as a property-free directed edge
between two equipment ports: it represents *piping realization* (`Pipe`,
segment, system, line number). DeepPlant's `Connection` is therefore not a
weaker version of DEXPI's `Pipe`; it is a different abstraction that DEXPI does
not have at plant level. That the two can describe the same fragment
(`P-101.discharge → FV-101.inlet`) is a coincidence of a small fragment, not
evidence that one should absorb the other.

**Finding C2.** The DEXPI evidence identifies precisely what `Connection` cannot
express and must never absorb:

```text
pipe identity and elementary-piece boundaries
item-vs-node endpoint refinement
piping class, fluid code, nominal diameter, insulation, tracing, test circuit
line number / segment number / system grouping
realized-by-pipe vs direct connection
```

These are candidate content of a **future, distinct physical-piping layer**, not
of `Connection`. Nothing in this spike implements that layer (§14).

## 7. Piping versus connectivity

*(confirmed by model/schema unless stated otherwise)*

```text
PipingNetworkSystem          (concrete, Core.ConceptualObject + PlantStructure.TechnicalItem)
    composition Segments → PipingNetworkSegment
    LineNumber, JacketLineNumber, JacketedLineNumber,
    PipingNetworkSystemGroupNumber
    templates: FluidCode, PipingClassCode, NominalDiameter*,
               Insulation*, HeatTracing*, JacketedPipe, OnHold
    │
    └── PipingNetworkSegment (concrete, also ActuatingElectricalLocation + SensingLocation)
        composition Items       → PipingNetworkSegmentItem  (e.g. PipingComponent)
        composition Connections → PipingConnection           (Pipe | DirectPipingConnection)
        SegmentNumber, ColorCode, FlowDirection, Inclination, OperatingTemperature,
        PrimarySecondaryPipingNetworkSegment, Siphon, Slope
        SourceItem/TargetItem → PipingSourceItem / PipingTargetItem
        SourceNode/TargetNode → PipingNode
        templates: FluidCode, PipingClassCode, NominalDiameter*, Insulation*,
                   HeatTracing*, JacketedPipe, OnHold, PressureTestCircuitNumber
```

DEXPI's physical layer therefore has a three-level identity hierarchy that is
independent of, and above, the elementary connectivity edge:

```text
PipingNetworkSystem    identity: LineNumber (e.g. "47126")   ← the "piping line"
    PipingNetworkSegment  identity: SegmentNumber (e.g. "S3") ← a segment of the line
        PipingConnection  (Pipe | DirectPipingConnection)     ← the elementary edge
        PipingComponent / PipeFitting / …                     ← items inside the segment
```

In the official instance: 11 `PipingNetworkSystem`, 23 `PipingNetworkSegment`,
29 `Pipe`, only 2 `DirectPipingConnection`, 5 `PipeTee`, and 22 `LineNumber`
occurrences (line numbers also appear as jacket/jacketed variants). *(confirmed
by official instance)*

### The four-way non-collapse, checked against evidence

| Concept | DEXPI representation | Present in DeepPlant `main`? |
|---|---|---|
| topological connection | no plant-level equivalent; piping uses `PipingConnection` | `Connection` (directed, property-free) |
| pipe / pipe segment | `Pipe` ("elementary piece of piping") nested in `PipingNetworkSegment` | **no** |
| piping network / line identity | `PipingNetworkSystem.LineNumber`, `PipingNetworkSegment.SegmentNumber` | **no** |
| process stream | `Process/Process.Stream` (Process model) | `ProcessStream` (separate submodel) |

```text
ProcessStream  !=  physical connectivity edge  !=  pipe segment  !=  piping line
```

**Finding P1.** DEXPI confirms this four-way distinction as real engineering
semantics, not as DeepPlant bookkeeping. A `ProcessStream` lives in a different
model from a `Pipe`; a `Pipe` has no line number; the line number belongs to a
`PipingNetworkSystem` that groups segments; and the directed edge inside a
segment is a third thing again.

**Finding P2 (direct answer to the Issue's question).** *Does DeepPlant
eventually need a canonical piping object distinct from `Connection`?* **Yes —
the evidence says a distinct piping-realization layer is needed for faithful
P&ID representation**, because line number, segment number, piping class, fluid
code, nominal diameter, and elementary pipe boundaries exist in the official
reference P&ID and have no honest home in today's `Connection` or `Equipment`.
**But no, that is not authorized or implemented now**: no DeepPlant requirement,
example, or executable check currently consumes any of those facts, and the
anti-roadmap rule in [roadmap.md](roadmap.md) forbids attaching pipe semantics to
`Connection` or introducing the layer without a current vertical slice. The
evidence is recorded here so a future slice starts from facts rather than
guesses.

## 8. Inline components

*(confirmed by model/schema; instance cross-check noted)*

```text
Piping.PipingComponent                       (abstract)
    superTypes: Core.ConceptualObject,
                Instrumentation.SensingLocation,
                Piping.PipingNetworkSegmentItem,
                Piping.PipingNodeOwner,
                Piping.PipingSourceItem,
                Piping.PipingTargetItem
    description: "A piping component"
    │
    ├── OperatedValve  → AngleBallValve, BallValve, ButterflyValve, GateValve,
    │                    GlobeValve, NeedleValve, PlugValve, StraightwayValve,
    │                    AngleGlobeValve, AnglePlugValve, AngleValve …
    ├── CheckValve     → GlobeCheckValve, SwingCheckValve
    ├── SafetyValveOrFitting → BreatherValve, FlameArrestor, RuptureDisc,
    │                    SpringLoadedGlobeSafetyValve, SpringLoadedAngleGlobeSafetyValve
    ├── PipeFitting    → BlindFlange, ClampedFlangeCoupling, Compensator,
    │                    ConicalStrainer, Flange, FlangedConnection, Funnel, Hose,
    │                    IlluminatedSightGlass, InLineMixer, LineBlind, Penetration,
    │                    PipeCoupling, PipeFlangeSpacer, PipeFlangeSpade, PipeReducer,
    │                    PipeTee, RestrictionOrifice, Sensorwell, SightGlass,
    │                    Silencer, SteamTrap, Strainer, VentLine
    └── InlineMeasuringElement → ElectromagneticFlowMeter, FlowMeasuringElement,
                        FlowNozzle, MassFlowMeasuringElement,
                        PositiveDisplacementFlowMeter, TurbineFlowMeter,
                        VariableAreaFlowMeter, VenturiTube, VolumeFlowMeasuringElement
```

### Answers to the inline-component questions

| Question | Evidence-backed answer |
|---|---|
| Are these `Equipment`? | **No.** `PipingComponent` does not inherit from `ProcessEquipment` and is not a `TaggedPlantItem`. It is an element of a piping segment. Valves carry piping-component numbering/name templates and `SubTagName`, not `TagName`. |
| Are they piping components? | **Yes.** Explicitly: "A piping component", a `PipingNetworkSegmentItem`. |
| Do they own connection points? | **Yes.** `PipingComponent` is a `PipingNodeOwner`, so it owns `PipingNode`s — exactly like a nozzle. |
| Do they break connectivity into separate edges? | **Yes.** Instance-proven: `Pipe3` ends at `GlobeValve2`, `Pipe4` starts from `GlobeValve2` — two `Pipe` objects, not one. |
| How is identity handled? | File-local XML `id` (`GlobeValve2`) plus data properties/templates for component name/number; no `TagName`. Valve labels are presentation (`Plant/Diagram.ValveLabel`, 8 instances). *(confirmed by official instance)* |
| Name collision warning | `Piping.FlowNozzle` is a **flow-measuring element**, unrelated to `ProcessEquipment.Nozzle`; `ProcessEquipment.SprayNozzle` is a third, separate class. "Nozzle" is not one concept in DEXPI. |

### The realistic DeepPlant fragment, re-examined

```text
P-101.discharge
   → FV-101.inlet
     FV-101.outlet
   → E-101.process_inlet
```

| Requirement | DEXPI evidence | DeepPlant `main` today | Faithful? |
|---|---|---|---|
| pump, control valve, exchanger are distinct physical items | `CentrifugalPump`, `GlobeValve`/`OperatedValve`, `TubularHeatExchanger` | `Equipment` with `type: pump` / `control-valve` / `heat-exchanger` | **yes** at the granularity DeepPlant claims |
| each item owns its connection points | `Nozzles` on equipment; `PipingNode`s on nozzles and valves | `ports` per equipment | **yes** |
| the run is a directed chain in which the valve is an endpoint | `Pipe` objects terminating at valve item+nodes | two directed `Connection`s | **yes for topology** — the valve correctly acts as an endpoint |
| the run has pipe identity, segments, line number | `Pipe` per elementary piece; `PipingNetworkSystem.LineNumber` | not represented | **no** (fixture documents this) |
| the valve carries valve-specific engineering data | `OperatedValve.NumberOfPorts`, `Operation`, piping class, `FailAction` | not represented; `type: control-valve` only | **no** (not claimed) |
| control valve is connected to a control function | `ProcessInstrumentationFunction` + `ActuatingFunction` + `SignalConveyingFunction` | not represented | **no** (not claimed) |

**Finding I1.** For the fragment as the fixture actually claims it — *physical
inventory plus directly known directed adjacency* — the current model is
faithful, and it is faithful **for the same reason DEXPI is**: an inline
component is an endpoint item, not something a single edge spans. The fixture's
`Connection` pair is therefore not a wrong model of a P&ID; it is a strictly
smaller claim about the same physical reality.

**Finding I2.** Where DeepPlant is *not* faithful is deliberate and documented:
pipe/segment/line identity and all engineering data. The important negative
result is that **none of these gaps can be closed by changing `Port` or
`Connection` semantics**. They require new objects in a new layer. That is why
this spike recommends a piping-realization slice rather than a `Connection`
widening.

**Finding I3.** DEXPI treats valves as *piping components*, not as equipment.
DeepPlant currently models `FV-101` as `Equipment` with `type: control-valve`.
That is an honest placeholder, not evidence of equivalence: a future piping
layer must decide whether inline components become their own component kind or
stay `Equipment`. This spike records the discrepancy and recommends **not**
deciding it now, because the fixture does not need the distinction and DEXPI's
class hierarchy is not a design mandate.

## 9. Instrumentation and signals

*(confirmed by model/schema unless stated otherwise. The goal is classification
only — no instrumentation support is designed or implemented here.)*

DEXPI does **not** model instrumentation as connections. It models a **function
layer** with its own objects, ownership, and directed references:

```text
ProcessInstrumentationFunction  (concrete: ConceptualObject +
                                 SignalConveyingFunctionSource +
                                 SignalConveyingFunctionTarget + TechnicalItem)
    description: "A requirement for instrumentation and/or control structures
                  relating to Process Engineering."
    composes: ActuatingFunctions, ActuatingElectricalFunctions,
              ProcessSignalGeneratingFunctions, SignalConveyingFunctions,
              SignalConnectors (SignalOffPageConnector)
    data:     ProcessInstrumentationFunctionNumber, Category, Modifier,
              Location, DeviceInformation, PanelIdentificationCode,
              GmpRelevance, GuaranteedSupplyFunction, …

ProcessSignalGeneratingFunction (concrete: ConceptualObject +
                                 SignalConveyingFunctionSource + TechnicalItem)
    references SensingLocation → Instrumentation.SensingLocation
    references Systems → MeasuringSystem

ActuatingFunction               (concrete: ConceptualObject + Source + Target + TechnicalItem)
    references ActuatingLocation → Piping.PipingNetworkSegment
    references Systems → ActuatingSystem

ActuatingElectricalFunction     (concrete: ConceptualObject + SignalConveyingFunctionTarget + TechnicalItem)
    references ActuatingElectricalLocation, Systems → ActuatingElectricalSystem

SignalConveyingFunction         (concrete: ConceptualObject)
    references Source → SignalConveyingFunctionSource
    references Target → SignalConveyingFunctionTarget
    data: SignalConveyingType, PortStatus, SignalPointNumber, SignalProcessControlFunctions
    └── SignalLineFunction, MeasuringLineFunction

MeasuringSystem                 (concrete: ConceptualObject + TechnicalItem)
    composes MeasuringElement, Transmitter, SensorwellReference
    └── FlowDetector
MeasuringElement → InlineMeasuringElementReference | OfflineMeasuringElement
Nozzle / PipingComponent / PipingNetworkSegment  are all SensingLocation subtypes
```

`SensingLocation` is documented as "An object that can act as the
`ProcessSignalGeneratingFunction.SensingLocation` of a
`ProcessSignalGeneratingFunction`."

### Instance evidence for a complete signal chain

```xml
<Object id="ProcessInstrumentationFunction1" type="Plant/Instrumentation.ProcessInstrumentationFunction">
  <Data property="ProcessInstrumentationFunctionCategory"><String>P</String></Data>
  <Data property="ProcessInstrumentationFunctionNumber"><String>4712.01</String></Data>
  <Components property="ProcessSignalGeneratingFunctions">
    <Object id="ProcessSignalGeneratingFunction1" type="Plant/Instrumentation.ProcessSignalGeneratingFunction">
      <References objects="#BlindFlange1" property="SensingLocation"/>
    </Object>
  </Components>
</Object>

<Object id="SignalConveyingFunction1" type="Plant/Instrumentation.SignalConveyingFunction">
  <References objects="#ProcessInstrumentationFunction2" property="Source"/>
  <References objects="#ActuatingFunction1"               property="Target"/>
</Object>
```

*(confirmed by official instance)*

Three important structural observations:

1. **`SensingLocation` can be a piping item, not just equipment.** In the
   instance a `ProcessSignalGeneratingFunction` senses at `#BlindFlange1` — a
   piping fitting. Instrumentation attaches to the *physical realization*, not
   only to tagged equipment.
2. **`ActuatingLocation` is a `PipingNetworkSegment`.** Actuation is localized
   at segment level, again coupling instrumentation to the piping layer rather
   than to `Equipment` directly.
3. **Signal direction reuses the same directed-reference idiom as piping.**
   `Source`/`Target` references with endpoint roles
   `SignalConveyingFunctionSource` / `SignalConveyingFunctionTarget`, and some
   classes (`ActuatingFunction`, `ProcessInstrumentationFunction`) hold both
   roles.

### Required classification of instrumentation concepts

| DEXPI concept | Current DeepPlant concept? | New canonical concept required? | Adapter-only? | Presentation-only? |
|---|---|---|---|---|
| `ProcessInstrumentationFunction` (control requirement, number, category, location) | no | **not now** — future-capability evidence | would be adapter-mapped if a slice existed | no |
| `ProcessSignalGeneratingFunction` (measurement function + `SensingLocation`) | no | **not now** | adapter boundary | no |
| `MeasuringSystem`, `MeasuringElement`, `Transmitter`, `OfflineMeasuringElement` | no | **not now** | adapter boundary | no |
| `ActuatingFunction`, `ActuatingSystem`, `ControlledActuator`, `Positioner` | no | **not now** | adapter boundary | no |
| `ActuatingElectricalFunction`, `ActuatingElectricalSystem`, `ElectronicFrequencyConverter` | no | **not now** | adapter boundary | no |
| `SignalConveyingFunction` / `SignalLineFunction` / `MeasuringLineFunction` (the directed signal edge) | no — and **must not** become `Connection` | **not now** | adapter boundary | no |
| `SignalOffPageConnector`, `PipeOffPageConnector` (+ reference-by-number / by-object variants) | no | **not now** — DEXPI's own way to express a cross-sheet dangling endpoint | must be adapter-handled explicitly, never silently dropped or invented | partly: number/description labels are `Plant/Diagram` classes |
| `SensingLocation` targets (nozzle / piping component / piping segment) | no | **not now** | adapter boundary | no |
| instrumentation labels (`ProcessInstrumentationFunctionLabel`, `SignalConveyingFunctionLabel`, `ActuatingSystemNumberLabel`, …) | no | no | no | **yes** |
| positions/symbols (`InstrumentationNodePosition`, `ShapeUsage`, `Core/Diagram.*`) | no | no | no | **yes** |

**Finding S1.** Instrumentation is a **third semantic layer**, not a variant of
physical connectivity. A signal edge (`SignalConveyingFunction`) and a material
piping edge (`PipingConnection`) share a direction idiom but are different
models with different endpoint roles. The DEXPI evidence therefore gives an
independent reason to keep `Connection` narrow: if `Connection` became "any
directed relationship", it would immediately contend with instrumentation
signals, which DEXPI itself keeps in a separate package.

**Finding S2 (sequencing dependency).** Instrumentation attaches to the
*physical realization* (`SensingLocation` = nozzle / piping component /
segment; `ActuatingLocation` = piping segment). A future instrumentation slice
therefore depends on the piping-realization layer existing first; it cannot be
modelled honestly by anchoring instrumentation to `Equipment` or `Port` alone.
This is recorded as a dependency, not as a reason to build anything now.

**Finding S3 (nothing implemented, nothing claimed).** No instrumentation class,
signal concept, sensing-location field, or `Connection` widening is added by
this spike. Instrumentation remains directional capability only (VISION.md
capability map, roadmap Stage 10 "Multi-discipline Engineering").

## 10. Presentation and graphics

*(confirmed by model/schema; counts confirmed by official instance)*

DEXPI keeps graphics out of the conceptual objects and inside the same document:

```text
Core.EngineeringModel.Diagram         → Core.Diagram.Diagram
Core.EngineeringModel.ShapeCatalogues → Core.Diagram.ShapeCatalogue (composes Shape)
Core.ConceptualModel.MetaData         → Core.Diagram.MetaData

Core.Diagram.*  primitives and representation:
    GraphicalElement, GraphicalPrimitive, NodePosition, Point, Color, Stroke,
    Ellipse, EllipseArc, Polygon, PolyLine, Text, TextTemplate,
    AttributeRepresentation, ConnectorLine, GraphicsGroup, RepresentationGroup,
    Border, Static, Label, LiteralText, Symbol (→ PipeFlowArrow,
    PipeSlopeSymbol, InsulationSymbol, CustomSymbol), Shape, ShapeUsage

Core.Diagram.ShapeUsage       (an element of a RepresentationGroup)
    IsMirrored (Boolean, required), Position (Point, required),
    Rotation, ScaleX, ScaleY, Shape (reference, required)

Plant.Diagram.*  plant-layer labels and positions:
    EquipmentBarLabel, EquipmentTagNameLabel, NozzleStandardLabel, FittingLabel,
    SafetyValveOrFittingLabel, PipingClassBreakLabel, PipingNodePosition
        (superTypes DIAGRAM.NodePosition; reference property Node → Piping.PipingNode),
    ProcessInstrumentationFunctionLabel, SignalConveyingFunctionLabel, ValveLabel,
    ActuatingSystemNumberLabel, InsulationLabel, PipingNetworkSystemLabel,
    PipingNetworkSegmentLabel, FailActionLabel, ReducerLabel,
    InstrumentationNodePosition, SignalHigh*/SignalLow*Label, SafetyRelevanceLabel,
    PlantMetaData, CustomLabel, OffPageConnector*Label, NoteIdentifierLabel…
```

Structural facts:

- **No geometry, position, colour, or label lives on the conceptual classes.**
  `Nozzle`, `Pipe`, `PipingNetworkSegment`, `CentrifugalPump`, and
  `ProcessInstrumentationFunction` have no coordinate or symbol properties.
  Position belongs to `ShapeUsage`/`NodePosition`; labels are `Diagram.Label`
  subclasses.
- `PipingNodePosition` is a `DIAGRAM.NodePosition` that **references** a semantic
  `PipingNode`: the graphical position is a separate object pointing at the
  semantic object, not a field on it.
- `PlantMetaData` (block name/number, creator, revision, confidentiality…) is a
  **`Core.Diagram`** construct reachable through `Core.ConceptualModel.MetaData`.
  It is drawing metadata, not plant data.
- The official instance is dominated by graphics objects alongside the semantic
  ones: 954 `Core/Diagram.Point`, 486 `Color`, 245 `Text`, 190 `PolyLine`,
  185 `RepresentationGroup`, 62 `ShapeUsage`, 65
  `Plant/Diagram.PipingNodePosition`, 19 `Plant/Diagram.NozzleStandardLabel`,
  8 `ValveLabel`, 5 `EquipmentBarLabel`, 8 `PipeFlowArrow`, 35 `ConnectorLine`.

**Finding G1.** DEXPI's own information model **independently corroborates
ADR-0003**. A standard designed for P&ID exchange separates `ConceptualModel`
from `Diagram`, keeps engineering objects free of coordinates and symbols, and
places drawing metadata in the graphical layer. DeepPlant's stricter file-level
separation (no graphics at all in semantic YAML) is a superset of the same
boundary, not a deviation from the domain.

**Finding G2.** DEXPI has no presentation construct that DeepPlant must treat as
semantic. `NozzleStandardLabel` exists because the *drawing* labels a nozzle; it
carries no engineering meaning DeepPlant would have to store. Likewise
`ShapeCatalogue`/`Shape` (with `SymbolRegistrationNumber`) is asset cataloguing —
the concern DeepPlant already handles as symbol packs with provenance
([svg-symbols.md](svg-symbols.md), ADR-0007/ADR-0008), not as model data.

**Finding G3.** `PlantMetaData` is the expected home of drawing-level facts in an
imported file. A future importer must decide explicitly whether to discard it
(lossy, documented) or surface it outside the semantic model; it must not become
a `PlantModel` field.

## 11. Concept classification matrix

Legend — "New semantic concept required?": **not now** = evidence recorded, no
implementation authorized; **candidate** = evidence-justified future canonical
concept in a distinct layer; **no** = not a canonical concern.

| DEXPI Plant/P&ID concept | Current DeepPlant concept? | New semantic concept required? | Adapter-only? | Presentation-only? |
|---|---|---|---|---|
| `Plant/PlantModel` (conceptual envelope) | `PlantModel` (different shape) | no | envelope mapping | no |
| `ProcessEquipment.TaggedPlantItem` (`TagName`, prefix/number/suffix) | `Equipment.id` (tag-like) | no | `TagName` → `id` mapping rule | no |
| `Core.PersistentIdentifier` | – | not now | documented as dropped when unused | no |
| `ProcessEquipment.*` concrete classes (pump, tank, exchanger, …) | `Equipment.type` (open string) | no taxonomy now | class name → `type` mapping | no |
| `ProcessEquipment.Chamber` | – | not now | out of scope / lossy-fail | no |
| `ProcessEquipment.SprayNozzle` | – | not now (name-collision hazard) | out of scope | no |
| `ProcessEquipment.Nozzle` (+ purpose subclasses) | `Port` (collapsed) | **not now** (§5 N1/N2) | `Nozzle` → `Port` is a candidate lossy rule | no |
| nozzle nominal-pressure data, `Nozzle.Chamber` | – | not now | lossy-fail or documented drop | no |
| `Piping.PipingNode` | collapsed into `Port` | **not now** | must be handled explicitly, never ignored | `PipingNodePosition` |
| `Piping.PipingConnection` (directed, item+node endpoints) | `Connection` (directed, port endpoints) | no for direction; **candidate** for node refinement later | endpoint mapping needs a stated rule | no |
| `Piping.Pipe` (identity, elementary piece) | – | **candidate** — piping-realization layer (§7 P2) | per-piece decomposition | no |
| `Piping.DirectPipingConnection` | – | **candidate** (same layer) | realized vs not-realized distinction | no |
| `Piping.PipingNetworkSegment` (+ `SegmentNumber`, class, fluid code, DN, insulation, tracing, slope, pressure-test circuit) | – | **candidate** (same layer) | adapter-only until canonicalized | segment/insulation labels |
| `Piping.PipingNetworkSystem` (+ `LineNumber`) | – | **candidate** — line identity (§7 P2) | adapter-only until canonicalized | `PipingNetworkSystemLabel` |
| `Piping.PipingComponent` + valve/fitting/measuring subclasses | `Equipment` + `type` (placeholder) | **candidate** for a component kind; **not now** (§8 I3) | class → `type`/lossy rule | `ValveLabel`, `FittingLabel`, … |
| `Piping.PipeOffPageConnector` (+ by-number/by-object) | – | not now | explicit handling of dangling endpoints | `OffPageConnector*Label` |
| `Instrumentation.*` functions, systems, elements | – | **not now** (§9) | adapter boundary | labels/positions |
| `Instrumentation.SignalConveyingFunction` (signal edge) | – and **must not** become `Connection` | **not now** | adapter boundary | `SignalConveyingFunctionLabel` |
| `Instrumentation.SensingLocation` / `ActuatingLocation` | – | **not now** (depends on piping layer) | adapter boundary | no |
| `PlantStructure.*` (enterprise, site, plant, area, system, train) | – | **not now** (asset hierarchy is a different concern) | out of scope | no |
| `Core.Diagram.*` primitives, `ShapeUsage`, `ShapeCatalogue` | – | no | no | **yes** |
| `Plant/Diagram.*` labels, `PipingNodePosition`, `InstrumentationNodePosition`, `PlantMetaData` | – | no | no | **yes** |
| DEXPI XML `Object@id` / `References` | – (engineering identity stays `Equipment.id`) | no | serialization mechanics | no |
| `Import` declarations, model URIs, `ExportDateTime`, originating-system metadata | – | no | version preflight + provenance | no |

## 12. Direct answers to the Issue's questions

| Issue question | Answer | Evidence level |
|---|---|---|
| Is today's `Port` sufficient as a canonical physical connection-point concept? | **Yes, for DeepPlant's currently claimed physical-topology abstraction.** It is owner-scoped, locally identified, direction-free, and referenced as `(component, port)` — exactly the properties DEXPI's connection points carry that matter today. This remains true only while DeepPlant has no piping components and no node-level connectivity. | confirmed by model/schema + official instance |
| Does evidence justify distinguishing a `Nozzle`? | **No, not now.** `Nozzle` adds engineering data, purpose classification, an item/node split, and instrumentation roles — each conditional on a capability DeepPlant lacks. `Port` is a *collapse* of `Nozzle` + `PipingNode`, acceptable only while the piping layer is absent. A future adapter's stable `Port.id` derivation from DEXPI identities remains unresolved. | confirmed by model/schema + official instance |
| Is DEXPI connectivity explicitly directed? | **Yes** — `SourceItem`/`TargetItem` + `SourceNode`/`TargetNode`, with separate `PipingSourceItem`/`PipingTargetItem` roles. | confirmed by model/schema |
| What exactly are connection endpoints? | **Item + `PipingNode` pairs** (`Nozzle1` + `PipingNode2`, `GlobeValve2` + node, off-page connector + node). | confirmed by official instance |
| Can one physical connection span intermediate components? | **No** — a `Pipe` is "not interrupted by any item"; a valve splits a run into two `Pipe` objects. | confirmed by model/schema + official instance |
| Is topology separate from piping-line identity? | **Yes** — `LineNumber` lives on `PipingNetworkSystem`, `SegmentNumber` on `PipingNetworkSegment`; neither is on the connection. | confirmed by model/schema + official instance |
| Do inline components own connection points and break connectivity? | **Yes on both counts** (`PipingNodeOwner`, `PipingSourceItem`/`PipingTargetItem`). | confirmed by model/schema + official instance |
| Does the existing `Connection` invariant remain valid? | **Yes.** Nothing in DEXPI collapses pipe/segment/line/stream/signal into one directed edge; DEXPI keeps them in three packages. The invariant should be kept *and* its scope stated explicitly. | confirmed by model/schema |
| Does DeepPlant eventually need a canonical piping object distinct from `Connection`? | **Yes as a direction, no as a current slice.** Line/segment/pipe identity and piping engineering data are real, present in the official reference P&ID, and cannot live on `Connection`. This is the physical-piping realization question: what is the physical piping graph? | confirmed by model/schema + official instance |
| Does DEXPI establish process↔physical realization? | **No.** The inspected evidence establishes neither `ProcessStep` ↔ equipment nor `ProcessStream` ↔ piping realization, and establishes no `1:1`, `1:N`, `N:1`, or `N:M` cardinality. | confirmed by model/schema + official instance |
| Should a generic Plant/P&ID importer be implemented now? | **No.** No evidence-backed, loss-aware minimal Plant/P&ID slice was found that does not require the piping-realization layer first. That layer does not decide process↔physical realization. | engineering conclusion from the above |
| Is an ADR justified? | **Yes** — the boundary decision (keep `Port`/`Connection`; keep piping/instrumentation out of them; keep Plant import unimplemented and fail-closed) is recorded in [ADR-0010](decisions/ADR-0010-dexpi-plant-pid-semantic-boundary.md). | this document |

The remaining physical-model work is split into two independent questions:

1. **Physical-piping realization:** pipe / segment / line / node / component
   representation — substantially bounded by this spike's DEXPI evidence.
2. **Process ↔ physical realization:** mapping between `ProcessStep` /
   `ProcessStream` and physical realization — still unresolved in shape and
   cardinality.

## 13. Evidence gaps and threats to validity

1. **No second official Plant/P&ID instance was found.** The official `V2.0.0`
   repository contains exactly one XML instance (`reference_pid.xml`) plus the
   generic envelope XSD. Vendor test material (`TrainingTestCases`,
   `GraphicBuilder`) is pre-2.0/Proteus era and was therefore **not** used as
   evidence for 2.0 semantics. Conclusions about *unused* optional features
   (e.g. `DirectPipingConnection`, `PipeOffPageConnector`, the nozzle purpose
   subclasses) rest on model/schema evidence plus a small instance sample, not
   on broad instance statistics.
2. **`DEXPI_XML_Schema.xsd` does not constrain class vocabulary**, so schema
   validation could not be used as independent corroboration of class names; the
   DSL model and the instance are the two sources used.
3. **DEXPI 2.0.1 is pending** and is stated to bring Process Model corrections
   and clarifications. Plant/P&ID findings here are corroborated by an official
   2.0.0 instance, but the pin must be rechecked before any Plant/P&ID mapping is
   encoded in code.
4. **No reverse-direction evidence.** This spike examined DEXPI → DeepPlant
   semantics only. It did not evaluate whether DeepPlant could *export* a
   Plant/P&ID model that third-party tools accept, and it makes no
   interoperability claim.
5. **No vendor-tool corroboration.** Implementation evidence from reputable DEXPI
   tooling (evidence level 5) was not needed and was not collected, because
   levels 1–3 were sufficient for every claim made.
6. **`PlantStructure` and utility/`PlantSystem` concepts were inspected only
   structurally.** They are outside this spike's scope; no conclusions about
   asset-hierarchy modelling are drawn beyond "different concern".
7. **The realistic DeepPlant fixture remains synthetic.** It is not evidence
   about DEXPI; it is used here only as the concrete representation under test.

## 14. Recommended next smallest vertical slice

The evidence identifies one genuinely small, executable, useful next step that
respects the anti-roadmap:

> **Make the physical-piping question decidable with an executable, loss-aware
> decision record before any new class exists.**

In smallest order:

1. **Preferred next step — a specification/decision slice with no new
   semantics.** Take the official `reference_pid.xml` piping fragment
   (`Nozzle → Pipe → GlobeValve → Pipe → Nozzle`, one `PipingNetworkSystem` with
   a `LineNumber`, one `PipingNetworkSegment`) and specify, in a short document,
   the exact candidate canonical shape of a piping-realization layer (line
   identity, segment, elementary pipe piece, endpoints) **plus** the explicit
   adapter mapping and the explicit loss it would avoid. No code, no model
   change, no fixture. This produces the decision input the next slice needs and
   leaves the current model untouched. It answers **what is the physical piping
   graph?**, not how `ProcessStep` maps to equipment or how `ProcessStream` maps
   to piping realization.
2. **Only after 1 is reviewed and accepted:** implement the *first* element of
   that layer as a vertical slice with executable tests — most plausibly piping
   line identity attached to real connected endpoints — with a YAML round-trip
   and a loadable example extending `examples/realistic-process-fragment/`
   **without** changing `Connection` semantics.
3. **Independent, lower-risk alternative if piping is not prioritized:** expand
   the existing DEXPI **Process** subset from fresh evidence (for example
   `ExchangingThermalEnergy` or the `StoringMaterial` storage classes), which
   needs no physical-model change and reuses the existing adapter boundary.

Explicitly **not** recommended by this spike: adding `Nozzle`, `PipingNode`,
`Pipeline`, `Instrument`, or signal classes to the canonical model; widening
`Connection`; implementing a generic Plant/P&ID importer; or importing DEXPI
graphics constructs.

## 15. Dependencies and semantic-model changes

- **Dependencies added: none.** No library, no XSD tooling, no UML/QEA reader.
  The official archive was inspected with standard tools in a temporary
  directory outside the repository; nothing from it is vendored.
- **Semantic-model changes: none.** `src/deepplant/model.py` is unchanged;
  `Equipment`, `Port`, `PortRef`, `Connection`, `ProcessStep`, `ProcessPort`,
  `ProcessRef`, `ProcessStream`, and `ProcessModel` keep their current shapes.
- **Adapter changes: none.** `src/deepplant/adapters/dexpi.py` still pins
  `V2.0.0` and still handles only the Process material subset. Its current
  Plant-content behaviour is verified and unchanged: Plant-only input is
  rejected, and in a mixed Plant + Process document Plant objects are ignored
  while the Process subset is imported.
- **Recorded observation (risk, not a change).** "Plant objects are ignored in
  mixed files" is lossy and currently silent at runtime. That is deliberate for a
  Process-only adapter, and it stays within the milestone principle
  ("unsupported populated content fails explicitly rather than being silently
  ignored") only because it is documented and Plant-only input fails closed. If
  Plant/P&ID work ever starts, the ignored-content report must become explicit.
  This spike records the observation and changes no behavior.
- **Licence and attribution.** DEXPI `V2.0.0` is CC BY 4.0; this document quotes
  class/property names and short instance fragments for identification, with
  source, tag, commit, and inspection date recorded in §1–§2, consistent with
  ADR-0007. No normative DEXPI text or graphics are reproduced, and no restricted
  ISO/ISA/IEC content is involved.

## 16. Quality gates

```bash
make validate-docs
make validate-agent-skills
make check        # ruff format --check, ruff check, pyright, pytest
```

This slice changes documentation only: no `src/` change, no test change, no new
fixture, no dependency, and no network access at test time.

## 17. Roadmap check

- **Completed by this slice:** the Plant/P&ID branch of backlog row 1 — the
  "DEXPI Plant/P&ID mapping spike" (Issue #19). The semantic boundary between
  DEXPI Plant/P&ID concepts and the current DeepPlant physical model is now
  established from official `V2.0.0` model and instance evidence; the
  `Port`/`Connection` invariants are confirmed rather than replaced; and the next
  physical-model decision is identified with an explicit evidence base.
- **What became clear:** the current `Connection` invariant survives real P&ID
  semantics; `Port` remains sufficient for DeepPlant's currently claimed
  physical-topology abstraction (with its DEXPI → `Port.id` adapter identity
  derivation still unresolved); piping line/segment/pipe identity and
  instrumentation are **separate layers** that must not be folded into `Port`,
  `Connection`, or `Equipment.type`.
- **Next task:** the specification/decision slice of §14 step 1 — specify the
  candidate piping-realization layer against a concrete official fragment
  (`reference_pid.xml`) before any class is implemented. §14 step 3 (further
  DEXPI Process subset expansion) remains the independent alternative.
- **Why that next task follows:** the remaining physical-model work is split into
  two independent questions, and only the first is bounded here. (1) The
  **physical-piping realization** question is now precisely bounded
  (pipe/piece/segment/line identity and where it attaches), and the anti-roadmap
  forbids implementing it without an accepted layer decision — that is the
  recommended next task, and it answers *what is the physical piping graph?*.
  (2) The **process ↔ physical realization** question (`ProcessStep` ↔
  equipment, `ProcessStream` ↔ piping realization, including shape and
  cardinality) is not answered or bounded by this spike and remains a separate
  unresolved decision. The Process-side gap (step/stream engineering quantities
  and material data) is unchanged and independent.
- **Milestone consistency:** Milestone 1 (validated YAML load) stays complete.
  Milestone 2 (prototype fragment and renderer) keeps its open P&ID-like
  coverage; this spike advances that at the *evidence* level only and does not
  complete it. No milestone is marked complete by this slice.
- **Stale-wording sweep:** `docs/roadmap.md` backlog row 1 previously said to run
  the Plant/P&ID mapping spike "if Plant evidence is stronger then"; that
  conditional is now resolved and the roadmap/Next-Task text is updated
  accordingly. `docs/architecture.md`'s statement that only a narrow DEXPI 2.0
  Process adapter exists remains true and is annotated with a pointer to this
  spike rather than rewritten.
