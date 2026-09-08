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

## Current Implementation Roadmap

DeepPlant ships the project foundation plus four semantic vertical slices, a
realistic process-fragment validation example, the standards/symbol-licensing
governance slice ([docs/standards.md](standards.md), ADR-0007), and the first
process presentation-asset slice: the SVG + anchor + initial basic symbol-pack
contract (`assets/symbols/process/basic/`, [docs/svg-symbols.md](svg-symbols.md),
ADR-0008):

- minimal domain model: `PlantModel` -> `Plant` + `list[Equipment]`
- equipment-owned `Port` objects; port identity is local to the owning equipment
- top-level `Connection` edges over structured `PortRef(component, port)`
  endpoints
- reference validation: every endpoint component must resolve to existing
  equipment and its port must exist on that equipment
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
  assets under `assets/symbols/process/basic/` (`source`, `mixing`, `pump`,
  `heat_exchanger`, `splitting`, `vessel`, `sink`) with canonical
  `viewBox="0 0 100 100"`, monochrome `currentColor` line art, and hidden
  ordered `anchor-in-N` / `anchor-out-N` slots; `ProcessStep.type` identifies a
  role, and a future presentation layer selects a pack and its pack-local SVG
  asset; contract in `docs/svg-symbols.md`, decision in ADR-0008, provenance in
  `assets/symbols/process/basic/README.md`; deterministic stdlib XML contract
  tests plus realistic-fragment role coverage; no semantic-model fields,
  renderer, frontend, or runtime pack-selection dependency

`Connection` is currently a directed semantic topological relationship from
`source` to `target`; it remains topology only and is not yet a pipe, process
stream, signal, cable, or physical line. Work proceeds as small vertical
changes with executable tests. `PlantModel` owns zero or one `ProcessModel`
under `process`; the loader populates it from YAML and `save_plant()` writes
canonical YAML that `load_plant()` reads back into a semantically equal model.
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
| Define `Connection` | Directed semantic topology only: `source`/`target` as `PortRef(component, port)`; not a pipe/stream/signal/physical line yet |
| Reference validation | Connections resolve to existing equipment and owned ports; referential integrity only |
| YAML load | YAML as serialization, validated via Pydantic into the domain model |
| Semantic validation (structural) | Non-empty ids; unknown fields rejected; unique equipment ids; unique port ids per equipment |
| First executable example | `examples/minimal-process/plant.yaml` runs through the CLI |
| Decide process-model container | ADR-0005 accepted (C1): `PlantModel` remains the overall aggregate; one independently valid `ProcessModel` owns the process graph and the S1–S4 validation boundary |
| Define `ProcessModel` | Standalone process-domain container owning `ProcessStep[]` and `ProcessStream[]`; step and stream ids are separate namespaces (S1); not yet part of `PlantModel` |
| Define `ProcessStep` / `ProcessPort` | Process steps with `id`, open non-empty `type`, `name`, owned `ProcessPort[]`; process-port ids local to the owning step (S2) |
| Define `ProcessRef` / `ProcessStream` | `ProcessRef(step, port)` endpoints; binary directed `ProcessStream` with `id`, optional `name`; no flow/designation/physical semantics |
| Process structural validation | S1 duplicate step/stream ids rejected; S3 endpoints resolve to process steps and owned process ports; S4 identical source/target endpoints rejected; cycles/recycle/mixing/splitting structurally allowed; no dependency on `Equipment`/`Port`/`Connection` |
| Integrate `ProcessModel` into the root/loadable model | `PlantModel.process: ProcessModel \| None`; YAML `process` section (`steps`, `streams`) loads through the existing loader; missing `process` and `process: null` load as no process model, `process: {}` as an empty one; S1–S4 stay on the process-domain models; process and physical ids remain separate namespaces; root/YAML shape recorded in ADR-0006 |
| YAML save / semantic round-trip | Canonical `save_plant()` through Pydantic `model_dump(exclude_none=True)` + PyYAML (`sort_keys=False`, `allow_unicode=True`); `load_plant(save_plant(model)) == model`; `None` optionals omitted; `process: None` omitted; explicit empty `ProcessModel` preserved; deterministic field order; UTF-8 with a trailing newline; comments/formatting not preserved; no domain-model changes; no CLI save/format command |
| Realistic process fragment as a loadable example | Synthetic public YAML (`examples/realistic-process-fragment/plant.yaml`) encodes the documented PFD fragment: seven `ProcessStep`s and seven `ProcessStream`s including recycle, mixing, and splitting; loads through `load_plant()` via `PlantModel.process` and round-trips through `save_plant()`; physical bootstrap layer (`T-101`, `P-101`, `FV-101`, `E-101`, `V-101`) stays independent; `PS-mix`/`PS-split` have no `Equipment` counterpart and `FV-101` has no `ProcessStep`; no new schema, process↔physical mappings, or piping model |
| Standards and symbol-licensing strategy | Governance/research slice (no implementation code): [docs/standards.md](standards.md) registers the normative restricted references (ISO 10628-1/-2, ISO 14617-1/-2, ANSI/ISA-5.1, IEC 62424) versus the open DEXPI 2.0 specification (CC BY 4.0, confirmed from the official announcement and GitLab repository); restricted-standards handling and AI-agent rules are explicit (AGENTS.md); conservative verification states (`reference` / `candidate-alignment` / `human-verified`) replace unverified “compliant” claims; future symbol provenance requirements and the seven-ProcessStep-type assessment are defined; candidate sources (ISPF `ispf-pid-v1`, draw.io P&ID shapes, DEXPI material, others) are assessed at file/licence level and none is imported; decision recorded in ADR-0007 |
| SVG + anchor + initial basic symbol-pack contract (process/PFD presentation) | First presentation-asset slice: seven DeepPlant-original non-normative fallback SVG assets under `assets/symbols/process/basic/` covering the realistic fragment's `ProcessStep.type` roles; role identity is distinct from graphical asset identity (future presentation-layer pack selection deferred); canonical `viewBox="0 0 100 100"`, monochrome `currentColor` line art, generic ordered `anchor-in-N` / `anchor-out-N` slots distinct from semantic ports; contract in [docs/svg-symbols.md](svg-symbols.md), decision in ADR-0008, provenance in `assets/symbols/process/basic/README.md`; deterministic stdlib XML tests; no semantic-model fields, no renderer, no runtime dependency |

