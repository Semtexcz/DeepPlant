---
type: evidence
status: historical
canonical_for:
  - qualified-engineering-quantity-semantic-boundary
read_when:
  - model-growth
  - canonical-model-change
  - interoperability-work
  - quantity-model-work
update_when:
  - canonical-model-change
  - dexpi-model-change
depends_on: []
decision: []
evidence: []
superseded_by: null
---

# Qualified Engineering Quantity Boundary (Issue #32)

## Outcome card

- **Question investigated:** what semantic boundary should DeepPlant use for
  numerical engineering values with units — does the canonical semantic model
  need a reusable representation for a *qualified engineering quantity*, and if
  so, what information does DeepPlant own inside it and where does it live?
- **Status:** historical evidence; Outcome B accepted and recorded by ADR-0013.
  No runtime, adapter, serialization, or dependency change was made.
- **Inspection scope and date:** the pinned official DEXPI `V2.0.0` model
  (`QualifiedValue`, `PhysicalQuantity`, `PhysicalQuantityVector`, `DataTypes`)
  and the DeepPlant model/adapter contracts, inspected 2026-10-01 against release
  commit `260c81c51039789a6148a98af4c6caf23f87a3e2`.
- **Conclusions:**
  1. DEXPI `QualifiedValue` is **not** `{value, unit}`: it is a wrapper whose one
     required `Value` is a `PhysicalQuantity` (magnitude + typed unit) or a bare
     `Double`, plus optional case/scope/provenance/range/URI qualifiers and a
     required `DisplayText`.
  2. The reusable part of an engineering quantity is the **value** — authored
     scalar magnitude plus engineering-unit semantics — not the engineering
     property name, which is domain-specific (`duty`, `head`, `temperature`,
     `nominal diameter`).
  3. An arbitrary property/parameter bag is rejected: it would erase explicit
     domain ownership and contradict the fail-fast, field-explicit model
     (ADR-0012).
  4. Units are **canonical semantic state**, not presentation: `10 bar` and
     `1 MPa` are distinct authored states that are only *mathematically*
     equivalent after conversion.
  5. A quantity boundary removes exactly **one** `ExchangingThermalEnergy`
     blocker and does not make that class supported; the mandatory `Method`,
     coupled multi-stream semantics, port kind, energy-flow kind, and
     `NominalDirection` blockers remain.
- **Resulting ADRs:** ADR-0013.
- **Current contracts operationalizing the result:** none yet — no canonical
  quantity is implemented. The decision constrains future model work and keeps
  [contracts/dexpi-process-adapter.md](../contracts/dexpi-process-adapter.md)
  describing current behaviour only (quantities stay unsupported).
- **Conditions for revisiting:** ADR-0013's *Revisit When* list — a concrete
  DeepPlant-native authoring, calculation, engineering-rule, or interoperability
  consumer that needs a quantity value; a DEXPI 2.0.1+ compatibility review; or
  evidence that scalar magnitude + unit is insufficient.

## 1. Problem statement

