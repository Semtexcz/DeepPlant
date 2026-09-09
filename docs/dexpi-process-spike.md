---
type: spike-report
status: active
source_of_truth_for:
  - dexpi-2-process-interoperability-evidence
read_when:
  - interoperability-work
  - dexpi-version-pinning
  - adapter-boundary-work
update_when:
  - dexpi-model-change
  - adapter-change
  - canonical-model-change
---

# DEXPI 2.x Process Adapter Spike

> This document is a primary analysis deliverable of the DEXPI Process adapter
> spike, not secondary documentation. Its purpose is to answer, with
> executable evidence, whether an externally defined DEXPI 2.x Process model
> can be mapped into the DeepPlant canonical `ProcessModel` without hidden
> semantic invention or architectural coupling, and whether a deliberately
> supported DeepPlant subset can be serialized back to DEXPI-native XML for that
> supported structural subset without inventing semantics DeepPlant does not
> currently store. This is not full DEXPI model/schema conformance validation.

## 1. Targeted DEXPI release (pinned)

Policy applied: *stable release exists → target the latest stable release;
beta/RC newer than stable → inspect but do not make the production target
unless strongly justified.*

| Fact | Value |
|---|---|
| Targeted DEXPI version | **2.0.0** (DEXPI Specification 2.0.0) |
| Targeted tag | `V2.0.0` |
| Tag commit | `260c81c51039789a6148a98af4c6caf23f87a3e2` |
| Release date | 2025-10-10 |
| Source URL | https://gitlab.com/dexpi/Specification |
| Licence | CC BY 4.0 (confirmed in the official announcement and in the official repository `src/documentation/index.rst`) |
| Inspection date | 2026-09-09 |

Official sources inspected on 2026-09-09:

- https://dexpi.org/ (project/news pages; DEXPI 2.0 publication announcement,
  DEXPI August 2026 update)
- https://gitlab.com/dexpi/Specification (repository page, GitLab releases
  API, GitLab tags API, and a shallow `V2.0.0` clone at the pinned commit)

### Version state on the inspection date

- **Latest stable tagged 2.x release: `V2.0.0`.** The GitLab releases API
  lists exactly one 2.x release (`DEXPI Specification 2.0.0`, tag `V2.0.0`,
  `upcoming_release: false`). Repository tags: `V2.0.0`, `V1.4.0`, `V1.3.0`,
  `1.2`.
- **DEXPI 2.0.1 is not released.** The official DEXPI August 2026 update
  (2026-08-25) states DEXPI 2.0.1 "is being prepared" as an update that
  "particularly addresses corrections and clarifications in the Process
  Model", and that the DEXPI Profile (constraint mechanism) is under
  development. No beta/RC tag or release exists on the Specification
  repository. Per the policy above, the production target for this spike is
  therefore **V2.0.0**, with the known-upcoming incompatibility risk (Process
  model clarifications in 2.0.1) recorded throughout this document.

All implementation evidence in `src/deepplant/adapters/dexpi.py` is pinned to
this exact version/tag/revision/source/date.

The runtime import preflight enforces this pin: top-level `<Import>` elements
must contain exactly the supported DEXPI 2.0.0 Core and Process model URIs
(`https://data.dexpi.org/models/2.0.0/Core.xml` and
`https://data.dexpi.org/models/2.0.0/Process.xml`). DEXPI 2.0.1 is being
prepared with Process-model clarifications; until that version is explicitly
reviewed, the adapter rejects model URIs other than the pinned supported 2.0.0
URIs (missing/wrong-prefix/other-version/conflicting imports fail with an
explicit `DexpiImportError` naming the expected and observed values) instead of
attempting automatic compatibility. Unrelated additional imports (for example
`Plant`) remain allowed unless they create an ambiguity.

## 2. Native DEXPI XML, not Proteus

DEXPI 2.0 introduced a standardized **DEXPI XML** serialization that replaced
the legacy Proteus schema (official announcement, 2025-10-10). This spike uses
DEXPI XML only:

- it inspects the official generic envelope schema
  (`src/documentation/_static/DEXPI_XML_Schema.xsd` in the pinned repo),
- it follows the serialization rules documented in
  `src/documentation/basics/metamodel_and_exchange_format.rst`,
- it models instance files on the official P&ID instance exemplar
  (`src/documentation/_static/reference_pid.xml`).

The DEXPI 1.2/1.3/1.4 → Proteus XML path is **not** implemented and is
explicitly out of scope. pyDEXPI is **not** a runtime dependency and was not
used as an implementation basis; at inspection time its public documentation
still described DEXPI 1.3 / Proteus XML support. pyDEXPI may only ever serve
as an architectural reference, never as adapter code.

## 3. Scope

This PR targets the DEXPI **Process** model only, in the shape observed in the
official 2.0.0 model source:

```text
Process.ProcessModel
    |- ProcessSteps        (ProcessStep objects, each owning Ports)
    '- ProcessConnections  (ProcessConnection objects: Stream / EnergyFlow* / InformationFlow)
```

The initial DeepPlant target remains `ProcessModel` with `ProcessStep[]`
(owning `ProcessPort[]`) and `ProcessStream[]`.

