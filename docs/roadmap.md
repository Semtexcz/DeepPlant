---
type: roadmap
status: proposed
source_of_truth_for:
  - roadmap
read_when:
  - roadmap-change
  - feature-planning
update_when:
  - roadmap-change
---

# Roadmap

This file distinguishes two levels:

- **Current Implementation Roadmap** — the actionable near-term plan that
  decides the next PR. It preserves completed work and the current state.
- **Directional Capability Roadmap** — long-term product context: capability
  progression and dependencies, not a delivery calendar, a fixed build order, or
  an implementation authorization.

This file contains no dates, estimates, release promises, fixed sequence
commitments, or completion percentages. GitHub Issues remain the place for
executable tasks.

The [GitHub Project](../README.md#navigation) visualizes capability state and
horizons; this document explains why the work is sequenced as it is. Planning
governance — the Vision → Architecture → Roadmap → Project → Milestones →
Issues → Pull Requests hierarchy, horizon semantics, and the just-in-time Issue
rule — is defined in [planning.md](planning.md).

## Current Implementation Roadmap

DeepPlant ships the project foundation plus four semantic vertical slices, a
realistic process-fragment validation example, the standards/symbol-licensing
governance slice ([docs/standards.md](standards.md), ADR-0007), the SVG +
anchor + initial basic symbol-pack contract (packaged inside the Python package
under `deepplant/assets/symbols/process/basic/`,
[docs/svg-symbols.md](svg-symbols.md), ADR-0008), the basic headless
read-only process renderer ([docs/rendering.md](rendering.md)), the DEXPI
2.x Process adapter spike ([docs/dexpi-process-spike.md](dexpi-process-spike.md)),
the canonical `ProcessStep.function` / presentation-symbol-role separation
slice (ADR-0009), the DEXPI 2.x Plant/P&ID semantic-mapping spike
([docs/dexpi-plant-pid-spike.md](dexpi-plant-pid-spike.md), ADR-0010), the
physical-piping specification/decision slice
([docs/physical-piping-model.md](physical-piping-model.md), ADR-0011), the
first physical piping-realization implementation slice (Issue #26), the
DEXPI `ExchangingThermalEnergy` mapping-evidence slice (Issue #22,
[docs/dexpi-exchanging-thermal-energy-evidence.md](dexpi-exchanging-thermal-energy-evidence.md)),
and the process-step classification decision slice (Issue #31,
[docs/process-step-classification.md](process-step-classification.md),
ADR-0012):

- minimal domain model: `PlantModel` -> `Plant` + `list[Equipment]`
- equipment-owned `Port` objects; port identity is local to the owning equipment
- top-level `Connection` edges over structured `PortRef(component, port)`
  endpoints, each carrying a required, non-empty, plant-unique canonical `id`
  (C1, ADR-0011; a documented pre-1.0 breaking change to authored YAML)
- reference validation: every endpoint component must resolve to existing
  equipment and its port must exist on that equipment
- optional physical piping-realization layer: `PlantModel.piping:
  PipingModel | None` owning `PipingLine` -> `PipingSegment` ->
  `PipingRealization`, where a realization references one identified
  `Connection` and states the closed `kind: pipe | direct` vocabulary (default
  `pipe`, unknown values rejected); structural rules P1–P5 ship (unique line
  ids, segment ids unique per owning line, resolvable connection references, at
  most one realization per connection across the whole piping model, non-empty
  segments); `line_number`/`segment_number`/`nominal_diameter`/`piping_class`/
  `fluid_code` are optional and never canonical identity; a segment boundary
  must currently coincide with a `Connection` boundary, so mid-connection
  `PropertyBreak` semantics, a canonical `Pipe`, `PipingComponent`,
  `Nozzle`/`PipingNode`, instrumentation, and process ↔ physical realization
  remain unimplemented
- YAML load through a small boundary into typed Pydantic models
- strict semantic input: unknown fields rejected, non-empty semantic ids,
  unique equipment ids, unique port ids per equipment item
- a runnable example: `examples/minimal-process/plant.yaml`
- `deepplant validate <path>` reporting plant, equipment, port, and connection
  counts
- standalone process-domain model: `ProcessModel` owning `ProcessStep[]` with
  `ProcessPort[]`, plus `ProcessStream[]` over `ProcessRef(step, port)`
  endpoints; structural rules S1–S4; independently constructible and valid in
  Python
- root/loadable process-model integration: `PlantModel.process: ProcessModel |
  None`; a YAML `process` section with `steps`/`streams` loads through the
  existing `load_plant` boundary into the typed submodel; missing `process` and
  `process: null` mean no authored process model, while `process: {}` is an
  explicitly empty `ProcessModel`; S1–S4 remain owned by `ProcessModel` and
  no cross-layer mappings or validation exist
- canonical YAML save / semantic round-trip: `save_plant()` serializes a
  `PlantModel` through Pydantic (`exclude_none`) into canonical, deterministic
  YAML that the existing `load_plant()` reads back as a semantically equal
  model; `process: None` is omitted while an explicitly empty `ProcessModel`
  stays present; formatting, comments, and quoting are not preserved
- realistic process fragment as a loadable public example:
  `examples/realistic-process-fragment/plant.yaml` encodes the documented PFD
  fragment (fresh feed, mixing, pump, heat exchanger, splitting, vessel,
  downstream boundary, recycle) through the production models, loads via
  `load_plant()`, and round-trips via `save_plant()`; mixing/splitting stay
  explicit `ProcessStep`s without `Equipment`, `FV-101` stays physical without a
  `ProcessStep`, recycle is an ordinary cycle, and no new schema, mappings, or
  piping model were introduced
- first process presentation-asset slice — SVG + anchor + initial basic
  symbol-pack contract: seven DeepPlant-original non-normative fallback SVG
  assets packaged under `deepplant/assets/symbols/process/basic/` (`source`,
  `mixing`, `pump`, `heat_exchanger`, `splitting`, `vessel`, `sink`) with
  canonical `viewBox="0 0 100 100"`, monochrome `currentColor` line art, and
  hidden ordered `anchor-in-N` / `anchor-out-N` slots; the assets realize
  *symbol roles* resolved by the presentation layer (since ADR-0009 roles are
  resolved from `ProcessStep.function` by renderer policy or explicit
  override), distinct from any graphical asset identity and from engineering
  functions; contract in
  `docs/svg-symbols.md`, decision in ADR-0008, provenance in the packaged pack
  README; deterministic stdlib XML contract tests plus realistic-fragment role
  coverage; no semantic-model fields, frontend, or runtime pack-selection
  framework
- basic headless read-only process renderer:
  `render_process_svg(process, symbol_pack="basic", symbol_role_overrides=None)`
  renders a standalone SVG process/PFD diagram from `ProcessModel` only (no
  physical layer, no `FV-101`, no process↔physical mapping): the renderer
  resolves each step's symbol role from its engineering `ProcessStep.function`
  through a default presentation policy or an explicit per-step override
  (ADR-0009), then maps role → pack → asset; deterministic layered layout;
  stable (port order, stream id) assignment of `ProcessStream` incidence onto
  pack `anchor-in-N`/`anchor-out-N` slots; renderer-owned anchor-capacity and
  unresolved-role errors; DFS back-edge classification with dedicated return
  lanes for recycle; orthogonal forward routing and self-contained arrowheads;
  step/stream labels; duplicate-safe symbol composition; pack assets resolved
  at runtime from the installed package through `importlib.resources` (single
  canonical copy, wheel-verified); committed golden artifact
  `examples/realistic-process-fragment/process.svg` with a determinism test;
  deterministic stdlib XML behaviour tests; no frontend, no interactive UI, no
  CLI, no new runtime dependency (documented in
  [docs/rendering.md](rendering.md))
- DEXPI 2.x Process adapter spike: a narrow native-DEXPI-XML Process adapter
  (`deepplant.adapters.dexpi`) pinned to the official stable DEXPI `V2.0.0`
  tag imports an explicit material subset (Source/Sink/Mixing/
  SplittingMaterial/Pumping with `MaterialPort`s and material `Stream`s) into
  the canonical `ProcessModel` as DeepPlant-native `ProcessStep.function`
  values (`source`, `sink`, `mixing`, `splitting_material`, `pumping`),
  enforces the pinned 2.0.0 Core/Process model
  imports and globally unique XML `Object@id` values before mapping, validates
  declared `ConnectorReference`s when present, fails closed on unsupported
  populated content, and exports the deliberately symmetric subset
  (`source`/`sink`/`mixing`/`splitting_material`, plus material-port-only
  `pumping` after ADR-0009) back as DEXPI-native XML for that
  supported structural subset;
  EnergyFlow/InformationFlow/P&ID content fails explicitly; Plant objects are
  ignored in mixed files while Plant-only input is rejected, never silently
  emptied; DEXPI
  engineering `Identifier` → canonical id, `Label` → name; XML object ids stay
  file-local resolution mechanics; explicit mapping table (never generic class
  conversion); deterministic structural envelope/reference-integrity validation; DeepPlant-owned
  synthetic conformance fixture with full provenance (no official Process
  instance exists upstream); optional DEXPI → `ProcessModel` → SVG render
  proof; no new dependency, no generic adapter framework (analysis in
  [docs/dexpi-process-spike.md](dexpi-process-spike.md),
  fixtures under `tests/fixtures/dexpi/2.0.0/`)

- canonical function/role separation (ADR-0009): `ProcessStep.type` (which
  doubled as a presentation symbol role) is removed from the semantic model
  and replaced by the open, non-empty engineering-function field
  `ProcessStep.function`; DEXPI mappings produce DeepPlant-native functions,
  never DEXPI class identifiers; the renderer owns a default
  function → symbol-role presentation policy plus an optional per-step
  `symbol_role_overrides` mapping that exists only at the rendering boundary
  (never stored in the model or YAML); `PS-vessel` in the realistic fragment is
  semantically honest as `function: unspecified` and still renders as the
  `vessel` symbol through an explicit override; legacy `type` input is rejected
  (intentional pre-1.0 breaking model correction); the DEXPI reverse exporter
  gains material-port-only `pumping → Pumping` with a proven minimal semantic
  round-trip; persistent view/presentation configuration stays deferred
  ([ADR-0009](decisions/ADR-0009-separate-process-function-from-symbol-role.md))
- physical-piping specification/decision slice (ADR-0011): documentation only —
  no `src/`, test, fixture, adapter, or dependency change. The canonical
  physical-piping shape is decided as an optional `PipingModel`
  (`PlantModel.piping`) owning `PipingLine` -> `PipingSegment` ->
  `PipingRealization`, referencing identified `Connection`s; `Connection` keeps
  its topology-only meaning and gains canonical identity only (a documented
  pre-1.0 breaking change to authored YAML); `PipingLine` carries canonical `id`
  plus optional human `line_number`/`name`; `PipingSegment` has owner-local
  canonical `id`, optional human/external `segment_number` (including DEXPI
  `SegmentNumber`), and DN/piping-class/fluid-code properties; first-slice
  segment boundaries align with `Connection` boundaries, while mid-connection
  property breaks are deferred; `PipingRealization.kind` is closed to `pipe |
  direct` (`pipe` default; invalid values fail validation) and records the
  elementary realization without a canonical `Pipe` class; C1 requires a
  non-empty plant-unique `Connection.id` and P4 is a conservative first-slice
  1:1 invariant; inline components stay `Equipment`; `Port` stays the endpoint
  with no `Nozzle`/`PipingNode`; a branch is an item with several named ports
  plus ordinary `Connection`s. That decision slice added no code; the layer it
  specified was implemented afterwards by Issue #26 (see the completed row
  above), and Process ↔ physical realization stays undecided
  ([docs/physical-piping-model.md](physical-piping-model.md),
  [ADR-0011](decisions/ADR-0011-canonical-physical-piping-realization.md))

`Connection` is a directed semantic topological relationship from `source` to
`target` with a canonical id; it remains topology only and is not a pipe, process
stream, signal, cable, or physical line. ADR-0011 preserves exactly that
meaning: the implemented piping layer lives in its own submodel and references
identified connections, so no pipe, segment, line, realization, piping-class, or
fluid data is attached to the topology primitive. Work
proceeds as small vertical changes with executable tests. `PlantModel` owns
zero or one `ProcessModel` under `process` and zero or one `PipingModel` under
`piping`; the loader populates both from YAML
and `save_plant()` writes canonical YAML that `load_plant()` reads back into a
semantically equal model.
Round-trip is semantic (`load(save(model)) == model`), not byte-preserving.
Process and physical graphs stay independently valid: process step/port ids
never imply equipment, and no cross-layer rules exist yet.

### Completed

| Item | Notes |
|---|---|
| Define `PlantModel` | Root container and composition of the model |
| Define `Plant` | Plant identity: `id`, `name` |
| Define `Equipment` | Engineering objects: `id`, `type`, `name`, owned `Port[]`; no fixed taxonomy yet |
| Define `Port` | Typed connection points owned by equipment; id local to the owning equipment |
| Define `PortRef` | Structured endpoint reference: `component` + `port` |
| Define `Connection` | Directed semantic topology only: `id` (required, non-empty, plant-unique) plus `source`/`target` as `PortRef(component, port)`; still not a pipe/stream/signal/physical line, and it gained identity only (C1, ADR-0011) |
| Reference validation | Connections resolve to existing equipment and owned ports; referential integrity only |
| YAML load | YAML as serialization, validated via Pydantic into the domain model |
| Semantic validation (structural) | Non-empty ids; unknown fields rejected; unique equipment ids; unique port ids per equipment |
| First executable example | `examples/minimal-process/plant.yaml` runs through the CLI |
| Decide process-model container | ADR-0005 accepted (C1): `PlantModel` remains the overall aggregate; one independently valid `ProcessModel` owns the process graph and the S1–S4 validation boundary |
| Define `ProcessModel` | Standalone process-domain container owning `ProcessStep[]` and `ProcessStream[]`; step and stream ids are separate namespaces (S1); not yet part of `PlantModel` |
| Define `ProcessStep` / `ProcessPort` | Process steps with `id`, open non-empty engineering `function`, `name`, owned `ProcessPort[]` (ADR-0009); process-port ids local to the owning step (S2) |
| Define `ProcessRef` / `ProcessStream` | `ProcessRef(step, port)` endpoints; binary directed `ProcessStream` with `id`, optional `name`; no flow/designation/physical semantics |
| Process structural validation | S1 duplicate step/stream ids rejected; S3 endpoints resolve to process steps and owned process ports; S4 identical source/target endpoints rejected; cycles/recycle/mixing/splitting structurally allowed; no dependency on `Equipment`/`Port`/`Connection` |
| Integrate `ProcessModel` into the root/loadable model | `PlantModel.process: ProcessModel \| None`; YAML `process` section (`steps`, `streams`) loads through the existing loader; missing `process` and `process: null` load as no process model, `process: {}` as an empty one; S1–S4 stay on the process-domain models; process and physical ids remain separate namespaces; root/YAML shape recorded in ADR-0006 |
| YAML save / semantic round-trip | Canonical `save_plant()` through Pydantic `model_dump(exclude_none=True)` + PyYAML (`sort_keys=False`, `allow_unicode=True`); `load_plant(save_plant(model)) == model`; `None` optionals omitted; `process: None` omitted; explicit empty `ProcessModel` preserved; deterministic field order; UTF-8 with a trailing newline; comments/formatting not preserved; no domain-model changes; no CLI save/format command |
| Realistic process fragment as a loadable example | Synthetic public YAML (`examples/realistic-process-fragment/plant.yaml`) encodes the documented PFD fragment: seven `ProcessStep`s and seven `ProcessStream`s including recycle, mixing, and splitting; loads through `load_plant()` via `PlantModel.process` and round-trips through `save_plant()`; physical bootstrap layer (`T-101`, `P-101`, `FV-101`, `E-101`, `V-101`) stays independent; `PS-mix`/`PS-split` have no `Equipment` counterpart and `FV-101` has no `ProcessStep`; no new schema, process↔physical mappings, or piping model |
| Standards and symbol-licensing strategy | Governance/research slice (no implementation code): [docs/standards.md](standards.md) registers the normative restricted references (ISO 10628-1/-2, ISO 14617-1/-2, ANSI/ISA-5.1, IEC 62424) versus the open DEXPI 2.0 specification (CC BY 4.0, confirmed from the official announcement and GitLab repository); restricted-standards handling and AI-agent rules are explicit (AGENTS.md); conservative verification states (`reference` / `candidate-alignment` / `human-verified`) replace unverified “compliant” claims; future symbol provenance requirements and the seven-ProcessStep-type assessment are defined; candidate sources (ISPF `ispf-pid-v1`, draw.io P&ID shapes, DEXPI material, others) are assessed at file/licence level and none is imported; decision recorded in ADR-0007 |
| SVG + anchor + initial basic symbol-pack contract (process/PFD presentation) | First presentation-asset slice: seven DeepPlant-original non-normative fallback SVG assets, packaged inside the Python package under `deepplant/assets/symbols/process/basic/`, realizing the realistic fragment's resolved *presentation symbol roles*; a symbol role is distinct from an engineering function and from graphical asset identity (role resolution from `ProcessStep.function` by renderer policy or explicit override was decided in ADR-0009); canonical `viewBox="0 0 100 100"`, monochrome `currentColor` line art, generic ordered `anchor-in-N` / `anchor-out-N` slots distinct from semantic ports; contract in [docs/svg-symbols.md](svg-symbols.md), decision in ADR-0008, provenance in the packaged pack README; deterministic stdlib XML tests; no semantic-model presentation fields, no runtime pack-selection framework |
| Basic headless read-only process renderer | `render_process_svg(process, symbol_pack="basic", symbol_role_overrides=None)` in `src/deepplant/render.py` consumes the pack-aware contract and renders a standalone SVG process/PFD diagram from `ProcessModel` only: it resolves each step's symbol role from engineering `ProcessStep.function` via a default presentation policy or an explicit per-step override (ADR-0009); pack assets resolved at runtime from the installed package through `importlib.resources` (single canonical copy, wheel verified); deterministic layered layout; `ProcessStream`-incidence anchor assignment in stable (port order, stream id) order; anchor-capacity, unresolved-role, and invalid-override errors stay renderer errors; deterministic DFS back-edge classification with dedicated return lanes; orthogonal forward routing; self-contained arrowheads; step/stream labels; duplicate-safe symbol composition; committed golden artifact `examples/realistic-process-fragment/process.svg` with a golden/determinism test; deterministic stdlib XML behaviour tests; documented in [docs/rendering.md](rendering.md); no frontend, no interactive UI, no CLI, no new runtime dependency |
| DEXPI 2.x Process adapter spike | Narrow native-DEXPI-XML Process adapter (`deepplant.adapters.dexpi`, [docs/dexpi-process-spike.md](dexpi-process-spike.md)) pinned to the official stable DEXPI 2.0.0 tag `V2.0.0` (commit `260c81c5`; inspected 2026-09-09; DEXPI 2.0.1 still being prepared): explicit material subset (Source/Sink/Mixing/SplittingMaterial/Pumping with MaterialPorts + material Streams) imports into the canonical `ProcessModel` as DeepPlant-native `ProcessStep.function` values (`source`, `sink`, `mixing`, `splitting_material`, `pumping`) through public Pydantic constructors (S1–S4 run); explicit mapping table (never generic class-name conversion); identity decision documented (engineering `Identifier` → canonical ids; XML object ids are file-local resolution mechanics; `Label` → name); EnergyFlow/InformationFlow/non-material ports/unsupported step classes/unresolved references/duplicate identifiers fail explicitly; pinned Core/Process 2.0.0 import preflight, globally unique XML `Object@id` preflight, and fail-closed ProcessModel/property parsing harden the trust boundary; declared ConnectorReference values are validated when present; direction consistency vs incidence validated; honest narrow exporter for the deliberately symmetric subset (source/sink/mixing/splitting_material, plus material-port-only `pumping` after ADR-0009) with deterministic output and explicit errors for ports whose DEXPI NominalDirection cannot be derived and for canonical functions without an unambiguous DEXPI class (heat_exchange, unspecified); deterministic structural envelope/reference-integrity validation (the official XSD is a generic envelope schema); no official DEXPI Process instance exists upstream, so the DeepPlant-owned synthetic conformance fixture is labelled and provenanced under `tests/fixtures/dexpi/2.0.0/`; no new dependency, no generic adapter framework; optional DEXPI → ProcessModel → SVG render proof; roadmap + spike conclusions recorded |
| Separate process function from presentation symbol role | Canonical-model correction driven by executable DEXPI evidence and recorded in ADR-0009: `ProcessStep.type` (which doubled as a presentation symbol role) is replaced by the open engineering-function field `ProcessStep.function`; the function vocabulary stays open and DeepPlant-native (`source`, `sink`, `mixing`, `splitting_material`, `pumping`, `heat_exchange`, `unspecified`, ...) — never DEXPI class identifiers; the renderer owns the default function → symbol-role presentation policy and accepts explicit per-step `symbol_role_overrides` that exist only at the rendering boundary (never stored in the model or YAML); `PS-vessel` is semantically honest as `function: unspecified` and still renders as `vessel` through an explicit override; legacy `type` input is rejected (intentional pre-1.0 breaking model correction); semantic YAML uses `function`; DEXPI import maps onto DeepPlant functions and the reverse exporter gains material-port-only `pumping → Pumping` with a proven semantic round-trip; persistent view/presentation configuration is explicitly deferred |
| DEXPI 2.x Plant/P&ID semantic-mapping spike (ADR-0010) | Evidence-producing architecture spike, documentation only — no `src/`, test, fixture, or dependency change. Re-verified from official sources that **DEXPI 2.0.0 (`V2.0.0`, commit `260c81c5`, 2025-10-10, CC BY 4.0) is still the latest stable release and 2.0.1 is still unreleased** (official August 2026 update: "being prepared", Process Model corrections), so the existing pin stands. Inspected the official `V2.0.0` model DSL (`src/model/Plant/**`, `src/model/Core/**`) **and the official DEXPI Reference P&ID instance** (`src/documentation/_static/reference_pid.xml`, 32,067 lines) — the only official 2.0 XML instance, giving this spike real instance-level evidence. Confirmed: `PlantModel` has no generic connection collection and does not own nozzles plant-level; physical items are `TaggedPlantItem`/`ProcessEquipment` (`TagName` identity) owning `Nozzles`/`Chambers`; connection points split into `Nozzle` and `PipingNode` (item + node endpoints); piping connectivity is directed (`SourceItem`/`TargetItem` + `SourceNode`/`TargetNode`); `Pipe` is an elementary uninterrupted piece and an inline valve splits a run into two `Pipe`s (instance-proven); line identity is `PipingNetworkSystem.LineNumber` and segment identity `PipingNetworkSegment.SegmentNumber`, both above the edge; inline valves/fittings are `PipingComponent`s (not equipment) that own nodes and terminate connections; instrumentation is a separate function layer whose signal edges are `SignalConveyingFunction.Source`/`Target` and whose sensing/actuating locations are physical-realization objects; DEXPI itself separates `Core.ConceptualModel` from `Core.Diagram` (labels, `ShapeUsage`, `PipingNodePosition`, `PlantMetaData`), corroborating ADR-0003. Outcome: the existing `Port`/`Connection` invariants are **confirmed, not replaced**; `Port` is a documented collapse of `Nozzle` + `PipingNode`; a distinct piping-realization layer and an instrumentation layer are recognized as future work needing their own evidence; Plant/P&ID import stays unimplemented and fail-closed; the next physical-model decision is bounded to a specification/decision slice against the official reference fragment |
| Implement the physical piping-realization layer (vertical slice) | First executable slice of the ADR-0011 shape (Issue #26), `src/deepplant/model.py` plus tests, YAML examples, and docs: `Connection.id` (required, non-empty via the canonical semantic-string contract, plant-unique; missing/blank/whitespace/duplicate ids rejected deterministically) — a documented pre-1.0 breaking change, with every authored `Connection` in examples and tests migrated to a stable id; `PlantModel.piping: PipingModel \| None`; `PipingModel` (`lines`), `PipingLine` (`id`, optional `line_number`/`name`, `segments`), `PipingSegment` (owner-local `id`, optional `segment_number`/`nominal_diameter`/`piping_class`/`fluid_code`, `realizations`), and `PipingRealization` (`connection`, closed `kind: pipe \| direct` defaulting to `pipe`); structural rules C1 and P1–P5 with focused success and failure tests (C1 missing/blank/whitespace/duplicate, P1 duplicate line ids, P2 duplicate segment ids per line while the same segment id stays legal in another line, P3 dangling/foreign connection references, P4 one realization per connection across all lines, P5 empty segment); unknown fields rejected on every new model and list fields use safe default factories; P3/C1 live on `PlantModel`, P1/P4 on `PipingModel`, P2 on `PipingLine`, P5 on `PipingSegment`; YAML `piping` section loads through the existing loader (missing/`null`/`{}` behave like `process`), canonical save omits `None` optionals and emits `kind: pipe` explicitly, and `load(save(model)) == model` holds; the realistic fragment keeps its honest physical chain with ids `C-001`/`C-002` and realizes it as one pipe-realized line `PL-P101-DISCHARGE`/`SEG-1` **without authoring any DN, piping-class, fluid-code, line-number, or segment-number value it has no evidence for**; `kind: direct` is proven by a focused synthetic executable test rather than by a false fragment assertion; `PipingLine`/`PipingSegment`/`PipingRealization`/`PipingModel` are exported from the public API; a test asserts `Connection`'s field set stayed `id`/`source`/`target` (no pipe/line/segment/kind/fluid/DN field) and that no piping model carries process, presentation, or geometry fields. Excludes DEXPI Plant import/export, P&ID rendering, rule engine, process ↔ physical mapping, `Nozzle`, `PipingNode`, `Pipe`, `PipingComponent`, `PropertyBreak`, instrumentation, and any new runtime dependency |
| DEXPI `ExchangingThermalEnergy` mapping evidence (Issue #22) | Evidence-first interoperability slice ([docs/dexpi-exchanging-thermal-energy-evidence.md](dexpi-exchanging-thermal-energy-evidence.md)): the official DEXPI `V2.0.0` Process model definition (`src/model/Process/Process/Process.py`, tag object `dc74c370…`, release commit `260c81c51039789a6148a98af4c6caf23f87a3e2`, CC BY 4.0, inspected 2026-09-22) was inspected for `ExchangingThermalEnergy`; the class is a `ProcessStep` subclass (a *process function*, not equipment and not presentation) whose definition is thermal transfer "between two or more streams of material … realized by a heat exchanger", so the realization sentence is not identity; it owns `Area`/`ColdFlow`/`Duty`/`HeatTransferCoefficient`/`HeatTransferResistance`/`HotFlow`/`SkinTemperature`/`TemperatureDifference` as qualified physical quantities plus a **mandatory** (`1..1`) `Method: HeatExchangeMethod` (`Generic`/`Plate`/`Spiral`/`Tubular`), and, if an explicit thermal-energy / utility connection is modelled, DEXPI represents it with `ThermalEnergyPort` + `ThermalEnergyFlow` rather than a material `Stream`; documented outcomes: canonical `ProcessStep(function="heat_exchange")` corresponds to the class **only as a process-function kind**, the class-level statement is honest, but import, export, and semantic round-trip are **not claimed** because of the exact gap G1–G6 recorded in the document (`Method` classification, coupled multi-stream semantics, no port kind, no energy-flow connection kind, no qualified-quantity model, non-stored mandatory `NominalDirection`); canonical `heat_exchange` keeps its DeepPlant-native meaning and is not reinterpreted; the smallest justified model change is *proposed and deliberately not authorized* (a model-level decision shared with the rest of the DEXPI ProcessStep family rather than a heat-exchanger-specific field); `ExchangingThermalEnergy` stays explicitly unsupported and is now pinned by a provenance-recorded negative fixture `tests/fixtures/dexpi/2.0.0/exchanging_thermal_energy.xml` and two focused tests proving the rejection is structural (stripping every property and port still fails at the class level) and that no canonical function string is synthesised from the DEXPI class name; no semantic-model, adapter-mapping, example, or dependency change |
| Specify the physical-piping realization layer | Documentation-only decision slice ([docs/physical-piping-model.md](physical-piping-model.md), [ADR-0011](decisions/ADR-0011-canonical-physical-piping-realization.md)): engineering requirements grouped as first-slice / likely-future / not-justified; three candidate models compared (line-over-topology, line + segment + realization, independent piping graph) plus the rejected `Connection`-widening variant; selected shape is `PipingModel` (`PlantModel.piping`) owning `PipingLine` -> `PipingSegment` -> `PipingRealization` referencing identified `Connection`s; `PipingLine` (`id`, optional `line_number`/`name`), `PipingSegment` (owner-local canonical `id`, optional human/external `segment_number` mapped from DEXPI `SegmentNumber`, DN/piping-class/fluid-code property boundary), and `PipingRealization.kind` (closed `pipe | direct`, default `pipe`, invalid values fail validation; no canonical `Pipe`/`DirectPipingConnection` class); DEXPI XML `Object@id` and `SegmentNumber` never become canonical identity automatically; first-slice segment boundaries align with `Connection` boundaries and mid-connection `PropertyBreak` semantics are explicitly deferred; `Connection` stays topology only and gains canonical identity (`Connection.id` required, non-empty, plant-unique, documented pre-1.0 breaking change); C1 plus P1–P5 are defined, with P4 a deliberately conservative first-slice 1:1 invariant; inline components stay `Equipment`; `Port` stays the endpoint (no `Nozzle`/`PipingNode`); branches are items with named ports plus ordinary `Connection`s; Git-diff behaviour, engineering-rule, DEXPI adapter, and P&ID rendering implications documented. No model, fixture, adapter, test, or dependency change in that slice; its implementation is the completed row above, while Process ↔ physical realization stays undecided |
| Decide non-derivable step classification semantics | Documentation-only evidence/decision slice (Issue #31, [docs/process-step-classification.md](process-step-classification.md), [ADR-0012](decisions/ADR-0012-process-step-single-classification-axis.md)): the full official DEXPI 2.0.0 (`V2.0.0`, release commit `260c81c…`, inspected 2026-09-22) Process model was searched, not only the known examples, and `Method` was found **only** in the Process model as **nine** property declarations across **seven** enumeration types (`HeatExchangeMethod` ×3, `CompressionMethod`, `PumpingMethod`, `ReactionProcessType`, `EngineDriveMethod`, `MotorDriveMethod`, `TurbineDriveMethod`) on `ExchangingThermalEnergy`/`RemovingThermalEnergy`/`SupplyingThermalEnergy`/`Compressing`/`Pumping`/`ReactingChemicals`/`DrivingByEngine`/`DrivingByMotor`/`DrivingByTurbine`, with mixed multiplicities (`1..1` and `0..1`); the enumeration domains are heterogeneous, mixing mechanism/principle labels (`CentrifugalMotion`, `PositiveDisplacement`), equipment technology or construction (`Plate`, `Tubular`, `Fan`, `Blower`, `GasTurbine`) and non-answers (`Unspecified`, `CustomMethod`, `Generic`) inside single enums. Many literals have direct or close counterparts in `Plant.ProcessEquipment`, demonstrating semantic overlap with physical realization rather than exact identity for every row; `ReactingChemicals.Method = PackedBed` and `ProcessStepDetail.ContactingInPacking` carry related packed-bed semantics through different constructs without proven equivalence. `ProcessStepDetail` remains a `0..*` composed sub-process refinement (not a classification axis and not `ProcessStep`), while `ProcessStep.HierarchyLevel` is supporting evidence that DEXPI can introduce explicitly named cross-cutting properties. Outcome A accepted — `ProcessStep.function` remains the only canonical step-classification axis, no generic second field or extension bag is added, and all `Method` values remain adapter-unsupported where required. Candidate B (generic union) and Candidate C (function-specific schema) are rejected; Candidate D is a plausible future home for part of the vocabulary, not implemented. Qualified engineering quantities remain separate as Issue #32, Issue #21 remains unchanged; no production code, adapters, tests, fixtures, examples, dependency, or runtime change; quality gates pass (352 tests, pyright 0 errors/warnings, docs/agent skills, build) |

### Backlog (Suggested Order)

The documented realistic process fragment is implemented as a loadable public
example through the production semantic model (see Completed), the basic
headless read-only process renderer derives a standalone SVG diagram from its
`ProcessModel` (see Completed; heuristics and limitations in
[docs/rendering.md](rendering.md)), the DEXPI 2.x Process adapter spike
(see Completed) answered the interoperability evidence question for an
explicit material subset, ADR-0009 separated canonical engineering
functions from presentation symbol roles (see Completed), and the DEXPI
Plant/P&ID semantic-mapping spike (see Completed;
[docs/dexpi-plant-pid-spike.md](dexpi-plant-pid-spike.md), ADR-0010)
established the Plant/P&ID semantic boundary from official model + instance
evidence without changing the canonical model, the physical-piping
specification/decision slice (see Completed;
[docs/physical-piping-model.md](physical-piping-model.md), ADR-0011) decided the
canonical piping shape, and its first implementation slice now ships (see
Completed; Issue #26). The DEXPI `ExchangingThermalEnergy` mapping-evidence slice
(see Completed; Issue #22,
[docs/dexpi-exchanging-thermal-energy-evidence.md](dexpi-exchanging-thermal-energy-evidence.md))
has since closed that one interoperability sub-question as an explicit
unsupported status. The process-step classification decision slice (see
Completed; Issue #31,
[docs/process-step-classification.md](process-step-classification.md),
ADR-0012) has closed the model-level *classification* half of the same Issue #22
finding — `ProcessStep` keeps exactly one classification axis, so no canonical
step-classification field is owed and no further per-class `Method` probing can
produce progress. The backlog rows below are the evidence-driven candidates for
the next slice.

| # | Item | Note |
|---|---|---|
| 1 | Expand the DEXPI Process subset (evidence-driven) | Independent alternative needing no physical-model change: re-open from fresh evidence now that ADR-0009 gave canonical engineering functions; candidates include material-port-only `pumping` reverse round-trip (proven) and `StoringMaterial` storage classes, each needing its own semantic review against a real instance before any mapping claim. **Partially advanced by Issue #22:** the `ExchangingThermalEnergy` candidate was investigated in full and resolved as an explicit documented + test-pinned unsupported status — canonical `heat_exchange` corresponds to the DEXPI class only as a process-function *kind*, and import/export/round-trip are not claimed because the blockers (`Method: HeatExchangeMethod` mandatory, coupled multi-stream semantics, no port kind, no energy-flow connection kind, no qualified-quantity model) are **model-level and shared with the rest of the DEXPI ProcessStep family** rather than specific to thermal steps; see [docs/dexpi-exchanging-thermal-energy-evidence.md](dexpi-exchanging-thermal-energy-evidence.md). **Partially advanced again by Issue #31:** the `Method` blocker was decided and is now closed as a canonical-model question — the nine DEXPI `Method` properties are heterogeneous and only partially overlap physical-realization semantics, canonical `ProcessStep` currently keeps exactly one classification axis, and the properties stay adapter-unsupported where DEXPI requires them (see Completed; [ADR-0012](decisions/ADR-0012-process-step-single-classification-axis.md)). Of the remaining blockers, `StoringMaterial` (Issue #21) is its own separate evidence slice and qualified engineering quantities are the outstanding model-level decision; neither is authorized here |
| 2 | Renderer/layout refinement (evidence-driven) | Only when a concrete diagram problem needs it: label-collision handling, row/column balancing, crossing reduction, persistent view/presentation configuration, or higher-fidelity symbol sourcing with explicit provenance; do not polish ahead of an evidence gap |

### Milestones

### Milestone 1 — validated YAML load

> DeepPlant can load a small process model from YAML, validate its semantic
> structure and report invalid references through the CLI.

Complete: structural validation and reference validation ship in the first two
slices.

### Milestone 2 — prototype fragment and renderer

> DeepPlant can represent a real process fragment of roughly 20–50 engineering
> objects, render it as a basic PFD/P&ID-like diagram and validate at least 10
> classes of engineering/model consistency errors.

Order within this milestone: the realistic process fragment is a loadable
synthetic example through the production semantic model (see Completed), the
standards/symbol-licensing governance slice (ADR-0007,
[docs/standards.md](standards.md)) governs symbol sourcing, the SVG + anchor +
initial basic symbol-pack contract (ADR-0008, [docs/svg-symbols.md](svg-symbols.md))
ships the `basic` process/PFD pack, and the basic headless read-only process
renderer now derives the standalone PFD diagram from the example
([examples/realistic-process-fragment/process.svg](../examples/realistic-process-fragment/process.svg)).
The milestone's remaining breadth (P&ID-like coverage and an engineering-rule
validation engine with several consistency-error classes) is still open. The
physical-piping specification slice
([docs/physical-piping-model.md](physical-piping-model.md), ADR-0011) is a
decision record, and its first implementation slice (Issue #26) now ships the
physical piping-realization layer: it adds representable P&ID-like structure
(lines, property-bounded segments, elementary realizations) and does **not**
claim the milestone's remaining breadth — no P&ID rendering exists, no
engineering-rule engine exists, and the piping layer's own rule set (C1, P1–P5)
is structural, not engineering.

### Next Task

The piping container and elementary realization layer from ADR-0011 is
**implemented** (Issue #26, see Completed): `PipingModel` (`PlantModel.piping`)
owns `PipingLine` -> `PipingSegment` -> `PipingRealization`, `Connection` carries
a required non-empty plant-unique `id`, rules C1 and P1–P5 are executable with
negative tests, the closed `kind: pipe | direct` vocabulary defaults to `pipe`,
YAML load/save round-trips semantically, and the realistic fragment realizes its
evidenced `P-101 → FV-101 → E-101` run as a pipe-realized line without inventing
engineering data.

The process-step classification decision slice is **complete** (Issue #31, see
Completed; [docs/process-step-classification.md](process-step-classification.md),
[ADR-0012](decisions/ADR-0012-process-step-single-classification-axis.md)): the
official DEXPI 2.0.0 Process model's nine `Method` properties across seven
enumeration types were inventoried in full, the same-name-versus-same-semantics
question was answered against the evidence, and the result is **Outcome A** —
the vocabulary is heterogeneous, with many values substantially overlapping
physical-realization / equipment-technology semantics and others expressing
function-specific mechanism/principle labels, so no generic second canonical
classification is justified and canonical `ProcessStep` currently keeps exactly
one classification axis. Candidate D is a plausible future home for the
overlapping subset only, and is not implemented. No model, adapter, example, or
test changed.

No single next task is promoted here. The next choice is deliberately left to
the later review this document's planning governance requires, because this
decision closed one model-level question without creating an implementation
obligation, and each remaining candidate is a different kind of work:

- **The remaining model-level question — qualified engineering quantities
  (C-3).** Issue #22 isolated exactly two model-level blockers: a
  required/non-derivable step classification and the absence of any canonical
  qualified-quantity representation. Issue #31 closed the first (no canonical
  field is owed). The second is untouched by that decision: DEXPI still requires
  `Duty`, `Area`, `Head`, `VolumeFlow`, `Pressure`, `Temperature`, side mass
  flows, and more as *qualified* values on the very classes examined here, and
  the canonical model still has nowhere to put value-plus-unit. This is the
  smallest remaining evidence-producing step of that pair, and it is recorded
  here as an **evidence-backed candidate**, not as an authorized task; it
  deserves its own decision Issue and must not be folded into a classification
  slice or grown into a units-library design.
- **Backlog row 1** — expand the DEXPI Process subset from fresh evidence (needs
  no physical-model change). Its `ExchangingThermalEnergy` sub-question is closed
  by Issue #22
  ([docs/dexpi-exchanging-thermal-energy-evidence.md](dexpi-exchanging-thermal-energy-evidence.md)):
  the class stays explicitly unsupported. Its `Method` blocker is closed by
  Issue #31. The remaining per-class candidate is `StoringMaterial` storage
  classes, which is its own separate slice (Issue #21) and is **not** closed by
  this decision. Neither candidate is authorized here.
- **Recorded physical-model gaps, not authorized work:** a concrete requirement
  for a property change that does not coincide with a `Connection` boundary
  (then `PropertyBreak` semantics), `1:N` parallel/as-built realization
  cardinality, a canonical `Pipe`/pipe-piece identity, and process ↔ physical
  realization — which is additionally the layer the DEXPI `Method` values belong
  to under ADR-0012. Each needs its own evidence and its own Issue per
  ADR-0011's and ADR-0012's Revisit-When lists; none is a mechanical continuation
  of this slice.
- **Backlog row 2** — renderer/layout refinement stays evidence-gated.

This follows from the current repository state: the DEXPI Plant/P&ID spike
([docs/dexpi-plant-pid-spike.md](dexpi-plant-pid-spike.md), ADR-0010) bounded
the question and kept the `Port`/`Connection` invariants, the physical-piping
specification/decision slice
([docs/physical-piping-model.md](physical-piping-model.md), ADR-0011) answered
*what is the physical piping graph?*, and the implementation slice proved the
decided shape against the realistic fragment with executable tests, so the
semantic model has met real example evidence before any rule engine, adapter, or
rendering work. The slice answered the physical side only; it did not decide how
`ProcessStep` maps to equipment or how `ProcessStream` maps to piping
realization.

The remaining physical-model work is split into two independent questions:

1. **Physical-piping realization:** pipe / segment / line / node / component
   representation. This is decided at the canonical-model level
   (`PipingLine` / `PipingSegment` / `PipingRealization` over `Port` and
   `Connection`) **and its first slice is implemented**; the deferred parts
   (mid-`Connection` property breaks, `1:N` realizations, pipe-piece identity,
   `Nozzle`/`PipingNode`) each need their own evidence and Issue.
2. **Process ↔ physical realization:** mapping between `ProcessStep` /
   `ProcessStream` and physical realization. Its shape and cardinality remain
   unresolved and must not be smuggled into the piping layer or `Connection`.

### Scope Discipline

- No database, ORM, web backend, containers, or external services.
- No empty architecture trees before real code exists.
- Schema and model design come from real example fragments, not abstraction.
- `Connection` is topology only; do not attach pipe/stream/signal engineering
  semantics until a real requirement justifies them.

## Directional Capability Roadmap

The stages below describe where DeepPlant may ultimately go. They are
**directional**: hypotheses about capability progression and dependencies, not
dates, release promises, commitments, or a guaranteed build order. A stage is
implemented only when its text says so; its presence never authorizes building
its architecture today (see the Anti-Roadmap at the end of this file).

The overall direction in one picture:

```text
Semantic plant model
        ↓
Topology and relationships
        ↓
Process streams / piping semantics
        ↓
PFD / P&ID rendering
        ↓
Interactive engineering editor
        ↓
Git diff / CI / engineering review
        ↓
Standards and DEXPI interoperability
        ↓
Engineering validation and rules
        ↓
Simulation and calculation adapters
        ↓
Safety / HAZOP / SIS workflows
        ↓
Multi-discipline engineering
        ↓
AI-assisted engineering workflows
```

The map is directional, not an implementation order.

### Stage 1 — Semantic Core

Goal: represent basic engineering objects explicitly and validate their
structure. Example concepts: `Plant`, `Equipment`, `Ports`, `Connections`,
identity, references.

Relationship to today: the core primitives of Stage 1 are implemented on
`main` — `PlantModel`, `Plant`, `Equipment`, equipment-owned `Port`,
`PortRef`, directed `Connection`, reference validation, YAML load, strict
structural validation, the standalone process model (`ProcessModel`, S1–S4),
its root/loadable integration (`PlantModel.process`), and canonical YAML
save/round-trip. Implemented primitives are not the same as a completed
capability stage: the Stage 1 exit signal below has now been exercised on the
documented realistic fragment encoded as a loadable synthetic example
([examples/realistic-process-fragment/plant.yaml](../examples/realistic-process-fragment/plant.yaml))
through the production models. Two physical-model questions were open at that
stage: the **physical-piping realization** question — decided at the
canonical-model level by ADR-0011 and now implemented by Issue #26 / PR #27 as
`Connection.id` plus `PipingModel` → `PipingLine` → `PipingSegment` →
`PipingRealization` with C1 and P1–P5 — and the **process ↔ physical
realization** mapping (`ProcessStep` ↔ equipment, `ProcessStream` ↔ piping
realization), whose shape and cardinality are still unresolved. The fragment
exposed both but required neither — no new schema was needed to represent it,
and the piping layer had not yet been implemented. Still unimplemented in that
layer: mid-`Connection` property breaks, `1:N` realizations, canonical
pipe/piece identity, `PipingComponent`, `Nozzle`/`PipingNode` refinement,
instrumentation, DEXPI Plant/P&ID import/export, engineering rules, and P&ID
rendering.

Exit signal:

> A small real process fragment can be represented faithfully enough to be
> useful outside the original drawing.

### Stage 2 — Process Topology

Goal: represent meaningful connectivity and distinguish different engineering
relationship concepts.

Open questions (deliberately unresolved here) — all on the physical-realization
side; `ProcessStream` itself is decided as the process-layer directed edge,
distinct from `Connection`:

- physical piping representation — decided by ADR-0011 (line / segment /
  realization over `Port` + `Connection`) and implemented as its first vertical
  slice by Issue #26 / PR #27; mid-`Connection` property breaks, `1:N`
  realizations, canonical pipe/piece identity, `PipingComponent`,
  `Nozzle`/`PipingNode` refinement, instrumentation, and DEXPI Plant/P&ID
  import/export remain unimplemented
- process ↔ physical realization: `ProcessStep` ↔ equipment and `ProcessStream`
  ↔ piping realization, including the mapping's shape and cardinality
- equipment nozzles
- instrumentation connectivity
- utilities

### Stage 3 — Engineering Views

Goal: derive human-readable engineering diagrams from the semantic model.
Likely capabilities: PFD rendering, P&ID rendering, symbol library,
presentation/layout model, manual layout override. Semantic and presentation
models stay separate.

### Stage 4 — Interactive Editing

Goal: let engineers modify the semantic model graphically without making the
drawing the source of truth. Potential surfaces: PFD/P&ID editor, property
editor, symbol placement, connection editing. Directional only; it does not
justify web architecture now.

### Stage 5 — Git-native Engineering Workflow

Goal: make semantic change review a first-class engineering workflow. Potential
capabilities: semantic diff, CI validation, PR review, model consistency checks,
generated reports.

### Stage 6 — Standards and Interoperability

Goal: exchange models with established engineering ecosystems (DEXPI, COMOS,
AVEVA, and other engineering tools).

Invariant:

> External representations are adapters, not the canonical DeepPlant model.

### Stage 7 — Engineering Rules

Goal: automate deterministic engineering checks. Examples may eventually
include: reference integrity, required properties, topology consistency, company
engineering rules, and selected standards checks. No standards compliance is
claimed that is not implemented.

### Stage 8 — Simulation and Calculations

Goal: connect semantic plant data to calculation and simulation tools. Potential
targets: DWSIM, SysCAD, the CAPE-OPEN ecosystem, and specialized engineering
calculations. The canonical model must not become simulator-specific.

### Stage 9 — Process Safety

Directional only. Potential future capabilities: HAZOP support, safeguards,
SIS / SIL concepts, reliability structures, and traceability between hazards and
safeguards. Nothing here implies automated safety approval.

### Stage 10 — Multi-discipline Engineering

Potential future expansion: process, mechanical, instrumentation, control,
electrical, documents, and requirements. The generic
`Component -> Port -> Connection` direction may eventually support multiple
disciplines, but that does not justify generalizing today's code.

### Stage 11 — AI-assisted Engineering

Goal: agents operate on the same explicit semantic engineering model as
engineers. A future workflow might be:

```text
Engineer:
"Add a standby pump parallel to P-101."

Agent:
changes semantic model
        ↓
Git diff
        ↓
validation
        ↓
updated engineering views
        ↓
human review
```

AI should operate through explicit engineering models and validation rather than
silently editing opaque documents.

## Anti-Roadmap — What Must Not Be Implemented Prematurely

> The directional roadmap provides product context, not implementation
> authorization. Implement only the currently scoped vertical slice.
>
> A future stage appearing in the roadmap is not sufficient justification to
> introduce its architecture today.
>
> Do not add abstractions, dependencies, or infrastructure for future stages
> until a current vertical slice requires them.

Concrete examples:

- the simulation stage does not justify simulator interfaces now
- the editor stage does not justify web architecture now
- the multi-discipline stage does not justify generic entity hierarchies now
- the DEXPI stage does not justify DEXPI-shaped domain objects now
- the physical-piping realization question and the separate process ↔ physical
  realization question do not justify attaching pipe or process-stream semantics
  to `Connection` now — and the decided piping layer (ADR-0011) honours that by
  referencing identified connections instead of widening `Connection`

Think broadly about the destination. Build narrowly in the current iteration.