Issue #22 left one engineering uncertainty unresolved: DEXPI process steps and
streams carry numerical engineering values with units (`Duty`, `Area`,
`HotFlow`/`ColdFlow`, `HeatTransferCoefficient`, `HeatTransferResistance`,
`SkinTemperature`, `TemperatureDifference`, `Pressure`, `Temperature`, `Head`,
`VolumeFlow`, `MassFlow`), and DeepPlant has no canonical place for any of them
(Issue #22 gap **G5**, "No engineering-quantity representation").

The primary question is **not** a Python class design. It is:

```text
What semantic information does DeepPlant need to own when an engineering
statement contains a numerical value with an engineering unit, and where should
that information live?
```

Four things must be kept apart before any answer is useful:

```text
classification   what kind of engineering function/thing is this?
                 (ProcessStep.function = pumping)              -- not a quantity
property         which engineering fact is being stated?
                 (pump head, stream temperature, duty, DN)    -- domain-specific
quantity value   what magnitude and engineering unit qualify it?
                 (45 m, 10 bar, 120 degC, 2.5 MW)             -- reusable value
presentation     how is it shown? ("120 degC", precision)     -- not semantics
```

This slice decides the boundary only. It does not implement it, and it does not
authorize a serialization contract.

## 2. Existing DeepPlant boundary

Current canonical objects (`src/deepplant/model.py`) carry **no** engineering
quantity, unit, or numeric property of any kind:

| Object | Owns today | Quantity-relevant absence |
|---|---|---|
| `ProcessStep` | `id`, `function`, `name`, `ports` | no `duty`/`head`/`pressure`; ADR-0012 gives it exactly one classification axis |
| `ProcessStream` | `id`, `name`, `source`, `target` | no `temperature`/`mass_flow`/`pressure` |
| `ProcessPort` | `id` | identity only |
| `Equipment` | `id`, `type`, `name`, `ports` | no design data |
| `PipingSegment` | `id`, `segment_number?`, `nominal_diameter?`, `piping_class?`, `fluid_code?` | open **strings**; ADR-0011 explicitly defers "quantity/unit typing for DN, pressure, temperature, and thickness" |
| `Connection` | `id`, `source`, `target` | property-free topology (ADR-0011) |

The DEXPI adapter (`src/deepplant/adapters/dexpi.py`) rejects any populated
Data/Components/References property outside its allow-list, which is the
mechanism that currently rejects `QualifiedValue` content and `Method`
([contracts/dexpi-process-adapter.md](../contracts/dexpi-process-adapter.md)).

Three durable constraints bound any answer:

1. **The semantic model is the core** (ADR-0002): consumers depend on it, never
   the reverse.
2. **Semantic and presentation data stay separate** (ADR-0003): formatting,
   display text, precision, and label placement are not semantic state.
3. **No generic property bag.** ADR-0012 already refused a generic
   property/attribute/metadata bag on `ProcessStep`; the same reasoning applies
   to a generic parameter bag on any entity.

## 3. Evidence inventory

Sources inspected for this decision (no restricted content is reproduced; only
class/property names, type expressions, multiplicities, and short definition
sentences):

| Source | Path / reference | Role |
|---|---|---|
| DEXPI `V2.0.0` Core model | `src/model/Core/Core.py` @ `260c81c5…` | `QualifiedValue` and its properties |
| DEXPI `V2.0.0` physical quantities | `src/model/Core/PhysicalQuantities/PhysicalQuantities.py` @ `260c81c5…` | `PhysicalQuantity`, `PhysicalQuantityVector` |
| DEXPI `V2.0.0` data types | `src/model/Core/DataTypes/DataTypes.py` @ `260c81c5…` | `Scope`, `QuantityProvenance`, `QuantityRange` |
| DEXPI `V2.0.0` Process model | `src/model/Process/Process/Process.py` @ `260c81c5…` | which process properties carry quantities |
| Issue #22 evidence | [dexpi-exchanging-thermal-energy-evidence.md](../dexpi-exchanging-thermal-energy-evidence.md) | the thermal-quantity property table and G5 |
| Process-step classification | [process-step-classification.md](../process-step-classification.md) | rejected generic property/second-axis shapes |
| Adapter contract | [contracts/dexpi-process-adapter.md](../contracts/dexpi-process-adapter.md) | current fail-closed behaviour for quantities |

Licence: DEXPI 2.0.0 is CC BY 4.0; only identifiers, type expressions,
multiplicities, and short class-definition sentences are quoted (ADR-0007).
DEXPI 2.0.1 is a separate compatibility target outside the current adapter
contract and is **not** used as evidence here; the runtime pin does not move.

## 4. DEXPI qualified-value semantics (verified, not assumed)

### 4.1 `QualifiedValue` is not `{value, unit}`

`Core.QualifiedValue` is a `CONCRETE_CLASS` (`superTypes=[Core.ConceptualObject]`)
with these declarations (exact types and multiplicities):

| Property | Kind | Type | lower | upper |
|---|---|---|---|---|
| `Type` | `DATA_TYPE_PARAMETER` | `PhysicalQuantity \| Double` | — | — |
| `Value` | `DATA_PROPERTY` | `QualifiedValue.Type` | **1** | **1** |
| `Case` | `DATA_PROPERTY` | `Undefined \| String` | 0 | 1 |
| `CaseUID` | `DATA_PROPERTY` | `Undefined \| String` | 0 | 1 |
| `Description` | `DATA_PROPERTY` | `MultiLanguageString` | 0 | 1 |
| `DisplayText` | `DATA_PROPERTY` | `Undefined \| String` | **1** | **1** |
| `Scope` | `DATA_PROPERTY` | `DataTypes.Scope` | 0 | 1 |
| `Provenance` | `DATA_PROPERTY` | `DataTypes.QuantityProvenance` | 0 | 1 |
| `ProvenanceURI` | `DATA_PROPERTY` | `Undefined \| AnyURI` | 0 | 1 |
| `Range` | `DATA_PROPERTY` | `DataTypes.QuantityRange` | 0 | 1 |
| `ReferenceDataURI` | `DATA_PROPERTY` | `Undefined \| AnyURI` | 0 | 1 |
| `SourceURI` | `DATA_PROPERTY` | `Undefined \| AnyURI` | 0 | 1 |

`QualifiedValue` therefore adds, beyond a magnitude and a unit:

- a **case / case-UID** qualifier (a named scenario the value belongs to);
- a **scope** qualifier (`Alarm`, `Allowable`, `Design`, `Expected`,
  `Incidental`, `Operating`, `Protection`, `Rated`, `Test`, `Warning`);
- a **provenance** qualifier (`Calculated`, `Estimated`, `Observed`, `Set`,
  `Specified`) plus a free provenance URI;
- a **range** qualifier (`Actual`, `Average`, `LowerLimit`, `Nominal`, `Normal`,
  `UpperLimit`);
- optional reference/source URIs and a multi-language description;
- a **required** `DisplayText`, which is presentation text.

### 4.2 `PhysicalQuantity` — magnitude and typed unit

`Core.PhysicalQuantities.PhysicalQuantity` is an `AGGREGATED_DATA_TYPE`:

> "A quantification of a scalar physical property such as a length or a force.
> A <!SELF> comprises a numerical <SELF.Value> and a <SELF.Unit>."

| Property | Kind | Type | lower | upper |
|---|---|---|---|---|
| `UnitType` | `DATA_TYPE_PARAMETER` | `PhysicalQuantityUnit` (abstract) | — | — |
| `Value` | `DATA_PROPERTY` | `BUILTIN.Double` | 1 | 1 |
| `Unit` | `DATA_PROPERTY` | `PhysicalQuantity.UnitType` | 1 | 1 |

Findings that matter for the boundary:

- **The magnitude is a scalar `Double`**, exactly one per `PhysicalQuantity`.
- **The unit is mandatory and typed.** `Unit` is bound to the `UnitType`
  parameter, and each owning property pins the unit family through its type
  parameter — e.g. `QualifiedValue[PhysicalQuantity[PowerUnit]]` for `Duty`,
  `…[TemperatureUnit]` for `Temperature`/`SkinTemperature`,
  `…[PressureAbsoluteUnit]` for `Pressure`, `…[MassFlowRateUnit]` for
  `HotFlow`/`ColdFlow`.
- **Unit values are controlled enumeration literals** of a per-quantity-kind unit
  enumeration (for example `PowerUnit.Kilowatt`, `TemperatureUnit.Kelvin`,
  `TemperatureUnit.DegreeCelsius`, `MassFlowRateUnit.KilogramPerHour`). They are
  not free strings.
- The **quantity kind / dimension is not a field of the value**; it is carried by
  the *type parameter of the owning property*. The same `PhysicalQuantity`
  aggregate is reused for every quantity kind.
- A separate `PhysicalQuantityVector` exists (`Values` array `0..*`,
  `isOrdered=True`, plus one `Unit`) for vector-valued data such as
  `Composition`. Scalar process properties use `PhysicalQuantity`, not the vector
  type.

### 4.3 What is *not* present

- **No uncertainty/tolerance property** on `QualifiedValue`.
- **No numeric interval/range object.** `QuantityRange` is a *categorical*
  qualifier enum (`Actual`, `Average`, `LowerLimit`, `Nominal`, `Normal`,
  `UpperLimit`), not a lower/upper numeric bound pair.
- **No multi-value `Value` list** on the scalar path: `Value` is `1..1`. The
  vector case is a distinct type (`PhysicalQuantityVector`), used by composition
  properties, not by the scalar step/stream properties inspected here.

### 4.4 Are equivalent values in different units distinguishable?

Yes. `10` with `Unit=…Bar` and `1` with `Unit=…Megapascal` are two different
`PhysicalQuantity` instances with different `Value` and different unit literals.
DEXPI stores the **authored unit** as part of the state and does not normalise to
a base unit. Equivalent magnitudes are therefore serialized differently and
remain distinguishable.

## 5. Engineering-semantic distinctions

The decision must separate four concepts that are easy to conflate.

### 5.1 Classification

```text
ProcessStep.function = pumping
```

Answers: **what kind of engineering function is this?** This is not a quantity
and not a property value. ADR-0012 remains authoritative: `ProcessStep` has
exactly one classification axis (`function`), and no generic second
classification or property bag is introduced. A classification must never be
smuggled in as a property name inside a quantity structure.

### 5.2 Parameter / engineering property

Conceptual statements such as:

```text
pump head
stream temperature
heat-exchanger duty
pipe nominal diameter
```

Answers: **which engineering fact is being stated?** The property *name and
meaning* are semantic and domain-specific, and they are owned by the domain
object that models the fact (`ProcessStep`, `ProcessStream`, `PipingSegment`,
`Equipment`, …). This is the concept a generic string-keyed bag would destroy: a
`properties["duty"]` map has no owner, no value domain, and no place in the
fail-fast, `extra="forbid"` model.

### 5.3 Qualified engineering quantity (the value)

```text
45 m      10 bar      120 degC      2.5 MW
```

Answers: **what numerical magnitude and engineering unit qualify that property?**

The reusable part is the *value*. The engineering-property name is **not** part of
the reusable value — it stays with the domain object. Additional semantics beyond
`value + unit` are only those the evidence justifies; this decision keeps the
core to an authored scalar magnitude plus engineering-unit semantics and defers
the DEXPI qualifier fields.

### 5.4 Presentation

```text
"120 degC"    "120 C"    two-decimal display    label placement
```

Answers: **how is the value shown?** This is **not** canonical engineering state
(ADR-0003). Spelling, unit-symbol rendering, decimal precision, and label
placement belong to the renderer or a presentation layer. DEXPI's own
`DisplayText` is presentation text and must not be copied into the semantic
quantity.

### 5.5 The relationship (hypothesis under test)

```text
ProcessStep.duty ─────┐
ProcessStream.temp ───┼─> qualified engineering value
PipingSegment.DN ─────┘        ├─ magnitude
                               └─ unit semantics
```

The arrows show *ownership of a value by an explicit domain property*. They do
**not** approve any of those example fields, and they explicitly exclude a
generic `entity.properties[...]` map. The hypothesis — that the value is reusable
while the property stays domain-specific — is what §6–§9 test.

## 6. Real consumer / use-case inventory

Where could an engineering quantity eventually be needed? This determines whether
the quantity concept is genuinely cross-cutting or only domain-local. This is a
*consumer inventory*, not a field-authorization list.

| Consumer | Example quantity need | Today | Local or cross-cutting? |
|---|---|---|---|
| `ProcessStep` | pump `head`, exchanger `duty`, step `pressure`/`temperature` | none | domain-local *property*, reusable *value* |
| `ProcessStream` | `temperature`, `pressure`, `mass_flow`, `volume_flow` | none | domain-local property, reusable value |
| `ProcessPort` | a port-level design value (e.g. design pressure) | none | domain-local property, reusable value |
| `Equipment` | design/rating data (design pressure, volume, power) | none | domain-local property, reusable value |
| `PipingLine` / `PipingSegment` | `nominal_diameter`, design pressure, wall thickness, temperature | open **strings** (`nominal_diameter: DN80`) | domain-local property, reusable value |
| Future process ↔ physical realization | mapping constraints expressed as values | not modelled | domain-local property |
| DEXPI interoperability | `QualifiedValue`/`PhysicalQuantity` on steps and streams | rejected fail-closed | adapter translates into a canonical value |
| Calculations / simulation | arithmetic on magnitudes with unit checking | not modelled | cross-cutting *value* consumer |
| Engineering rules | bounds, ranges, comparisons ("design pressure ≥ operating") | not modelled | cross-cutting *value* consumer |
| Git diff / review | small, stable, authorable numeric changes | n/a | cross-cutting *presentation-of-state* |

**What the inventory shows.** The *value representation* (magnitude + unit) is the
same everywhere — that is the reusable, cross-cutting part. The *property* is
always domain-specific: `head` on a pump step, `nominal_diameter` on a segment,
`mass_flow` on a stream. No consumer suggests that the property name should become
generic, and none suggests that every entity should acquire an arbitrary
parameter collection.

```text
reusable:      magnitude + engineering unit            (cross-cutting)
domain-owned:  the property name/meaning that owns it  (per domain object)
```

That distinction is exactly the difference between "the value representation is
reusable" and "every object should have a generic parameters collection". The
second is explicitly **not** authorized.

## 7. Candidate models

Four candidate boundaries are compared, plus one refinement of B.

### Candidate A — no canonical quantity representation yet

Quantities remain an adapter/external-schema concern; DeepPlant stores no
quantity until a native authoring or calculation use-case forces one.

- **Honest case for A:** no DeepPlant-native consumer exists today. Every
  quantity use-case in §6 is currently *hypothetical* for DeepPlant (no
  calculation engine, no rules, no authoring of quantities). Implementing a
  quantity value now would be abstraction ahead of a real requirement
  (AGENTS.md, ADR-0001).
- **Cost of A alone:** it answers "not yet" but not "what the boundary will be",
  so a later slice would re-open the same design question under deadline
  pressure, and the fail-closed adapter would keep rejecting quantity-bearing
  DEXPI files without a stated target shape.

### Candidate B — reusable canonical quantity value + explicit domain fields

A reusable value representation (magnitude + engineering-unit semantics),
owned by explicit, domain-specific properties:

```text
ProcessStep
    duty: <qualified quantity>
ProcessStream
    temperature: <qualified quantity>
```

(The example fields are illustrative only and are **not** authorized.)

The value is generic; the engineering property stays explicit and domain-owned.

### Candidate B′ — B with unit-kind typed value

As B, but the value carries a quantity-kind/dimension bound so that a
`PowerQuantity` cannot be assigned to a `TemperatureQuantity` property at
validation time (i.e. B plus a *unit-kind* dimension tag on the value, without
proliferating per-property classes).

### Candidate C — generic property/parameter bag

```text
entity.properties["duty"] = ...
```

Strongly disfavoured by existing architecture. It would erase the domain owner of
the property, defeat `extra="forbid"` fail-fast validation, invite typos as new
"properties", and directly contradict ADR-0012's rejection of a generic
property/attribute/metadata bag. Evaluated explicitly and **rejected** (§8.3).

### Candidate D — strongly typed dimension/property-specific quantity types

Distinct types such as `PressureQuantity`, `TemperatureQuantity`,
`PowerQuantity`, `MassFlowQuantity`.

- **Strength:** compile-time-style safety that a power value cannot be placed in a
  temperature slot.
- **Risk:** premature proliferation. DEXPI itself does *not* do this — it uses one
  reusable `PhysicalQuantity` aggregate plus a *type parameter* on the owning
  property (§4.2). DEXPI's own design is the argument against per-property classes
  for the value; the typing lives on the property, not the value.

## 8. Comparison / trade-offs

| | Reusable value? | Property owner | Fail-fast fit | Type safety | Abstraction cost | Verdict |
|---|---|---|---|---|---|---|
| **A** no quantity yet | n/a | n/a | n/a | n/a | lowest | insufficient — answers "not yet", not the boundary |
| **B** reusable value + explicit fields | yes | domain object | yes | per-property (checklist) | low | **selected as the boundary** |
| **B′** B + unit-kind tag | yes | domain object | yes | value rejects wrong unit kind | low–medium | compatible extension; not required to state the boundary |
| **C** generic bag | value only | nobody | **no** | none | medium (hidden semantics) | **rejected** |
| **D** per-property quantity classes | yes | domain object | yes | strong | high (proliferation) | **rejected now** |

### 8.1 Why B is selected

- The reusable value is genuinely cross-cutting (§6), so a single shared value
  concept removes real repetition rather than adding an abstraction (AGENTS.md:
  introduce abstractions only when repetition/coupling/complexity justifies).
- It keeps the property explicit and domain-owned, preserving `extra="forbid"`
  fail-fast validation.
- It matches DEXPI's own design (one reusable quantity aggregate + a per-property
  type parameter), so the canonical shape is not invented against the external
  evidence.
