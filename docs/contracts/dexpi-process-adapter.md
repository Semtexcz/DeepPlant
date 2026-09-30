---
type: contract
status: active
canonical_for:
  - dexpi-process-adapter-contract
read_when:
  - interoperability-work
  - adapter-boundary-work
  - dexpi-version-pinning
depends_on:
  - docs/contracts/process-model.md
  - docs/architecture.md
decision:
  - docs/decisions/ADR-0002-semantic-model-is-the-core.md
  - docs/decisions/ADR-0009-separate-process-function-from-symbol-role.md
  - docs/decisions/ADR-0010-dexpi-plant-pid-semantic-boundary.md
  - docs/decisions/ADR-0012-process-step-single-classification-axis.md
evidence:
  - docs/dexpi-process-spike.md
  - docs/dexpi-exchanging-thermal-energy-evidence.md
superseded_by: null
---

# DEXPI Process Adapter Contract

> **Question this document answers:** which DEXPI 2.x Process subset is supported,
> and exactly where does the adapter fail closed?
>
> Implemented in `src/deepplant/adapters/dexpi.py`. DEXPI is an external
> representation; the canonical model is DeepPlant's own
> ([process-model.md](process-model.md), ADR-0002, ADR-0003). Research and
> mapping rationale: [../dexpi-process-spike.md](../dexpi-process-spike.md).

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
automatic compatibility. DEXPI 2.0.1 is not released; a future release must be
reviewed deliberately before the pin changes.

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

## Supported subset (explicit, never derived from class names)

| DEXPI Process class | Canonical `ProcessStep.function` |
|---|---|
| `Process/Process.Source` | `source` |
| `Process/Process.Sink` | `sink` |
| `Process/Process.Mixing` | `mixing` |
| `Process/Process.SplittingMaterial` | `splitting_material` |
| `Process/Process.Pumping` | `pumping` |

- Steps may carry **material ports only** (`Process/Process.MaterialPort`).
- Connections are `Process/Process.Stream` between material ports.
- DEXPI engineering `Identifier` maps to canonical ids, `Label` maps to `name`,
  and `Description` is dropped as documented lossy annotation metadata.
- `NominalDirection` is used only to check consistency with stream incidence and
  is never stored, because canonical ports have no direction field.
- Declared `Port.ConnectorReference` values are validated when present.

## Fail-closed behaviour (import)

Everything outside the supported subset is rejected with a `DexpiImportError`
naming the offending object and reason, never silently dropped or reinterpreted:

- any ProcessStep class outside the table above (for example
  `ExchangingThermalEnergy`, `RemovingThermalEnergy`, `SupplyingThermalEnergy`,
  `Compressing`, `ReactingChemicals`, `DrivingBy*`, `Storing*`);
- non-material ports (`EnergyPort`, `InformationPort`, `ThermalEnergyPort`);
- `EnergyFlow` / `InformationFlow` connections, which are never collapsed into a
  material `ProcessStream`;
- nested `SubProcessSteps` and any Data property, Component, or Reference not on
  the supported allow-list for the parsed object;
- duplicate XML `Object@id` values (a global uniqueness preflight), unresolved
  references, and wrongly typed references;
- `ConnectorReference` values that cannot be resolved;
- missing data DEXPI requires for a supported object (for example an
  engineering `Identifier`);
- model URIs that do not match the pinned Core/Process URIs.

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

## Not claimed

- Full DEXPI model or schema conformance. The official XSD is a generic envelope,
  so the adapter validates structure and references only.
- Round-trip or mapping claims for classes outside the symmetric subset, in
  particular `ExchangingThermalEnergy`
  ([../dexpi-exchanging-thermal-energy-evidence.md](../dexpi-exchanging-thermal-energy-evidence.md)).
- DEXPI `Method` properties on classes where DEXPI requires them (ADR-0012), and
  qualified engineering quantities (no canonical home yet).
- Plant/P&ID import or export, `Nozzle`/`PipingNode`, piping, instrumentation and
  signals, graphics, and presentation metadata (ADR-0010).
- Proteus XML, DEXPI 1.x, and any additional library: the adapter uses only the
  Python standard library.

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
- [process-model.md](process-model.md) — the canonical target model.
- [ADR-0009](../decisions/ADR-0009-separate-process-function-from-symbol-role.md),
  [ADR-0010](../decisions/ADR-0010-dexpi-plant-pid-semantic-boundary.md),
  [ADR-0012](../decisions/ADR-0012-process-step-single-classification-axis.md).
