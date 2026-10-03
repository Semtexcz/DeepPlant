---
type: design-evidence
status: active
canonical_for:
  - engineering-editor-reuse-architecture
read_when:
  - interactive-editor-planning
  - gui-slice-planning
  - gui-technology-selection
  - reuse-or-licensing-review
  - roadmap-change
update_when:
  - gui-technology-decision-change
  - upstream-license-or-maintenance-materially-changes
  - first-gui-slice-evidence
depends_on:
  - docs/dev/planning/product.md
  - docs/dev/planning/direction.md
  - docs/dev/planning/roadmap.md
  - docs/dev/architecture/index.md
  - docs/dev/research/engineering-editor-ux.md
  - docs/dev/research/reference-products.md
  - docs/contracts/rendering.md
  - docs/contracts/process-model.md
  - docs/dev/reference/svg-symbols.md
decision:
  - docs/dev/decisions/ADR-0002-semantic-model-is-the-core.md
  - docs/dev/decisions/ADR-0003-separate-semantic-and-presentation-models.md
  - docs/dev/decisions/ADR-0009-separate-process-function-from-symbol-role.md
  - docs/dev/decisions/ADR-0016-process-physical-realization-boundary.md
evidence:
  - docs/dev/research/reference-products.md
  - docs/dev/research/engineering-editor-ux.md
superseded_by: null
---

# Engineering Editor Reuse-First Architecture

> **Question this document answers:** which reusable GUI technologies should
> underpin the DeepPlant Engineering Editor, and where are their boundaries?