- It does not commit to a units library, an enum, or a serialization syntax —
  those remain implementation-slice decisions.

### 8.2 Why B is not yet B′

The unit-kind/dimension typing of B′ adds real safety, but only once a consumer
actually assigns values to typed properties. Today no canonical property owns a
quantity, so there is nothing to type-check. B′ is recorded as the *likely* next
refinement; committing to it now would design validation for fields that do not
exist.

### 8.3 Why C is rejected

- It reintroduces exactly the generic bag ADR-0012 rejected, on a different
  object. The reasoning transfers unchanged: a string-keyed bag has no owner, no
  value domain, and no authoring workflow, and it defeats fail-fast validation.
- It answers "which engineering fact is being stated?" with an arbitrary string,
  so a typo becomes new engineering semantics instead of an error.
- It cannot state whether a `temperature` is a quantity, a string, or a label,
  so it cannot preserve units or support future calculations.

### 8.4 Why D is rejected *now*

- Per-property quantity classes proliferate with no current value: `PressureQuantity`,
  `TemperatureQuantity`, `PowerQuantity`, `MassFlowRateQuantity`,
  `HeatTransferCoefficientQuantity`, `HeatTransferResistanceQuantity`,
  `ParticleSizeQuantity`, `VolumeFlowQuantity`, and more — before any of them has
  a consumer.
