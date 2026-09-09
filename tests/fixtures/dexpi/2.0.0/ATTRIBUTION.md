# DEXPI 2.0 fixture provenance and attribution

Directory: `tests/fixtures/dexpi/2.0.0/`

Targeted DEXPI release: **V2.0.0** (DEXPI Specification 2.0.0, released
2025-10-10).

| File | Type | Source of structure | Licence | Local modifications | Purpose |
|---|---|---|---|---|---|
| `ATTRIBUTION.md` | provenance record | DeepPlant-authored | AGPL-3.0-only (repository) | — | provenance and licence index for this directory |
| `conformance_process.xml` | DeepPlant synthetic DEXPI 2.x Process conformance fixture | class names, `type` strings, enumeration literals, and the DEXPI XML envelope derived from the official DEXPI 2.0.0 specification (CC BY 4.0); XML content authored by DeepPlant | fixture XML: AGPL-3.0-only (repository); derived-from content: CC BY 4.0 with attribution | original DeepPlant-authored instance | supported-subset import, export round-trip, and renderer evidence |
| `mixed_plant_and_process.xml` | DeepPlant synthetic probe | same official sources as above plus a minimal Plant/PlantModel stub shaped like the official `reference_pid.xml` | same | original DeepPlant-authored instance | proves non-Process (Plant) objects are ignored |
| `plant_only.xml` | DeepPlant synthetic probe | `Plant/Diagram.PlantMetaData` property names and the `Plant/PlantModel` type string from the official DEXPI 2.0.0 model / `reference_pid.xml` | same | original DeepPlant-authored instance | proves a Plant-only file is rejected (Plant adapter out of scope), never silently imported |
| `energy_flows.xml` | DeepPlant synthetic negative probe | `Process/Process.EnergyFlow`, `.ThermalEnergyFlow`, `.ElectricalEnergyFlow`, `.MechanicalEnergyFlow` class identifiers from the official model | same | original; intentionally not a complete/valid process instance (diagnostic probe) | proves EnergyFlow subclasses raise, never become `ProcessStream` |
| `information_flow.xml` | DeepPlant synthetic negative probe | `Process/Process.InformationFlow` class identifier from the official model | same | original; intentionally not a complete/valid process instance (diagnostic probe) | proves InformationFlow raises, never becomes `ProcessStream` |
| `non_material_ports.xml` | DeepPlant synthetic negative probe | `Process/Process.ThermalEnergyPort`, `Process/Process.InformationPort` class identifiers from the official model | same | original; intentionally minimal (diagnostic probe) | proves non-material ports raise instead of mapping to `ProcessPort` |

## Official source record

- Official project page: https://dexpi.org/ (inspected 2026-09-09)
- Official specification repository: https://gitlab.com/dexpi/Specification
  (inspected 2026-09-09)
- Upstream release/tag: `V2.0.0`
- Upstream tag commit: `260c81c51039789a6148a98af4c6caf23f87a3e2`
  ("Merge branch 'spec_2.0.0-rc2' into 'master'", 2025-10-10)
- Licence: **Creative Commons Attribution 4.0 International (CC BY 4.0)** —
  confirmed in the official DEXPI 2.0 publication announcement and in the
  official repository `src/documentation/index.rst`
  (https://creativecommons.org/licenses/by/4.0/)
- Copyright holder (as stated upstream): the DEXPI Initiative / DEXPI e.V.
- Upstream files whose identifiers/structure are referenced by these fixtures:
  - `src/model/Process/Process.py` (model `Process`, `ProcessModel`)
  - `src/model/Process/Process/Process.py` (Process classes used in the
    supported subset and the probe class identifiers)
  - `src/model/Process/Enumerations/process_enumerations.ods`
    (`PortDirection` = `Inlet` / `Outlet`)
  - `src/documentation/basics/metamodel_and_exchange_format.rst` (DEXPI XML
    envelope: `Model`/`Import`/`Object`/`Components`/`Data`/`References`,
    `ID`/`IDREF` rules)
  - `src/documentation/_static/DEXPI_XML_Schema.xsd` (generic envelope schema)
  - `src/documentation/_static/reference_pid.xml` (official P&ID instance
    exemplar for the envelope shape and Plant metadata property names)

## Important caveats (read before using)

1. **No official DEXPI 2.x Process XML instance exists upstream.** As of the
   inspection date the official V2.0.0 repository contains exactly two XML
   files: `DEXPI_XML_Schema.xsd` (the generic envelope schema) and
   `reference_pid.xml` (a Plant/P&ID instance). There is **no** official DEXPI
   Process instance file. All files in this directory are therefore
   **DeepPlant-authored synthetic conformance/probe fixtures**, built from the
   official model's class identifiers, enumeration literals, and XML envelope
   rules. They prove the DeepPlant parser behaves correctly on a conformant
   shape; they do **not** prove vendor/external round-trip interoperability.
2. The `type` strings such as `Process/Process.Source` and
   `Process/Enumerations.PortDirection.Outlet` follow the model serialization
   pattern evidenced by the official Plant instance (`Plant/PlantModel`,
   `Plant/Instrumentation.ActuatingSystem`,
   `Plant/Enumerations.FailActionClassification.FailClose`). No official
   Process instance exists to confirm the Process package path string
   byte-for-byte; this inference is recorded in
   [`docs/dexpi-process-spike.md`](../../../../docs/dexpi-process-spike.md).
3. `energy_flows.xml` and `information_flow.xml` intentionally omit required
   reference values: they exist only to trigger the class-level "unsupported
   DEXPI connection" diagnostic before reference resolution, and are **not**
   complete or valid process instances.
4. Retrieval date: 2026-09-09. DEXPI is evolving; DEXPI 2.0.1 was reported as
   "being prepared" (dexpi.org, 2026-08-25) and may change these identifiers.
5. These fixtures reference DEXPI identifiers and model facts only; no
   restricted ISO/ISA/IEC content is present, and no DEXPI normative text or
   graphics are reproduced.

| `unsupported_process_step.xml` | DeepPlant synthetic negative probe | `Process/Process.ReactingChemicals` class identifier from the official model | same | original; intentionally minimal (diagnostic probe) | proves an out-of-subset ProcessStep class raises |
| `unresolved_reference.xml` | DeepPlant synthetic negative probe | official DEXPI XML `References`/`#`-IDREF envelope | same | original; intentionally broken reference (diagnostic probe) | proves unresolved port references raise clearly |
| `duplicate_identifier.xml` | DeepPlant synthetic negative probe | official `Identifier` data-property semantics | same | original; intentionally duplicated Identifier (diagnostic probe) | proves duplicate imported canonical ids raise |
