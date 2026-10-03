---
type: design-evidence
status: active
canonical_for:
  - engineering-editor-ux-architecture
read_when:
  - interactive-editor-planning
  - gui-slice-planning
  - pfd-pid-editor-design
  - roadmap-change
update_when:
  - ux-architecture-change
  - gui-slice-evidence
depends_on:
  - docs/dev/planning/product.md
  - docs/dev/planning/direction.md
  - docs/dev/planning/roadmap.md
  - docs/dev/architecture/index.md
  - docs/contracts/process-model.md
  - docs/contracts/plant-model.md
  - docs/contracts/physical-piping.md
  - docs/contracts/rendering.md
  - docs/dev/research/reference-products.md
decision:
  - docs/dev/decisions/ADR-0003-separate-semantic-and-presentation-models.md
  - docs/dev/decisions/ADR-0009-separate-process-function-from-symbol-role.md
  - docs/dev/decisions/ADR-0016-process-physical-realization-boundary.md
evidence:
  - docs/dev/research/process-physical-realization-boundary.md
  - docs/dev/research/reference-products.md
superseded_by: null
---

# Engineering Editor UX Architecture

> **Question this document answers:** how should an engineer interact with the
> DeepPlant Engineering Editor MVP v0.1 — which permanent and contextual surfaces
> exist, what each surface owns and must not own, how engineering objects are
> added, selected, edited, connected, and diagnosed, and how the frontend mutates
> the semantic model?