- DEXPI deliberately uses *one* reusable `PhysicalQuantity` plus a property-level
  type parameter, so per-property classes are not required for interoperability.
- The real semantic-safety need (a power value must not fill a temperature slot)
  is addressed by the *property's* declared unit kind, i.e. by B/B′, not by a
  class explosion on the value.

## 9. Unit semantics

The decision must resolve, conceptually and without implementing a units library,
the distinction between six ideas:

| Concept | Meaning | Canonical? |
|---|---|---|
| numerical magnitude | the number the author wrote (`45`, `10`, `2.5`) | yes — canonical |
| engineering unit | which unit the author used (`m`, `bar`, `MW`) | yes — canonical |
| physical dimension / quantity kind | `length`, `pressure`, `power` (what the property means) | yes — via the owning **property** |
| authored unit | the unit as written by the author | yes — preserved |
| normalized / base-unit value | a derived, unit-converted magnitude | **deferred / derived** |
| display unit | the unit symbol as rendered | no — presentation |

### 9.1 The `10 bar` vs `1 MPa` question

```text
Are 10 bar and 1 MPa:
  (a) the same canonical state,
  (b) merely mathematically equivalent states, or
  (c) distinct authored engineering states with an equivalent normalized value?
```

**Answer: (c).** The authored magnitude and the authored engineering unit are part
of the canonical state; `10 bar` and `1 MPa` are *distinct authored states* whose
magnitudes are *mathematically equivalent after conversion*. This mirrors the
verified DEXPI behaviour (§4.4): DEXPI stores the authored unit literal and does
not normalise, so the two values are serialized differently and remain
distinguishable.

