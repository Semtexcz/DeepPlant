---
type: direction
status: active
canonical_for:
  - directional-capability-progression
read_when:
  - roadmap-change
  - feature-planning
  - capability-planning
depends_on:
  - docs/dev/planning/roadmap.md
  - docs/dev/planning/product.md
decision: []
evidence: []
superseded_by: null
---

# Directional Capability Roadmap

> **Status:** product context, moved out of [roadmap.md](roadmap.md) when the
> roadmap was reduced to current state, immediate direction, and unresolved
> evidence gaps. This stage list describes capability progression and
> dependencies; it is not a delivery calendar, a fixed build order, or an
> implementation authorization. The
> [anti-roadmap](roadmap.md#anti-roadmap--what-must-not-be-implemented-prematurely)
> still governs, and the GitHub Project holds the current strategic horizons.


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
([examples/realistic-process-fragment/plant.yaml](../../../examples/realistic-process-fragment/plant.yaml))
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
models stay separate. Any future generic rendering, layout, or routing choice
starts from the evidence-first
[reference-product landscape](../research/reference-products.md), which authorizes no
implementation.

### Stage 4 — Interactive Editing

Goal: let engineers modify the semantic model graphically without making the
drawing the source of truth. Potential surfaces: PFD/P&ID editor, property
editor, symbol placement, connection editing. Directional only; it does not
justify web architecture now. Generic editor, workspace, and interaction
technology must be compared against the
[reference-product landscape](../research/reference-products.md) rather than assumed, and no
GUI framework may dictate the domain model.

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