> **Status:** design evidence and architecture decision-support. This document
> decides **which generic GUI capabilities DeepPlant reuses, prefers, rejects, or
> defers, and where DeepPlant-specific code must begin** (Issue #70). It does
> **not** implement the GUI, add a dependency, create a `frontend/` directory, or
> select the first executable GUI slice. The interaction requirements are owned by
> [engineering-editor-ux.md](engineering-editor-ux.md) (Issue #69); this document
> must be read as a technology and boundary layer over them, never as a
> replacement. Selecting a technology here means "the preferred architecture
> candidate when a slice authorizes it", never "installed by this document".

## Outcome card

- **Question investigated:** which generic GUI capabilities the DeepPlant
  Engineering Editor should reuse rather than build, which libraries are the
  preferred candidates, which are selected, rejected, or deferred, and where
  DeepPlant-specific engineering code must begin and generic framework code end.
- **Status:** active design evidence. It selects preferred **architectures and
  candidate technologies**, not dependencies; it records unresolved questions
  rather than resolving them by invention. No GUI exists and nothing is installed.
- **Inspection scope and date:** the authoritative product, planning,
  architecture, contract, and decision documents; the loadable
  [realistic fragment](../../../examples/realistic-process-fragment/plant.yaml);
  the existing [reuse landscape](reference-products.md) and
  [UX architecture](engineering-editor-ux.md); the current headless renderer
  (`src/deepplant/render.py`) and its `basic` symbol pack; and public
  primary sources (official documentation, source repositories, package metadata,
  and licence files) for each candidate library. External sources were inspected
  **2026-10-03**; the repository was inspected on `main` at
  `656c38051344e95d0411c845cee31a7c4445bf04`.
- **Conclusions:**
  1. The reusable stack is deliberately small: **Vue 3 + TypeScript + Vite** as the
     SPA foundation, **Vue Flow** as the preferred engineering-canvas candidate,
     and **Reka UI** as the minimal accessible UI-primitive candidate. Every
     canvas technology is isolated behind a DeepPlant projection/UI-adapter
     boundary and remains replaceable.
  2. Docking (**Dockview**), text editing (**Monaco**), automatic layout/routing
     (**ELK / elkjs**), a state-management library (**Pinia**), and a general
     utility library (**VueUse**) are **deferred** or **rejected for the initial
     slice**; each has a recorded adoption trigger rather than a pre-emptive
     dependency.
  3. Undo/redo belongs at the **application-command boundary**, not in a canvas
     library's internal graph history; no dedicated undo dependency is selected.
  4. Presentation state must remain **DeepPlant-owned**; no selected library may
     hold project truth, and the framework graph must be reconstructable from
     semantic + presentation state.
  5. The existing DeepPlant **Process/PFD** SVG symbol/anchor contract and headless
     renderer are **reused, not duplicated**; the interactive canvas is another
     consumer of that DeepPlant-owned **Process/PFD** presentation contract. The
     current contract is Process/PFD-specific, and no physical/P&ID symbol contract
     exists today (see [Existing renderer and SVG symbol
     reuse](#existing-renderer-and-svg-symbol-reuse)).
- **Resulting ADRs:** none. The durable invariants this document relies on are
  already owned by [ADR-0002](../decisions/ADR-0002-semantic-model-is-the-core.md),
  [ADR-0003](../decisions/ADR-0003-separate-semantic-and-presentation-models.md),
  [ADR-0009](../decisions/ADR-0009-separate-process-function-from-symbol-role.md),
  and [ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md).
  The threshold decision is recorded in this document (see
  [ADR threshold](#adr-threshold)); a first-slice library preference is
  intentionally replaceable and does not warrant a new ADR.
- **Current contracts operationalizing the result:** none yet. This document
  informs [roadmap.md](../planning/roadmap.md); the first executable GUI slice is
  selected only at the [re-evaluation gate](../planning/roadmap.md#re-evaluation-gate).
- **Conditions for revisiting:** an authorized GUI slice needs a deferred
  capability (docking, YAML/diff editing, automatic layout/routing), a selected
  library's licence or maintenance condition materially changes, or evidence shows
  the framework cannot be cleanly reconstructed from DeepPlant-owned state.

## Scope and authority

This document owns the **reuse-first frontend architecture question only**. It
does not own, restate, or override:

- **product scope and MVP boundaries** — [product.md](../planning/product.md)
  (Issue #68);
- **interaction/UX behaviour** — [engineering-editor-ux.md](engineering-editor-ux.md)
  (Issue #69);
- **semantic model contracts** — [contracts/](../../contracts/index.md);
- **the semantic/presentation separation** —
  [ADR-0002](../decisions/ADR-0002-semantic-model-is-the-core.md) and
  [ADR-0003](../decisions/ADR-0003-separate-semantic-and-presentation-models.md);
- **the function/role separation** —
  [ADR-0009](../decisions/ADR-0009-separate-process-function-from-symbol-role.md);
- **process ↔ physical realization ownership** —
  [ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md).

It also does **not** select the local transport/API technology between the SPA and
the Python core. The frontend must talk to a **transport-neutral local application
boundary**; whether that is a local HTTP service, a socket, or something else is
decided by the concrete first slice that requires it, and never by a GUI library.

### Reconciliation of stale Issue #70 wording

Issue #70 predates the delivered Issue #39 and Issue #69 evidence. The following
Issue-wording assumptions are **corrected to current repository authority** here:

| Stale Issue #70 assumption | Current authority |
|---|---|
| `MapProcessRealization(...)` is treated as an existing command/schema | No such command or schema exists. [ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md) decides **ownership only**; a cross-layer realization action is described generically, never as a named call. |
| Presentation state treated as an existing persisted schema | The MVP **requires** presentation state to survive save/reload, but its schema is undecided. Issue #70 only ensures selected libraries **do not prevent** DeepPlant from owning it. |
| Issue #70 as a "GUI technology decision" implying implementation | Issue #70 is a documentation/evidence slice only. It authorizes no dependency, directory, or runtime code, and the first executable slice is selected later at the re-evaluation gate. |

## Requirements inherited from Issue #69

The selected stack must support, or have a credible path to support, the
interaction architecture already decided in
[engineering-editor-ux.md](engineering-editor-ux.md). Issue #70 does not redesign
these; if a library conflicts with one, the library is constrained or rejected.

| Requirement (from #69) | Category |
|---|---|
| canvas-dominant workspace with minimum permanent chrome | workspace |
| selection, multi-selection, box selection | interaction |
| pan / zoom / fit view, dragging representations | interaction |
| custom engineering-node rendering | rendering |
| explicit / contextual connection points; connection creation interaction | interaction |
| PFD and P&ID editor views / tabs | workspace |
| Engineering Explorer (engineering-concept navigation) | workspace |
| selection-driven Properties Inspector | workspace |
| Problems / validation navigation (non-modal) | workspace |
| searchable Add interaction | interaction |
| command palette (searches commands **and** objects) | interaction |
| keyboard + mouse, never keyboard-only | interaction |
| semantic / presentation / framework / transient state separation | boundary |
| application-command boundary; future Copilot uses the same command path | boundary |

The last two rows are non-negotiable architectural filters, not feature checkboxes.

## Evaluation methodology

Every candidate was assessed qualitatively against four axes, with no arbitrary
numeric scoring:

1. **Requirement fit** — does it supply the #69 capability, or leave a large gap?
2. **Engineering-fit** — does it model node/port/connection concepts in a way that
   maps honestly onto DeepPlant semantics (or at least does not fight them)?
3. **Boundary fit** — can DeepPlant own semantic and presentation state, keep the
   framework graph as a pure projection, translate framework events into
   application-command intent, and avoid treating library serialization as project
   truth?
4. **Adoption surface and licence** — direct/transitive dependencies, CSS/build
   assumptions, generated code, bundled assets, maintenance posture, and licence
   compatibility with an AGPL-3.0-only repository.

Licence, maintenance, and dependency facts are recorded once, in
[reference-products.md](reference-products.md), and referenced here; this document
records only the DeepPlant-specific comparison and boundary decisions.

## Selected architecture overview

The target keeps three boundaries strictly nested: a DeepPlant-specific UI, a thin
replaceable generic-GUI layer, and a transport-neutral local application boundary
to the Python core.

```text
┌──────────────────────────────────────────────────────────────┐
│ DeepPlant Engineering Editor                                 │
│                                                              │
│ DeepPlant-specific UI                                        │
│ ├── Engineering Explorer                                     │
│ ├── Properties Inspector                                     │
│ ├── Problems surface                                         │
│ ├── Engineering view projections (PFD / P&ID)                │
│ └── command intents                                          │
│                    │                                         │
│                    ▼                                         │
│ Generic reusable GUI infrastructure (replaceable)            │
│ ├── canvas (Vue Flow)                                        │
│ └── minimal UI primitives (Reka UI)                          │
└────────────────────┬─────────────────────────────────────────┘
                     │  local application boundary (transport-neutral)
                     ▼
             DeepPlant Python core
             (semantic model + validation + rendering)
```

The generic layer is intentionally narrow. DeepPlant never builds a second
engineering model in the browser, never serializes the canvas graph as project
truth, and never lets a UI generation or canvas library decide engineering
meaning.

## Engineering canvas evaluation

### Vue Flow — preferred candidate

Vue Flow (`@vue-flow/core`) is the **preferred engineering-canvas candidate** when
a slice authorizes an interactive canvas, isolated behind a DeepPlant
projection/adapter boundary.

What it solves (verified against current official documentation):

- **Vue 3-first, TypeScript.** It is a Vue 3 component library written fully in
  TypeScript, with a bundled type surface (`dist/index.d.ts`). Vue 2 is explicitly
  unsupported. This matches the product's stated SPA direction.
- **Built-in interaction.** Element dragging, zoom/pan, and selection are
  built-in; the viewport surface exposes `fitView`, `setViewport`, and centring.
- **Custom nodes and edges.** User-defined node and edge components are a
  first-class mechanism; default nodes carry no styles and are meant to be
  replaced. This is where DeepPlant renders engineering symbols.
- **Handles as explicit connection points.** The `<Handle>` component provides
  explicit, multiple, uniquely-identified connection points per node
  (`type="source"|"target"`, `position`, per-handle `connectable` boolean/number/
  function), plus `connection-mode` (`Loose`/`Strict`). `onConnect` reports
  `source`/`target`/`sourceHandle`/`targetHandle`. This maps directly onto the
  #69 requirement for explicit/contextual connection points.
- **Connection validation hooks.** A `valid`/`isValidConnection` mechanism
  (`ValidConnectionFunc(connection, elements) => boolean`) can veto a connection
  before an edge is created — the hook DeepPlant uses to refuse connections the
  semantic model cannot honestly allow.
- **Selection, multi-selection, and box selection.** A `SelectionMode` enumeration,
  a `SelectionRect`/`Box` shape, and helpers such as `getNodesInside`/`getRectOfNodes`
  are part of the public surface; multi-selection and rectangular selection exist
  as configuration/behaviour that the first slice must pin to its exact modifiers.
- **Keyboard behaviour.** Documented node/edge accessibility: `Enter`/`Space`
  selects, arrow keys move a selected node, `Delete` removes, `Escape` cancels;
  `useKeyPress` is available. This is a positive signal for the #69 "never
  keyboard-only, but keyboard-accelerated" rule, though the canvas does not claim
  full screen-reader parity and must not be the only path to any capability.
- **Controlled state.** A documented "controlled flow" mode
  (`applyDefault=false`, `onNodesChange`/`onEdgesChange`, `applyNodeChanges`/
  `applyEdgeChanges`, `v-model:nodes`/`v-model:edges`, `useVueFlow`) lets DeepPlant
  intercept every framework change and apply it only after validation — the exact
  mechanism the application-command direction needs.

Known limitations and constraints:

- The library's own graph state (`nodes`, `edges`, positions, selection) is a
  **framework model**. It must never be serialized as the DeepPlant project model.
  Position changes are framework changes that DeepPlant decides how to interpret
  (a presentation command), not semantic mutations.
- The default edge types are generic flowchart edges. DeepPlant engineering
  connection semantics (a `ProcessStream` vs a physical `Connection` vs a
  `PipingRealization`) are **not** expressible by the library and must remain
  DeepPlant concepts projected onto edges.
- Accessibility is best-effort at the canvas layer; DeepPlant must keep every
  capability reachable from non-canvas surfaces (Explorer, Inspector, command
  palette).
- The core `@vue-flow/core` depends on D3 sub-packages and on `@vueuse/core`
  `^10.5.0`, a different major from the `@vueuse/core` major Reka UI uses. Both
  majors may therefore be present at once. This is a maintenance/adoption-surface
  observation, not a blocker, and is recorded in
  [reference-products.md](reference-products.md).

### Credible alternative: AntV X6

AntV X6 (`@antv/x6`) is a **credible alternative** and is **rejected for the
initial slice** (kept as a future comparison, not a dependency).

- It is a professional HTML/SVG graph-editing engine with custom node rendering
  (SVG/HTML/React/Vue/Angular), lasso/box selection, alignment lines, a minimap,
  history, ports, and a rich event system; it is MIT-licensed and actively
  maintained.
- Reasons for not selecting it first: it is framework-agnostic rather than
  Vue-native, so DeepPlant would write more Vue↔X6 bridging; it carries its own
  opinionated graph/Model-View-Controller engine and a larger dependency set
  (`lodash-es`, `mousetrap`, `dom-align`, `utility-types`); and it trends toward
  being the application's graph framework rather than a replaceable canvas. The
  boundary work is heavier than Vue Flow's for the same #69 capabilities.
- It remains a legitimate reconsideration target if Vue Flow proves insufficient
  for schematic interaction, because it is not architecturally excluded.

### Credible alternative: Cytoscape.js

Cytoscape.js is a **credible alternative** and is **rejected for an engineering
schematic canvas**.

- It is a mature, dependency-free (runtime), MIT-licensed graph-theory and
  visualisation library with selection, viewport, stylesheet-driven rendering,
  and a large layout-algorithm ecosystem.
- It is optimised for **graph theory and network analysis**, not for bespoke
  engineering-symbol editing: custom node rendering is constrained by its
  stylesheet model, its port/attribute model is a poor match for engineering
  connection points, and schematic-style drag/connect editing is not its core
  interaction. It fits analysis views (topology review) better than the PFD/P&ID
  editing surface, so it is out of scope for the first editor slice.

### Build-it-yourself control: custom SVG / custom canvas

A bespoke Vue + SVG (or canvas) implementation is the **control case** and is
**not selected**.

- It is the only option with zero third-party GUI surface and full control over
  rendering and interaction, which is attractive for a long-lived engineering
  product.
- It is rejected for the first slices because it forces DeepPlant to build and
  maintain generic infrastructure — hit-testing, marquee selection, pan/zoom,
  connection dragging, keyboard navigation, viewport transforms — that Vue Flow
  already provides and documents. That maintenance is unrelated to process/plant
  engineering semantics, which is exactly what the reuse-first principle forbids
  building.
- A build-it-yourself path stays viable for a **narrow**, DeepPlant-specific
  rendering concern (for example a specialised symbol or a small schematic glyph)
  without adopting it as the whole canvas strategy.

### Semantic isolation test

Each serious canvas candidate was tested against the isolation questions from the
reuse-first principle. Any candidate that requires the framework graph to become
canonical is rejected.

| Question | Vue Flow | AntV X6 | Cytoscape.js | Custom SVG |
|---|---|---|---|---|
| Can DeepPlant own semantic objects independently? | Yes | Yes | Yes | Yes |
| Can framework objects be pure projections? | Yes | Yes, with more bridging | Partly (stylesheet model) | Yes |
| Can the framework be replaced without migrating the engineering model? | Yes, if isolated behind a DTO/adapter | Heavier but possible | Heavier but possible | N/A (it *is* the code) |
| Can DeepPlant generate nodes/edges from semantic + presentation state? | Yes | Yes | Yes | Yes |
| Can GUI events be translated back into application commands? | Yes (`onNodesChange`/`onEdgesChange`/`onConnect`/`isValidConnection`) | Yes (events) | Yes (events) | Yes |
| Can library serialization be fully avoided as project truth? | Yes | Yes | Yes | Yes |

**Verdict:** Vue Flow passes the isolation test by construction — its controlled
mode exists precisely so external state can own truth. X6 and Cytoscape.js could be
isolated too, but with more bespoke glue, so they are not preferred. Rejecting a
candidate requires that the framework graph become canonical; none of these is
architecturally forced into that, so the choice is one of fit and cost, not
possibility.

## UI primitives evaluation

The #69 surfaces — dialogs, popover, context menu, dropdown, tabs, tooltip,
selection controls, forms, and the searchable Add/command surfaces — need
accessible primitives. The goal is a **small maintainable primitive strategy**, not
a component collection or a design system.

### Reka UI — preferred primitive candidate

Reka UI (formerly Radix Vue; `reka-ui`) is the **preferred accessible-primitive
candidate**.

- It is an unstyled, accessibility-first Vue 3 component library aligned with
  WAI-ARIA patterns, handling aria attributes, keyboard navigation, and focus
  management. It covers the primitives #69 needs (dialog, popover, dropdown,
  context menu, tabs, tooltip, combobox, etc.).
- It is **headless and unstyled**: DeepPlant keeps its own visual identity with
  plain CSS and is not forced into a CSS framework.
- It supports **controlled and uncontrolled** usage, so components can participate
  in DeepPlant-owned state, and it is `sideEffects: false` and tree-shakeable, so
  unused primitives do not inflate the bundle.
- Licence is MIT, and current release/peer information is recorded in
  [reference-products.md](reference-products.md).

It is a genuine dependency with its own transitive set (Floating UI, TanStack
Virtual, internationalised date/number, VueUse, `aria-hidden`, `defu`, `ohash`),
which is a real adoption surface and is recorded, not hidden.

### shadcn-vue — deferred (adoption model matters)

`shadcn-vue` is **deferred**, and its relationship to Reka UI is the decisive
point.

- shadcn-vue is **not a runtime component library**. It is a **code-distribution**
  model: a CLI copies component source into the project (`@/components/ui/...`)
  which the project then owns and maintains.
- Its documented installation requires **Tailwind CSS** (`tailwindcss` +
  `@tailwindcss/vite`), path aliases, and an init/add CLI step. Its components
  compose Reka UI primitives and use `@lucide/vue` icons.
- Adopting shadcn-vue therefore means adopting Tailwind, copied-and-owned
  component source (an ongoing maintenance and upstream-sync surface), and an icon
  package — a much larger permanent footprint than headless primitives, and
  contrary to "minimum permanent chrome" and "do not add Tailwind unless evidence
  establishes why it is necessary".
- It is **deferred, not rejected**: it may be selectively reconsidered when an
  authorized slice needs one composed component. If it is, at minimum the Tailwind
  requirement, the copied-source maintenance model, and icon-asset provenance must
  each be justified first.

**Relationship summary:** Reka UI is the dependency; shadcn-vue is an optional
source-distribution layer *over* Reka UI plus Tailwind. Choosing Reka UI does not
require shadcn-vue, and choosing shadcn-vue would imply Reka UI **and** Tailwind
**and** copied components.

## Workspace / docking evaluation

### Dockview — deferred

Dockview (`dockview-vue`) is a **credible but deferred** docking technology.

- It is a zero-runtime-dependency docking layout manager with tabs, groups, grids,
  split views, serialization/deserialization, and Vue 3 bindings (peer `vue` ≥3.4);
  the used packages are MIT. The enterprise superset is separately
  commercially licensed and is not needed.
- Issue #69's initial workspace is deliberately **fixed and simple**: a collapsible
  Explorer, a collapsible Inspector, editor tabs (PFD/P&ID), and a Problems
  surface. Split views, custom workspace layouts, saved docking, and per-user
  customisation are **later**.
- **Does the MVP actually need a docking framework?** No. A small, fixed Vue layout
  with two collapsible sides and a tab strip satisfies the MVP and avoids adopting
  a full docking engine, its CSS, and its serialization model for features that are
  explicitly deferred.

**Adoption trigger:** adopt Dockview only when a concrete requirement needs
user-arrangeable split views, drag-to-dock, floating panels, or saved workspace
layouts — and only with the boundary that its serialized layout is DeepPlant-owned
presentation state, never project truth.

## YAML / text-editor evaluation

### Monaco — deferred

Monaco Editor is a **credible future candidate** and is **deferred**.

- It is the browser code editor extracted from VS Code: MIT-licensed, with rich
  editing, diff, and language-service capability that would suit a future YAML/diff
  workflow.
- It has a heavy adoption surface: large build size, worker/web-server requirements
  (it cannot run from `file://`, needs an HTTP(S) origin), no mobile support, and
  its own asset/`ThirdPartyNotices.txt` obligations. It is overkill for the MVP.
- Issue #69 states that YAML/text editing is **not** the primary workflow and a full
  YAML editor is **later**.

**Adoption trigger:** adopt Monaco only when an authorized slice needs a real text
or diff surface (for example a future YAML editor or Git-diff view). Reaching for it
merely because "Engineering-as-Code eventually benefits from YAML" is premature.

## Layout / routing evaluation

Issue #70 names ELK / elkjs explicitly. The distinction that governs this section:

```text
generic graph geometry / layout      ← reusable engine
        ↓
DeepPlant presentation policy        ← DeepPlant owns this
        ↓
engineering view (PFD / P&ID)
```

### ELK / elkjs — conditional preferred candidate, deferred

- ELK (Eclipse Layout Kernel) implements automatic graph layout with a layer-based
  algorithm suited to node-link diagrams **with ports** — exactly the shape of a
  PFD. Its documentation describes nodes, edges, **ports** (explicit connection
  points) and orthogonal routing as first-class concepts; `elkjs` exposes the
  layout-relevant part of ELK to JavaScript and runs in the browser (main-thread or
  worker bundle). It is the layout engine behind several diagramming tools
  (mermaid, reactflow examples, sprotty, and others).
- Licence is **EPL-2.0 OR GPL-3.0-or-later** (a dual licence; the earlier
  "needs review" note in [reference-products.md](reference-products.md) is now
  resolved). Under the GPL-3.0-or-later option it is combinable with this
  AGPL-3.0-only repository, but this is a real licence consideration to record
  rather than gloss over.
- It is a **layout/routing engine, not a diagramming framework**: it consumes a
  graph with positions/sizes/ports and returns geometry. That makes it a clean fit
  behind DeepPlant presentation policy — it must never decide engineering meaning,
  only geometry.

**Why deferred:** the first executable slice does not obviously need automatic
layout. DeepPlant already owns a deterministic headless layout policy
([contracts/rendering.md](../../contracts/rendering.md)) and can project an initial
presentation from it (manual or derived positions, simple deterministic placement).
Selecting a full layout/routing dependency before a slice requires it would be
premature.

**Adoption trigger:** adopt ELK/elkjs when a slice genuinely needs automatic layout
or orthogonal routing beyond the existing deterministic renderer heuristic — for
example "auto-arrange an imported/edited fragment" or adaptive routing on large
diagrams. When adopted, DeepPlant supplies the graph and interprets the output;
layout output is presentation-only.

### Existing renderer layout reuse

The current headless renderer is **Process/PFD-only**. Its deterministic layered
placement, ordered `ProcessPort` anchor assignment, `ProcessStream` routing, label
placement, and grid are reusable evidence and a baseline for Process/PFD
presentation; they must not be described as an established P&ID layout/routing
policy.

The first interactive Process/PFD projection should reuse or learn from that
behaviour where practical rather than needlessly duplicating it or adding a new
layout engine. Physical/P&ID layout and routing may have materially different
requirements and must not be assumed to inherit the same policy without evidence.

## State-management evaluation

**No frontend state-management library is selected for the initial slice.**

- The #69 state model separates **semantic engineering state**, **persistent
  presentation state**, **framework state**, and **transient UI state**. A frontend
  store is only the framework/UI side; it can never be the engineering owner.
- A small app whose shared state is (a) the loaded semantic model projection and
  (b) DeepPlant-owned presentation state does not obviously exceed ordinary Vue
  reactivity plus composables. Vue's own Composition API, with `provide`/`inject`
  or a small composable, is sufficient until a concrete need appears.
- **Pinia** (MIT; the current Vue-official store) is **deferred**, not adopted. It is
  a reasonable choice *if* a slice develops genuinely cross-cutting frontend state
  that plain composables make awkward — but "frontend state manager" ≠ "engineering
  state owner", and adding one now would be a dependency without evidence.

**Adoption trigger:** adopt a store (likely Pinia) only when multiple independent
frontend surfaces need the same non-semantic UI state and composables prove
insufficient. Even then, the store holds UI/framework state only; the semantic model
and presentation model remain DeepPlant-owned and outside the store's authority.

## Undo/redo ownership

Issue #69 requires **one coherent user-facing undo model**. Issue #70 decides the
**architectural owner**, not the implementation.

```text
user action  →  application command  →  semantic + presentation change  →  history entry
```

- Undo/redo belongs at the **application-command boundary**. A command is the unit
  of a user intent; the history is a sequence of those units.
- It must **not** be owned by the canvas library's internal graph history. Vue
  Flow's framework-level changes (add/remove/select/position) are framework events
  that DeepPlant translates; letting the library's own history become authoritative
  for engineering changes would violate semantic isolation and would not span
  semantic + presentation mutations.
- Semantic mutation and presentation mutation are **DeepPlant concepts**; a single
  user action may touch both, and it must be representable as one undo step.

**Outcome:** **no dedicated undo/redo dependency is selected.** Undo/redo is an
application-command-layer responsibility. A generic command/history helper may be
considered later only if the command layer's own implementation becomes
burdensome, and never as a canvas-library feature.

## Presentation-persistence compatibility

Issue #69 established that the completed MVP must persist enough presentation state
to survive save/reload **without loss**, but deliberately left the schema undefined.
Issue #70 does **not** design that schema; it only verifies **compatibility**.

Each selected library was checked against four compatibility questions:

| Question | Vue Flow | Reka UI | Result |
|---|---|---|---|
| Can presentation state be extracted from framework state? | Yes — positions/selection are readable via `useVueFlow`/`v-model` and change events | UI state is DeepPlant-constructed; nothing is hidden in the library | compatible |
| Can DeepPlant persist only its own presentation model? | Yes — persist a DeepPlant-owned record (e.g. per-object position/role/view config), not the framework node/edge array | N/A | compatible |
| Can the framework be reconstructed from semantic + presentation state? | Yes — nodes/edges are projections regenerated on load | N/A | compatible |
| Can transient framework-only fields be discarded? | Yes — internal ids, `dimensions`, transient selection, and viewport are not persisted as project truth | N/A | compatible |

**Outcome:** the selected libraries **do not prevent** DeepPlant from owning
presentation persistence independently. Non-goals restated: **do not** design a
presentation-state schema, presentation YAML, storage files, or a serialization
format here.

## Existing renderer and SVG symbol reuse

The interactive canvas is a **new consumer of DeepPlant-owned presentation
contracts**, not their replacement. The currently implemented contract has a
strictly Process/PFD scope:

```text
existing DeepPlant Process/PFD SVG symbol + anchor contract
(ADR-0008 + dev/reference/svg-symbols.md)
        ↓                                  ↓
headless PFD renderer              interactive PFD projection
(src/deepplant/render.py)                  ↓
                                  future Process/PFD consumers
```

- The `basic` symbol pack
  (`src/deepplant/assets/symbols/process/basic/`) and its `<role>.svg` +
  `deepplant-anchors` contract are DeepPlant-owned assets with DeepPlant provenance
  under AGPL-3.0-only. The symbol **role**, not the file, is the presentation
  concept; the SVG asset is one realization.
- For Process/PFD rendering, the interactive editor should reuse the existing
  `ProcessStep` function → symbol role → process symbol pack → SVG geometry and
  ordered-anchor contract ([svg-symbols.md](../reference/svg-symbols.md)). It must
  not invent a frontend-specific canonical symbol library for that view.
- **Do not duplicate the `basic` Process/PFD pack** into a frontend-specific
  canonical symbol library. DeepPlant owns engineering presentation contracts and
  assets; frontend frameworks consume DeepPlant-owned presentation projections and
  do not become the owner of engineering symbols.
- The current contract is **Process/PFD-specific**. **No physical/P&ID symbol
  contract exists today** for `Equipment`, physical `Port`, `Connection`, `Nozzle`,
  `PipingLine`, `Valve`, instrumentation, or related physical presentation concepts.
  A future physical/P&ID presentation slice may define an analogous or extended
  DeepPlant-owned symbol/anchor contract from evidence. **Issue #70 does not design
  that contract.**
- **Integration question recorded (not implemented):** delivering the packaged SVG
  assets (and their anchor metadata) to a browser consumer requires a mechanism
  (embedding, a fetch endpoint, or a build-time copy). Recording this is Issue #70's
  obligation; implementing the asset-delivery mechanism belongs to the first slice.

## Application-command boundary

The frontend target remains:

```text
user interaction
        ↓
GUI / canvas (framework events)
        ↓
DeepPlant UI adapter      ← framework events → command intent
        ↓
application command       ← the only mutation path
        ↓
DeepPlant semantic model
        ↓
validation
        ↓
projection
        ↓
GUI
```

- Never:

  ```text
  framework graph  →  serialize framework state  →  treat it as the DeepPlant model
  ```

- Vue Flow's controlled mode (`onNodesChange`/`onEdgesChange`/`onConnect`,
  `applyDefault=false`) is the concrete hook where a framework event is intercepted
  and translated into a **command intent**, not applied directly to a canonical graph.
- Issue #70 may refine the **frontend-side** boundary. It does **not** implement
  application commands, and it does **not** select a Python transport/backend
  framework. The command surface is conceptually shared by direct manipulation, the
  command palette, keyboard shortcuts, and a future Copilot
  ([engineering-editor-ux.md](engineering-editor-ux.md)).

### Command palette implementation

The command palette is a **small DeepPlant-specific component over the selected
headless primitives** (Reka UI's combobox/listbox primitives, or a minimal custom
search surface). The **command catalogue is DeepPlant-specific** and must not come
from a library. **No large library is introduced solely for command-palette
behaviour.** `shadcn-vue`'s `Command` component is one possible future composition
(it wraps Reka UI primitives) but adopting it would pull in Tailwind and copied
source, so it is deferred with the rest of shadcn-vue.

## Dependency, licence, and provenance review

All external facts below were inspected on **2026-10-03** from primary sources and
are recorded once in [reference-products.md](reference-products.md). DeepPlant is
**AGPL-3.0-only**, so material licence/redistribution implications are noted.

```text
code licence  !=  asset licence
```

For every selected library the two questions are answered separately:

| Technology | Code licence (SPDX) | Assets shipped/relevant | Asset note |
|---|---|---|---|
| Vue 3 | MIT | none of concern | no reusable engineering assets |
| Vite | MIT | none of concern | build tool only |
| Vue Flow | MIT | no symbol/asset library | generic flowchart visuals are library-generated, not engineering symbols |
| Reka UI | MIT | unstyled; no bundled icon set as a requirement | DeepPlant supplies its own styling; no third-party icon asset implied |
| shadcn-vue (deferred) | MIT | components use `@lucide/vue` icons | icon assets would need their own provenance check **if** adopted |
| Dockview (deferred) | MIT (used packages); enterprise package commercial | none of concern | enterprise package not needed |
| Monaco (deferred) | MIT | ships fonts/`ThirdPartyNotices.txt` | asset/notice review required **if** adopted |
| elkjs (conditional) | EPL-2.0 OR GPL-3.0-or-later | algorithm code only | combinable under the GPL-3.0-or-later option |

Notes:

- No third-party GUI/engineering **asset** is imported by this document. DeepPlant's
  own `basic` symbol pack stays the only symbol asset, and it is DeepPlant-original
  under AGPL-3.0-only ([standards.md](../workflow/standards.md),
  [ADR-0007](../decisions/ADR-0007-standards-and-symbol-provenance.md)).
- Where a candidate's licence is not a plain permissive licence (elkjs), the
  implication is recorded here rather than assumed away. This is an engineering
  observation, **not legal advice**; a future slice that adopts elkjs must confirm
  the chosen licence option and its attribution/notice obligations.
- Maintenance posture was inspected as evidence, not reputation: each candidate has
  recent releases and active source repositories; "mature and low-churn" and
  "active" were distinguished in [reference-products.md](reference-products.md).
  No candidate was selected or rejected on popularity.

## Build-vs-reuse rule

This is a reusable decision rule for future GUI subsystems. Before DeepPlant
implements generic GUI infrastructure, answer:

```text
1. What existing libraries solve most of this problem?
2. Why are they insufficient?
3. Is the missing behaviour genuinely DeepPlant-specific?
4. Can DeepPlant wrap/extend an existing library?
5. Can the dependency remain replaceable?
6. Would custom code create long-term maintenance unrelated to
   process/plant engineering semantics?
```

If a generic capability is solved well by a mature library, is not
DeepPlant-specific, can be wrapped, and can remain replaceable, **reuse it**. Custom
generic GUI infrastructure requires explicit evidence.

## ADR threshold

**No new ADR is created by Issue #70.**

- The durable invariants this document depends on are already decided: the semantic
  core ([ADR-0002](../decisions/ADR-0002-semantic-model-is-the-core.md)), the
  semantic/presentation separation
  ([ADR-0003](../decisions/ADR-0003-separate-semantic-and-presentation-models.md)),
  the function/role separation
  ([ADR-0009](../decisions/ADR-0009-separate-process-function-from-symbol-role.md)),
  and process ↔ physical ownership
  ([ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md)).
- The candidate durable rule "**canvas/framework state is always isolated behind a
  DeepPlant projection/adapter boundary and is never project truth**" is a direct
  application of ADR-0002/ADR-0003 to the frontend, not a new boundary. It is
  recorded here and enforced by the [replaceability boundary](#replaceability-boundaries).
- A specific first-slice preference such as "use Vue Flow first" is intentionally
  **replaceable** and does not clear the ADR threshold.

A new ADR would be warranted only if an authorized slice introduced a durable
constraint that must survive individual library replacement **and** is not already
owned — for example, if evidence forced a persistent presentation model with a
schema that ADR-0003/ADR-0009 cannot express. That is not the case today.

## Selected / rejected / deferred matrix

`SELECT` means "preferred architecture candidate when the relevant executable slice
authorizes it". It does **not** mean "added as a dependency by this document".

| Subsystem | Decision | Preferred candidate | Reason |
|---|---|---|---|
| SPA foundation (Vue 3 + TypeScript + Vite) | **SELECT** | Vue 3 + TypeScript + Vite | Vue-native, first-class TypeScript; matches the product's stated direction |
| Engineering canvas | **SELECT** | Vue Flow | Vue 3-native, TypeScript, custom nodes/edges, handles, connection validation, selection, controlled state |
| UI primitives | **SELECT** | Reka UI | Accessible, unstyled, tree-shakeable, controlled/uncontrolled, MIT |
| State-management helper | **REJECT** (for the initial slice) | Pinia (if later needed) | Ordinary Vue reactivity/composables suffice; a store is not the engineering owner |
| Undo/redo helper | **REJECT** (for now) | — | Belongs at the application-command boundary, not a canvas library |
| Workspace / docking | **DEFER** | Dockview | MVP workspace is fixed/simple; docking is a later need |
| YAML / text editor | **DEFER** | Monaco | YAML editing is not the primary workflow and is later |
| Layout / routing | **DEFER** (conditional preference) | ELK / elkjs | Existing deterministic layout suffices until automatic layout/routing is required |
| UI component distribution layer | **DEFER** | shadcn-vue | Implies Tailwind + copied source + icons; larger footprint than headless primitives |
| General Vue utilities | **DEFER** | VueUse | Adopt specific composables only when a slice needs them; not a state architecture |
| Alternative canvas | **REJECT** (for the initial slice) | AntV X6, Cytoscape.js | Credible but heavier bridging / poorer schematic fit than Vue Flow |
| Custom canvas build-out | **REJECT** (as the canvas strategy) | custom SVG/canvas | Rebuilds generic infrastructure unrelated to engineering semantics |

## Minimal preferred stack

The deliberately small stack, with the distinction between a foundation technology
and a slice dependency made explicit:

| Capability | Decision | Preferred technology | Why | Adoption trigger |
|---|---|---|---|---|
| SPA foundation | SELECT | Vue 3 + TypeScript + Vite | Product-foundation framework; TypeScript-first | first GUI slice (product foundation, not a library preference) |
| Engineering canvas | SELECT | Vue Flow (`@vue-flow/core`) | Supplies #69 canvas interaction behind a DeepPlant projection/adapter | first interactive-canvas slice |
| UI primitives | SELECT | Reka UI | Accessible headless primitives for menus/inspector/dialogs/command surface | only if the first slice needs menus, dialogs, or inspector controls |
| Docking | DEFER | Dockview | Fixed/simple MVP workspace does not need a docking engine | split views / custom / saved workspace layout requirement |
| Text editor | DEFER | Monaco | YAML/diff editing is not the primary MVP workflow | YAML editor or Git-diff surface becomes concrete |
| Layout / routing | DEFER | ELK / elkjs | Existing deterministic layout suffices initially | automatic layout or orthogonal routing is concretely required |
| State manager | REJECT (for now) | Pinia (if later needed) | Vue reactivity/composables suffice; a store ≠ engineering owner | multiple frontend surfaces genuinely need shared non-semantic UI state |
| Undo helper | REJECT (for now) | — | History is an application-command responsibility | only if the command layer's own history becomes burdensome |
| General Vue utilities | DEFER | VueUse | Individual composables only where a slice needs them | a specific composable is justified by a slice |

Each selected technology is categorized:

- **product foundation:** Vue 3 + TypeScript + Vite.
- **likely first-slice dependency:** Vue Flow (canvas); Reka UI (only if the first
  slice needs its primitives).
- **conditional later dependency:** ELK / elkjs.
- **future candidate only:** Dockview, Monaco, shadcn-vue, Pinia, VueUse.

No router is included: the MVP is a single-canvas SPA with editor tabs, not a
multi-route application. It may be reconsidered only if a slice introduces real
navigation between distinct top-level screens.

## DeepPlant-specific layer

Even after aggressive reuse, these remain **DeepPlant code**, because they carry
engineering meaning no generic library may own:

```text
semantic → view projection
engineering node representations (function → role → symbol)
engineering connection semantics
ProcessStream vs Connection distinction (and vs PipingRealization)
properties interpretation
validation integration
engineering Problems navigation
application commands (the only mutation path)
process ↔ physical related-object UX (once realized)
presentation policy
engineering search/Add catalogue
future Copilot engineering operations
```

Generic libraries provide interaction primitives; they must not own these meanings.

## Replaceability boundaries

For each selected frontend library, the intended isolation boundary:

```text
DeepPlant semantic state
        ↓
DeepPlant view projection

Process/PFD:
    existing Process/PFD symbol contract where applicable

Physical/P&ID:
    future DeepPlant-owned presentation contract, not yet defined

        ↓
DeepPlant UI adapter / presentation DTOs
        ↓
Vue Flow node/edge/handle state
        ↓
Vue Flow
```

Event direction:

```text
canvas event (onNodesChange / onEdgesChange / onConnect)
        ↓
DeepPlant UI adapter
        ↓
application command intent
```

Rules:

- The core must not import or understand canvas-library types.
- The presentation model must remain DeepPlant-owned.
- Replacing Vue Flow (or X6, or a future canvas) must not require migrating the
  engineering model; only the projection/adapter layer changes.
- The same boundary applies to the UI primitive library: Reka UI supplies behaviour,
  never DeepPlant meaning.

## Remaining uncertainties

Recorded deliberately rather than resolved by invention:

1. **Presentation-state schema** remains undecided. Issue #70 confirms the selected
   libraries are compatible with DeepPlant-owned persistence; it does not design the
   stored shape (see [presentation-persistence compatibility](#presentation-persistence-compatibility)).
2. **Mixed semantic/presentation undo** — whether one user action touching both is a
   single undo step under the final command-layer design is deferred to the slice
   that implements the command layer.
3. **Exact Vue Flow selection modifiers** — multi-selection and box selection exist
   in the public surface, but the exact keys/modes the #69 Interaction depends on
   must be pinned at the first canvas slice.
4. **Symbol/asset delivery to the browser** — how the packaged `basic` pack and its
   anchor metadata reach the canvas (embedding, endpoint, or build-time copy) is
   recorded as an integration question, not decided.
5. **Transport** — the local application/transport boundary between the SPA and the
   Python core is deliberately unselected.
6. **Automatic layout adoption** — whether ELK/elkjs is ever needed depends on real
   fragment sizes and editing workflows.

## Revisit conditions

- An authorized slice needs a currently deferred capability (docking, YAML/diff
  editing, automatic layout/routing, a frontend store).
- A selected library's licence, maintenance, or security condition materially
  changes.
- Evidence shows a selected library cannot be cleanly reconstructed from
  DeepPlant-owned semantic + presentation state.
- The existing deterministic layout policy proves insufficient for real fragments.
- A first-slice probe shows Vue Flow cannot support a required #69 interaction
  (e.g. a specific connection-point or schematic-editing behaviour).

## Related

- [engineering-editor-ux.md](engineering-editor-ux.md) — the Issue #69 interaction
  architecture this document supplies technology for.
- [reference-products.md](reference-products.md) — the canonical factual home for
  candidate projects, licences, upstream URLs, maintenance evidence, and
  provenance observations.
- [roadmap.md](../planning/roadmap.md) — current priority and the
  [re-evaluation gate](../planning/roadmap.md#re-evaluation-gate) that follows
  #39/#69/#70.
- [product.md](../planning/product.md) — MVP boundaries and the SPA direction.
- [direction.md](../planning/direction.md) — Stages 3–4 (engineering views,
  interactive editing), product context only.
- [architecture.md](../architecture/index.md) — current boundary map and durable
  invariants.
- [contracts/rendering.md](../../contracts/rendering.md),
  [dev/reference/svg-symbols.md](../reference/svg-symbols.md) — the existing
  presentation contract and symbol/anchor contract the canvas reuses.
- [ADR-0002](../decisions/ADR-0002-semantic-model-is-the-core.md),
  [ADR-0003](../decisions/ADR-0003-separate-semantic-and-presentation-models.md),
  [ADR-0009](../decisions/ADR-0009-separate-process-function-from-symbol-role.md),
  [ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md) — the
  decisions this document applies.
- [conventions.md](../workflow/conventions.md) — documentation conventions.
