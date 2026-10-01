---
type: contract
status: active
canonical_for:
  - dexpi-process-adapter-contract
read_when:
  - interoperability-work
  - adapter-boundary-work
  - dexpi-version-pinning
  - dexpi-compatibility-review
update_when:
  - adapter-change
  - canonical-model-change
  - dexpi-model-change
depends_on:
  - docs/contracts/process-model.md
  - docs/architecture.md
decision:
  - docs/decisions/ADR-0002-semantic-model-is-the-core.md
  - docs/decisions/ADR-0009-separate-process-function-from-symbol-role.md
  - docs/decisions/ADR-0010-dexpi-plant-pid-semantic-boundary.md
  - docs/decisions/ADR-0012-process-step-single-classification-axis.md
  - docs/decisions/ADR-0013-qualified-engineering-quantity-boundary.md
evidence:
  - docs/dexpi-process-spike.md
  - docs/dexpi-exchanging-thermal-energy-evidence.md
superseded_by: null
---

# DEXPI Process Adapter Contract

> **Question this document answers:** which DEXPI 2.0.0 Process concepts does
> DeepPlant support, **in which direction**, under which semantic constraints,
> with what executable evidence, and exactly where does the adapter fail closed?
>
> Implemented in `src/deepplant/adapters/dexpi.py`. DEXPI is an external
> representation; the canonical model is DeepPlant's own
> ([process-model.md](process-model.md), ADR-0002, ADR-0003). Research and
> mapping rationale: [../dexpi-process-spike.md](../dexpi-process-spike.md).
>
> Support is **not** a single yes/no feature: every DEXPI concept has a per-row
> state and per-direction claim in the
> [compatibility matrix](#compatibility-matrix).

## Pinned target

| Fact | Value |
|---|---|
| DEXPI version / tag | `2.0.0` / `V2.0.0` |
| Release commit | `260c81c51039789a6148a98af4c6caf23f87a3e2` |
| Licence | CC BY 4.0 |
| Official source | <https://gitlab.com/dexpi/Specification> |
| Import preflight URIs | `https://data.dexpi.org/models/2.0.0/Core.xml`, `https://data.dexpi.org/models/2.0.0/Process.xml` |

The pin is enforced at runtime: an import whose model URIs are missing,
differently prefixed, from another version, or conflicting fails with
`DexpiImportError` naming the expected and observed values instead of attempting
automatic compatibility.

DEXPI 2.0.1 was released on 2026-09-30. DeepPlant remains deliberately pinned to
DEXPI 2.0.0; DEXPI 2.0.1 has not yet been reviewed for compatibility and is
therefore outside the supported adapter contract. The pin may move only after a
separate compatibility review.

## Public API

```python
from deepplant.adapters.dexpi import (
    import_dexpi_process,  # (source: str | Path) -> ProcessModel
    import_dexpi_process_xml,  # (xml_text: str) -> ProcessModel
    export_dexpi_process,  # (process, *, model_name, model_uri) -> str
    validate_dexpi_xml_structure,  # (xml_text: str) -> None
    DexpiImportError,
    DexpiExportError,
)
```

The `DEXPI_*` module constants (`DEXPI_TARGET_VERSION`, `DEXPI_TARGET_TAG`,
`DEXPI_TARGET_REVISION`, `DEXPI_SOURCE_URL`, `DEXPI_LICENCE`,
`DEXPI_INSPECTION_DATE`, `DEXPI_CORE_MODEL_URI`, `DEXPI_PROCESS_MODEL_URI`)
expose the pin above for callers and tests.

Both import functions construct the canonical `ProcessModel` through its public
Pydantic constructors, so S1–S4 (see [process-model.md](process-model.md)) run on
imported content.

## Support states (closed vocabulary)

Every row in the [compatibility matrix](#compatibility-matrix) uses exactly one
of these states. Vague states ("partial", "mostly supported", "should work") are
deliberately not used.

| State | Meaning |
|---|---|
| `supported` | Implemented and exercised by a committed test in `tests/test_dexpi_adapter.py`. |
| `import-only` | Consumed or validated on import; never produced on export. |
| `export-only` | Produced on export; not consumed on import. |
| `experimental` | Implemented but outside the pinned, test-backed subset. |
| `investigated / unsupported` | Inspected against the pinned model; deliberately rejected; no mapping claimed. |
| `not investigated` | No inspection evidence; not attempted in this adapter. |
| `not applicable` | No canonical home and no adapter role by design. |

Currently no row is `export-only` or `experimental`; `import-only` applies only
to concepts the adapter consumes but never re-emits (`Description`,
`Port.ConnectorReference`).

## Semantic round-trip (definition)

**Semantic round-trip means that the engineering semantics represented by the
supported subset survive translation through the canonical DeepPlant model,
subject to the explicitly documented lossy metadata and deterministic regenerated
serialization details below.** It is **not** textual XML equality.

Semantic equality is the canonical content DeepPlant owns, matching the
`semantic_fingerprint` used by the tests:

```text
steps   : id, function, name, ports[id]                        (per ProcessStep)
streams : id, name, source(step, port), target(step, port)     (per ProcessStream)
```

Four equality notions are deliberately separated:

| Notion | Claimed? |
|---|---|
| Semantic equality (the fingerprint above) | Yes, for the supported subset |
| Serialization equality (identical XML/YAML text, byte order) | No |
| DEXPI XML `Object@id` equality | No — file-local, deterministically regenerated |
| Annotation preservation (`Description`, formatting) | No — annotation metadata is dropped |

## Directional support claims

Import, export, and round-trip are separate claims and are never inferred from
one another.

| Direction | Claim | Executable evidence |
|---|---|---|
| DEXPI → DeepPlant (import) | `supported` for the subset | `tests/test_dexpi_adapter.py::test_expected_process_steps_import`, `::test_material_streams_import` |
| DeepPlant → DEXPI (export) | `supported` for the subset | `::test_export_is_deterministic`, `::test_exported_xml_passes_structural_subset_validation` |
| DEXPI → DeepPlant → DEXPI (semantic round-trip) | `supported` for the subset | `::test_material_only_pumping_reverse_exports_and_round_trips` |
| DeepPlant → DEXPI → DeepPlant (semantic round-trip) | `supported` for the subset | `::test_semantic_roundtrip_preserves_fingerprint` |

Both round-trip directions have executable evidence; both are semantic, not
serialization, equality.

## Compatibility matrix

Evidence legend: `t:<name>` = `tests/test_dexpi_adapter.py::<name>`;
`fix:<file>` = `tests/fixtures/dexpi/2.0.0/<file>`. Provenance names the
evidence/decision document that justifies the row. Concepts outside a `supported`
row are never claimed in any direction.

**Runtime support state and evidence maturity are separate axes.** Every DEXPI
`ProcessStep` class outside the supported subset is rejected at runtime by the
generic unsupported-class boundary, but that rejection alone is **not** evidence
that the class's semantic mapping was investigated. A row is
`investigated / unsupported` only when a provenance document actually inspected
the concept (a class-level mapping, or `Method` property semantics where the row
says so); otherwise the row is `not investigated`. Runtime rejection is not
evidence maturity.

| DEXPI concept / class | Import | Canonical DeepPlant mapping | Export | Semantic round-trip | Limitations / conditions | Executable evidence | Provenance / evidence |
|---|---|---|---|---|---|---|---|
| `Process/ProcessModel` | supported | the single `ProcessModel` | supported | supported | exactly one accepted; multiple, Plant-only, or mixed-version rejected | `t:test_conformance_fixture_parses`, `t:test_pinned_2000_core_and_process_imports_succeed` | spike §4–§5; ADR-0002 |
| `Process/Process.Source` | supported | `ProcessStep.function = source` | supported | supported | — | `t:test_expected_process_steps_import`, `t:test_semantic_roundtrip_preserves_fingerprint` | spike §5.3; ADR-0009 |
| `Process/Process.Sink` | supported | `ProcessStep.function = sink` | supported | supported | — | `t:test_expected_process_steps_import` | spike §5.3; ADR-0009 |
| `Process/Process.Mixing` | supported | `ProcessStep.function = mixing` | supported | supported | — | `t:test_expected_process_steps_import` | spike §5.3; ADR-0009 |
| `Process/Process.SplittingMaterial` | supported | `ProcessStep.function = splitting_material` | supported | supported | abstract `Splitting` / `SplittingEnergy` are not covered | `t:test_expected_process_steps_import` | spike §5.3; ADR-0009 |
| `Process/Process.Pumping` | supported | `ProcessStep.function = pumping` | supported | supported | **material-port-only**; see [Pumping boundary](#pumping-boundary) | `t:test_material_only_pumping_reverse_exports_and_round_trips`, `t:test_pumping_with_unsupported_head_property_fails` | ADR-0009; ADR-0012 |
| `Process/Process.MaterialPort` | supported | `ProcessPort(id)` | supported | supported | only port class accepted; ids unique within the step | `t:test_process_step_owned_ports_import` | spike §5.1 |
| `Process/Process.Stream` | supported | `ProcessStream(id, name, source, target)` | supported | supported | only material connection class accepted; endpoints must resolve to imported `MaterialPort`s | `t:test_material_streams_import`, `t:test_source_target_references_resolve` | spike §5.1 |
| Data `Identifier` (step/port/stream) | supported | canonical `id` | supported | supported | exactly one, non-empty; duplicate canonical ids rejected | `t:test_identifiers_map_from_engineering_identifier_not_xml_object_id`, `t:test_duplicate_imported_canonical_id_fails_clearly` | spike §5.2 |
| Data `Label` (step/stream) | supported | `name` | supported | supported | absent or `Undefined` → `name = None`; never identity | `t:test_expected_process_steps_import`, `t:test_material_streams_import` | spike §5.2 |
| Data `Description` (step/port/stream) | import-only | none — dropped | not applicable (never emitted) | does not break the defined round-trip | lossy annotation metadata by design | `t:test_no_presentation_data_enters_the_semantic_model` | spike §5.2 |
| Data `NominalDirection` (port) | supported (validated) | validated against, and derived from, `ProcessStream` incidence; never stored | supported (derived) | supported (preserved via incidence) | contradiction with incidence rejected; required on every port for export | `t:test_direction_contradiction_fails_clearly`, `t:test_export_rejects_port_without_incident_stream` | ADR-0009; spike §5.2 |
| `Port.ConnectorReference` | import-only (validated) | validated against stream incidence; never stored | not applicable (never emitted) | does not break the defined round-trip; redundant with incidence | DEXPI multiplicity unresolved (`TODO check multiplicities`); tolerated when absent | `t:test_valid_connector_reference_to_matching_stream_succeeds`, `t:test_inconsistent_connector_reference_incidence_fails` | spike §5.1 |
| `ProcessConnection.Source` / `Target` references | supported | `ProcessRef(step, port)` endpoints | supported | supported | must be `#`-IDREF tokens resolving to imported `MaterialPort`s; unresolved or mistyped rejected | `t:test_source_target_references_resolve`, `t:test_unresolved_references_fail_clearly` | spike §5.1 |
| `Process/Process.ExchangingThermalEnergy` | investigated / unsupported | none — `heat_exchange` stays DeepPlant-native, not equal to the class | investigated / unsupported | none | mandatory `Method: HeatExchangeMethod`; couples ≥2 material streams; thermal side is a separate `ThermalEnergyPort`/`ThermalEnergyFlow`; no canonical port kind or qualified quantity | `t:test_exchanging_thermal_energy_step_class_is_explicitly_unsupported`, `t:test_exchanging_thermal_energy_is_unsupported_without_its_properties` | [Issue #22 evidence](../dexpi-exchanging-thermal-energy-evidence.md); ADR-0012 |
| `Process/Process.ThermalEnergyPort` | investigated / unsupported | none | investigated / unsupported | none | no canonical non-material port kind | `t:test_non_material_ports_are_not_imported`, `fix:non_material_ports.xml` | Issue #22 §3.1 |
| `Process/Process.EnergyPort` | investigated / unsupported | none | investigated / unsupported | none | abstract general energy port; no canonical port kind | no dedicated executable fixture/test; canonical port-kind gap established by the Process model evidence | Issue #22 §3.1 |
| `Process/Process.EnergyFlow` (`ThermalEnergyFlow`, `ElectricalEnergyFlow`, `MechanicalEnergyFlow`) | investigated / unsupported | none | investigated / unsupported | none | never collapsed into `ProcessStream`; carries `Duty`/`Temperature` | `t:test_energy_flows_are_not_imported_as_process_streams`, `fix:energy_flows.xml` | Issue #22 §3.2 |
| `Process/Process.InformationPort` | investigated / unsupported | none | investigated / unsupported | none | no canonical port kind | `t:test_non_material_ports_are_not_imported` | Issue #22 §3.1 |
| `Process/Process.InformationFlow` | investigated / unsupported | none | investigated / unsupported | none | never collapsed into `ProcessStream` | `t:test_information_flow_is_not_imported_as_process_stream`, `fix:information_flow.xml` | Issue #22 §3.2 |
| `ProcessStep.SubProcessSteps` | investigated / unsupported | none — no step hierarchy | investigated / unsupported | none | populated `SubProcessSteps` rejected; no dedicated test | no dedicated test; enforced by `_collect_step` populated-`SubProcessSteps` branch | ADR-0012 |
| DEXPI `*Method` **properties** (`HeatExchangeMethod` on `ExchangingThermalEnergy`/`RemovingThermalEnergy`/`SupplyingThermalEnergy`, `CompressionMethod` on `Compressing`, `ReactionProcessType` on `ReactingChemicals`, `EngineDriveMethod`/`MotorDriveMethod`/`TurbineDriveMethod` on `DrivingBy*`, `PumpingMethod` on `Pumping`) | investigated / unsupported | none | investigated / unsupported | none | the `Method` **property semantics** were investigated as one generic canonical-classification concept (ADR-0012), not the class-level mapping of each owning step; heterogeneous enum domains; no second classification axis | no dedicated `Method` test; rejection follows from the `ProcessStep` Data-property allow-list, with `Method` semantics established by ADR-0012 evidence | [ADR-0012](../decisions/ADR-0012-process-step-single-classification-axis.md); [process-step-classification.md](../process-step-classification.md) |
| Qualified engineering quantities (`Head`, `VolumeFlow`, `Duty`, `Temperature`, `Pressure`, `MassFlow`) | investigated / unsupported | none | investigated / unsupported | none | no implemented canonical qualified-quantity representation; [ADR-0013](../decisions/ADR-0013-qualified-engineering-quantity-boundary.md) defines the semantic boundary only, so the adapter still rejects quantity-bearing content | `t:test_pumping_with_unsupported_head_property_fails`, `t:test_stream_with_unsupported_property_fails`, `t:test_material_port_with_unsupported_property_fails` | [ADR-0013](../decisions/ADR-0013-qualified-engineering-quantity-boundary.md); [research/qualified-engineering-quantities.md](../research/qualified-engineering-quantities.md); ADR-0012 (original deferral) |
| Plant / P&ID (`Plant/PlantModel`, `Nozzle`, `PipingNode`, `PipingNetworkSystem`, …) | investigated / unsupported | none | investigated / unsupported | none | Plant-only input rejected; Plant objects ignored in mixed files | `t:test_plant_objects_are_not_imported_and_plant_only_files_fail`, `fix:plant_only.xml`, `fix:mixed_plant_and_process.xml` | [ADR-0010](../decisions/ADR-0010-dexpi-plant-pid-semantic-boundary.md) |
| Graphics / presentation metadata (`Core.Diagram`, coordinates, `PlantMetaData`) | investigated / unsupported | none | investigated / unsupported | none | presentation data must not enter the semantic model | `t:test_no_presentation_data_enters_the_semantic_model` | ADR-0003; ADR-0010 |
| Other DEXPI `ProcessStep` classes (for example the owners of an inspected `Method` property: `Compressing`, `ReactingChemicals`, `DrivingBy*`, `RemovingThermalEnergy`, `SupplyingThermalEnergy`, …) | not investigated | none established | not investigated | none claimed | the owning classes' **class-level import/export semantic mapping** was not investigated — only their `Method` property semantics were (see the `*Method` row); they fail by name through the generic unsupported-class boundary, and runtime rejection is not semantic investigation | `t:test_unsupported_process_step_class_fails_clearly`, `fix:unsupported_process_step.xml` (runtime rejection only) | spike §5.3; ADR-0009; [ADR-0012](../decisions/ADR-0012-process-step-single-classification-axis.md) (via `Method` semantics, not class-level mapping) |
| `Process/Process.StoringMaterial` / storage semantics (`StoringInPressureVessel`, `StoringSolids`, …) | not investigated | none established | not investigated | none claimed | rejected by the generic unsupported-class boundary, but no semantic mapping conclusion exists — runtime rejection is not semantic investigation; deliberately deferred, not resolved | no dedicated test; runtime rejection via the generic unsupported-class boundary | deferred `StoringMaterial` evidence context (Issue #21); [ADR-0012](../decisions/ADR-0012-process-step-single-classification-axis.md) |
| `Core.PersistentIdentifier` | not applicable | none | not applicable | none | originating-system context, not canonical identity; not imported | no dedicated test; analysis only | spike §5.2 |
| DEXPI 2.0.1 and later | not investigated | none | not investigated | none | DEXPI 2.0.1 released 2026-09-30 but not investigated and not supported by the current 2.0.0 pin; a separate compatibility review is required before the pin may move | `t:test_wrong_process_version_uri_fails_explicitly` | adapter pin |
| Proteus XML, DEXPI 1.x | not investigated | none | not investigated | none | only the DEXPI 2.0.0 XML envelope is handled | none | adapter scope |

## Pumping boundary

`Pumping` is `supported` **only for the material-port-only subset**. The adapter
asserts `pumping ↔ Process/Process.Pumping` (ADR-0009) and nothing more.

- **Accepted populated content:** `Identifier`, `Label`, `Description`, and a
  `Ports` collection of `Process/Process.MaterialPort` children. Empty wrappers
  carry no semantics and are tolerated.
- **Rejected (fail closed, by name):** `Method`, `Head`, `VolumeFlow`, and any
  other Data property; a populated `SubProcessSteps`; and any non-material port
  (`EnergyPort`, `ThermalEnergyPort`, `InformationPort`), including a driver
  energy port.
- **Consequence:** DEXPI `Pumping` content that carries method, head,
  volume-flow, or energy/driver semantics is neither importable nor exportable,
  and no round-trip is claimed for it. The material-only pump step round-trips
  because its canonical form (`function="pumping"` plus material ports and
  streams) reproduces exactly the supported DEXPI subset.

## `ExchangingThermalEnergy` (investigated / unsupported)

Carried forward from Issue #22
([evidence](../dexpi-exchanging-thermal-energy-evidence.md): import, export, and
round-trip stay unsupported). The blockers are model-level, not class-local:

- mandatory `Method: HeatExchangeMethod`, with no canonical home (ADR-0012);
- coupling of two or more material streams through one step;
- no canonical port *kind* (all canonical ports are untyped material ports);
- no canonical non-material / energy-flow connection kind;
- no canonical qualified engineering quantity (`Duty`, `Temperature`): the
  boundary is decided by
  [ADR-0013](../decisions/ADR-0013-qualified-engineering-quantity-boundary.md)
  but no value is implemented, so G5 stays an implementation/interoperability
  blocker;
- mandatory `NominalDirection` is derived from incidence rather than stored.

No mapping is implemented, no field is added to `ProcessStep`, and the
provenance-recorded negative fixture and its tests stay in place.

## Method semantics

Consistent with ADR-0012, canonical `ProcessStep` keeps exactly one
classification axis (`function`): no `Method` value is imported, stored, or
exported, and DEXPI classes whose `Method` is mandatory stay unsupported rather
than losing it silently.

## Fail-closed behaviour (import)

Unsupported semantic content inside the `ProcessModel` boundary fails closed: it
is rejected with a `DexpiImportError` naming the offending object and reason,
never silently dropped or reinterpreted.

Unrelated Plant/P&ID objects may coexist in a mixed DEXPI file and are outside
this Process-only adapter's mapping scope; they are ignored when a supported
`ProcessModel` is present. Plant-only input is rejected explicitly rather than
converted to an empty `ProcessModel`.

The per-concept state is in the [compatibility matrix](#compatibility-matrix); the
fail-closed checks are:

- a `ProcessStep` class outside the supported subset (see the "Other DEXPI
  ProcessStep classes" and "StoringMaterial / storage semantics" rows);
- a non-material port class, or a connection class other than material `Stream`;
- a populated `SubProcessSteps` collection, or any Data/Components/References
  property outside the allow-list for the parsed object (this is the mechanism
  that rejects `Method` and the untyped engineering quantities);
- duplicate XML `Object@id` values (a global uniqueness preflight), unresolved or
  wrongly typed references, and unresolvable `ConnectorReference` tokens;
- missing data DEXPI requires for a supported object (engineering `Identifier`,
  `NominalDirection`);
- model URIs that do not match the pinned Core/Process URIs, or conflicting
  duplicate imports.

Failing by name is deliberate: unsupported content stays visible as an explicit,
test-pinned gap instead of becoming a silent modelling over-claim.

## Export contract

```python
xml_text: str = export_dexpi_process(
    process,
    model_name="ProcessModel",  # DEXPI XML name pattern
    model_uri="https://example.org/deepplant/process-model",
)
```

- Exports the deliberately symmetric subset: `source`, `sink`, `mixing`,
  `splitting_material`, and material-port-only `pumping`. Reverse export is an
  engineering-classification assertion (ADR-0009), not a convenience mapping.
- Output is deterministic: object ids are derived deterministically and the same
  `ProcessModel` produces the same XML.
- `NominalDirection` is derived from `ProcessStream` incidence. A port with no
  incident stream, or with both an incident source and an incident target,
  raises `DexpiExportError` instead of inventing or contradicting DEXPI direction
  semantics.
- Functions without an unambiguous DEXPI class in this subset — for example
  `heat_exchange` and `unspecified` — raise `DexpiExportError`.
- The produced XML is structurally validated (envelope and referential
  integrity) before it is returned.

## Lossy mappings (intentional)

Every mapping that is intentionally lossy is listed here with its consequence, so
no loss stays implicit. "Defined round-trip" is the semantic round-trip of this
document.

| DEXPI source | Canonical treatment | Loss | Semantic round-trip | Export | Stronger fidelity claim |
|---|---|---|---|---|---|
| engineering `Identifier` | canonical `id` | none for the supported subset | does not break | does not prevent | none |
| `Label` | `name` | formatting not retained; `Undefined` and absent both → `None` | does not break | does not prevent (`Label` re-emitted, `Undefined` when `None`) | limits exact label-text fidelity |
| `Description` | dropped | annotation text lost | **does not break** the defined round-trip | does not prevent export (never emitted) | **prevents** an annotation-preservation claim |
| XML `Object@id` | file-local resolution key only | not canonical identity; ids regenerated on export | does not break (excluded from semantic equality) | does not prevent | **prevents** an XML-identity-preservation claim |
| `NominalDirection` | validated on import / derived on export | raw port direction not stored | does not break (incidence carries the same fact; contradictions rejected) | does not prevent (must be derivable, else raises) | **prevents** a raw port-metadata-preservation claim |
| `Port.ConnectorReference` | validated on import when present | not stored; not regenerated on export | does not break (redundant with stream incidence) | does not prevent | **prevents** a full connector-reference-preservation claim |

No row above prevents export of the supported subset, and none breaks the defined
semantic round-trip; each only caps a stronger (serialization- or
metadata-fidelity) claim.

## Not claimed

- Full DEXPI model or schema conformance. The official XSD is a generic envelope,
  so the adapter validates structure and references only.
- Any mapping or round-trip outside the `supported` rows of the
  [compatibility matrix](#compatibility-matrix); in particular
  `ExchangingThermalEnergy`, energy/information ports and flows, Plant/P&ID
  content, and graphics/presentation metadata.
- DEXPI `Method` semantics (ADR-0012) and qualified engineering quantities:
  Issue #32 decided a boundary for a reusable canonical quantity value
  ([ADR-0013](../decisions/ADR-0013-qualified-engineering-quantity-boundary.md))
  but implemented nothing, so the adapter still rejects the untyped engineering
  quantities and the DEXPI `QualifiedValue` qualifier fields.
- Proteus XML and DEXPI 1.x: the adapter targets the pinned DEXPI 2.0.0 XML
  envelope using only the Python standard library.

## Fixtures and provenance

- Fixtures live under `tests/fixtures/dexpi/2.0.0/` with an `ATTRIBUTION.md`
  record covering source, licence, and limitation.
- No official DEXPI Process instance exists upstream, so the DeepPlant-owned
  conformance fixture is labelled as synthetic rather than presented as neutral.
- A provenance-recorded negative fixture pins the `ExchangingThermalEnergy`
  rejection so a future widening of the subset breaks a test instead of silently
  producing an over-claiming model.
- No DEXPI normative text or graphics are vendored; identifiers are referenced
  under CC BY 4.0 attribution (ADR-0007).

## Related

- [../dexpi-process-spike.md](../dexpi-process-spike.md) — pin research, mapping
  matrix, identity semantics, export-feasibility assessment.
- [../dexpi-exchanging-thermal-energy-evidence.md](../dexpi-exchanging-thermal-energy-evidence.md)
  and [../process-step-classification.md](../process-step-classification.md) —
  the evidence for the unsupported areas.
- `tests/test_dexpi_adapter.py` and `tests/fixtures/dexpi/2.0.0/` — the
  executable evidence and provenance behind every matrix row.
- [process-model.md](process-model.md) — the canonical target model.
- [ADR-0002](../decisions/ADR-0002-semantic-model-is-the-core.md),
  [ADR-0009](../decisions/ADR-0009-separate-process-function-from-symbol-role.md),
  [ADR-0010](../decisions/ADR-0010-dexpi-plant-pid-semantic-boundary.md),
  [ADR-0012](../decisions/ADR-0012-process-step-single-classification-axis.md).
