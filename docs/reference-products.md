---
type: reference-product-landscape
status: active
source_of_truth_for:
  - future-generic-ux-and-infrastructure-research-principles
read_when:
  - engineering-view-planning
  - interactive-editor-planning
  - external-tool-or-library-evaluation
  - reuse-or-licensing-review
update_when:
  - candidate-evaluated-in-a-bounded-spike
  - upstream-license-or-scope-materially-changes
---

# Reference Products and Reuse Landscape

> **Status:** directional product and architecture research. This document selects
> no GUI framework, editor, renderer, layout engine, routing engine, dependency,
> adapter, or external-tool integration, and it authorizes no implementation.

## Purpose

DeepPlant should innovate primarily in canonical semantic engineering models,
engineering workflows, validation, interoperability, and domain-specific UX.

Generic capabilities — workspace shells, docking, graph interaction, routing,
layout, symbol manipulation, Git UX, editors, and CAD-like interaction — should be
studied systematically and reused from suitable existing projects where the
evidence shows reuse is preferable to reinvention.

> Existing tools are references, not architectural authorities. No external
> GUI or editor framework may dictate the canonical DeepPlant domain model.

The landscape below is deliberately a study list, not a plan.

## Scope and the reuse-first design rule

This document supports the directional
[Engineering Views](roadmap.md#stage-3--engineering-views) and
[Interactive Editing](roadmap.md#stage-4--interactive-editing) stages. It changes
nothing about their timing, and the
[anti-roadmap](roadmap.md#anti-roadmap--what-must-not-be-implemented-prematurely)
still governs: a future stage justifies no architecture today.

Future design rule:

> Before implementing a substantial generic capability — graph layout,
> orthogonal routing, docking, undo/redo, property grids, command palettes, tree
> views, diff viewers, symbol editors, or a workspace shell — perform a focused
> OSS landscape review first.

That review should establish the user problem, candidate scope and maturity,
licence and asset terms, the integration boundary, data ownership, and the
smallest evidence-producing vertical slice. It may conclude that a small
DeepPlant implementation is better; it must not assume that before comparing.

## Vocabulary

These terms are used consistently across this document.

| Term | Meaning |
|---|---|
| **direct reuse candidate** | Code could be considered as a dependency after technical and licence review. |
| **integration candidate** | A future in-process or protocol boundary may be evaluated. |
| **external-tool candidate** | A process, file, or API boundary is preferred over embedding. |
| **reference implementation** | Study behaviour and architecture; no code-reuse implication. |
| **UX inspiration** | Learn interaction patterns only. |
| **architecture inspiration** | Learn composition or layering patterns only. |
| **unsuitable / incompatible** | Not a direct-reuse option under the known terms. |
| **needs review** | Evidence is incomplete, version-sensitive, or unresolved. |

## Architectural invariants

[ADR-0002](decisions/ADR-0002-semantic-model-is-the-core.md),
[ADR-0003](decisions/ADR-0003-separate-semantic-and-presentation-models.md),
[ADR-0009](decisions/ADR-0009-separate-process-function-from-symbol-role.md),
and [ADR-0010](decisions/ADR-0010-dexpi-plant-pid-semantic-boundary.md) remain
authoritative. Reuse never relaxes them.

### The semantic model remains authoritative

A future UI node is never the canonical engineering object. Both the process and
the physical/P&ID model keep this direction:

```text
ProcessStep / ProcessStream / Equipment / Connection
                ↓
presentation and view state, owned outside the domain model
                ↓
GUI-framework node, edge, port, or inspector selection
```

The domain therefore stays usable from Python and the CLI. A GUI framework must
remain replaceable: its identifiers, lifecycle, mutation model, serialization
conventions, and widget state are never a reason to reshape the engineering
model.

### Presentation stays separate from semantics

```text
engineering semantics != presentation state != rendering-framework state
```

Coordinates, viewport and zoom, routing hints, docking state, selection, editor
layout, interactive handles, sheet tabs, and framework node/edge objects must not
silently become canonical engineering semantics. If evidence later requires a
persistent view model, it belongs outside semantic YAML and must be designed
deliberately, consistent with the deferral already recorded in
[ADR-0009](decisions/ADR-0009-separate-process-function-from-symbol-role.md).

### DeepPlant-specific differentiation

DeepPlant is not building another generic diagram editor, another CAD package,
another VS Code clone, or another process simulator. The differentiated layer is:

```text
canonical semantic engineering model
engineering semantics and process <-> physical relationships
engineering validation and rules
semantic diff and review
Git-native engineering workflow
interoperability and adapters
domain-specific orchestration
future AI operations over explicit engineering semantics
```

Generic graphical, workspace, and infrastructure capability is subordinate to
those outcomes and should be reused where feasible.

## IDE and workspace UX

Reference products: **Visual Studio Code (Code - OSS)**, **Eclipse Theia**, and
**JetBrains IDEs** where useful as a UX reference.

Concepts worth studying because engineering work needs them:

- activity bar / sidebar navigation
- project and workspace tree
- editor tabs, split views, breadcrumbs
- command palette and keyboard-centric workflows
- Problems / diagnostics panel
- terminal and output panels
- Git, diff, and review UX
- status bar

What makes this relevant to DeepPlant is not the layout. It is that these
patterns are proven ways to keep a large, structured, versioned body of
information navigable and reviewable.

DeepPlant should not clone VS Code. The Code - OSS source repository is MIT
licensed, but the Microsoft-branded Visual Studio Code distribution, its
marketplace, and its product terms are separate matters. The principle is to
reuse established IDE interaction patterns where they fit engineering work.

## Multi-view application architecture

Reference applications: **Blender**, **Godot**, and **JupyterLab**.

Concepts worth studying:

- several synchronized views over one underlying model
- object/tree selection synchronized with inspectors
- dockable and resizable panels
- context-specific editors
- property inspectors
- saved workspace layouts

For DeepPlant the durable hypothesis is that the following are views or editors
over the same engineering state rather than independent documents:

```text
PFD
P&ID
YAML
equipment tables
property inspector
simulation views
Git diff
validation results
```

That multiplicity is exactly the reason the canonical model must stay outside
any one view. Their licences — Blender under the GPL, Godot and JupyterLab under
permissive terms — are recorded only to keep the reference honest; none of them
selects a DeepPlant implementation path.

## Engineering schematic, CAD, and EDA UX

Reference products: **KiCad**, **FreeCAD**, and other strong OSS engineering
editors discovered during research.

Concepts worth studying:

- symbol libraries and symbol organization
- ports and connection points
- snapping behaviour
- wiring and routing interaction
- hierarchical navigation
- object and property editing
- engineering validation feedback
- generated lists and tables
- cross-highlighting between artifacts
- selection and multi-selection behaviour
- multi-sheet workflows

These products solve related interaction problems well, and their UX deserves
study. Their domain models must not be copied into DeepPlant: a schematic net, a
PCB net, or a CAD parametric feature is not a plant-engineering semantic concept.
KiCad and FreeCAD are also copyleft; any code-level reuse or embedding needs its
own evaluation rather than being implied by this reference.

## Close-domain reference: IPD Studio

**IPD Studio** is an important close-domain reference product: a browser-based
intelligent P&ID editor that treats the drawing as a view over structured
engineering data rather than as the data itself. That is directly adjacent to
DeepPlant's thesis, which makes it worth studying closely — and studying only.

Areas worth studying as product and UX concepts:

- **Symbol palette** — searchable palette, symbol variants, palette organization.
- **Connection editing** — connection points, compatible-endpoint rules, and how
  an editor guides a valid connection.
- **Orthogonal routing** — how the editor produces industrial-looking orthogonal
  routes rather than arbitrary curves.
- **Waypoints** — user-adjustable route points and how they survive reconnect.
- **Snapping and magnetic docking** — alignment and attachment feedback.
- **Multi-sheet P&ID workflow** — sheets, navigation between them, and
  cross-sheet consistency.
- **Property editing** — editing tags and properties alongside the graphic.
- **Line lists and instrument indexes** — generating engineering registers from
  the model rather than maintaining them by hand.
- **Validation UX** — surfacing engineering problems and helping the user reach
  the offending object.
- **DEXPI-related capability** — import/export behaviour and its stated limits.
- **Persistence and serialization** — how a project is stored, and what that
  implies for review and diffing.

The DeepPlant-specific boundary is firm: IPD Studio's document format, GUI
framework choice, and internal data structures must not become DeepPlant's
canonical model or be copied. Every item above is a question about UX and
concept, not an interface to adopt.

### Licensing boundary

Licence status is the decisive constraint here, and the two boundaries must stay
separate:

| Aspect | Status | DeepPlant consequence |
|---|---|---|
| Code that may legally be reused | Not established. The repository URL recorded in [standards.md](standards.md#ipd-studio-historicalcurrent-symbol-assets) was **not reachable at the 2026-09-30 re-check**, so neither the current licence nor the historical version boundary could be re-confirmed from upstream at that time. | Treat as **needs review**. Do not incorporate code. |
| Code that must not be incorporated | Any release whose terms are source-available/non-commercial or otherwise incompatible with DeepPlant's public AGPL-3.0-only repository and commercial-use requirements. The earlier assessment recorded in [standards.md](standards.md) placed current releases (`v0.13.0+`) under a non-commercial source-available licence. | Not a reuse candidate; re-verify terms before any future claim. |
| UX and architectural concepts that may be studied | The product's interaction and workflow ideas are public product behaviour. | Study freely as **UX inspiration**. |

Do not copy source code from IPD Studio. The already-recorded version-based
assessment in [standards.md](standards.md) and
[ADR-0007](decisions/ADR-0007-standards-and-symbol-provenance.md) remains the
governing provenance policy; this document adds no new permission, and a future
reuse proposal must pin an exact upstream revision and verify the licence text
at that revision before anything else.

## Graph and editor implementation candidates

The projects below are candidates for future evaluation, not selections. Nothing
here may be introduced as a dependency by this document.

| Project | Purpose | License | Possible DeepPlant use | Architectural boundary | Strengths | Risks / limitations | Status |
|---|---|---|---|---|---|---|---|
| Vue Flow | Vue 3 node/flowchart component: pan, zoom, drag, selection, minimap, graph/state utilities | MIT | Interactive graph surface for a future editor view | Framework node/edge state stays replaceable and non-canonical | Complete interaction vocabulary, active project | Vue commitment; generic flowchart semantics do not encode P&ID behaviour | candidate |
| React Flow (xyflow) | React and Svelte node-editor libraries | MIT | Comparison baseline, or graph surface in a React stack | Same boundary; application state stays outside the domain model | Very mature ecosystem, strong documentation | Framework lock-in; graph state ownership must be designed | candidate |
| ELK / elkjs | Automatic graph layout; port-aware layered layout plus routing infrastructure | Needs review: upstream repository licence metadata reports `NOASSERTION`; ELK is an Eclipse project whose exact licence text must be confirmed at the pinned revision | Layout and routing evaluation against a real engineering fragment | Consumes a projection; positions and routes are presentation-only | Purpose-built for node-link diagrams with ports and direction | Layout-only (no rendering); incremental layout and packaging need testing | needs review |
| Konva | Canvas 2D scene graph with events, drag/drop, transforms, export | MIT | Low-level canvas interaction and rendering substrate | Owns transient scene state only | Flexible, widely used, performance-oriented | DeepPlant still owns editor semantics, routing, widgets, accessibility | candidate |
| Fabric.js | Canvas library with SVG-to-canvas and canvas-to-SVG parsing | MIT | Comparison for object manipulation and SVG interop | Object serialization must never become engineering persistence | Rich object model, SVG interop | Application-owned semantics remain DeepPlant's responsibility | candidate |
| Paper.js | Vector graphics scripting framework | MIT | Comparison for vector geometry manipulation | Geometry only; not a model or shell | Strong vector geometry primitives | No engineering or workspace concepts | candidate |

Any evaluation must start from a concrete evidence need, and each candidate must
be assessed for data ownership, replaceability, and licence fit before adoption.

## External engineering tools and simulation

The same strategy applies outside the UI. The reuse mode matters more than the
product name.

| Project / class | What DeepPlant can learn or evaluate | License | Likely reuse mode | DeepPlant-specific boundary |
|---|---|---|---|---|
| FreeCAD | Workbenches, property panels, multi-view CAD UX, parametric editing | LGPL-2.1 | UX/architecture reference; possible external-tool or file interchange | No CAD kernel or CAD model in the canonical domain model |
| DWSIM | Steady-state and dynamic process simulation and flowsheet workflow | GPL-3.0 | external-tool candidate, adapter, or file interchange | The canonical model must not become simulator-specific |
| Other process simulators, CAPE-OPEN, vendor engineering tools | Semantic exchange, workflow, and validation behaviour | varies | adapter, external process/tool, or file interchange | Each needs its own licence and boundary evaluation |

For copyleft software, no unsupported legal conclusion is drawn here. The licence
is recorded, and the integration strategy must be evaluated before
implementation. Note that the DWSIM repository consulted reported an **archived**
state at the 2026-09-30 check, so its current upstream home and release line must
be confirmed before any adapter work is proposed.

## Licensing strategy

This is an engineering decision framework, not legal advice. Each branch below
describes how DeepPlant intends to think about a licence class, not a conclusion
about any specific project.

```text
permissive OSS
    → strong candidate for direct reuse if the architecture also fits

weak copyleft / reciprocal licenses
    → evaluate case by case and preserve clear boundaries

strong copyleft
    → evaluate carefully, especially in light of DeepPlant's future
      licensing strategy; external-tool or adapter boundaries may
      sometimes be preferable

source-available / non-commercial / incompatible licensing
    → useful as product, UX, architecture, and workflow references;
      do not copy code unless the license explicitly permits the
      intended use
```

Two consequences follow:

- "Permissive" removes a licence obstacle; it does not by itself justify a
  dependency. Architecture fit, maintenance health, and boundary clarity still
  decide.
- "Copyleft" does not automatically mean unusable. It means the integration
  boundary must be chosen deliberately and evaluated before implementation.

### Code licences and asset licences are evaluated separately

A permissive code licence says nothing about the symbols, icons, templates, or
graphics shipped with or generated by that code. For an engineering product,
asset licensing is frequently the harder question:

- PFD/P&ID symbol libraries
- icons and UI glyphs
- drawing templates and title blocks
- standard-derived graphics
- third-party engineering symbol packs

Asset decisions follow the provenance, restricted-standards, and
human-verification rules already recorded in [standards.md](standards.md) and
[ADR-0007](decisions/ADR-0007-standards-and-symbol-provenance.md). This document
deliberately does not restate or extend them; it only records that a reuse
proposal must answer the code question and the asset question independently.

## Target UX direction (hypothesis)

The following is the current high-level hypothesis for a future DeepPlant
engineering IDE. It is a **directional UX hypothesis, not an implementation
specification**: no framework, no component library, no windowing model, and no
layout engine is chosen or implied.

```text
┌──────────────────────────────────────────────────────────────┐
│ command/menu/breadcrumb area                                 │
├────┬──────────────┬──────────────────────────┬───────────────┤
│    │ Plant /      │                          │ Properties /  │
│ A  │ Project tree │      Main editor         │ Inspector     │
│ c  │              │                          │               │
│ t  │ Process      │ PFD / P&ID / YAML /      │ selected      │
│ i  │ Equipment    │ table / diff / report    │ engineering   │
│ v  │ Documents    │                          │ object        │
│ i  │              │                          │               │
│ t  │              │                          │               │
│ y  │              │                          │               │
├────┴──────────────┴──────────────────────────┴───────────────┤
│ Problems │ Validation │ Git │ Calculations │ Agent │ Terminal│
├──────────────────────────────────────────────────────────────┤
│ branch │ validation │ interoperability │ project status      │
└──────────────────────────────────────────────────────────────┘
```

The more important principle is not the layout but synchronized engineering
context across views:

```text
select P-101 in PFD
        ↓
highlight P-101 in Plant tree
        ↓
show P-101 in Properties
        ↓
locate its semantic representation
        ↓
show relevant validation / calculations / Git changes
```

The value is that a selection resolves to one identified semantic object and
every view reflects that same object. Synchronization is an engineering-context
feature, not a requirement to mimic an IDE shell.

## Reuse matrix

Licences below were checked from upstream sources on **2026-09-30** and are a
snapshot, not a standing fact; re-verify at the pinned revision before proposing
anything.

| Project | Domain | What DeepPlant can learn / reuse | License | Expected reuse mode | DeepPlant-specific boundary |
|---|---|---|---|---|---|
| VS Code (Code - OSS) | IDE UX | Navigation, diagnostics, command palette, Git/diff/review, status bar, keyboard workflows | MIT for the source repository; Microsoft-branded distribution and marketplace are separate | UX inspiration | No VS Code clone, no workspace mandate |
| Eclipse Theia | IDE framework | Docked workspace composition, extensibility, desktop/web app shell | EPL-2.0 (upstream README also lists a secondary GPL-2.0-with-Classpath-Exception path) | architecture reference / needs review | Framework must not select the domain model |
| JetBrains IDEs | IDE and tooling UX | Inspections, refactoring, navigation, review, keyboard-centric tooling | Products are proprietary; `intellij-community` source is Apache-2.0 with JetBrains Open-Source Build Terms (metadata reports `NOASSERTION`) | UX inspiration / needs review for code | No reuse permission inferred from source availability |
| Blender | Multi-editor application | Synchronized editors, selection/inspector patterns, workspace layouts | GPL | UX/architecture inspiration | No embedding conclusion; no code reuse implied |
| Godot | Multi-pane editor | Editor composition, inspector interaction, dock behaviour | MIT | UX/architecture inspiration | No engine selection |
| JupyterLab | Multi-document workspace | Multi-document tabs, output panels, layout and extension concepts | BSD-3-Clause | UX/architecture inspiration | Engineering semantics stay outside UI documents |
| KiCad | EDA schematic / PCB | Symbols, ports, snapping, hierarchy, cross-highlighting, generated artifacts | GPL-3.0 | reference implementation | No EDA model adoption; no code reuse without evaluation |
| FreeCAD | Parametric CAD | Workbenches, property panels, multi-view engineering UX | LGPL-2.1 | reference / external-tool candidate | No CAD kernel or CAD model commitment |
| IPD Studio | Intelligent P&ID editor | P&ID editor UX, palette, routing/waypoints, generated registers, validation UX, DEXPI workflow | Not re-verifiable at the 2026-09-30 check; earlier project record: current releases non-commercial source-available, versions through `v0.12.1` AGPL-3.0-only | reference implementation (product/UX study only) | No code, format, or asset reuse pending verified terms |
| Vue Flow | Web graph editor | Generic node/edge interaction for a future editor view | MIT | direct reuse candidate pending a slice | Framework objects remain transient view state |
| React Flow (xyflow) | Web graph editor | Comparison baseline for graph interaction | MIT | candidate | Graph state ownership stays in the presentation layer |
| ELK / elkjs | Layout and routing | Port-aware automatic layout and routing evaluation | needs review (metadata `NOASSERTION`; confirm project licence text) | candidate / needs review | Layout input and output are presentation-only |
| Konva | Canvas graphics | Interactive scene graph and canvas rendering | MIT (per upstream `LICENSE`; metadata reports `NOASSERTION`) | candidate | No semantic persistence in scene objects |
| Fabric.js | Canvas graphics | Object manipulation, SVG interop comparison | MIT | candidate | No engineering persistence in canvas serialization |
| Paper.js | Vector graphics | Vector geometry and path manipulation | MIT (per upstream `LICENSE.txt`; metadata reports `NOASSERTION`) | candidate | Geometry only; no model or shell |
| DWSIM | Process simulation | Simulator workflow, flowsheet semantics, interchange questions | GPL-3.0 (repository consulted reported `archived` at the 2026-09-30 check) | external-tool / adapter candidate | Simulator data must not define canonical semantics |

## Research basis

Licence and capability claims above were checked against upstream sources on
**2026-09-30**. Primary sources consulted:

- [microsoft/vscode](https://github.com/microsoft/vscode) — `LICENSE.txt` (MIT).
- [eclipse-theia/theia](https://github.com/eclipse-theia/theia) — `README.md`
  licence section and repository licence metadata (EPL-2.0 plus a secondary
  GPL-2.0-with-Classpath-Exception path).
- [JetBrains/intellij-community](https://github.com/JetBrains/intellij-community)
  — `LICENSE.txt` (JetBrains Open-Source Build Terms over Apache-2.0 software).
- [blender/blender](https://github.com/blender/blender) — `COPYING` (GNU GPL;
  upstream development lives at <https://projects.blender.org/blender/blender>).
- [godotengine/godot](https://github.com/godotengine/godot) — `LICENSE.txt`.
- [jupyterlab/jupyterlab](https://github.com/jupyterlab/jupyterlab) —
  `LICENSE` (BSD 3-Clause).
- [KiCad/kicad-source-mirror](https://github.com/KiCad/kicad-source-mirror) —
  repository licence metadata (GPL-3.0); upstream development is on GitLab.
- [FreeCAD/FreeCAD](https://github.com/FreeCAD/FreeCAD) — repository licence
  metadata (LGPL-2.1).
- IPD Studio — the upstream repository URL recorded in
  [standards.md](standards.md) returned HTTP 404 at the 2026-09-30 check, and
  the maintainer account no longer lists it publicly, although it is still
  advertised. **Unresolved.**
- [bcakmakoglu/vue-flow](https://github.com/bcakmakoglu/vue-flow) — `LICENSE`
  (MIT).
- [xyflow/xyflow](https://github.com/xyflow/xyflow) — `LICENSE` (MIT).
- [kieler/elkjs](https://github.com/kieler/elkjs) and
  [eclipse-elk/elk](https://github.com/eclipse-elk/elk) — metadata
  `NOASSERTION`; licence text not yet confirmed.
- [konvajs/konva](https://github.com/konvajs/konva) — `LICENSE` (MIT).
- [fabricjs/fabric.js](https://github.com/fabricjs/fabric.js) — `LICENSE`
  (MIT).
- [paperjs/paper.js](https://github.com/paperjs/paper.js) — `LICENSE.txt`
  (MIT).
- [DanWBR/dwsim](https://github.com/DanWBR/dwsim) — repository licence metadata
  (GPL-3.0); repository reported `archived`.

Where repository licence metadata and the licence file disagree (Konva,
Paper.js, ELK, `intellij-community`), the pinned licence text governs and must be
read directly.

## Unresolved questions

Deliberately open. These are research items, not approved work.

- Which GUI technology, if any, is appropriate for the first interactive slice?
- Is a graph framework or a lower-level canvas library the better fit for
  engineering schematic editing?
- Is an external layout engine needed, or is a small domain-specific layout
  adequate for the views DeepPlant actually derives?
- Where would a persistent presentation/view model live, if evidence ever
  requires one?
- What is the current authoritative upstream location and licence of IPD Studio,
  and would any of its code or assets actually qualify for reuse?
- What is the current upstream home and licence of the DWSIM release line a
  future adapter would target?
- Which reuse decisions would need legal review rather than an engineering
  decision?

## Explicitly deferred

Nothing in this document authorizes:

- choosing a GUI framework, graph library, layout or routing engine, or shell;
- introducing any dependency, adapter, integration, or renderer;
- creating frontend directories, speculative APIs, or interfaces;
- adding source code or tests solely because of this documentation slice;
- changing the current planning horizon or the implementation sequence;
- promoting engineering-view or interactive-editing work out of its current
  horizon.

## Related

- [roadmap.md](roadmap.md) — Stage 3 (Engineering Views) and Stage 4
  (Interactive Editing) are the stages this landscape informs; the anti-roadmap
  still governs.
- [standards.md](standards.md) — standards registry, symbol provenance policy,
  and the existing IPD Studio asset assessment.
- [rendering.md](rendering.md) — the implemented headless renderer and its
  explicit deferrals.
- [svg-symbols.md](svg-symbols.md) — the symbol and anchor contract a future
  editor would consume.
- [architecture.md](architecture.md) — current architecture and durable
  boundaries.
- [ADR-0002](decisions/ADR-0002-semantic-model-is-the-core.md),
  [ADR-0003](decisions/ADR-0003-separate-semantic-and-presentation-models.md),
  [ADR-0007](decisions/ADR-0007-standards-and-symbol-provenance.md),
  [ADR-0009](decisions/ADR-0009-separate-process-function-from-symbol-role.md),
  [ADR-0010](decisions/ADR-0010-dexpi-plant-pid-semantic-boundary.md).
