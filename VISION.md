# DeepPlant Vision

## Why DeepPlant

Conventional process engineering is still heavily drawing-centric,
document-centric, PDF-centric, spreadsheet-centric, and GUI-centric. Engineering
information is fragmented across PFDs and P&IDs, Excel workbooks, simulators,
equipment lists, instrument lists, datasheets, vendor documents, COMOS / AVEVA
installations, PDF revisions, and human review.

Typical consequences are the ones software engineering learned to remove decades
ago:

```text
manual synchronization
duplicated data
weak machine-readable semantics
poor diff/review
difficult automation
difficult consistency checking
high integration friction
```

This is an architectural opportunity. The root cause is that engineering intent
is encoded as graphics and documents instead of as explicit, machine-readable
semantics. DeepPlant exists to fix that root cause, not to become one more tool
that stores intent inside a drawing or a PDF.

## Core Thesis

> DeepPlant is a Git-native semantic engineering platform for process plants.

The DeepPlant semantic model is the **authoritative system of record for
engineering intent and project state managed by DeepPlant**. DeepPlant does not
claim to be the ultimate source of every engineering fact: external systems and
evidence remain authoritative for the data they own and are integrated through
explicit adapters, references, and provenance.

```text
external authoritative evidence/data
        ↓
adapter / reference / provenance
        ↓
DeepPlant-managed engineering intent and state
        ↓
derived views / checks / calculations / exports
```

External authoritative sources may include vendor data, laboratory and plant
measurements, material databases, standards and legislation, as-built surveys,
and COMOS / AVEVA or other engineering systems owned by another organization.

Drawings, reports, exchange representations, and other artifacts are derived
from that semantic state where DeepPlant owns the information:

```text
DeepPlant-managed semantic model         authoritative for managed intent/state
        ├── PFD views                    derived views
        ├── P&ID views                   derived views
        ├── calculations                 computations
        ├── simulation inputs/views      computations / adapters
        ├── validation results           computations
        ├── reports                      derived views
        └── DEXPI / vendor formats       adapters
```

The distinction is deliberate:

```text
authoritative system of record for DeepPlant-managed design intent
        !=
ultimate source of every engineering fact
```

This preserves the semantic-first thesis: DeepPlant is authoritative for what
it manages and reaches everything else through explicit adapters — it is not
merely an integration database that mirrors external state without semantic
ownership.

## Engineering as Code

DeepPlant applies the *Engineering as Code* analogy:

```text
software engineering             process / plant engineering

source code                      semantic engineering model
Git                              Git
code review                      engineering review
tests                            engineering rules/checks
CI                               automated engineering validation
build                            generated drawings / reports / models
API adapters                     DEXPI / vendor / simulator adapters
IDE                              engineering IDE
```

This is a **workflow analogy**, not a claim that plant engineering is identical
to software engineering. Engineering judgment, physical constraints, and domain
expertise remain essential; DeepPlant only makes intent explicit and
machine-checkable where that is genuinely possible.

## Semantic Source of Truth

A process plant has several distinct semantic layers. They must never be
collapsed into one graph:

```text
simulation graph
        !=
process / PFD graph
        !=
physical plant / P&ID graph
```

The corresponding object distinctions are equally durable:

```text
ProcessStep   != Equipment
ProcessPort   != physical Port / Nozzle
ProcessStream != physical Connection / PipingLine
```

The engineering function a step performs is not its presentation role, its
symbol-pack identity, or a particular SVG asset:

```text
engineering function
        !=
presentation symbol role
        !=
symbol pack
        !=
SVG asset
```

`ProcessStep.function` is canonical engineering semantics. Symbol roles are
resolved at the rendering boundary by presentation policy or explicit per-step
overrides (ADR-0009); they are never stored in the semantic model. A semantic
model may be valid yet not renderable without presentation information — that is
desirable, because semantic completeness is not presentation completeness.

## Engineering Constraint Hierarchy

DeepPlant's long-term automation target is the deterministic part of the
constraint hierarchy:

```text
1. physical laws / mathematical consistency
2. legislation / hard standards requirements
3. company / project engineering rules
4. configurable design preferences
5. explicit human engineering decisions
```

DeepPlant should automate checks as far down this hierarchy as deterministic
engineering rules can honestly reach — and should stop there. It does not
pretend to automate engineering judgment, trade-offs, or professional
safety-engineering practice.

