---
type: product
status: active
canonical_for:
  - product-vision
  - long-term-non-goals
read_when:
  - discovery
  - roadmap-change
update_when:
  - product-vision-change
depends_on: []
decision: []
evidence: []
superseded_by: null
---

# Product

The durable long-term thesis and capability map live in
[VISION.md](../../../VISION.md); this page is the product-level view of the same
direction. Planning governance is in [planning.md](index.md).

## Vision — Engineering as Code

DeepPlant is the first product implementing the broader idea of **Engineering as
Code** for process plants:

> Engineering intent should exist as explicit, machine-readable, versionable
> semantic data rather than being trapped primarily inside drawings and
> documents.

The long-term destination is a canonical semantic representation of a process
plant from which multiple engineering views and workflows are derived — PFDs,
P&IDs, line lists, validation reports, simulation inputs, and exchange formats.
That destination is reached one small vertical slice at a time
([roadmap.md](roadmap.md)), with the capability progression in
[direction.md](direction.md).

```text
                     engineers
                         │
                         ▼
                 DeepPlant model
                         │
      ┌──────────┬───────┼─────────┬──────────┐
      ▼          ▼       ▼         ▼          ▼
   CLI/API    PFD/P&ID validation  AI       adapters
                         │                    │
                         ▼             ┌──────┼───────┐
                       Git/CI          ▼      ▼       ▼
                                    DEXPI simulators tools
```

The diagram is conceptual, not a mandated architecture. What is actually
implemented today is described under "Where DeepPlant Is Now".

## Problem

Process plants are engineered through drawings and documents. The semantic
content — equipment, ports, connections, instruments, properties, and
relationships — is buried in symbols and coordinates, so engineering intent
cannot be queried, validated, diffed, or reused across tools. Engineering is
documented as graphics instead of expressed as data.

DeepPlant applies the **Engineering as Code** idea: engineering intent is an
explicit, versionable semantic model with tooling around it.

## PFD and P&ID Are Views, Not the Product Core

DeepPlant is not fundamentally "a P&ID editor". PFD and P&ID are initial
high-value engineering views over a deeper semantic model:

```text
                  Semantic model
                  /            \
                PFD            P&ID
          higher abstraction   more detail
```

