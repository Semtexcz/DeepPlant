# ADR-0013: A Reusable Qualified Engineering Quantity, Owned by Explicit Domain Properties

> Status: Accepted
> Date: 2026-10-01

## Context

Issue #22 recorded one unresolved model-level gap: DEXPI process steps and streams
carry numerical engineering values with units (`Duty`, `Area`, `HotFlow`/`ColdFlow`,
`HeatTransferCoefficient`, `HeatTransferResistance`, `SkinTemperature`,
`TemperatureDifference`, `Pressure`, `Temperature`, `Head`, `VolumeFlow`,
`MassFlow`), and DeepPlant has no canonical place for any of them (gap **G5**).
ADR-0012 deferred "qualified engineering quantities" as a separate decision, and
the DEXPI adapter keeps rejecting quantity-bearing content fail-closed.

Issue #32 asked, before any field or class existed:

```text
What semantic boundary should DeepPlant use for numerical engineering values
with units?
```

The investigation is in
[docs/research/qualified-engineering-quantities.md](../research/qualified-engineering-quantities.md),
based on the pinned official DEXPI `V2.0.0` model (release commit
`260c81c51039789a6148a98af4c6caf23f87a3e2`, inspected 2026-10-01). It found that:

- DEXPI `QualifiedValue` is **not** `{value, unit}`: its single required `Value`
  is a `PhysicalQuantity` (one `Double` magnitude + a mandatory typed unit) or a
  bare `Double`, plus optional case/scope/provenance/range/URI qualifiers and a
  required presentation `DisplayText`;
- DEXPI reuses one `PhysicalQuantity` aggregate for every quantity kind and pins
  the unit family on the *owning property* through a type parameter
  (`QualifiedValue[PhysicalQuantity[PowerUnit]]`, `…[TemperatureUnit]`, …), with
  unit values as controlled enumeration literals;
- DEXPI carries no uncertainty/tolerance property and no numeric interval object;
  its `Range` is a categorical qualifier enum;
- DEXPI stores the **authored** unit and does not normalise, so `10 bar` and
  `1 MPa` remain distinguishable;
- in DeepPlant no canonical object carries a quantity, and quantities appear as a
  genuine gap across process, physical/piping (ADR-0011 deferred DN/pressure
  typing), interoperability, future calculations/rules, and review.

## Options

- **A — no canonical quantity yet:** quantities stay adapter/external-schema
  concerns until a native consumer requires them.
- **B — reusable canonical quantity value + explicit domain fields:** a generic
  value (authored scalar magnitude + engineering-unit semantics) owned by
  explicit, domain-specific properties.
- **B′ — B with a unit-kind/dimension tag on the value.**
- **C — generic property/parameter bag:** `entity.properties["duty"] = …`.
- **D — strongly typed per-property quantity classes** (`PressureQuantity`,
  `TemperatureQuantity`, …).

Candidate analysis and trade-offs are in
[docs/research/qualified-engineering-quantities.md](../research/qualified-engineering-quantities.md)
§7–§9.

## Decision

**B is accepted as the durable architectural boundary**, on these explicit terms:

1. A reusable canonical qualified-engineering **value** concept is justified: the
   magnitude-plus-unit value is genuinely cross-cutting, so it belongs in the
   semantic model, not only in an adapter.
2. The engineering **property stays explicit and domain-owned** (`duty`, `head`,
   `temperature`, `nominal_diameter`, …). Property names/meaning are never
   replaced by generic string keys.