Consequences:

- **Git diff:** changing `10 bar` to `1 MPa` is a real, reviewable change to
  authored state (both magnitude and unit tokens change), not a no-op. Small,
  stable, authorable diffs are a DeepPlant goal, and preserving the authored unit
  keeps intent visible.
- **Semantic equality:** equality must compare magnitude **and** authored unit.
  Two values are equal only if both match. A normalized comparison is a *derived*
  operation, not the definition of equality.
- **Round-trip fidelity:** preserving the authored magnitude and unit is what
  makes a faithful import/export possible; normalising on load would silently
  rewrite engineering intent and prevent a faithful round-trip.
- **Human review:** engineers author and review in their working units; a model
  that silently converts would be harder to review and trust.
- **Future calculations:** calculations need conversion and normalization — but
  these are *derived* operations that consume the canonical authored value. The
  conversion mechanism (factor tables, units library, dimension algebra) is
  deliberately **deferred** to a later implementation slice; this decision only
  fixes that the authored state must be preserved.
- **DEXPI import/export:** the adapter maps DEXPI's authored unit literal onto the
  canonical authored unit and back, rather than normalising, so the mapping stays
  faithful.

### 9.2 What is canonical, and what is derived

- **Canonical:** authored scalar magnitude + authored engineering unit, with the
  quantity kind owned by the property.