### Backlog (Suggested Order)

The documented realistic process fragment is now implemented as a loadable
public example through the production semantic model (see Completed):
[examples/realistic-process-fragment/plant.yaml](examples/realistic-process-fragment/plant.yaml).
It exposed no blocking semantic gap for the process graph. The
standards/symbol-licensing governance slice (ADR-0007,
[docs/standards.md](standards.md)) fixed the provenance and licensing rules, and
the SVG + anchor + initial basic symbol-pack contract (ADR-0008,
[docs/svg-symbols.md](svg-symbols.md)) now provides the `basic` process/PFD pack
with deterministic ordered anchors. The next task is the first row below.

| # | Item | Note |
|---|---|---|
| 1 | Basic headless read-only process renderer | Derive a simple standalone SVG process/PFD diagram from `ProcessModel` using the explicitly chosen `basic` pack and the anchor contract (`assets/symbols/process/basic/`, [docs/svg-symbols.md](svg-symbols.md)): simple layout, symbol placement, anchor assignment from `ProcessStream` incidence, stream routing — no frontend, no interactive UI; the renderer must not hardcode `assets/symbols/process/{ProcessStep.type}.svg` as a permanent global identity model |
| 2 | DEXPI adapter spike | Prove import/export feasibility on a real fragment |

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
[docs/standards.md](standards.md)) governs symbol sourcing, and the SVG +
anchor + initial basic symbol-pack contract (ADR-0008,
[docs/svg-symbols.md](svg-symbols.md)) now ships the `basic` process/PFD pack.
The basic headless read-only process renderer (backlog row 1) then derives the
diagram from that example.

### Next Task

The next task is the basic headless read-only process renderer: a small
standalone component (no frontend, no interactive UI, no new dependencies) that
derives a simple SVG process/PFD diagram from a `ProcessModel` using the
explicitly chosen `basic` development pack and the anchor contract:

```text
ProcessModel
→ simple layout
→ symbol placement
→ anchor assignment (ProcessStream incidence → anchor-in / anchor-out)
→ stream routing
→ standalone SVG
```

The SVG + anchor + initial basic symbol-pack contract (ADR-0008,
[docs/svg-symbols.md](svg-symbols.md), `assets/symbols/process/basic/`) now
provides the `basic` pack-local geometry and ordered anchor slots for every
`ProcessStep.type` role used by the realistic fragment
([examples/realistic-process-fragment/plant.yaml](examples/realistic-process-fragment/plant.yaml)),
which remains the reference workload. The realistic fragment exposed no blocking
semantic gap for the process graph, so no further process-model decision is
required before starting renderer work. The open physical-piping /
process-to-physical-realization question remains a tracked, unresolved semantic
decision, but it is not a prerequisite for the process/PFD renderer. The
smallest renderer may simply use `basic` as its explicitly chosen/default
development pack, but it must not hardcode
`assets/symbols/process/{ProcessStep.type}.svg` as the permanent global identity
model; later standards-aligned symbol sourcing and pack selection remain a
separate task.

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
([examples/realistic-process-fragment/plant.yaml](examples/realistic-process-fragment/plant.yaml))
through the production models. The open physical-piping /
process-to-physical-realization question remains an unresolved semantic
decision; the fragment exposed it but did not require it — no new schema was
needed to represent the fragment.

Exit signal:

> A small real process fragment can be represented faithfully enough to be
> useful outside the original drawing.

### Stage 2 — Process Topology

Goal: represent meaningful connectivity and distinguish different engineering
relationship concepts.

Open questions (deliberately unresolved here) — all on the physical-realization
side; `ProcessStream` itself is decided as the process-layer directed edge,
distinct from `Connection`:

- physical piping representation
- `ProcessStream` ↔ physical realization mapping
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
- the open physical-piping / process-to-physical-realization question does not
  justify attaching pipe or process-stream semantics to `Connection` now

Think broadly about the destination. Build narrowly in the current iteration.