3. **No generic property/parameter bag** is introduced on any entity
   (Candidate C rejected; ADR-0012's reasoning transfers unchanged).
4. **No per-property quantity classes** now (Candidate D rejected); quantity-kind
   typing belongs on the owning property, matching DEXPI's own design.
5. The quantity value is **canonical semantic state**, not presentation
   (ADR-0003). Formatting, display text, precision, and labels stay out.
6. **Units are semantic state, not presentation-only.**
7. The **authored magnitude and authored unit are preserved**; `10 bar` and
   `1 MPa` are distinct authored states with mathematically equivalent
   magnitudes, and semantic equality compares magnitude **and** authored unit.
   Normalisation/conversion is a *derived, deferred* operation.
8. The **adapter translates** external representations (for example DEXPI
   `QualifiedValue`/`PhysicalQuantity`) into the canonical value and back; it does
   not own the semantics.
9. **Only scalar values** are in scope; richer value semantics and DEXPI `0..*`
   multiplicity mapping are deferred.
10. **Nothing is implemented by this decision** — no class, field, unit enum,
    registry, validation, conversion, arithmetic, serialization, or dependency.

## Consequences

### Positive

- The quantity boundary is decided once, so a later slice does not re-litigate it.
- The reusable value is defined once while every engineering property keeps its
  domain owner and fail-fast (`extra="forbid"`) validation.
- Authored units are preserved, keeping Git diffs, review, round-trips, and future
  calculations faithful to engineering intent.
- The boundary matches DEXPI's design (one reusable quantity aggregate plus a
  per-property type parameter) instead of being invented against it.
- Presentation concerns (including DEXPI `DisplayText`) stay out of the semantic
  model (ADR-0003).

### Negative

- A new canonical semantic primitive is authorized but not yet implemented; it
  must be introduced deliberately in a later slice with executable tests.
- Deferring conversion/normalization means calculations need a future conversion
  mechanism; the canonical model alone does not compute.
- Deferring DEXPI's qualifier fields means a faithful `QualifiedValue` round-trip
  is not yet available.

## DEXPI consequence (explicit)

This decision removes **one** `ExchangingThermalEnergy` blocker and only one. It
does **not** mark `ExchangingThermalEnergy` supported and changes no adapter
mapping. The mandatory `Method` (ADR-0012), coupled multi-stream/thermal-side
semantics, port kind, energy-flow kind, and `NominalDirection` handling
(G1–G4, G6) remain unresolved.

## Deferred

- Implementing the canonical quantity value and its first owning property field.
- Concrete DEXPI `QualifiedValue` import/export mappings and the qualifier fields
  (case, case UID, scope, provenance, range, reference/source URIs).
- Conversion/normalization mechanics, unit registries, dimension algebra,
  arithmetic, and any units-library or dependency selection.
- Non-scalar value semantics: vector values, numeric ranges,
  uncertainty/tolerance, and `float`-vs-exact-decimal precision policy.
- DEXPI `0..*` property-multiplicity mapping (`Quantity` vs `list[Quantity]`).
- Production YAML syntax for quantities.
- Process ↔ physical realization, `StoringMaterial` storage semantics, and DEXPI
  Process subset expansion.

## Revisit When

- A DeepPlant-native authoring, calculation, engineering-rule, or design workflow
  needs a quantity value on a canonical object.
- A faithful DEXPI `QualifiedValue` import/export is required.
- Evidence shows scalar magnitude + unit is insufficient, or that the
  property/quantity boundary is wrong.
- A units library or conversion mechanism must be selected.

## Related

- [docs/research/qualified-engineering-quantities.md](../research/qualified-engineering-quantities.md)
  — the full evidence and candidate analysis (Issue #32).
- [ADR-0002](ADR-0002-semantic-model-is-the-core.md),
  [ADR-0003](ADR-0003-separate-semantic-and-presentation-models.md),
  [ADR-0011](ADR-0011-canonical-physical-piping-realization.md),
  [ADR-0012](ADR-0012-process-step-single-classification-axis.md).
- [dexpi-exchanging-thermal-energy-evidence.md](../dexpi-exchanging-thermal-energy-evidence.md),
  [contracts/dexpi-process-adapter.md](../contracts/dexpi-process-adapter.md),
  [contracts/process-model.md](../contracts/process-model.md),
  [contracts/physical-piping.md](../contracts/physical-piping.md),
  [docs/roadmap.md](../roadmap.md).