The next product target is **DeepPlant Engineering Editor MVP v0.1**: a
local-first, standalone, browser-based editor initially launched locally. It
edits the same semantic model through a deliberately bounded subset of PFD and
P&ID; the drawing is not the source of truth. The initial implementation
direction is Vue 3 + TypeScript + Vite. The interaction architecture is decided by
Issue #69 ([engineering-editor-ux.md](../research/engineering-editor-ux.md)) and the
reuse-first frontend architecture by Issue #70
([engineering-editor-reuse-architecture.md](../research/engineering-editor-reuse-architecture.md)).
The first executable slice (**Issue #75**) is delivered: a local, read-only
Process/PFD editor over the existing Python semantic core, using exactly that
stack. Its foundation was hardened by the explicitly sequenced slices
[#79](roadmap.md) (application layout + FastAPI boundary) → #80 (frontend
engineering contract) → #81 (frontend refactor) → #82 (browser E2E), all
delivered. No semantic
editing, presentation persistence, or P&ID authoring is implemented. The post-#82
[re-evaluation gate](roadmap.md#re-evaluation-gate) selected
[Issue #89](https://github.com/Semtexcz/DeepPlant/issues/89) — the DeepPlant
project format and portable package — as the sole next product capability, so
persistence semantics are decided before the first write-capable editor slice.
Detailed view-projection rules remain deliberately undecided here.

## Engineering Editor MVP v0.1

The MVP is the first usable product vertical slice, not a replacement for the
semantic-model-first thesis. It is intended to be:

- local-first, standalone, file-based, and Git-native;
- a browser-based SPA launched locally rather than a hosted service;
- an interactive editor, not a read-only viewer;
- limited to a deliberately bounded PFD and P&ID subset;
- explicit about three separate state concerns: semantic engineering state,
  presentation/layout state, and frontend-framework state.

### Bounded engineering scope

The MVP PFD subset is limited to a useful small process fragment: create, delete,
connect, select, move, and edit basic properties of supported process steps and
streams; validate; save; and reload. Initial supported process functions are
limited to source, sink, pumping, heat exchange, mixing, splitting, and basic
vessel/storage representation where the canonical model supports them.

The MVP P&ID subset is intentionally narrower than a production P&ID system:
basic pump, vessel, and heat-exchanger equipment; their basic physical
connection points/ports; basic piping realization; and at most one basic valve
concept when supported by the selected semantic slice. It excludes full
instrumentation and detailed piping semantics.

PFD and P&ID are not independent drawing documents. They are views over distinct
but related semantic layers: `ProcessModel` for the PFD, and the physical plant
and piping model for the P&ID. `ProcessStep` is not `Equipment`,
`ProcessStream` is not physical piping realization, and `ProcessPort` is not a
physical `Port`/`Nozzle`. Issue #39 delivered the evidence-first decision about how
those layers are related: ADR-0016 decides that any future relationship is owned
in a separate cross-layer realization layer, but no mapping is implemented. That
boundary must precede a stable PFD ↔ P&ID realization workflow while still not
blocking a pure Process/PFD UI slice.

### Source-of-truth interaction direction

The editor must send user actions through an application command that mutates
and validates the semantic model, then updates the view:

```text
user interaction
      ↓
application command
      ↓
semantic model mutation
      ↓
validation
      ↓
view update
```

It must not treat SVG/canvas mutation as the authoritative state and infer
engineering semantics afterward.

Its target user journey is:

```text
open project
    ↓
open/create PFD
    ↓
graphically create/edit process semantics
    ↓
realize part of the process physically
    ↓
open/create P&ID
    ↓
graphically edit basic equipment/piping
    ↓
validate
    ↓
save semantic + presentation state
    ↓
reload without loss
```

The MVP does not require cloud hosting, authentication, databases,
collaboration, complete instrumentation, simulation, 3D, complete DEXPI,
HAZOP/SIS workflows, or all EPC disciplines. A future Copilot/multimodal agent
is a first-class UX direction, but is a placeholder rather than MVP scope.

## Semantic Model as the Authoritative Record of Managed Intent

The semantic engineering model is the durable core artifact and the
authoritative system of record for engineering intent and project state managed
by DeepPlant (see [VISION.md](../../../VISION.md)). Conceptually it feeds the
engineering deliverables — where DeepPlant owns the information — instead of
each deliverable being authored in isolation:

```text
semantic engineering model
          │
          ├── PFD
          ├── P&ID
          ├── line lists
          ├── validation
          ├── reports
          ├── simulation inputs
          └── exchange formats
```

External systems and evidence (vendor data, measurements, material databases,
standards/legislation, as-built surveys, COMOS / AVEVA data owned by another
organization) remain authoritative for the data they own and are reached
through explicit adapters, references, and provenance. DeepPlant is therefore
not the ultimate source of every engineering fact, but it is authoritative for
what it manages.

This does **not** claim every document will necessarily be generated
automatically. The principle is that semantic information should be reusable
instead of manually duplicated wherever practical. Presentation data stays
separate from engineering semantics.

## Workflow, Judgment, and Product Position

Three durable positions are stated in full in [VISION.md](../../../VISION.md) and are
deliberately not repeated here:

- **Git-native engineering workflow** — semantic diff, validation, engineering
  review, and CI over a versionable model. The versionable YAML model and the
  `validate` CLI exist today; the rest is target direction.
- **Human engineering judgment remains essential** — only deterministic
  constraints should be automated. Judgment, trade-offs, and design intent stay
  human responsibilities, and this document designs no rules engine.
- **Product position: a semantic and automation layer** — DeepPlant complements
  rather than replaces heterogeneous engineering tools. External ecosystems
  (DEXPI, COMOS, AVEVA, simulators, calculations) are adapters around the
  canonical model, and no external schema shape dictates that model.

## Users

- Process and piping engineers who produce and review PFDs and P&IDs.
- Engineering organizations that need review, CI, and auditability for
  engineering deliverables.
- Integrators who exchange plant models with DEXPI, simulators, and engineering
  tools.

Product hypothesis (not a validated market fact): DeepPlant may be especially
useful for individual engineers, freelancers, small engineering teams,
organizations that cannot justify expensive integrated engineering platforms,
and teams wanting automation around existing engineering tools. It may
complement rather than replace systems such as COMOS or AVEVA. No business model
is assumed by this document.

## Where DeepPlant Is Now

Current implementation facts are not repeated here. The boundary map is
[architecture.md](../architecture/index.md); the current obligations are the
[contracts](../../contracts/index.md) (plant model, process model, physical piping,
YAML format, CLI, renderer, symbol pack, DEXPI Process adapter); the actionable
current and next state is [roadmap.md](roadmap.md).

## Hypotheses

Current working hypotheses, not validated facts:

- A small process fragment can be represented and validated as a semantic model;
  the near-term target is a real fragment of roughly 20–50 engineering objects.
- A semantic-model-first representation, kept free of presentation data,
  supports PFD/P&ID rendering and DEXPI exchange without redesign.
- Engineers can use a local graphical editor while semantic data remains
  file-based, reviewable, and independent of presentation/framework state.
- The audiences and the complement-not-replace position under "Users" describe a
  real market need.

## Long-Term Capability Vision

The capability progression — the stages, their goals, their dependencies, and
the questions deliberately left open in each — is recorded in
[direction.md](direction.md). It is product context, not implementation
authorization: the [anti-roadmap](roadmap.md#anti-roadmap--what-must-not-be-implemented-prematurely)
still governs, and the actionable current/next state lives in
[roadmap.md](roadmap.md).

## Product Principles

- The semantic engineering model is the product core. CLI, GUI, renderers, and
  adapters depend on it.
- PFD and P&ID are engineering views over the model, not the fundamental data
  model.
- Semantic engineering data and presentation data (sheet, symbol, coordinates,
  geometry, routing, labels) stay strictly separate.
- YAML is a serialization format, not the domain model.
- Connectivity points toward generic `Component -> Ports -> Connections`
  relationships rather than hard-coded equipment-to-equipment links.
- External engineering ecosystems (DEXPI, COMOS, AVEVA, simulators) are
  reachable through adapters; external schema shape must not dictate the
  canonical model.
- Consumer-specific representation concerns must not leak into the semantic
  domain model. A genuine engineering concept discovered through DEXPI,
  simulation, or another integration may legitimately cause the domain model to
  evolve.

## Long-Term Non-Goals

- Do not add hosted/cloud backends, authentication, databases, ORMs,
  collaboration services, containers, or production server infrastructure before
  a concrete requirement justifies them. A minimal local
  application/transport/API boundary may be introduced only when an authorized
  standalone SPA vertical slice requires it; this product document selects no
  framework.
- Do not embed drawing coordinates or SVG concepts into core engineering
  objects.
- The directional roadmap is product context, not implementation authorization;
  a future stage never justifies premature architecture (see the Anti-Roadmap in
  [roadmap.md](roadmap.md)).
- No automated safety approval is implied by any safety-related direction.
- No standards compliance is claimed beyond what is implemented and verified.

## Related

- [architecture.md](../architecture/index.md) — boundary map of what exists, and the
  durable invariants.
- [contracts/index.md](../../contracts/index.md) — current model, format, CLI,
  renderer, and adapter obligations.
- [direction.md](direction.md) — long-term capability progression (product
  context, not authorization).
- [roadmap.md](roadmap.md) — current state, next direction, anti-roadmap.
- [workflow.md](../workflow/index.md) — the daily change loop.
- [decisions/index.md](../decisions/index.md) — architectural decisions.
- [VISION.md](../../../VISION.md) — the durable long-term thesis and capability map.