### 3.1 Supported executable subset (explicit)

| DEXPI 2.0 class (XML `type`) | DeepPlant mapping |
|---|---|
| `Process/Process.Source` | `ProcessStep(type="source")` |
| `Process/Process.Sink` | `ProcessStep(type="sink")` |
| `Process/Process.Mixing` | `ProcessStep(type="mixing")` |
| `Process/Process.SplittingMaterial` | `ProcessStep(type="splitting")` |
| `Process/Process.Pumping` | `ProcessStep(type="pump")` |
| `Process/Process.MaterialPort` | `ProcessPort` |
| `Process/Process.Stream` | `ProcessStream` (material flow) |

The mapping is an **explicit table** in the adapter. It is never derived by
generic class-name conversion (no `dexpi_class_name.lower()`), because such a
conversion would silently pretend that class name spelling is engineering
semantics.

The import preflight also enforces the pinned DEXPI 2.0.0 Core/Process model
URIs and requires non-empty XML `Object@id` values to be globally unique
(file-local reference mechanics) before any mapping starts. `Pumping → pump` is
an importable lossy normalization; it is **not** part of the reverse map because
`type="pump"` still doubles as a presentation role and DEXPI `Pumping` may carry
energy-port/driver, `Head`, `Method`, and `VolumeFlow` semantics that DeepPlant
cannot represent. The reverse (DeepPlant → DEXPI) serialization covers only the
deliberately symmetric canonical subset: `source`, `sink`, `mixing`,
`splitting`.

### 3.2 Why these five step classes?

- **Source / Sink** (official descriptions: a flow of material into/out of the
  process; usable as an off-page connector in a PFD/BFD) correspond directly to
  DeepPlant boundary steps with a single material port.