- **Derived (deferred):** normalized/base-unit magnitude, conversion factors,
  dimension algebra, arithmetic, and any unit registry.
- **Presentation (not semantic):** display unit symbol, decimal formatting,
  precision, unit-symbol spelling, and DEXPI `DisplayText`.

This deliberately **defers conversion/normalization mechanics while defining the
semantic information that must be preserved**: the authored magnitude, the
authored unit, and the property's quantity kind.

## 10. Value domain and multiplicity

Only what the evidence justifies is decided.

| Question | Decision now | Basis |
|---|---|---|
| float vs exact decimal | **deferred**; the evidence establishes a scalar numeric magnitude but not a precision/exactness rule. DEXPI uses `Double`. | §4.2 |
| integer values | representable as a scalar magnitude; no separate integer concept. | §4.2 |
| undefined / absent | an absent property means *not specified yet* (existing DeepPlant convention). | model conventions |
| multiple values | **deferred**; scalar properties use one value (`1..1`). Vector values exist in DEXPI only as a distinct type (`PhysicalQuantityVector`) for composition, not for the scalar step/stream properties here. | §4.2, §4.3 |
| ranges | **deferred**; DEXPI's `Range` is a categorical qualifier, not a numeric interval (§4.3). No numeric-range evidence. | §4.3 |
| uncertainty / tolerance | **deferred**; no such property exists on `QualifiedValue`. | §4.3 |
| conditions / qualifiers (case, scope, provenance) | **deferred**; real DEXPI qualifiers exist but have no DeepPlant-native consumer yet. | §4.1 |

