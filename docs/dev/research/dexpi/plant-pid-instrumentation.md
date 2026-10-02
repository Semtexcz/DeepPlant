---
type: evidence
status: historical
canonical_for:
  - dexpi-2-plant-pid-instrumentation-and-signal-evidence
read_when:
  - interoperability-work
  - dexpi-version-pinning
  - instrumentation-boundary-work
  - physical-model-growth
update_when:
  - dexpi-model-change
  - canonical-model-change
  - adapter-change
depends_on: []
decision: []
evidence: []
superseded_by: null
---

# DEXPI 2.x Plant / P&ID Instrumentation and Signal Evidence

## Outcome card

- **Question investigated:** what does inspected DEXPI Plant/P&ID evidence show
  about instrumentation, signals, and their relationship to DeepPlant's current
  semantic layers?
- **Status:** historical evidence (investigation complete; no instrumentation
  model is designed or implemented, and none is authorized here).
- **Inspection scope and date:** official DEXPI `V2.0.0`
  `Plant/Instrumentation/**` model definitions and the official Reference P&ID
  instance, inspected 2026-09-21 — the same inspection whose shared release pin,
  sources, and method are recorded in the sibling
  [physical semantic-boundary evidence](plant-pid-semantic-boundary.md#1-targeted-dexpi-release-pinned).
- **Conclusions:**
  1. DEXPI models instrumentation as a **function layer** with its own objects,
     ownership, and directed references — not as connections.
  2. The directed signal edge (`SignalConveyingFunction`) is a different model
     from the material piping edge and **must never** become `Connection`.
  3. Instrumentation sensing/actuating locations attach to the *physical
     realization* (nozzle, piping component, piping segment), so a future
     instrumentation slice depends on the piping-realization layer existing
     first; it cannot be anchored to `Equipment` or `Port` alone.
  4. The evidence proves only that instrumentation belongs in a **separate future
     layer**; it does not justify a canonical instrumentation, signal, or control
     model.
  5. Nothing is implemented or claimed: no `Instrument`, `Signal`, loop, I/O,
     control-system, or MaR/I&C production semantic is introduced.
- **Resulting ADRs:** ADR-0010 (which keeps instrumentation outside `Port`,
  `Connection`, and `Equipment.type`).
- **Current contracts operationalizing the result:**
  [contracts/plant-model.md](../../../contracts/plant-model.md) and
  [contracts/physical-piping.md](../../../contracts/physical-piping.md) keep the
  physical boundary deliberately narrow; no instrumentation contract exists.
- **Conditions for revisiting:** a concrete instrumentation requirement with its
  own evidence and Issue, arriving after the physical-realization anchors it
  depends on.

> This document is the instrumentation/signal part of the former monolithic DEXPI
> Plant/P&ID semantic-mapping spike (Issue #19), decomposed by durable
> responsibility. It records only what the inspected evidence shows about
> instrumentation and signals and where that evidence places the boundary; it
> designs no instrumentation model, signal model, loop model, I/O model, or
> control-system schema, and it authorizes no implementation.
>
> The shared DEXPI release pin, inspected-source inventory, evidence levels, and
> methodology are recorded once in the sibling
> [physical semantic-boundary evidence](plant-pid-semantic-boundary.md#1-targeted-dexpi-release-pinned)
> and are not duplicated here. Section numbering follows the original spike, so
> this document is that spike's §9.

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

## 11. Concept classification matrix (instrumentation rows)

Legend — "New semantic concept required?": **not now** = evidence recorded, no implementation authorized; **candidate** = evidence-justified future canonical concept in a distinct layer; **no** = not a canonical concern.

Rows decomposed from the former mixed matrix. The physical and presentation rows
are owned by [plant-pid-semantic-boundary.md](plant-pid-semantic-boundary.md) and
[plant-pid-presentation.md](plant-pid-presentation.md).

| DEXPI Plant/P&ID concept | Current DeepPlant concept? | New semantic concept required? | Adapter-only? | Presentation-only? |
|---|---|---|---|---|
| `Instrumentation.*` functions, systems, elements | – | **not now** (§9) | adapter boundary | labels/positions |
| `Instrumentation.SignalConveyingFunction` (signal edge) | – and **must not** become `Connection` | **not now** | adapter boundary | `SignalConveyingFunctionLabel` |
| `Instrumentation.SensingLocation` / `ActuatingLocation` | – | **not now** (depends on piping layer) | adapter boundary | no |

### Validity limits

The shared release pin, source list, evidence levels, and general validity limits
of this investigation are recorded in the sibling
[physical semantic-boundary evidence](plant-pid-semantic-boundary.md#13-evidence-gaps-and-threats-to-validity)
and are not restated here. Specific to this evidence: the official instance proves
one complete signal chain and corroborates the model structure, but it neither
proves a complete instrumentation ontology nor justifies a production
`Instrument` / `Signal` / loop / I/O / control-system semantic. Instrumentation
remains a capability direction only.