- **Mixing** ("combine several flows of material into a single flow") and
  **SplittingMaterial** ("split an incoming flow of material into two or more
  outgoing flows of material") correspond to the DeepPlant mixing/splitting
  functions already exercised by the realistic fragment.
- **Pumping** ("transfer of mechanical energy to a liquid to increase pressure
  and generate a flow") is a defensible material-only function mapping. A
  fully realized DEXPI `Pumping` step may additionally own an energy port to a
  driver; such energy ports are rejected by this slice, which means only
  material-port Pumping instances import today. Because of that loss, the
  reverse mapping deliberately excludes `pump` (see §3.1): it is an importable
  normalization, not yet a safely exportable engineering classification, until
  the next `ProcessStep.type` semantics slice.

### 3.3 Explicitly out of scope (this slice)

DEXPI Plant model and P&ID import; Equipment/Piping/Nozzles/Valves/
Instrumentation/Signals; DEXPI graphical representations and any x/y/geometry
data; Plant↔Process mapping; physical `Connection` import; EnergyFlow and
InformationFlow; all ProcessStep classes outside 3.1; stream/step engineering
property values; material data libraries; step hierarchies; nested ports;
RDL/role resolution; DEXPI profiles; Proteus/DEXPI 1.x; pyDEXPI. See the full
list in §11 and in the roadmap's anti-roadmap.

## 4. Fixture status and provenance

**No suitable official DEXPI 2.x Process XML instance exists.** The official
V2.0.0 repository contains exactly two XML files: `DEXPI_XML_Schema.xsd`
(generic envelope schema) and `reference_pid.xml` (a Plant/P&ID instance).
There is no official Process instance, and no clearly-licensed DEXPI-authored
2.x Process fixture was found in the official material.

Per the task policy, this spike therefore:

1. documents that no official Process instance was found (above);
2. builds a **DeepPlant-owned synthetic conformance fixture** from the
   official model/schema/supporting material (smallest useful instance needed
   to exercise the parser);
3. labels it clearly as *DeepPlant synthetic DEXPI 2.x fixture* (see
   [`tests/fixtures/dexpi/2.0.0/ATTRIBUTION.md`](../tests/fixtures/dexpi/2.0.0/ATTRIBUTION.md));
4. does **not** claim the PR proved vendor/external round-trip
   interoperability.

Full provenance (source, upstream revision/tag, original filenames, licence,
copyright holder, local modifications, retrieval date, and the caveat list) is
recorded next to the fixtures. The XML fixtures were authored by DeepPlant;
they reference only official DEXPI class identifiers, enumeration literals,
and the official XML envelope shape. No restricted ISO/ISA/IEC content and no
DEXPI normative text or graphics are reproduced.

## 5. Mapping matrix

Status vocabulary: `exact` / `lossless-normalization` / `lossy` /
`unsupported` / `requires-model-change` / `unknown`. Status rows deliberately
do not maximize green: honest gaps matter more than coverage.

### 5.1 Top-level concepts

| DEXPI concept | DeepPlant concept | Status | Notes |
|---|---|---|---|
| `Process/ProcessModel` | `ProcessModel` | `lossless-normalization` | The container is structurally compatible (owning ProcessSteps + ProcessConnections). DeepPlant keeps step and stream ids in separate namespaces; DEXPI does the same implicitly (two composition collections) without requiring cross-collection Identifier uniqueness. Exactly one ProcessModel per file is supported by this slice. |
| `Process/ProcessStep` (abstract parent) | `ProcessStep` | `exact` (shape) | Composition parent; instantiable only via concrete subclasses (see 5.3). Step hierarchy (`SubProcessSteps`), operating conditions, and details are unsupported. |
| `Process/Process.Port` (abstract parent) | `ProcessPort` | `lossless-normalization` (flat material ports only) | Ports are owned by one ProcessStep and identified by their engineering `Identifier` (local to the step), matching DeepPlant `ProcessPort.id` locality. Nested ports (`SubReference`/`SuperReference`) unsupported. |
| `Process/Process.MaterialPort` | `ProcessPort` | `exact` (supported subset) | A material-transfer anchor. Requires a `NominalDirection` (Inlet/Outlet) which DeepPlant derives from stream incidence; consistency is checked on import, not stored. A declared `ConnectorReference` is validated when present (it must resolve to the port's material `Stream` and agree with incidence); absence is tolerated because the upstream multiplicity is unresolved. |
| `Process/Process.EnergyPort` / `ElectricalEnergyPort` / `MechanicalEnergyPort` / `ThermalEnergyPort` | — | `unsupported` | Non-material topology; rejected with the port class name. Never silently imported as a material `ProcessPort`. |
| `Process/Process.InformationPort` | — | `unsupported` | Control/information topology; rejected. |
| `Process/Process.ProcessConnection` (abstract parent) | `ProcessStream` | `lossless-normalization` (Stream subtype only) | Directed `Source`/`Target` reference properties to Port objects, each exactly one reference. |
| `Process/Process.Stream` | `ProcessStream` | `exact` (supported subset) | Official model: a flow of fluid or solid material between two `MaterialPort` objects. Canonical `ProcessStream` is the material process-graph edge. |
| `Process/Process.EnergyFlow` and subclasses | — | `unsupported` | Rejected with the class name. Never silently mapped to `ProcessStream`. |
| `Process/Process.InformationFlow` | — | `unsupported` | Rejected with the class name. Never silently mapped to `ProcessStream`. |
| `Process/ProcessConnection.Source` / `.Target` | `ProcessRef(step, port)` | `lossless-normalization` | DEXPI references ports through file-local XML object ids; the adapter resolves each to the owning step and the port's engineering Identifier, then builds canonical refs. Resolution is validated. |
| `ProcessConnection.ConnectorReference` (Port side, 1..1) | — | `unknown` | Upstream marks the multiplicity `TODO check multiplicities`; DEXPI 2.0.1 is preparing Process-model clarifications. This slice accepts declared connector references without enforcing the flagged cardinality (documented tolerance). |

### 5.2 Identity semantics (investigation and decision)

DEXPI 2.0 Process XML exposes several candidate identity concepts. Their
normative/official meanings, from the pinned model and the DEXPI XML
documentation, are:

| Identity candidate | Where defined | Scope | Unique guarantee | Engineering-facing | Persistent across exchange |
|---|---|---|---|---|---|
| XML `Object@id` (`xsd:ID`) | DEXPI XML envelope | **file-local** reference handle | Yes — unique within one DEXPI XML file (documented and XSD-enforced as `xsd:ID`) | No; reference mechanics | No |
| XML `Object@name` | DEXPI XML envelope | cross-file reference name | Not guaranteed | No; reference mechanics | No |
| Data property `Identifier` (1..1 string) | `ProcessStep`, `ProcessConnection`, `Port` in the Process model | engineering context | **Not schema-guaranteed** | **Yes** — the engineering-facing identifier | Yes (intended to survive exchange) |
| Data property `Label` | `ProcessStep` (0..1), `ProcessConnection` (1..1 Undefined\|String) | engineering context | No | Display label | No (display text) |
| `Core.PersistentIdentifier` (0..* on `ConceptualObject`) | Core model | originating-system context (`Context` + `Value`, e.g. a database URL plus an id) | Per context | Indirect | Only if a source tool records it |
| Data property `Description` | step/port/connection | annotation | No | No | No |

**Decision for the spike**

1. DeepPlant canonical `ProcessStep.id`, `ProcessStream.id`, and
   `ProcessPort.id` are taken **deterministically from the DEXPI engineering
   `Identifier`** (the required, engineering-facing identity), not from the
   XML object id and not from `Label`.
2. The file-local XML object id is used **only as the resolution key** for
   `Source`/`Target`/`#`-IDREF references inside one file. It is never
   promoted to a canonical id, because it is file-local by definition and
   changes with serialization mechanics.
3. `Label` maps to DeepPlant `name`; `Label = Undefined` or absent maps to
   `name = None`. Labels are never used as identity.
4. Duplicate engineering Identifiers inside one canonical namespace are
   rejected explicitly (a DEXPI file may legally contain duplicate
   Identifiers because DEXPI does not schema-enforce uniqueness; DeepPlant S1
   does, so a deterministic choice between two identical identifiers would
   otherwise be impossible).
5. `PersistentIdentifier` values are not imported (context-dependent,
   originating-system specific). If broader work needs them, the smallest safe
   step is an adapter-side provenance result, not a canonical field.

No identity change to the canonical model was required for this slice.

### 5.3 Functional ProcessStep classes observed in the official model

The official Process model defines a large vocabulary of concrete step
classes. Observed families (inspected in the official model source before any
status below was assigned) include: boundary steps (`Source`, `Sink`,
`Emitting`); flow generation/transport (`GeneratingFlow` and children such as
`Pumping`, `Compressing`, `Coalescing`; `TransportingFluids`,
`TransportingSolids`); combination/split (`Mixing` and children such as
`MixingSimple`, `StaticMixing`, `RotaryMixing`, `Kneading`, `Humidifying`;
`Splitting` abstract, `SplittingMaterial`, `SplittingEnergy`); heat and
storage functions (`ExchangingThermalEnergy`, `RemovingThermalEnergy`,
`StoringMaterial` and children such as `StoringFluids`, `StoringInTank`,
`StoringInPressureVessel`, `StoringSolids`); separation (`Separating` and its
large subtree such as `Distilling`, `Filtering`, `Drying`, `Evaporating`,
absorption/adsorption and mechanical/physical/thermal children); reaction
(`ReactingChemicals`); control/steering (`SteeringFlow` children such as
`RegulatingFlow`, `PreventingBackflow`, `ShuttingOffFlow`); energy supply
(`Supplying*`, `StoringEnergy` children); instrumentation/signal classes; and
detail classes (`ProcessStepDetail` and children). The full class registry is
a factual part of the official model, not a DeepPlant analysis; this document
records only the decisions taken.

| DEXPI class | DeepPlant type | Status | Notes |
|---|---|---|---|
| `Source` | `source` | `exact` | Boundary: a flow of material into the process; one material Outlet port. |
| `Sink` | `sink` | `exact` | Boundary: a flow of material out of the process; one material Inlet port. |
| `Mixing` | `mixing` | `exact` | Combines material flows; multiple Inlet ports + one Outlet. Children (`Humidifying`, `Kneading`, `MixingSimple`, `RotaryMixing`, `StaticMixing`) are unsupported in this slice. |
| `SplittingMaterial` | `splitting` | `lossless-normalization` | Material split; one Inlet + several Outlets. Abstract `Splitting` parent and `SplittingEnergy` are not mapped. |
| `Pumping` | `pump` | `lossy` | Defensible for liquid pumping with material ports only. DEXPI Pumping may own a driver energy port and carries `Head`/`Method`/`VolumeFlow`; the energy port is rejected and those properties are unsupported data. See Q10. `pump` is **not** reverse-exported: it is importable normalization only until the `ProcessStep.type` semantics decision. |

| `ExchangingThermalEnergy` | (`heat_exchanger`) | `requires-model-change` (not imported) | Realized by a heat exchanger; transfers thermal energy between two or more material streams. DeepPlant's fragment models only one selected side, and canonical `ProcessStep` has no coupling/side/role concept to pair two flows. Energy-utility sides would additionally require EnergyFlow. Not mapped in this slice. |
| `StoringFluids` / `StoringInTank` / `StoringInPressureVessel` / other `StoringMaterial` children | (`vessel`) | `requires-model-change` (not imported) | DeepPlant `vessel` is a containment *role*; the DEXPI classes also distinguish tank vs pressure-vessel regimes that canonical `type` cannot represent. Not mapped in this slice. |
| `ReactingChemicals`, `Separating` subtree, `Transporting*`, `SteeringFlow` subtree, `Emitting`, `Flaring`, `Supplying*`, and the remaining classes | — | `unsupported` (this slice) | Rejected with class name and object identity. Each family needs its own semantic review against a real instance before any mapping claim. |
| Instrumentation/signal classes (`InstrumentationActivity`, `MeasuringProcessVariable`, `ControllingProcessVariable`, `Calculating*`, `TransformingProcessVariable`, `ConveyingSignal`, `InstrumentationSystemActivity`) | — | `unsupported` | Signal/instrumentation semantics; out of scope. |
| `ProcessStepDetail` and children (`Agitating`, `ContactingOnTray`, `ContactingInPacking`, ...) | — | `unsupported` | Step-detail refinement; canonical model has no detail level. |

## 6. Port mapping findings

- DEXPI `Port` is an abstract class owning `Identifier` (1..1), `NominalDirection`
  (1..1), `Description`, optional `SubReference`/`SuperReference` (nested ports),
  and `ConnectorReference` (1..1, flagged `TODO check multiplicities` upstream).
  `ProcessStep.Ports` is a composition of `Port` objects, so ports are **local to
  one ProcessStep** — structurally identical to DeepPlant `ProcessPort` ownership
  (S2).
- For the supported subset only flat `MaterialPort` objects map to `ProcessPort`;
  ownership and the port's engineering `Identifier` are preserved. `ProcessPort.id`
  is deterministic and unique within the step (verified; collisions rejected).
- DEXPI `PortDirection` has exactly two literals: `Inlet` and `Outlet` (verified
  in the official enumeration workbook). DeepPlant derives presentation
  input/output from stream incidence; the adapter checks that the declared DEXPI
  direction is **consistent with** incidence (Source port must be `Outlet`, Target
  port `Inlet`) and rejects contradictions instead of silently importing them.
- **Finding on `Port.direction`:** within the supported material subset, DEXPI
  direction is redundant with stream incidence and does **not** expose a missing
  canonical semantic concept; no `ProcessPort.direction` field was added. A
  canonical port that is *both* a stream source and a stream target has no DEXPI
  equivalent (no `InOut` literal) and would need explicit two-port modeling or a
  documented model decision — recorded as a limitation, not a silent mapping.
- Nested ports (`SubReference`/`SuperReference`) and non-material ports are
  rejected with the class name rather than flattened or ignored.

## 7. Stream mapping findings

- DEXPI `ProcessConnection` is the abstract parent of all connections and owns
  `Identifier` (1..1), `Label` (1..1, Undefined|String), and single-valued
  `Source` / `Target` reference properties to `Port` objects. DEXPI `Stream` is a
  concrete connection "between two MaterialPort objects" — the material-flow edge.
- For the supported subset, `Stream` → `ProcessStream` preserves: the engineering
  `Identifier` (canonical `id`), the `Label` or explicit `Undefined` (canonical
  `name`), and the resolved `Source`/`Target` endpoints (canonical
  `ProcessRef(step, port)` after object-id → step/port resolution).
- Endpoint resolution, port ownership, direction consistency, duplicate canonical
  ids, and the S1–S4 invariants are all enforced by the normal `ProcessModel`
  Pydantic validation on construction.
- **Non-material connections (`EnergyFlow`, `ElectricalEnergyFlow`,
  `MechanicalEnergyFlow`, `ThermalEnergyFlow`, `InformationFlow`) are never mapped
  to `ProcessStream`.** They raise an explicit error carrying the DEXPI class and
  object identity (§8).

## 8. Unsupported DEXPI concepts (this slice) and their diagnostics

All of the following raise a `DexpiImportError`/`DexpiExportError` whose message
contains the DEXPI class and, when known, the XML object id and engineering
Identifier. None are silently dropped:

| DEXPI construct | Reason it is not imported |
|---|---|
| `EnergyFlow` / `ElectricalEnergyFlow` / `MechanicalEnergyFlow` / `ThermalEnergyFlow` | Non-material topology; collapsing into `ProcessStream` would corrupt material semantics. |
| `InformationFlow` and information ports | Signal/control topology; separate concept. |
| Non-material ports (`EnergyPort*`, `InformationPort`) | Ports of unsupported flow types. |
| `ProcessStep` classes outside the five supported | No semantic mapping verified yet. |
| Nested `ProcessStep` (`SubProcessSteps`) | DeepPlant has no step hierarchy. |
| Nested ports (`SubReference`/`SuperReference`) | DeepPlant has no port hierarchy. |
| ProcessModel content beyond steps/connections (material data libraries, `Compositions`, `MaterialTemplates`, `MaterialStates`, `MaterialComponents`, `ListsOfMaterialComponents`, `InstrumentationSystemActivities`) | Canonical model has no material-data library. |
| Engineering property data on supported objects (step `Pressure`/`Temperature`, stream `MassFlow`/`VolumeFlow`/`Pressure`/`Temperature`, `MaterialStateReference`, `MaterialTemplateReference`, etc.) | Canonical `ProcessStep`/`ProcessStream` store no engineering quantities; ignoring them silently would be lossy without evidence. |
| Multiple `ProcessModel` objects per file | Canonical import target is one `ProcessModel`. |
| DEXPI Plant objects in the file | Plant adapter is a separate future slice; Process import ignores non-Process objects and a Plant-only file is rejected explicitly. |

`Description` on supported objects is the one documented annotation-metadata
exception: present values are ignored (lossless for topology; lossy for free text)
and recorded in §9. The adapter does **not** recursively ignore unknown content:
unknown non-empty properties and unexpected child elements fail.

## 9. Canonical-model gaps discovered

The spike deliberately left `src/deepplant/model.py` **unchanged**. Gaps found
are reported here; none required a model change to prove the supported subset:

1. **Non-material topology** — EnergyFlow/InformationFlow have no canonical
   equivalent. Expected for a material-stream slice; a genuine gap for full
   DEXPI Process.
2. **Engineering quantities on steps and streams** — DEXPI `ProcessStep`
   `Pressure`/`Temperature`, DEXPI `Stream` `Pressure`/`Temperature`/`MassFlow`/
   `VolumeFlow`, `Composition`, `MaterialStateReference`,
   `MaterialTemplateReference`, and the ProcessModel material-data libraries have
   no canonical representation. Files carrying them are rejected (visible), not
   silently stripped. Any broader DEXPI Process work must first decide the
   canonical representation of engineering property values (units, qualified
   values) — a model-level decision this spike does not make.
3. **Type-vocabulary conflation** — canonical `ProcessStep.type` is currently the
   presentation symbol-role string used by the basic pack (ADR-0008), not a
   process-function engineering classification. DEXPI classes are engineering
   functions. The mapping table bridges them on import for five classes, but the
   reverse (DeepPlant → DEXPI) classification is asserted only for the four
   deliberately symmetric types (`source`, `sink`, `mixing`, `splitting`);
   `heat_exchanger` and `vessel` cannot be exported without inventing an exact
   DEXPI function because one canonical role maps to several DEXPI classes or to
   classes with semantics canonical cannot express. See Q10.
4. **Coupled-flow functions** — `ExchangingThermalEnergy` couples two material
   flows through one step; canonical `ProcessStep` has no side/role/coupling
   concept. Recorded as `requires-model-change` (not imported).
5. **Storage regime** — `StoringInTank` vs `StoringInPressureVessel` regimes are
   not representable in the canonical `vessel` role. Recorded as
   `requires-model-change`.
6. **Step/port hierarchy** — `SubProcessSteps` and nested ports have no canonical
   equivalent (rejected).
7. **Bidirectional ports** — DEXPI has no `InOut` PortDirection; a canonical port
   used as both source and target cannot be exported without a two-port rewrite.
8. **Identifier uniqueness** — DEXPI does not schema-guarantee engineering
   Identifier uniqueness; DeepPlant S1 does. Duplicates are rejected with a clear
   error rather than disambiguated by an invented suffix.
9. **Annotation text** — `Description` free text is intentionally lossy metadata:
   it is accepted and dropped on import, never stored in the canonical model.
   The conformance fixture includes one such description and the tests prove it
   does not leak into the semantic model.
10. **Upstream ambiguity** — `Port.ConnectorReference` carries an upstream
    `TODO check multiplicities`; DEXPI 2.0.1 is preparing Process-model
    clarifications. This slice therefore never invents a cardinality: an absent
    `ConnectorReference` is tolerated, while every connector reference that is
    actually declared must be valid and consistent (syntax, resolvable object,
    supported material `Stream`, and incidence agreement with the port's nominal
    direction). Full model-level cardinality conformance of exported XML cannot
    be certified until the upstream clarification lands.

## 10. Identity decision (summary)

| Question | Answer |
|---|---|
| Which identity is file-local? | XML `Object@id` (xsd:ID), guaranteed unique within one file; used only for `#`-IDREF resolution. |
| Which identity is engineering-facing? | The required data property `Identifier` on ProcessStep/ProcessConnection/Port. |
| Which identity is guaranteed unique? | Only the XML `Object@id`; engineering Identifiers are not schema-guaranteed unique. |
| Which identity is persistent across exchange? | `Identifier` is the exchange-stable engineering identity; `Core.PersistentIdentifier` only if a source records it. |
| Mapping chosen | Canonical DeepPlant ids ← DEXPI engineering `Identifier`; `Label` → `name`; XML object ids never become canonical ids. |
| Collision policy | Explicit error (no invented suffixes). |

## 11. Import API and executable fixture result

```python
from deepplant.adapters.dexpi import import_dexpi_process, DexpiImportError

process = import_dexpi_process("tests/fixtures/dexpi/2.0.0/conformance_process.xml")
```

API surface (all in `deepplant.adapters.dexpi`, deliberately not exported from
the top-level package): `import_dexpi_process(path)`, plus the XML-string
variant `import_dexpi_process_xml(xml)` used by tests. The adapter exposes one
narrow exception family (`DexpiImportError(ValueError)` /
`DexpiExportError(ValueError)`) and pinned target constants. There is **no**
adapter registry, plugin manager, or generic exchange framework.

Import result on the supported conformance fixture (see
`tests/test_dexpi_adapter.py`): a valid canonical `ProcessModel` with

- 5 `ProcessStep`s (`FEED` source, `MIX-101` mixing, `P-101` pump,
  `SPLIT-101` splitting, `SINK` sink) owning their declared `ProcessPort`s;
- 5 material `ProcessStream`s (`S-001`…`S-005`) with resolved source/target
  step/port references, including the **recycle cycle** `S-004`
  (SPLIT-101 → MIX-101) and the mixing/splitting branch;
- names/identifiers mapped deterministically from DEXPI `Identifier`/`Label`
  (never from XML object ids);
- globally unique non-empty XML `Object@id` values enforced before mapping
  (duplicate file-local ids fail explicitly instead of silently overwriting);
- declared `ConnectorReference` values validated when present (unresolved,
  wrong-type, and incidence-inconsistent declarations fail explicitly);
- unsupported populated ProcessModel content (unknown `Data`, populated
  unknown `Components`, direct `Object` children, engineering properties such
  as `Head`/`Method`/`Pressure`/`Temperature`/`MassFlow`) fails closed with the
  property/class named;
- canonical S1–S4 validation passing through the normal Pydantic constructors;
- repeated import producing an equal canonical model;
- no presentation, Plant, or DEXPI-extension data in the canonical model.

The conformance fixture's roles all exist in the basic symbol pack, so an
optional end-to-end test also proves `DEXPI XML → ProcessModel →
render_process_svg() → SVG`. Rendering is *not* an adapter requirement: an
imported model may legally contain a type the current pack cannot draw (that is
a presentation-layer concern, ADR-0003/ADR-0008), which is why the exporter
and renderer stay decoupled from the adapter.

## 12. Export feasibility assessment

Reverse-direction fields were separated into the task's four categories.

### 12.1 Available directly from DeepPlant

Step `type` (via the explicit reverse mapping table — the symmetric subset
`source`/`sink`/`mixing`/`splitting` only), step/port/
stream engineering ids, step/port/stream order, step `name`, stream `name`
(or explicit `Undefined`), stream `source`/`target` endpoints, and the whole
stream graph topology.

### 12.2 Can be generated as serialization mechanics

XML `Object@id` attributes (deterministic, generated from canonical ids,
never part of semantic comparison); the `<Model>`/`Import`/`EngineeringModel`/
`ConceptualModel` envelope (following the official `reference_pid.xml` shape);
`Undefined` leaves where the model allows an explicit undefined value; file
`name`/`uri` parameters.

### 12.3 Can use explicit DEXPI undefined representation

`ProcessConnection.Label` when a DeepPlant stream has no name → `<Undefined/>`
(required-by-model field expressed without inventing a value).

### 12.4 Would require inventing engineering semantics → not emitted

- `NominalDirection` for a canonical port with **no** incident stream (DEXPI
  requires it; DeepPlant does not store it) → exporter error.
- `NominalDirection` for a canonical port that is both source and target
  (DEXPI has no `InOut`) → exporter error.
- `ExportDateTime` / `OriginatingSystemName` / `OriginatingSystemVendorName` /
  `OriginatingSystemVersion` on the `EngineeringModel` wrapper — the official
  reference instance itself omits these despite 1..1 model cardinality; this
  slice mirrors the official instance and does **not** invent originating-system
  metadata.
- Exact DEXPI classes for canonical roles without an unambiguous function
  mapping (`heat_exchanger`, `vessel`, and any other role outside the four
  reverse-exported canonical types; `pump` is included on the import side only)
  → exporter error.

### 12.5 Conclusion

**Import is feasible for the supported material subset.** Reverse serialization
is demonstrated only for a deliberately supported DEXPI-compatible canonical
subset (`source`, `sink`, `mixing`, `splitting`) and is **not** evidence that
arbitrary `ProcessModel` instances have sufficient engineering classification
for DEXPI export. The exporter (`export_dexpi_process`) is therefore implemented
but narrow: deterministic DEXPI-native XML, no Proteus, no graphics, explicit
errors for unsupported/ambiguous canonical step types (including `pump`, which
is importable normalization but not yet a safe reverse classification) and for
ports whose DEXPI direction cannot be derived, and an internal
structural-subset validation of its own output.

The two directions must not be conflated:

- **DEXPI → DeepPlant** is a normalization that may legitimately lose
  unsupported engineering semantics only when they are explicitly rejected
  (fail-closed), never silently dropped.
- **DeepPlant → DEXPI** is an engineering-classification assertion; it is
  deliberately limited to the symmetric subset the current canonical model
  evidence supports.

**What export cannot honestly do today** (exact blocker summary):

- export arbitrary DeepPlant `ProcessStep.type` values (type vocabulary is a
  role vocabulary, not an engineering classification) — blocker category:
  canonical-model decision;
- export step/stream engineering quantities DeepPlant does not store (any
  DEXPI file *receiving* such data would need canonical property values) —
  blocker category: canonical-model growth;
- certify full model-level cardinality conformance while upstream
  `Port.ConnectorReference` multiplicity is unresolved (`TODO check
  multiplicities`) and DEXPI 2.0.1 Process-model clarifications are pending.

### 12.6 Produced-XML validation (honest label)

Produced XML is validated with a deterministic **structural-subset validation**
(`validate_dexpi_xml_structure`): well-formedness, `<Model>` root, globally
unique XML object ids, resolvable `#`-references, plus the adapter's
supported-subset content rules. This is **not** full DEXPI model/schema
conformance: the official DEXPI XML schema is a generic envelope schema
(instance classes are data, not schema elements), so XSD validation would only
check the envelope, and model-level class/cardinality conformance is not
enforceable from the schema alone. No XML/XSD dependency was added; tests run
fully offline. The documentation and tests label this exactly as structural
subset validation.

## 13. Answers to the spike's architecture questions

1. **Is `ProcessModel` ↔ DEXPI `ProcessModel` structurally compatible?**
   Yes for the material subset: both own a process-step collection (each step
   owning its ports) and a process-connection collection with directed
   source/target references. Canonical step/stream id namespaces and S1–S4 map
   cleanly. Incompatibilities appear at the *edges* (engineering data,
   hierarchy, energy/information topology), not in the container shape.
2. **Does DEXPI Port map cleanly to `ProcessPort`?** Yes for flat
   `MaterialPort`s owned by one step: the engineering `Identifier` maps to the
   step-local `ProcessPort.id`; nested ports are rejected; ownership matches S2.
3. **Does DEXPI Stream map cleanly to `ProcessStream`?** Yes for the material
   `Stream` subtype: single Source/Target port references resolve to
   `ProcessRef(step, port)` and preserve identity and topology. Energy and
   information flows are separate classes and are not mapped.
4. **Which DEXPI ProcessStep classes map exactly?** `Source`, `Sink`,
   `Mixing` (material topology) and, as lossless-normalization,
   `SplittingMaterial`. `Pumping` maps with loss (energy-port/driver and
   `Head`/`Method`/`VolumeFlow` unsupported). See §5.3.
5. **Which mappings are lossy?** `Pumping` (function-level equivalence only);
   `Description` text is dropped; canonical import of the whole file is blocked
   (not merely lossy) for unsupported concepts. `ExchangingThermalEnergy`,
   `StoringFluids`/`StoringInTank`/`StoringInPressureVessel` are
   `requires-model-change`, not mapped.
6. **Does `Port.direction` expose a real missing semantic concept?** No for the
   supported material subset: DEXPI direction (`Inlet`/`Outlet`) is consistent
   with stream incidence and is validated, not stored. A bidirectional canonical
   port has no DEXPI equivalent (`InOut` does not exist) — a modeling gap, not a
   direction-field gap.
7. **Which DEXPI required properties are absent in DeepPlant?** For the
   supported subset, none on the imported objects beyond what the adapter
   supplies mechanically (Identifiers, Labels, direction consistency). For a
   *full* process exchange the absent canonical concepts are step/stream
   engineering quantities, material data libraries, flow types beyond material,
   hierarchy, and a function classification (§9).
8. **Can current DeepPlant honestly export the supported subset?** Yes, via the
   narrow exporter, and the semantic round-trip
   `ProcessModel → DEXPI XML → ProcessModel` is proven with a normalized
   semantic fingerprint. Arbitrary DeepPlant models cannot be exported without
   inventing meaning (§12.4/§12.5).
9. **What information is lost on import?** For the supported fixture: nothing
   topological; `Description` free text (documented metadata) is dropped. For
   unsupported constructs the import fails visibly instead of losing data.
10. **Does `ProcessStep.type` vocabulary need reconsideration?** Yes — this is
    the spike's clearest vocabulary finding. Canonical `type` currently doubles
    as the renderer symbol role (ADR-0008), while DEXPI step classes are
    engineering functions. The five-class mapping works only because the chosen
    roles happen to coincide with functions; `heat_exchanger` and `vessel` are
    already ambiguous, and exporter honesty depends on separating a canonical
    function classification from the presentation symbol role. This is a model
    decision for the next slice, not a change made here.
11. **Does the canonical model need any change before broader DEXPI work?**
    Not for the supported material subset. Broader DEXPI Process work needs,
    in smallest order: (a) a decision on `ProcessStep.type` semantics /
    engineering classification, (b) a decision on step/stream engineering
    property representation (quantities with units), (c) a decision on material
    data libraries, (d) then energy/information flow modeling. None is
    authorized by this spike.
12. **What is the smallest next evidence-producing slice?** Decide the
    canonical `ProcessStep.type` semantics (separate engineering classification
    from presentation role) on the realistic fragment with executable examples,
    because every further DEXPI Process expansion and honest export depends on
    it; then re-open DEXPI Process subset expansion (or the DEXPI Plant/P&ID
    mapping spike) from the evidence. See the Roadmap check below.

## 14. Dependencies and semantic-model changes

- **Dependencies added: none.** The adapter uses only the Python standard
  library (`xml.etree.ElementTree`, `re`, `pathlib`) plus the existing
  `pydantic`/domain-model dependency for canonical construction. No
  `networkx`, `pyDEXPI`, RDF/SPARQL, XML/XSD validator, or generic graph
  dependency was added. `uv.lock` is unchanged.
- **Semantic-model changes: none.** `src/deepplant/model.py` is unchanged.
  Adapter-specific information (DEXPI class, XML object ids, target pins) lives
  in the adapter boundary and in this document, not in canonical fields.
- **No new ADR was created.** The durable architecture invariants used here
  (semantic model is the core; presentation data separate; YAML/external
  formats are serialization boundaries; standards content policy incl. DEXPI
  CC BY 4.0) are already captured by ADR-0002/0003/0004/0005/0007/0008. The
  genuinely new findings (identity policy, Port.direction, type-vocabulary
  conflation) are recorded in this spike document because the next slice must
  first decide the `ProcessStep.type` question on model evidence before any new
  ADR is warranted.

## 15. Quality gates

Run on this branch before merge:

```bash
make validate-docs
make validate-agent-skills
make check        # ruff format --check, ruff check, pyright, pytest
uv build          # wheel + sdist build (uv.lock unchanged)
```

All tests run offline; research happened during development only.

## 16. Roadmap check

- **Completed by this PR:** backlog row "DEXPI adapter spike" — executable
  DEXPI 2.0 Process import for an explicit material subset with a hardened trust
  boundary (pinned Core/Process 2.0.0 model-URI import preflight, globally
  unique XML `Object@id` preflight, fail-closed ProcessModel/property parsing,
  ConnectorReference validation when present), a narrow honest exporter for the
  deliberately symmetric subset only, fixture provenance, and the
  mapping/identity/gap analysis above.
- **Next task (from evidence):** decide the canonical `ProcessStep.type`
  semantics — separate an engineering process-function classification from the
  presentation symbol role — using the realistic fragment as the executable
  example, because (a) exporter honesty and (b) every further DEXPI Process
  subset expansion (storage, exchange, reaction/separation classes) depend on
  it, and the spike proved `heat_exchanger`/`vessel` cannot be mapped or
  exported while `type` is a renderer-role vocabulary.
- After that decision, re-open either "expand the DEXPI Process subset" or the
  "DEXPI Plant/P&ID mapping spike" from fresh evidence; do not mechanically
  promote the old backlog row.