> **Status:** design evidence and interaction architecture. This document
> decides **how an engineer interacts with DeepPlant**, not **which frontend
> libraries implement that interaction** (Issue #70) and not **what product
> scope the MVP covers** (Issue #68, [product.md](../planning/product.md)). It
> selects no framework or library, adds no dependency, creates no `frontend/`
> directory, and authorizes no implementation. It is the interaction authority
> the first executable GUI slice must follow when one is eventually selected at
> the [re-evaluation gate](../planning/roadmap.md#re-evaluation-gate).

## Outcome card

- **Question investigated:** what product interaction architecture does a
  canvas-first, context-sensitive, command-driven engineering editor need so that
  the first GUI implementation slice does not have to invent fundamental UX
  behaviour, while the semantic model stays authoritative and the user never
  experiences DeepPlant as "a YAML editor + a graph widget + a property form + an
  AI chat" assembled as unrelated tools?
- **Status:** open design evidence. It states durable interaction rules and
  required capabilities; it records unresolved UX questions rather than
  resolving them by invention. No GUI exists.
- **Inspection scope and date:** the authoritative product, planning,
  architecture, contract, and decision documents; the loadable
  [realistic fragment](../../../examples/realistic-process-fragment/plant.yaml);
  the existing [reference-product landscape](reference-products.md); and public
  documentation of external editors (VS Code, KiCad, Figma), inspected
  **2026-10-03** on `main` at `a0e2fd9b5a63f91cad2053355c0df2884a634863`.
- **Conclusions:**
  1. The default workspace is canvas-dominant and uses the **minimum permanent
     chrome**: a compact explorer, a compact inspector, editor tabs, and a
     Problems strip. Everything else is contextual, search-driven, or
     command-only.
  2. Interaction flows in one direction only: user interaction → application
     command → semantic mutation → validation → updated projection/view. Canvas
     or framework state is never serialized as project truth.
  3. Four state kinds stay explicitly separate: semantic, persistent
     presentation, framework, and transient UI. Only the first is canonical
     engineering truth today; persistent presentation is deliberately deferred,
     and neither presentation nor framework state may appear as fields on
     semantic objects.
  4. PFD and P&ID are **editor views (tabs)**, never global application modes.
     The explorer exposes engineering concepts (not filesystem structure), the
     inspector is selection-driven, and Problems is non-modal.
  5. Per [ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md),
     process ↔ physical realization is read through **cardinality-neutral**
     related-object navigation; no `realized_by` shape, no universal 1:1, and no
     invented physical target for `ProcessPort` are implied.
  6. Direct manipulation, the command palette, and a future Copilot share **one
     conceptual application-command boundary**; Copilot is a future layer with no
     backend, and its MVP placeholder is deferred (see the Copilot decision).
- **Resulting ADRs:** none. The durable rules this document applies are already
  decided by [ADR-0003](../decisions/ADR-0003-separate-semantic-and-presentation-models.md),
  [ADR-0009](../decisions/ADR-0009-separate-process-function-from-symbol-role.md),
  and [ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md);
  no new durable rule cleared the ADR threshold (see
  [ADR threshold](#adr-threshold)).
- **Current contracts operationalizing the result:** none yet — no editor is
  implemented. The semantic contracts it depends on
  ([process-model.md](../../contracts/process-model.md),
  [plant-model.md](../../contracts/plant-model.md),
  [physical-piping.md](../../contracts/physical-piping.md),
  [rendering.md](../../contracts/rendering.md)) continue to describe the current
  model.
- **Conditions for revisiting:** when the [re-evaluation gate](../planning/roadmap.md#re-evaluation-gate)
  selects the first GUI slice, when Issue #70's reuse-first architecture
  constrains a surface, or when real user evidence shows a permanent surface is
  missing, redundant, or wrong.

## Scope and authority

This document owns **interaction architecture**: user interaction, workspace
responsibilities, discoverability, contextual behaviour, state semantics from
the UX perspective, and the required capabilities of the first GUI slice. It is
the smallest truthful authority structure for Issue #69 — one focused
design/evidence document plus minimal navigation and planning reconciliation. It
deliberately does not create a new documentation hierarchy.

It does **not** own:

- product scope — decided by Issue #68 and [product.md](../planning/product.md);
- semantic-model contracts — owned by [contracts/](../../contracts/index.md);
- process ↔ physical realization ownership — decided by
  [ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md);
- GUI library, framework, docking, canvas, routing, or editor-technology
  selection — owned by Issue #70 and the [reference-product landscape](reference-products.md);
- presentation-state **persistence design** — deliberately deferred
  (ADR-0009, [rendering.md](../../contracts/rendering.md)).

## Boundary with Issue #70

Issue #69 and Issue #70 are deliberately distinct:

| Issue #69 decides (this document) | Issue #70 decides/evaluates |
|---|---|
| user interaction | which libraries/frameworks can supply those capabilities |
| workspace responsibilities | build vs reuse |
| discoverability | canvas implementation choice |
| contextual behaviour | UI primitives |
| state semantics from the UX perspective | workspace/docking technology |
| required capabilities | layout/routing reuse |
| | dependency/provenance decisions |

Candidates such as Vue Flow, Reka UI, shadcn-vue, Dockview, Monaco, or ELK are
**Issue #70 candidates**, named here only where a capability must be described.
They are not selected, compared, or committed to by this document, and no
dependency is added.

## ADR threshold

No ADR is created by Issue #69. The candidate statements below are already
established by existing authority, so a new ADR would duplicate it:

| Candidate durable rule | Already owned by |
|---|---|
| UI interactions mutate semantic state only through application commands | [ADR-0002](../decisions/ADR-0002-semantic-model-is-the-core.md) (semantic model is the core; consumers depend on it) |
| canvas/framework state is never canonical engineering state | [ADR-0003](../decisions/ADR-0003-separate-semantic-and-presentation-models.md) |
| PFD and P&ID are editor views, not global application modes | [product.md](../planning/product.md) ("PFD and P&ID Are Views, Not the Product Core"); [ADR-0002](../decisions/ADR-0002-semantic-model-is-the-core.md) |
| process ↔ physical realization is a separate cross-layer concern | [ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md) |

This document therefore **applies** those rules rather than re-deciding them. A
new ADR would clear the threshold only if a future slice established a durable
rule not already owned above (for example, a decided persistence shape for
presentation state, which today is explicitly deferred).

## Core interaction principle

```text
Maximum engineering capability,
minimum permanent UI.

DeepPlant is:
    canvas-first
    context-sensitive
    command-driven
```

The application exposes functionality through three interaction layers that all
operate on the same underlying application commands and the same semantic model:

```text
1. Direct manipulation      click · drag · connect · inspect
2. Commands                 keyboard · search · command palette
3. Copilot                  natural language · images · documents · model context  (future)
```

The UI must read as **one coherent engineering application**, not as:

```text
a YAML editor
  + a graph widget
  + a property form
  + an AI chat
```

assembled as unrelated tools. The unifying mechanism is that every layer emits
the same conceptual application commands.

## Semantic source-of-truth direction

Every interaction follows exactly one direction:

```text
user interaction
        ↓
application command
        ↓
semantic model mutation
        ↓
validation
        ↓
updated projection / view
```

The drawing is a **view**. The semantic model remains authoritative. Two
inversions are explicitly rejected:

```text
REJECTED:  canvas/framework state → serialized as project truth
REJECTED:  SVG mutation → infer engineering semantics afterward
```

Practical consequences:

- Moving a symbol on the canvas is a **presentation** mutation, not a change to
  `ProcessStep`, `Equipment`, or `Connection`.
- Creating a stream between two process ports is a **semantic** command that
  produces a `ProcessStream`; the visible line is a rendering of that stream.
- Editing YAML directly is a serialization-boundary edit, not a second mental
  model; the YAML surface is optional and never primary.

## Four kinds of state

The UX must keep four state kinds explicitly separate:

```text
semantic engineering state
    !=
persistent presentation state
    !=
frontend / framework state
    !=
transient UI state
```

Only **semantic engineering state** is canonical project truth today. The other
three must never be confused with it.

### Semantic engineering state

Canonical, authored, loadable from YAML, validated by the model contracts
([plant-model.md](../../contracts/plant-model.md),
[process-model.md](../../contracts/process-model.md),
[physical-piping.md](../../contracts/physical-piping.md)). Examples:

```text
ProcessStep     id, function, name, ports
ProcessStream   id, name, source, target      (process edge)
Equipment       id, type, name, ports
Port            id
Connection      id, source, target            (directed physical adjacency)
PipingLine / PipingSegment / PipingRealization
```

Future process ↔ physical realization relationships (ADR-0016) would also be
semantic — but they have **no schema yet** and are never implied here as existing
fields.

### Persistent presentation state

State that describes **how** a semantic object is drawn in a view, saved
separately from semantic YAML. Per ADR-0003 and [rendering.md](../../contracts/rendering.md),
its persistence is **deliberately deferred**, so every candidate below is
classified rather than assumed:

| Concern | Disposition | Why |
|---|---|---|
| diagram object position (a symbol's x/y on a sheet) | **candidate for later** | Useful and edit-time meaningful, but no persistence format exists yet; may at first be recomputed by layout (as the current renderer does). |
| view/sheet membership (which objects appear on PFD-001) | **candidate for later** | Needed once multiple sheets are real; the MVP may derive one bounded view per submodel. |
| label placement | **transient only** for MVP | Current renderer computes label geometry; no authored placement exists. |
| route hints / waypoints | **candidate for later** | Current renderer derives orthogonal routes; manual waypoints are a later routing tool. |
| chosen presentation symbol role / variant per step | **transient only** today, candidate for later | Exists only at the render boundary as a per-call override (ADR-0009); persistence is explicitly deferred. |

The rule is unconditional regardless of disposition: **none of these is a field
on a semantic object.**

### Framework state

State owned by a UI framework or canvas library. Examples:

```text
canvas node objects / node ids
canvas edge objects
component instances
dock-panel objects
reactive stores holding rendered items
```

Framework state must **never** become canonical engineering state. The mapping
framework-object → semantic object is one-directional:

```text
framework node != ProcessStep / Equipment
framework edge != ProcessStream / Connection / PipingRealization
framework state != semantic state
```

### Transient UI state

State that describes the current interaction and is normally not project data at
all:

```text
selection
hover
zoom / pan viewport
open menu / open palette
temporary connection preview (rubber band)
active command / current tool
```

Transient UI state is expected to be lost on reload without harming the project.

## Default workspace

The canvas dominates normal engineering work. The default desktop workspace
(wireframe A, low fidelity) is:

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ DeepPlant   demo — Realistic Process Fragment    Valid   ⌘K Commands   AI │
├────────────────┬────────────────────────────────────┬────────────────────┤
│ EXPLORER       │ [PFD-001] [P&ID-001]               │ INSPECTOR          │
│                │                                     │                    │
│ ▾ Process      │                                     │ (no selection)     │
│    PFD-001     │                                     │                    │
│ ▾ Physical     │               CANVAS                │ Selection-driven.  │
│    P&ID-001    │                                     │ Collapsible.       │
│ ▾ Equipment    │                                     │                    │
│ ▾ Streams      │                                     │                    │
│ ▾ Piping       │                                     │                    │
│ ▾ Views        │                                     │                    │
│                │                                     │                    │
├────────────────┴────────────────────────────────────┴────────────────────┤
│ Problems    ✓ 0 errors    ⚠ 3 warnings                        ▲ expand   │
└──────────────────────────────────────────────────────────────────────────┘
```

The Issue #69 sketch proposed this structure as a hypothesis; it is retained
only where each region answers the ownership question below. Regions are **not**
preserved merely because the sketch contained them.

| Region | Why must this remain visible? | Can it collapse? | What replaces it when hidden? | Owns | Must NOT own |
|---|---|---|---|---|---|
| Top bar | Project identity, global validity, and the command entry point are the only truly global facts. | No (minimal; stays one line) | — | project name/path, global validity indicator, command entry (`⌘K`), Copilot entry point | per-object properties, tool palettes, mode switches |
| EXPLORER (left) | Cheap orientation and navigation; helps discovery without a toolbar. | Yes | command palette `Go to…` / search | engineering navigation (Process/Physical/Equipment/Streams/Piping/Views) | raw filesystem tree as the primary model; properties; editing |
| Editor tabs | PFD/P&ID must be distinguishable, closable **views**. | N/A (per-open-view) | explorer "Views" node re-opens them | which views are open and active | application-wide mode; canonical data |
| CANVAS (centre) | The primary working surface; engineering work is spatial. | No (it is the work) | — | the current view's projection + direct manipulation | canonical semantics; framework state as truth |
| INSPECTOR (right) | Selection-driven understanding of the semantic model. | Yes | command palette `Inspect…`; double-click to increase context | selected object's identity, semantic properties, validation, related navigation | framework fields (`x`, `y`, `nodeType`); mass-editing UI |
| Problems (bottom) | Validation must be visible without interrupting work. | Yes (collapses to a status chip) | top-bar validity indicator opens it | diagnostics list + navigation | modal blocking dialogs; runtime validation internals |

A region earns permanent space only if hiding it loses a global fact or breaks a
discoverable path. The explorer and inspector are therefore **compact and
collapsible** by default; the Problems strip collapses to a status chip in the
top bar.

## Permanent vs contextual vs command-only

| Capability | Permanent | Contextual | Command-only acceptable | Notes |
|---|---:|---:|---:|---|
| canvas | yes | — | no | primary workspace |
| editor tabs (PFD/P&ID) | yes (open views) | — | no | views, not modes |
| project navigation (explorer) | compact | yes | yes | collapsible; command palette can replace it |
| properties (inspector) | no (compact) | yes | yes | selection-driven; hidden when nothing is selected |
| add object | no | yes | yes | search-driven; no permanent palette |
| validation summary | compact | yes | yes | no routine modals |
| command palette | no | yes | yes | first-class discovery, opened on demand |
| symbol catalogue | no | yes | yes | never a huge permanent palette |
| Copilot | no | yes | yes | future layer; entry point only |
| YAML view | no | yes | yes | secondary surface, not the mental model |
| Problems detail | no (chip permanent) | yes | yes | expands on demand / on error |

**MVP interaction model:** permanence is limited to the canvas, the open-view
tabs, a compact explorer, a compact inspector, and a validity chip. Everything
else is contextual, search-driven, or command-only.

## Engineering Explorer

The explorer exposes **engineering concepts**, not the filesystem. File paths and
YAML are available but do not define the primary mental model. The explorer has
two top-level halves:

```text
ENGINEERING MODEL                    VIEWS
▾ Process                            ▾ Process views (PFD)
   · PS-feed   (source)                 · PFD-001
   · PS-mix    (mixing)              ▾ Physical views (P&ID)
   · PS-pump   (pumping)                · P&ID-001
   · ...                             ...
▾ Physical
   ▾ Equipment
      · P-101   (pump)
      · FV-101  (control-valve)
   ▾ Connections
      · C-001   P-101.discharge → FV-101.inlet
▾ Piping
   ▾ PL-P101-DISCHARGE
      ▾ SEG-1
         · C-001 (pipe)
         · C-002 (pipe)
```

> **Deliberate correction to the Issue sketch.** The sketch showed `Process >
> PFD-001` and `Physical > P&ID-001`. A `ProcessModel` in DeepPlant owns the
> `ProcessStep`/`ProcessStream` objects; a **PFD is a derived view** over that
> model, not a container of canonical process objects (see
> [process-model.md](../../contracts/process-model.md) and
> [product.md](../planning/product.md)). Nesting `PFD-001` under `Process` would
> imply that a view owns the process graph, which reverses ownership. Views are
> therefore a **separate top-level half**, and the engineering model is grouped by
> semantic layer.

The explorer must **not** invent hierarchy the model does not have:

- Do **not** nest `Equipment` inside `ProcessStep` (or the reverse). The realistic
  fragment proves a process step with no equipment (`PS-mix`, `PS-split`) and
  equipment with no process step (`FV-101`).
- Do **not** nest `ProcessStream` under `Connection`, or vice versa; process and
  physical connectivity are separate layers
  ([process-model.md](../../contracts/process-model.md),
  [plant-model.md](../../contracts/plant-model.md)).
- Do **not** group `ProcessStep` under `PipingLine`; piping realizes physical
  `Connection`s, not process steps ([physical-piping.md](../../contracts/physical-piping.md)).

Responsibilities:

| Question | Answer |
|---|---|
| What is navigable? | every semantic object (`ProcessStep`, `ProcessStream`, `Equipment`, `Port`, `Connection`, `PipingLine`, `PipingSegment`, `PipingRealization`) and every **view** (PFD/P&ID). |
| What is hierarchical? | only real containment: `PlantModel → ProcessModel → ProcessStep → ProcessPort`; `PlantModel → Equipment → Port`; `PlantModel → PipingModel → PipingLine → PipingSegment → PipingRealization`. `Connection` and `ProcessStream` are flat, identified lists. |
| What is a filtered projection? | `Streams` (a flat filter of `ProcessStream`), `Equipment` (all `Equipment`), and every search result. Filters change grouping, never ownership. |
| What opens an editor? | a **View** node opens (or focuses) a PFD/P&ID editor tab. Selecting a semantic object does not open a separate editor; it selects the object and reveals it in a compatible open view. |
| What selects an object? | clicking an explorer entry selects that semantic object globally (see [Select once, inspect everywhere](#select-once-inspect-everywhere)). |
| What belongs only in search? | rarely used types, objects without a natural position in the tree, and cross-cutting queries (e.g. "every pumping step"). |

## PFD and P&ID editor tabs

PFD and P&ID are **editor views**, not application-wide modes:

```text
[PFD-001] [P&ID-001]
```

There is no global "PFD mode" versus "P&ID mode". Switching a tab changes the
projection, not the application state, the toolset, or the selection model.

| Behaviour | Decision |
|---|---|
| opening | a View node in the explorer, or `Open view…` in the command palette, opens (or focuses) the tab. Opening does not mutate the model. |
| closing | closing a tab is a **transient UI** action; it removes a projection, never semantic or persistent data. |
| tab identity | a tab is identified by a **view** (its sheet id, e.g. `PFD-001`), not by a semantic object and not by a framework view instance. |
| selection behaviour | selecting an object in a tab selects the **semantic object** globally; the same object selected in another tab is the same selection, not a second one. |
| unsaved-state indication | "unsaved" is a **project-level** fact (the model has commands not yet saved), not a per-tab document fact, because several views project one model. The top bar shows the project dirty flag; affected tabs may show a subtle marker. It is **not** a second copy of state. |
| fit-to-view behaviour | `Fit view` is a **transient UI** (viewport) action scoped to the active tab; it never changes presentation or semantic state. |
| navigation from diagnostics | selecting a diagnostic opens/focuses the relevant view, reveals the object, selects it, and focuses the relevant inspector context (see [Problems / validation UX](#problems--validation-ux)). |
| navigation from related objects | `Open related …` reveals a related object in a compatible view when the relationship exists; where the relationship is not authored, the action is absent or explains the absence (see [Related-object navigation](#related-object-navigation-and-adr-0016)). |

### Split view

A future split view is a **target interaction**, not required for the first
executable slice:

```text
┌─────────────────────┬─────────────────────┐
│ PFD-001             │ P&ID-001            │
│                     │                     │
│ selected process    │ related physical    │
│ object              │ objects             │
└─────────────────────┴─────────────────────┘
```

Cross-highlighting between related process and physical objects is desirable, but
the first slice must not depend on it: it needs the cross-layer related-object
navigation (which requires the future realization layer) to be meaningful, and
that layer is unimplemented (ADR-0016). Split view is therefore listed under
[Later](#mvp-vs-later-vs-explicitly-not-now), and the MVP uses single-view tabs
plus related-object navigation that honestly reports "no authored realization".

## Select once, inspect everywhere

The principle:

> **Select once, inspect everywhere.**

A selected **semantic object** may expose:

```text
properties
validation state
current view representation
related views
YAML / source location
future Git / diff context
future process ↔ physical relations
```

These must not appear to the user as unrelated copies. Three different things
must nevertheless stay distinct:

```text
semantic identity        the engineering object (ProcessStep / Equipment / ...)
view representation      how that object appears in one view (a symbol, a line, a row)
current UI selection     the transient fact that the user selected it now
```

Only semantic identity is canonical. A **view representation is a projection** of
it (ADR-0003), and the current UI selection is transient UI state.

Selection propagation rules:

| Situation | Rule |
|---|---|
| one semantic object, one representation | selecting either the canvas representation or the explorer entry selects the same semantic object; both highlight. |
| one semantic object, several view representations | all representations of that object in **open** views highlight together; selecting any one selects the same object. There is still exactly one selection. |
| object has no representation in the current view | the object can still be selected (for example from the explorer or a diagnostic); the active view shows an honest "not shown in this view" state instead of inventing a symbol. |
| a relation points to multiple physical facts | selecting the *relation subject* does not silently select one of several facts; the inspector lists them (see [Related-object navigation](#related-object-navigation-and-adr-0016)). |

The long-term extension is stated but not required now:

> **Change once, update every affected view.**

That extension is a consequence of the semantic source-of-truth direction: a
semantic command re-projects every open view. The first slice needs only that a
change re-projects the views it can honestly re-project.

## Related-object navigation and ADR-0016

[ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md) decides
that process ↔ physical realization relationships belong to a **separate
cross-layer realization layer**, but **no mapping schema exists yet**. The UX may
therefore offer conceptual navigation actions:

```text
Show physical realization
Open related P&ID
Show related process intent
```

but must **not** imply an implementation shape such as:

```text
ProcessStep.realized_by
Equipment.process_step
mandatory 1:1 correspondence
```

Cardinality is deliberately not assumed. The realistic fragment proves all of
these are valid simultaneously:

```text
ProcessStep may have no Equipment
Equipment may have no ProcessStep
ProcessStream may have no authored physical route
one ProcessStream may span multiple physical realization facts
ProcessPort's exact physical target remains unresolved
```

Wireframes and inspector examples must reflect that. Misleading fixed labels such
as `Equipment: P-101` are avoided. The inspector instead shows a **Related
realization** group whose content is honest about what is authored:

```text
Related realization
───────────────────
Physical realization
P-101
[Open in P&ID]

Related realization
───────────────────
No authored physical realization

Related realization
───────────────────
2 related physical objects
[Inspect]
```

Rules for cross-view UX:

1. Related-object navigation is **read-only** in the MVP: it reveals and selects a
   related object; it never edits or fabricates a relationship.
2. It never encodes a cardinality. "0", "1", "many", and "not authored" are all
   presented explicitly rather than assumed.
3. It never invents a physical target for a `ProcessPort`; ADR-0016 explicitly
   leaves that boundary unresolved.
4. Until the realization layer exists, actions such as `Open related P&ID` are
   **enabled only when a defensible relationship can be shown**; otherwise the
   surface states that no authored realization exists.

## Properties Inspector

The inspector is **selection-driven**: with no selection it shows a neutral hint;
with a selection it shows grouped sections for the selected semantic object. It
never contains framework fields. The forbidden fields are explicit:

```text
x, y
sourceHandle, targetHandle
nodeType, edgeId
componentName
```

unless a field is **explicitly presentation state** (and even then it belongs to a
labelled *Presentation* group, never the engineering-semantic group).

Standard sections, in order:

```text
Identity            id, name (semantic identity)
<domain section>    the object's own semantic properties
Read-only context   derived/contextual facts (counts, endpoints, resolutions)
Validation          this object's diagnostics
Related             related-object navigation (honest, cardinality-neutral)
Presentation        only if applicable; explicitly presentation, not semantics
```

### `ProcessStep` (e.g. `PS-pump`)

```text
PS-pump
────────────────────────────
Identity
  ID        PS-pump          (editable)
  Name      Feed Pumping     (editable)
Process
  Function  pumping          (editable, open vocabulary; ADR-0009)
  Ports     suction, discharge   (read-only list; structural)
Read-only context
  Streams   3 incident streams (read-only, derived)
Validation
  ✓ no diagnostics           (from the model rules S1–S4)
Related
  Related realization
    No authored physical realization     (ADR-0016; cardinality-neutral)
Presentation
  (only if a persisted presentation state exists — today: none)
```

Note that `Function` is engineering semantics and is **not** the symbol role: the
inspector never shows `pump` as the step's function (ADR-0009). Where a
presentation override exists it appears under *Presentation*, labelled as such.

### `ProcessStream` (e.g. `S-004`)

```text
S-004
────────────────────────────
Identity
  ID        S-004            (editable)
  Name      Pump Discharge   (editable)
Process
  Source    PS-pump.discharge   (read-only; resolved endpoint)
  Target    PS-hx.in_side_A     (read-only; resolved endpoint)
Read-only context
  (no flow/thermodynamic/composition semantics exist)
Validation
  ✓ endpoints resolve (S3); source != target (S4)
Related
  Related physical route
    No authored physical route           (ADR-0016; cardinality-neutral)
```

A stream has **no** property field for pipe size, fluid, or route; those belong to
the physical/piping layer, not the process edge
([process-model.md](../../contracts/process-model.md)).

### `Equipment` (e.g. `P-101`)

```text
P-101
────────────────────────────
Identity
  ID        P-101            (editable)
  Name      Feed Pump        (editable)
Engineering
  Type      pump             (editable, open string; no fixed taxonomy)
  Ports     suction, discharge   (read-only list)
Read-only context
  Connections  C-001 (to FV-101.inlet)   (read-only, derived)
Validation
  ✓ no diagnostics           (reference rules)
Related
  Related process intent
    No authored process step             (ADR-0016; cardinality-neutral)
Presentation
  (none persisted today)
```

### `Connection` (e.g. `C-001`)

```text
C-001
────────────────────────────
Identity
  ID        C-001            (editable)
Topology
  Source    P-101.discharge  (read-only; resolves to Equipment + Port)
  Target    FV-101.inlet     (read-only)
Read-only context
  Realizations  1 (PipingRealization in SEG-1)   (read-only, derived)
Validation
  ✓ both endpoints resolve
Related
  Piping
    PL-P101-DISCHARGE / SEG-1            (physical, same-layer navigation)
```

A `Connection` is topology only: the inspector shows no flow, no fluid, and no
process meaning ([physical-piping.md](../../contracts/physical-piping.md)).

### `PipingLine` / `PipingSegment`

```text
PL-P101-DISCHARGE            SEG-1
────────────────────         ────────────────────
Identity                     Identity
  ID   PL-P101-DISCHARGE       ID   SEG-1
  No.  (optional, empty)       No.  (optional, empty)
Segments                     Engineering (optional, open strings)
  SEG-1                        Nominal diameter  (empty)
                               Piping class      (empty)
                               Fluid code        (empty)
                             Realizations
                               C-001 (pipe), C-002 (pipe)
                             Related
                               Connecting equipment (via C-001, C-002)
```

Optional property strings render as **empty**, never with invented values; the
realistic fragment deliberately carries none.

### No selection

```text
PROPERTIES
────────────────────────────
Nothing selected.

Select an object on the canvas, in the explorer,
or from Problems to inspect it.
```

### Multi-selection

```text
PROPERTIES
────────────────────────────
3 objects selected

Common        (sections shared by all)
  Type: ProcessStep
Validation    (aggregated diagnostics across the selection)
Related       (only relationships common to all selected objects)
Per object    expandable list → select one to inspect it alone
```

Multi-selection shows **common** semantics and an aggregated validation summary;
it does not invent a merged pseudo-object, and it never edits conflicting values
silently.

## Direct manipulation

Baseline canvas gestures and what each one mutates. This classification is a
**required deliverable**: it keeps gesture behaviour from accidentally becoming
semantic truth.

| Gesture | Mutates | Notes |
|---|---|---|
| click select | transient UI | sets selection only |
| Ctrl/Cmd click multi-select | transient UI | extends selection |
| box selection | transient UI | selects the enclosed representations |
| drag a semantic object's representation | **presentation** | moves the symbol, not the object; today no persisted position exists, so this is transient until presentation persistence is designed |
| pan | transient UI | viewport only |
| zoom | transient UI | viewport only |
| fit view | transient UI | viewport only |
| delete selection | **semantic** | a delete command removes the semantic object (with confirmation when it has dependents) |
| connection creation | **semantic** | emits a domain command (`ConnectProcessPorts` **or** `ConnectPhysicalPorts`) |
| connection reconnection | **semantic** | emits a domain command; where the model cannot express reconnection safely, the gesture is unavailable |
| context menu | transient UI | offers commands; the chosen command has its own mutation class |
| Escape cancel | transient UI | cancels the active command; no model change |
| undo | command history | reverses the last command's effect (semantic and/or presentation) |
| redo | command history | re-applies a reversed command |

The examples in the Issue map exactly:

```text
move symbol on canvas          → presentation mutation
connect two ProcessPorts       → semantic ProcessStream command
pan viewport                   → transient UI state
rename ProcessStep             → semantic mutation
```

Note the current reality: persisted presentation state does not exist yet
(ADR-0009, [rendering.md](../../contracts/rendering.md)), so "move a symbol" is
**transient** until a later slice designs presentation persistence. It is never a
semantic mutation in any case.

## Adding engineering objects

There is **no large always-visible symbol palette**. Insertion is searchable and
contextual. The critical teaching moment is that a process function and a
physical object are different things:

```text
ProcessStep(function="pumping")   !=   Equipment(type="pump")
```

The add UX must **teach** that distinction, not hide it. Searching "pump" groups
results by semantic domain:

```text
Add
──────────────────────────────────────
Search engineering objects…  > pump

Process
  Pumping
    → creates a ProcessStep with function "pumping"

Physical
  Pump (equipment)
    → creates an Equipment with type "pump"
```

Flows:

| Flow | Steps |
|---|---|
| keyboard | `A` opens Add → type → results grouped by domain → `Enter` accepts the highlighted result → place → semantic command executes. |
| mouse | click `+` in the top bar or the canvas hint → same search surface → click a result → place. |
| search-result grouping | always grouped by **semantic domain** (`Process` / `Physical` / later `Piping`), never by visual symbol only. |
| placement step | the accepted result is placed on the canvas; placement is a **presentation** act, the creation is a **semantic** command. |
| cancel behaviour | `Escape` (or closing the surface) cancels before placement; after placement, `Ctrl/Cmd+Z` undoes the creation command. |
| default naming/identity | the surface prompts for or pre-fills a **user-visible** id/name. DeepPlant does **not** invent automatic engineering ids: no auto-generated tag numbers or line numbers are created unless the model/product later justifies them (the current model requires authored, non-positional identity — see [plant-model.md](../../contracts/plant-model.md)). |

Until a value is committed, the creation command is not executed, so no
half-authored engineering object exists.

## Engineering connection interaction

Connections are engineering operations, not generic graph edges. Process and
physical authoring are **separate** operations and are never collapsed into one
generic `connect()`:

```text
ProcessStream creation      process layer, between ProcessPorts
physical Connection creation   physical layer, between Ports
```

The conceptual flow (shown here for a process stream):

```text
hover / select source                 (transient)
        ↓
show eligible connection points       (projection of the semantic model)
        ↓
start connection                      (transient preview / rubber band)
        ↓
highlight possible targets            (only what the model can honestly allow)
        ↓
choose target                         (transient)
        ↓
application command                   (ConnectProcessPorts)
        ↓
semantic validation                   (S3 / S4 for streams; reference rules for connections)
        ↓
view update                           (re-projected)
```

Branch behaviour:

| Case | Behaviour |
|---|---|
| target is invalid | the invalid target is not offered as a candidate; if the model cannot decide validity, the candidate is offered but validated at command time and rejected with a clear message. |
| validation needs more context | the command commits the model change, and the resulting diagnostic appears non-modally in Problems (see below); the editor never blocks with a modal for a rule it cannot decide up-front. |
| connection is cancelled | `Escape` clears the preview and selects nothing; no command is emitted. |
| existing connection is selected | it opens the inspector for that `ProcessStream`/`Connection`; it does not start a new connection. |

Compatibility is **not invented**. Where the core cannot yet determine
compatibility (for example, whether two `ProcessPort`s are physically realizable,
or any process ↔ physical relation), the surface says so rather than guessing:

```text
This relation cannot be authored yet (no mapping schema exists — ADR-0016).
```

## Command architecture from the UX perspective

Issue #69 owns the **interaction requirement** for commands; Issue #70 may later
decide implementation/library choices. Direct manipulation, the command palette,
keyboard shortcuts, and a future Copilot all funnel into **one** conceptual
command surface:

```text
AddProcessStep            DeleteProcessStep        ConnectProcessPorts
AddEquipment              DeleteEquipment          ConnectPhysicalPorts
UpdateProperty            MovePresentationObject
ValidateProject           OpenView                 RevealObject
```

These are **conceptual interaction commands**, not a frozen Python/TypeScript API
and not an implementation. This document does not define class names, wire
formats, or payloads.

Rules:

- The command surface is the **only** mutation path for all three interaction
  layers. There is no second path such as an AI rewriting project YAML directly.
- A command states the engineering intent; the model validates it; the view
  re-projects.
- A cross-layer realization action, if shown at all, is described generically:

  ```text
  Create / edit process ↔ physical realization   (implementation deferred)
  ```

  It must **not** be written as `MapProcessRealization(...)` or any name that
  pretends a schema exists — ADR-0016 provides an ownership boundary only.

The shared command surface is what makes the following possible across all
layers: validation, undo/redo, change preview, auditability, Git diff, and human
approval.

## Command palette

A searchable command interface is first-class discovery, opened on demand
(never permanent chrome). It is the primary path to functionality that does not
deserve a permanent control.

MVP commands (**available now in the MVP UX**):

```text
navigation      Go to object…          Open view…
creation        Add process object…   Add equipment…
editing         Rename…               Delete selection
validation      Validate project
view            Fit view              Reveal selection
project         Save project
```

Future, discoverable commands (**clearly labelled future** — not shown as
available):

```text
future          Show physical realization        (needs ADR-0016 realization layer)
future          Export DEXPI                     (adapter not implemented)
future          Open Copilot                     (future interaction layer)
```

Command palette behaviour: it searches commands **and** objects; it never
executes something the current model cannot honestly support, and where a command
depends on an unimplemented capability it is either hidden or clearly marked
future. Category grouping is `navigation`, `creation`, `editing`, `validation`,
`view`, `project`, and later `adapters/export`.

## Keyboard-first without keyboard-only

Keyboard accelerates, but every important capability stays **mouse-discoverable
and accessibility-compatible**. A minimal philosophy:

| Key | Intent (indicative, not locked) |
|---|---|
| `A` | Add / search object |
| `Ctrl/Cmd+K` (or equivalent) | command palette |
| `Delete` | delete selection |
| `Esc` | cancel current action |
| `Ctrl/Cmd+Z` | undo |
| `Ctrl/Cmd+Shift+Z` | redo |
| `F` | fit / reveal selection |

Exact shortcuts are **not locked** here; they are a decision for the first GUI
slice because shortcut conventions depend on the chosen UI technology (Issue
#70). The durable requirement is that no capability exists **only** on a
keyboard shortcut.

## Problems / validation UX

Validation is surfaced **non-modally**. Routine validation never opens a blocking
dialog. The Problems surface is a strip/chip that expands on demand or on a new
error.

Only **real current validations** are shown as current; anything else is clearly
labelled future. Today the model is fail-fast and its diagnostics are **errors**
(there is no warning severity yet):

```text
Problems
────────
✕ connections[2].target: unknown component 'FV-999'
✕ connections[2].target: component 'FV-101' has no port 'in'
✕ process.streams[3]: source and target must not be identical   (S4)
✕ piping.lines[0].segments[0].realizations[1]: connection 'C-009' not found   (P3)
```

Clearly labelled **future** examples (not implemented — shown to fix the target
shape, not to claim behaviour):

```text
future  ⚠ incomplete physical realization
future  ⚠ missing optional/required engineering information
```

Presentation model:

| Aspect | Decision |
|---|---|
| error vs warning | errors block the project from being considered valid; warnings are advisory. **Only errors exist today**; the warning severity is a future concept. |
| global validity indicator | the top bar shows a compact validity chip (`Valid` / `N errors`). It is always visible; the detailed list is not. |
| empty Problems state | shows a calm confirmation (`✓ 0 errors`) rather than an empty panel. |
| validation refresh model | validation runs on load and after each command re-validates the affected scope; the Problems list and validity chip update from the result. This document does not design runtime validation internals. |

Navigation from a diagnostic:

```text
select diagnostic
        ↓
open relevant view
        ↓
reveal object
        ↓
select it
        ↓
show relevant inspector context
```

Diagnostics are **selectable objects** that navigate; they are not a dead-end
text list.

## Undo / redo UX requirements

Issue #69 defines expected **user behaviour**, not implementation. Both

```text
semantic edit
presentation edit
```

should eventually participate in a coherent, user-facing undo history where
feasible, so the user has one mental "undo" rather than several unrelated ones.

This document does **not** choose an undo library, an event-sourcing
architecture, or a command implementation. It records the requirement and the
open question:

- Undo must reverse the *user-visible effect* of a command (semantic and/or
  presentation), not an incidental framework side effect.
- Where a single user action mixes semantic and presentation effects
  (for example, delete-object-and-its-placement), a **single** undo step should
  ideally restore both. Whether that is achievable with the chosen architecture
  is an open question for the first GUI slice and Issue #70.

## Copilot UX boundary

Copilot is a first-class **future interaction layer**, not an MVP AI
implementation. It lives **contextual / command-accessible** rather than as a
permanent large chat panel:

```text
contextual / command-accessible   ✓
permanent large chat panel        ✗
```

The future Copilot should receive relevant context:

```text
current project
active view
selection
validation diagnostics
semantic model
attached engineering material
```

but it must **not** silently rewrite project files. Its interaction reuses the
same path as human editing:

```text
user intent
      ↓
Copilot proposes engineering operations
      ↓
preview
      ↓
validate
      ↓
human Apply / Reject
```

Copilot must use the **same conceptual application-command path** as human
interaction (see [Command architecture](#command-architecture-from-the-ux-perspective)).
It never gets a second mutation path such as editing YAML directly.

Issue #69 does **not** implement:

```text
LLM backend
prompt infrastructure
agent runtime
API keys
chat persistence
```

### MVP Copilot placeholder decision

**Decision: defer the MVP Copilot placeholder.** No permanent `◇ Copilot` control
is added in the MVP.

Rationale:

- The core principle is **minimum permanent UI**; a non-functional entry point
  consumes permanent top-bar space for no current capability.
- A placeholder that only says "AI-assisted engineering is planned" is close to
  the "dead decorative control without purpose" the issue warns against, and a
  permanent `AI` affordance in a validation/engineering header can imply a
  capability that does not exist.
- The Copilot **boundary is preserved architecturally** without a permanent
  control: Copilot is defined as a future layer that shares the command surface,
  so nothing about the layout or command model needs to change to introduce it.

If a discovery affordance is later wanted before a real Copilot exists, the
command-only form is acceptable and adds no permanent chrome:

```text
Command palette → "Copilot (future)…"   →  informational surface, clearly labelled future
```

This keeps the interaction concept and the command boundary without shipping a
dead control.

## External UX references studied

Publicly accessible primary documentation was inspected on **2026-10-03** for
interaction **patterns**, not for visual copying. No screenshots, icons, assets,
or proprietary UI resources are imported into the repository.

### VS Code — official user-interface documentation

- **Source:** <https://code.visualstudio.com/docs/getstarted/userinterface>
  (inspected 2026-10-03).
- **Patterns observed:** a central editor dominant over the window; a collapsible
  primary side bar and a secondary side bar; editor **tabs/groups** that can be
  split; a non-modal **Problems** view; a **Command Palette** as the primary
  discovery mechanism for commands that do not deserve permanent chrome;
  context-sensitive secondary panels; a status bar carrying global state.
- **Relevant because:** it is the closest available model of a "modern engineering
  IDE" workspace, exactly the reference the Issue names.
- **Reuse conceptually:** editor-dominant layout; collapsible primary/secondary
  side bars; tabs with split as a later enhancement; Command Palette as
  first-class discovery; non-modal Problems; a compact global validity indicator.
- **Deliberately not copy:** the file-system tree as the primary explorer mental
  model (DeepPlant's explorer is engineering-concept-first); the very large
  extension/marketplace surface; settings/profiles complexity; treating files as
  the product core.

### KiCad — Schematic Editor manual

- **Source:** <https://docs.kicad.org/8.0/en/eeschema/eeschema.html>
  (inspected 2026-10-03).
- **Patterns observed:** canvas-first editing; selection and multi-select on the
  canvas; placement tools and object property editing; connection/wire creation
  by drawing between points; hierarchical sheets and navigation between them;
  cross-probing between views; a distinct **Electrical Rules Check** surface with
  navigable violations; extensive keyboard hotkeys; context menus on objects.
- **Relevant because:** it is a mature **engineering schematic editor** whose
  canvas-first interaction and rules-check navigation map directly onto DeepPlant's
  PFD/P&ID target.
- **Reuse conceptually:** canvas-first selection/placement; draw-to-connect;
  hierarchical navigation; a navigable rules-check surface (DeepPlant's Problems);
  context menus; keyboard accelerators.
- **Deliberately not copy:** a permanently dense symbol/tool palette and toolbar
  rows; electrical-specific semantics (nets, netclasses, ERC) as the interaction
  grammar; multiple persistent palettes; the assumption that the schematic file is
  the source of truth (DeepPlant's semantic model is).

### Figma — Layers panel and property editing help

- **Source:** <https://help.figma.com/hc/en-us/articles/360039956914-View-and-navigate-layers-in-the-Layers-panel>
  (inspected 2026-10-03).
- **Patterns observed:** selection synchronizes between canvas and a
  layers/objects list; a right-side properties panel whose content is driven by
  the current selection; multi-selection producing a "mixed"/common view;
  precise numeric property editing with scrub interactions.
- **Relevant because:** it is the reference the Issue names for
  **context-sensitive interaction** — the inspector is exactly a
  selection-driven property surface.
- **Reuse conceptually:** selection-driven inspector; canvas↔list selection
  synchronization; multi-selection common-value view; precise editing of numeric
  values.
- **Deliberately not copy:** a graphics-first layer tree as the **engineering**
  model (DeepPlant's tree is semantic, not z-order/group hierarchy); the
  heavy graphics authoring vocabulary (fills, effects, strokes) that has no
  engineering meaning; pixel/frame-centric concepts.

### IPD Studio

- **Source:** <https://www.ipdstudio.com/> (inspected 2026-10-03).
- **Finding:** the publicly accessible site inspected does **not** present a
  process-engineering editor UX; it is not usable as interaction evidence, and its
  current status as a close-domain reference is already recorded as rejected in
  [standards-licensing-evidence.md](standards-licensing-evidence.md).
- **Reuse conceptually:** none (insufficient evidence).
- **Deliberately not copy:** nothing is adopted from it.

Pattern categories retained across references: workspace organization, command
discovery, property inspection, canvas interactions, diagnostics surface,
multi-view navigation, object insertion, contextual actions, keyboard
interaction, and UI density.

## Low-fidelity wireframes

These guide the first GUI slice. They are intentionally approximate; they fix
behaviour and ownership, not pixels. Wireframe **A** (default workspace) is above;
**B–H** follow.

### B. Process / PFD object selected

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ DeepPlant   demo — Realistic Process Fragment    Valid   ⌘K Commands      │
├────────────────┬────────────────────────────────────┬────────────────────┤
│ EXPLORER       │ [PFD-001] [P&ID-001]               │ INSPECTOR          │
│ ▾ Process      │          ┌─────────┐               │ PS-pump            │
│   · PS-feed    │  S-003 ─▶│ PS-pump │─▶ S-004       │ ─────────────────  │
│   · PS-mix     │          └─────────┘               │ Identity           │
│ ▸ PS-pump  ◀───│        ▲ selected (highlighted)    │   ID    PS-pump    │
│   · PS-hx      │                                    │   Name  Feed Pumping│
│ ▾ Physical     │                                    │ Process            │
│   · P-101      │                                    │   Function  pumping│
│                │                                    │ Related realization│
│                │                                    │   No authored ...  │
├────────────────┴────────────────────────────────────┴────────────────────┤
│ Problems   ✓ 0 errors                                             ▲       │
└──────────────────────────────────────────────────────────────────────────┘
```

### C. Physical / P&ID object selected

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ DeepPlant   demo — Realistic Process Fragment    Valid   ⌘K Commands      │
├────────────────┬────────────────────────────────────┬────────────────────┤
│ EXPLORER       │ [PFD-001] [P&ID-001]               │ INSPECTOR          │
│ ▾ Physical     │   ┌───────┐        ┌────────┐      │ P-101              │
│  ▾ Equipment   │   │ P-101 │─C-001─▶│ FV-101 │      │ ─────────────────  │
│    · P-101 ◀───│   └───────┘        └────────┘      │ Identity           │
│    · FV-101    │        ▲ selected (highlighted)    │   ID    P-101      │
│  ▾ Connections │                                    │   Name  Feed Pump  │
│    · C-001     │                                    │ Engineering        │
│ ▾ Piping       │                                    │   Type  pump       │
│    · PL-P101…  │                                    │ Related process    │
│                │                                    │   No authored step │
├────────────────┴────────────────────────────────────┴────────────────────┤
│ Problems   ✓ 0 errors                                             ▲       │
└──────────────────────────────────────────────────────────────────────────┘
```

### D. Add / search flow

```text
┌───────────────────────────────────────────────┐
│ Add                                      Esc  │
├───────────────────────────────────────────────┤
│ Search engineering objects…   pump            │
│                                               │
│ Process                                       │
│   ▸ Pumping              → ProcessStep        │
│ Physical                                      │
│   ▸ Pump (equipment)     → Equipment          │
│                                               │
│ ↑/↓ choose · Enter accept · Esc cancel        │
└───────────────────────────────────────────────┘
```

### E. Connection creation

```text
┌───────────────────────────────────────────────────────────┐
│ [PFD-001]                                                 │
│                                                           │
│   ┌─────────┐                    ┌─────────┐              │
│   │ PS-pump │                    │  PS-hx  │              │
│   └────○────┘                    └────○────┘              │
│     discharge                    in_side_A               │
│        │                                                  │
│        └───────── preview ─────────▶ (candidate target)  │
│                                                           │
│  Drag from PS-pump.discharge                             │
│  Eligible targets highlighted · others dimmed            │
│  Release on target → ConnectProcessPorts → validate      │
│  Esc → cancel (no command)                               │
└───────────────────────────────────────────────────────────┘
```

### F. Problems navigation

```text
┌───────────────────────────────────────────────────────────────────────┐
│ Problems                                                    ▲ collapse │
├───────────────────────────────────────────────────────────────────────┤
│ ✕ connections[2].target: component 'FV-101' has no port 'in'  ▶ reveal │
│ ✕ process.streams[3]: source and target must not be identical ▶ reveal │
└───────────────────────────────────────────────────────────────────────┘
   ▲ select → open P&ID → reveal object → select → inspector context
```

### G. Command palette

```text
┌───────────────────────────────────────────────┐
│ ⌘K  Command palette                      Esc  │
├───────────────────────────────────────────────┤
│ > fit                                         │
│                                               │
│ View                                          │
│   ▸ Fit view                                  │
│   ▸ Reveal selection                          │
│ Navigation                                    │
│   ▸ Go to object…                             │
│   ▸ Open view…                                │
│                                               │
│ Future commands are labelled "future"         │
│ (Show physical realization, Export DEXPI)     │
└───────────────────────────────────────────────┘
```

### H. Process ↔ physical related-object navigation

```text
INSPECTOR — PS-pump              INSPECTOR — PS-pump
──────────────────────────────   ──────────────────────────────
Related                          Related
  Related realization              Related realization
  ───────────────────              ───────────────────
  No authored physical             2 related physical objects
  realization                      [ Inspect ]
  [ Create / edit realization ]
    (future — disabled)


INSPECTOR — PS-pump
──────────────────────────────
Related
  Related realization
  ───────────────────
  Physical realization
  P-101
  [ Open in P&ID ]
```

All three shapes are valid simultaneously in one project; none implies a fixed
cardinality, and none invents a `ProcessPort` physical target.

## Interaction-state walkthroughs

Each walkthrough uses only behaviour current semantics can honestly support, with
future-only steps labelled.

### Walkthrough A — inspect an existing process object

```text
1. Open project            → loads PlantModel (semantic state)
2. Open PFD-001            → projection appears (view, not mode)
3. Select PS-pump on canvas→ transient selection of the semantic ProcessStep
4. Inspector shows         → Identity (PS-pump), Process (function: pumping)
5. Inspector Validation    → ✓ no diagnostics
6. Inspector Related       → "Related realization: no authored physical
                              realization" (ADR-0016, cardinality-neutral)
7. (future) if a realization existed → [Open in P&ID] reveals & selects it
```

### Walkthrough B — add a process object

```text
1. Press A                 → Add surface opens (transient)
2. Type "pump"             → results grouped by semantic domain
3. Choose Process / Pumping→ intent = create ProcessStep(function="pumping")
4. Place on canvas         → placement is presentation; the semantic command
                             AddProcessStep runs and requires an authored id
5. Validation              → S1 (unique step id) + S3/S4 for its streams
6. Inspector               → shows the new PS-* step, its function, and
                             "no authored physical realization"
7. Ctrl/Cmd+Z              → undoes the creation command as one step
```

### Walkthrough C — create a ProcessStream

```text
1. Select PS-pump.discharge   → shows eligible connection points
2. Start connection           → transient preview
3. Highlight valid targets    → only what the model can honestly allow
4. Choose PS-hx.in_side_A     → transient target choice
5. Application command        → ConnectProcessPorts(source, target)
6. Semantic validation        → S3 (endpoints resolve), S4 (source != target)
7. Projection updates         → S-* stream line appears in the PFD
8. Cancel earlier (Esc)       → no command, no model change
```

### Walkthrough D — diagnose an error

```text
1. Problems shows an error  → e.g. "component 'FV-101' has no port 'in'"
2. Select the diagnostic    → navigation begins
3. Correct editor opens     → the view that can show the failing object
4. Object revealed + selected→ transient selection; inspector focuses context
5. Fix: add the port / correct the reference → semantic command
6. Re-validate              → the diagnostic clears; validity chip returns "Valid"
```

Future-only steps (for example, navigating to a *physical realization* that does
not exist yet) are not implied by these walkthroughs; they appear only where the
model can honestly support them.

## MVP vs later vs explicitly not now

This matrix is UX scope guidance, **not an implementation authorization**. It
keeps the MVP intentionally small.

### MVP UX

```text
canvas
selection (single + multi)
pan / zoom / fit view
basic engineering explorer (concept-first, collapsible)
basic selection-driven inspector
basic Problems surface + global validity chip
basic command / search surface (palette + Add)
PFD / P&ID editor tabs
semantic create / edit / delete / connect commands
non-modal validation after commands
```

### Later

```text
split views (PFD + P&ID side by side, cross-highlighting)
custom workspace layouts / saved docking
Git diff UX
full YAML editor surface
advanced routing tools (manual waypoints)
rich Copilot (proposed-operations preview → Apply/Reject)
multi-sheet navigation
persisted presentation state (positions, sheet membership, role overrides)
```

### Explicitly not now

```text
process ↔ physical realization authoring (no schema; ADR-0016)
automatic engineering id/tag generation
Copilot backend / LLM integration
provider-specific AI integration
standards-compliance editing claims
3D / simulation surfaces
multi-user / cloud collaboration
framework- or library-specific UX commitments (#70 owns technology)
```

## Remaining UX uncertainties

Recorded deliberately rather than resolved by invention:

1. **Persistent presentation state shape** — what is persisted (positions, sheet
   membership, waypoints, per-step role overrides) and where it lives, if
   evidence ever requires persistence (ADR-0009 defers this).
2. **Mixed semantic/presentation undo** — whether one user action that changes
   both can be a single undo step under the chosen architecture (Issue #70).
3. **`ProcessPort` physical boundary** — how a junction-adjacent process port maps
   to a physical boundary; ADR-0016 leaves this unresolved.
4. **Related-object navigation with no realization layer** — how much cross-view
   navigation is honest before the ADR-0016 layer exists.
5. **Exact keyboard shortcuts** — deferred to the first GUI slice (Issue #70),
   subject to the "never keyboard-only" rule.
6. **Command palette scope** — whether it also performs object creation inline or
   only opens the Add surface.

## Related

- [product.md](../planning/product.md) — MVP scope, PFD/P&ID as views.
- [direction.md](../planning/direction.md) — Stages 3–4 (engineering views,
  interactive editing); product context only.
- [roadmap.md](../planning/roadmap.md) — current priority; the
  [re-evaluation gate](../planning/roadmap.md#re-evaluation-gate) that follows
  Issues #39/#69/#70.
- [architecture.md](../architecture/index.md) — current architecture and durable
  invariants.
- [contracts/process-model.md](../../contracts/process-model.md),
  [contracts/plant-model.md](../../contracts/plant-model.md),
  [contracts/physical-piping.md](../../contracts/physical-piping.md),
  [contracts/rendering.md](../../contracts/rendering.md) — the semantic and
  presentation contracts the UX projects.
- [reference-products.md](reference-products.md) and
  [standards-licensing-evidence.md](standards-licensing-evidence.md) — reuse and
  provenance evidence for future GUI technology (Issue #70).
- [process-physical-realization-boundary.md](process-physical-realization-boundary.md)
  — the ADR-0016 evidence behind the cross-view rules.
- [ADR-0003](../decisions/ADR-0003-separate-semantic-and-presentation-models.md),
  [ADR-0009](../decisions/ADR-0009-separate-process-function-from-symbol-role.md),
  [ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md) —
  the decisions this document applies.
- [conventions.md](../workflow/conventions.md) — documentation conventions.