**Conclusion:** current evidence justifies **scalar engineering values with
units** only. Richer value semantics are explicitly deferred with the revisit
conditions in §15.

### 10.1 Multiplicity

DEXPI process properties frequently have `0..*` multiplicity (for example
`Duty`, `Pressure`, `Temperature` on a step). This must **not** be mechanically
translated into `list[Quantity]`.

What `0..*` means for these properties is that a property *may* carry several
distinct qualified values (for example several `Duty` values distinguished by
scope/range qualifiers). Whether DeepPlant needs to preserve that as a list, and
under what disambiguation rule, **cannot be determined from the inspected
evidence**. Multiplicity mapping is therefore **left explicitly unresolved**;
this decision does not decide `Quantity` vs `list[Quantity]`.

The one multiplicity fact that *is* established is inside the value: a single
`PhysicalQuantity` has exactly one `Value` (`1..1`) and one `Unit` (`1..1`).

## 11. Serialization boundary

No YAML syntax is designed here. Issue #32 must not establish a production
serialization contract, and
[contracts/yaml-format.md](../contracts/yaml-format.md) remains a description of
implemented behaviour only.

If an illustration is useful, it is labelled and non-authoritative:

```text
illustrative only — not an authorized serialization contract
```

Whether a scalar magnitude and a unit are authored as two adjacent keys, a single
string (`"10 bar"`), or a nested mapping is an implementation-slice decision that
depends on the eventual value domain and on fail-fast validation design. Nothing
in this document authorizes any of those shapes.

## 12. Decision

**Candidate B is accepted as the durable architectural boundary**, on these
explicit terms:

1. **A reusable canonical qualified-engineering-value concept is justified.** The
   value — an authored scalar magnitude plus engineering-unit semantics — recurs
   across process, physical/piping, interoperability, calculation, rule, and
   review consumers, so it is cross-cutting and belongs in the semantic model, not
   only in an adapter.
2. **The engineering property stays explicit and domain-owned.** `duty`, `head`,
   `temperature`, `nominal_diameter`, and similar are domain-field names with
   domain meaning; they are never replaced by generic string keys.
3. **No generic property/parameter bag.** Candidate C is rejected (§8.3). No
   entity gains an arbitrary `properties[...]` collection.
4. **No per-property quantity classes now.** Candidate D is rejected (§8.4).
   Quantity-kind typing belongs on the owning property (B/B′), matching DEXPI's
   own design.
5. **The value is canonical semantic state and lives in the semantic model, not in
   presentation.** Magnitude and unit are semantic; formatting, display text, and
   precision are not.
6. **The unit is semantic, not presentation-only.** The authored unit is part of
   canonical state (§9).
7. **Authored magnitude and authored unit are preserved.** `10 bar` and `1 MPa`
   are distinct authored states with mathematically equivalent magnitudes;
   normalisation/conversion is a derived, deferred operation (§9.1). Semantic
   equality compares magnitude **and** authored unit.
8. **The adapter translates.** An external representation such as DEXPI
   `QualifiedValue`/`PhysicalQuantity` is translated by the adapter into the
   canonical value (and back); the adapter does not become the home of the
   semantics. Concrete DEXPI mappings are a separate implementation slice and are
   not decided here.
9. **Only scalar values are in scope.** Richer value semantics and multiplicity
   mapping are deferred (§10, §15).
10. **Nothing is implemented by this decision.** No class, field, unit enum,
    registry, validation, conversion, arithmetic, serialization, or dependency is
    added. The boundary is decided so that a later slice can implement it
    deliberately.

## 13. Explicit non-goals

This decision does **not** authorize, and this slice does **not** perform:

- any change to `src/deepplant/model.py` or the adapter;
- any quantity class, unit class, registry, or enum;
- any serialization, conversion, arithmetic, or validation runtime;
- any generic property bag;
- any DEXPI mapping change;
- any units library or dependency (`Pint`, `unyt`, Astropy units, QUDT, UCUM,
  etc.);
- making `ExchangingThermalEnergy` supported, or reopening `StoringMaterial`;
- establishing production YAML syntax;
- promoting any implementation task.

## 14. Consequences

### Positive

- The recurring quantity question from Issue #22 now has a decided target
  boundary, so a later implementation slice does not re-litigate the shape under
  pressure.