## Capability Map

The DeepPlant vision spans the following strategic capability areas:

| Capability | Long-term intent |
|---|---|
| Semantic Foundation | A canonical, typed, validated semantic model of a plant; authoritative system of record for DeepPlant-managed engineering intent and state |
| Process / PFD | Standalone process graphs (`ProcessStep` / `ProcessStream`) and derived PFD views |
| P&ID Semantic Model | Physical topology, equipment realization, piping, instrumentation, and derived P&ID views |
| Interoperability | Exchange with the engineering ecosystem through adapters (DEXPI today; others later) |
| Engineering Rules as Code | Deterministic engineering checks running in Git / CI |
| Simulation Integration | Connect semantic plant data to simulators without making the simulation graph canonical |
| Safety Engineering | Semantic support around HAZOP, safeguards, SIS / SIL, and traceability |
| Interactive Engineering IDE | Graphical authoring and review over the semantic model |
| EPC Ecosystem Integrations | COMOS / AVEVA / company-system interoperability as an integration layer |
| Production / Collaboration | Git-native team workflows, diff/review, and CI at organizational scale |

These are strategic capability areas, not implementation commitments. Their
implementation designs stay open until evidence justifies each one.

### Current capability reality

Only a subset exists today, in executable, evidence-producing vertical slices:

- the semantic foundation and strict YAML validation;
- a standalone process domain model (`ProcessModel` with `ProcessStep[]` /
  `ProcessPort[]` / `ProcessStream[]`, mixing / splitting / recycle legal);
- canonical `ProcessStep.function` semantics separated from presentation symbol
  roles (ADR-0009);
- YAML semantic round-trip (`load_plant` / `save_plant`);
- a packaged `basic` process symbol pack and a headless read-only process SVG
  renderer;
- a narrow DEXPI 2.0 Process import/export adapter spike
  ([docs/dexpi-process-spike.md](docs/dexpi-process-spike.md)).

Everything else in the capability map is direction, tracked as horizon state in
the strategic GitHub Project and sequenced by evidence in
[docs/roadmap.md](docs/roadmap.md).

## North-Star Workflow

The long-term target workflow for a change such as:

> Add standby pump P-102 parallel to P-101.

```text
1.  update the semantic model
2.  show the engineering diff
3.  validate references and topology
4.  run engineering rules
5.  update affected PFD / P&ID views
6.  identify affected calculations and simulations
7.  create a reviewable Git change
8.  synchronize configured external systems
```

Steps 5–8 are future vision; the reviewable Git change (steps 1–3, 7) is the
implemented direction of today's model and CLI.

## Architectural Principles

- The semantic engineering model is the product core; CLI, GUI, renderers,
  adapters, and agents depend on it — never the reverse.
- YAML is a serialization format, not the domain model.
- Presentation data (symbols, coordinates, routing) stays separate from
  engineering semantics.
- Domain objects remain usable from Python and CLI, with no GUI required.
- External representations are adapters around the canonical model; an external
  schema shape never dictates the canonical model.
- DeepPlant integrates with the engineering ecosystem rather than assuming it
  replaces every existing tool.
- A genuine engineering concept discovered through an adapter may legitimately
  evolve the domain model — after evidence, not before it.
- Long-term capabilities are relatively stable; their implementation design is
  not.
- Build narrowly, one vertical slice at a time; the directional roadmap is
  product context, not implementation authorization.

## What DeepPlant Is Not

DeepPlant is not merely:

```text
a P&ID drawing tool
a CAD clone
a process simulator
a COMOS clone
an AVEVA clone
a YAML editor
an AI chatbot
```

It is a semantic engineering, integration, and workflow layer. PFD / P&ID
rendering, simulator connectivity, and AI assistance matter, but they are views,
adapters, and agents over the semantic model — not the model itself.

## Current Status

DeepPlant is an experimental repository (AGPL-3.0-only) in its early
evidence-driven phase. The current state, sequenced reasoning, unresolved
questions, and next evidence candidates are recorded in
[docs/roadmap.md](docs/roadmap.md). The strategic capability state is
visualized in the GitHub Project; the roadmap document remains the source of
sequencing rationale.

Nothing in this vision document authorizes implementation. The current scoped
vertical slice does; this document describes the destination, not a delivery
schedule or a fixed build order.