- The reusable value is defined once, while every engineering property keeps its
  domain owner and fail-fast validation.
- Authored units are preserved, keeping diffs, review, and round-trips faithful.
- The decision is aligned with the external evidence (DEXPI's one reusable
  quantity aggregate + per-property typing) rather than invented against it.
- DEXPI `DisplayText` and other presentation concerns are explicitly kept out of
  the semantic model (ADR-0003).

### Negative / accepted trade-offs

- Adding a canonical quantity concept is a new semantic primitive; it must be
  introduced carefully in a later slice with executable tests, not opportunistically.
- Deferring conversion/normalization means downstream calculations will need a
  future conversion mechanism; the canonical model alone does not compute.
- Deferring the DEXPI qualifier fields means a faithful `QualifiedValue`
  round-trip (case/scope/provenance/range/URI) is not available yet, so
  quantity-bearing DEXPI files can still not be imported losslessly.

### DEXPI / `ExchangingThermalEnergy` consequence

A quantity boundary removes **one** blocker and **only** one:

```text
G5  No engineering-quantity representation  -> addressed by this decision
G1  Mandatory Method                        -> still unresolved (ADR-0012)
G2  Coupled multi-stream / thermal-side semantics -> still unresolved
G3  No port kind                            -> still unresolved
G4  No energy-flow connection kind          -> still unresolved
G6  NominalDirection handling               -> still unresolved
```

Therefore:

- `ExchangingThermalEnergy` **remains explicitly unsupported**; this decision does
  not mark it supported and does not change any adapter mapping.
- The other Issue #22 blockers are unaffected: a quantity value does not provide
  the mandatory `Method`, the hot/cold-side grouping, port kind, energy-flow kind,
  or `NominalDirection`.
- Even the quantity objective (G5) is only *partially* unblocked: DeepPlant would
  own the value, but the DEXPI `QualifiedValue` qualifier fields remain unmapped.

## 15. Revisit conditions

Revisit this boundary (through ADR-0013) when any of these occurs:

- A DeepPlant-native authoring, calculation, engineering-rule, or design workflow
  needs an actual quantity value on a canonical object — then implement the
  boundary in a dedicated slice.
- A faithful DEXPI `QualifiedValue` import/export is required — then decide the
  case/scope/provenance/range/URI qualifier and multiplicity mappings.
- Evidence shows scalar magnitude + unit is insufficient (vector values, numeric
  ranges, uncertainty/tolerance) — then design the richer value domain.
- Division of `float` vs exact-decimal magnitude becomes decision-relevant.
- A concrete requirement shows the property-name/quantity boundary is wrong (for
  example a genuine need for a controlled property vocabulary).
- A units library or conversion mechanism must be selected — a separate
  implementation decision, not part of this boundary.

## 16. Roadmap implications

- Issue #32 delivered its decision/evidence. A canonical reusable qualified
  engineering quantity is justified, owned by explicit domain properties, with
  units as semantic state.
- **No next executable task has yet been promoted.** The next direction must be
  selected from the new evidence this document and ADR-0013 produce.
- This slice does **not** promote `ExchangingThermalEnergy`, reopen
  `StoringMaterial`, start quantity implementation, create a units-framework
  Issue, or promote GUI/P&ID work.
- A follow-up implementation slice (implementing the quantity value and its
  first owning property, or mapping DEXPI `QualifiedValue`) is now
  *justifiable* but is deliberately not created or auto-promoted here.

## Related

- [ADR-0013](../decisions/ADR-0013-qualified-engineering-quantity-boundary.md) —
  the decision this evidence produces.
- [dexpi-exchanging-thermal-energy-evidence.md](../dexpi-exchanging-thermal-energy-evidence.md)
  — the Issue #22 evidence and gaps G1–G6.
- [process-step-classification.md](../process-step-classification.md) — the
  rejected generic property/second-axis shapes (ADR-0012).
- [contracts/dexpi-process-adapter.md](../contracts/dexpi-process-adapter.md),
  [contracts/process-model.md](../contracts/process-model.md),
  [contracts/physical-piping.md](../contracts/physical-piping.md) — current
  behaviour, unchanged.
- [ADR-0002](../decisions/ADR-0002-semantic-model-is-the-core.md),
  [ADR-0003](../decisions/ADR-0003-separate-semantic-and-presentation-models.md),
  [ADR-0011](../decisions/ADR-0011-canonical-physical-piping-realization.md),
  [ADR-0012](../decisions/ADR-0012-process-step-single-classification-axis.md).












