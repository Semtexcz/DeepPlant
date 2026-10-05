---
type: governance
status: active
canonical_for:
  - frontend-design-to-code-workflow
read_when:
  - frontend-design-work
  - frontend-change
  - editor-frontend-work
  - implement-change
  - review-change
update_when:
  - frontend-design-workflow-change
depends_on:
  - docs/dev/frontend/index.md
  - docs/dev/frontend/architecture.md
  - docs/dev/frontend/styling.md
  - docs/dev/workflow/quality.md
  - docs/dev/planning/roadmap.md
decision:
  - docs/dev/decisions/ADR-0002-semantic-model-is-the-core.md
  - docs/dev/decisions/ADR-0003-separate-semantic-and-presentation-models.md
  - docs/dev/decisions/ADR-0009-separate-process-function-from-symbol-role.md
  - docs/dev/decisions/ADR-0016-process-physical-realization-boundary.md
evidence:
  - docs/dev/research/engineering-editor-ux.md
  - docs/dev/research/engineering-editor-reuse-architecture.md
superseded_by: null
---

# Frontend Design-to-Code Workflow

> **Question this document answers:** how is DeepPlant frontend UI designed in
> Figma, and how is that design translated into `apps/editor/` implementation
> through coding agents, without Figma becoming the source of truth for domain
> semantics, application architecture, or business logic?

This is developer-owned governance for the **design → behavior → issue →
implementation** path of the Engineering Editor frontend. It defines the official
workflow, the source-of-truth boundaries, and the context a coding agent receives.

It is a documentation policy. It adds no design tool, no Figma integration, no MCP
integration, no design-token infrastructure, no Vue component, and no frontend
functionality.

## Status vocabulary

| State | Meaning |
|---|---|
| **Implemented** | Already true in the repository today. |
| **Canonical rule** | Required for future frontend work, even where no artifact exists yet. |
| **Future direction** | Direction decided here; it applies once the relevant artifact is actually created. |

**Current reality (implemented).** DeepPlant has the authoritative engineering
documents (see [architecture.md](../architecture/index.md),
[contracts/](../../contracts/index.md)) and the canonical frontend engineering
contract for `apps/editor/` ([frontend/index.md](index.md)). It has **no** Figma
file under version control, **no** UX-contract directory, **no** `design/tokens/`
tree, **no** Figma MCP integration, and **no** design-token generation pipeline.
This document therefore defines the workflow to follow when that UI work starts;
it must not be read as a description of implemented tooling.

No new ADR is created. The source-of-truth boundaries below restate accepted
boundaries — [ADR-0002](../decisions/ADR-0002-semantic-model-is-the-core.md),
[ADR-0003](../decisions/ADR-0003-separate-semantic-and-presentation-models.md),
[ADR-0009](../decisions/ADR-0009-separate-process-function-from-symbol-role.md),
[ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md) — and
apply them to design tooling. Figma is a design surface, never a semantic or
architectural authority.

## The workflow

```text
Product requirement / user workflow
        │
        ▼
UX contract draft
        │
        ▼
Figma wireframe
        │
        ▼
Figma final design
        │
        ├──────────────┐
        ▼              ▼
UX contract       design tokens
in Git                 │
        │              │
        └──────┬───────┘
               ▼
          GitHub Issue
               │
               ▼
         Coding agent
      Figma MCP preferred
      Dev Mode fallback
               │
               ▼
        Vue implementation
               │
               ▼
   visual + behavioral review
               │
               ▼
              PR
```

## Sources of truth

| Source | Owns | Must never own |
|---|---|---|
| Figma | the visual specification | domain semantics, behavior, architecture |
| UX contract in Git | behavioral intent | visual detail, engineering meaning |
| domain documentation / schemas | engineering semantics | presentation and UI layout |
| API contracts | transport, commands, queries | UX intent, domain rules |
| Vue implementation | implementation only | new UX or new domain semantics |

### Figma — the visual specification

Figma owns **what the user sees**:

- layout, spacing, typography, colors, visual hierarchy;
- component appearance, variants, and visual states;
- composition of screens;
- responsive / resize behavior where it is represented;
- the visual portion of interaction states (hover, selected, disabled, error).

Figma must **not** define domain semantics. A symbol, layer, or component name in
Figma never becomes a DeepPlant domain concept, and a visual grouping never
becomes an ownership boundary. The engineering semantics DeepPlant ships are the
semantic contracts and the ADRs, not a design file.

### UX contracts in Git — behavioral intent

Git-tracked UI/UX documentation owns **what the UI does**:

- what actions do, and their consequences;
- selection behavior;
- synchronization between views;
- keyboard interaction;
- transitions and focus movement;
- editing behavior;
- validation behavior and how model state is surfaced;
- loading, error, empty, and read-only states;
- relationships between UI surfaces.

Behavior is authoritative in Git, not in Figma and not in a prototype. A Figma
prototype may *demonstrate* behavior; it does not own it.

### Domain model — engineering semantics

Existing DeepPlant domain documentation and schemas own engineering meaning:
entity identity, the Process vs Physical boundary, `ProcessStep` vs `Equipment`,
`ProcessPort` vs a physical `Port`/nozzle, `ProcessStream` vs a physical
`Connection`/piping line, and the validation semantics that belong to the
engineering model. The UI **consumes** these concepts and never redefines them.

Canonical homes: [contracts/plant-model.md](../../contracts/plant-model.md),
[contracts/process-model.md](../../contracts/process-model.md),
[contracts/physical-piping.md](../../contracts/physical-piping.md),
[contracts/rendering.md](../../contracts/rendering.md), and the boundary map in
[architecture.md](../architecture/index.md). UI copy must not rename a domain
concept to fit a panel title.

### API contracts — data flow

The local application boundary and its transport own how data flows: commands,
queries, request/response structures, persistence interaction, and the
frontend/backend boundary. Today that boundary is the DeepPlant-owned read-only
Process/PFD projection with its hand-written, explicitly validated DTO contract
(`apps/editor/src/process-pfd/transport/`), described in
[architecture.md](../architecture/index.md). The frontend never invents a second
model of the same data, and the transport shape stays framework-free
([typescript.md](typescript.md)).

### Vue implementation — implementation only

Vue code owns implementation. Implementation must not silently introduce new UX or
new domain semantics: if the required behavior is not in the UX contract, or the
required concept is not in the domain or API contracts, the gap is resolved in the
owning document first (see [Reconciliation](#stage-j--reconciliation)).

## UI behavior documentation (`docs/ui/`) — canonical rule

Behavioral intent is documented in Git in a dedicated UI layer:

```text
docs/ui/
    pfd-editor/
        index.md
        equipment-inspector.md
```

This is the **intended convention**, not a directory that exists today: no
`docs/ui/` tree is created by this document, and none should be created until a
real UI surface needs a behavior contract. One file per UI surface, named for the
domain concept rather than for a screen position. Keep it small: a UX contract
states behavior, not pixels, and it links to the domain and API contracts instead
of restating them.

## Lifecycle of a UI feature — canonical rule

| Stage | Output | Owner |
|---|---|---|
| A | user workflow / product requirement | product scope + the GitHub Issue |
| B | UX contract draft | behavior documentation (`docs/ui/`) |
| C | Figma wireframe | design |
| D | design review | design + engineering review |
| E | final Figma design (frames/states) | design |
| F | extracted design-system primitives | design + frontend |
| G | GitHub Issue | planning + the Issue author |
| H | Vue implementation | the coding agent |
| I | behavioral + visual review | reviewer |
| J | reconciliation across design, contract, Issue, code | the author |

### Stage A — user workflow / product requirement

Start from the task the engineer must accomplish, not from a screen.

```text
A process engineer selects a pump on the PFD and edits its process properties.
```

Define the user goal, the primary actions, the important states, and the
constraints. This stage consumes product authority
([product.md](../planning/product.md), [roadmap.md](../planning/roadmap.md), the
relevant Issue); it does not create product scope.

### Stage B — UX contract draft

Define behavior before polishing visuals. A UX contract describes behavior such
as:

```text
When Equipment is selected:

- select the corresponding object in the Engineering Explorer
- highlight it on Engineering Canvas
- update the Inspector
- expose validation state
- preserve current canvas viewport
```

Avoid pixel-level design detail here; that belongs to Figma.

### Stage C — Figma wireframe

Create a low-fidelity design to test information architecture, hierarchy,
navigation, panel placement, discoverability, and workflow efficiency. Do not
optimize visual polish this early.

### Stage D — design review

Review the wireframe primarily as an **engineering workflow**, not as a visual
artifact:

- Is the primary task obvious?
- How many interactions are required?
- Is important context permanently visible?
- Does the design waste canvas space?
- Does it scale to information-dense engineering work?
- Are Process and Physical concepts understandable without conflating them?
- Are validation and model state visible?
- Does the UI behave like a professional engineering application rather than a
  generic SaaS dashboard?

The interaction architecture behind these questions is already decided in
[engineering-editor-ux.md](../research/engineering-editor-ux.md); that document is
the interaction authority this review checks against.

### Stage E — final Figma design

Produce explicit frames/states rather than one overloaded frame:

```text
PFD Editor / No Selection
PFD Editor / Equipment Selected / Default
PFD Editor / Equipment Selected / Validation Error
```

Use reusable Figma components and variables instead of repeated arbitrary values,
so that a frame names a design decision rather than a set of copied pixels. State
names here are design-frame names; they do not name domain objects.

### Stage F — design-system extraction (incremental, not up front)

Do **not** require a large design-system project before UI work can start. Extract
reusable primitives incrementally, when repetition is real:

```text
DeepPlant/Button
DeepPlant/IconButton
DeepPlant/Panel
DeepPlant/Tree
DeepPlant/TreeItem
DeepPlant/Tab
DeepPlant/PropertyRow
DeepPlant/PropertySection
DeepPlant/StatusBadge
DeepPlant/Toolbar
DeepPlant/CanvasToolbar
```

The corresponding implementation may later evolve toward components such as:

```text
DpButton.vue
DpIconButton.vue
DpPanel.vue
DpTree.vue
DpTreeItem.vue
DpPropertyRow.vue
```

These are **future direction, not current implementation requirements**: none of
these components exists today, and this document prescribes no component set. When
an extraction does happen it follows the existing rules — feature-first ownership,
a new component only when a second real use exists, and the styling ownership and
size guardrails in [architecture.md](architecture.md), [styling.md](styling.md),
and [frontend/index.md](index.md).

### Stage G — GitHub Issue

The implementation Issue references:

- the exact Figma frame/state;
- the relevant UX contract;
- the relevant domain/API contracts;
- implementation boundaries;
- explicit acceptance criteria.

Issues represent **small vertical or horizontal slices**, never vague tasks:

```text
bad:  Implement the PFD editor.
good: Implement application shell with empty engineering canvas.
good: Implement Equipment selection and Inspector synchronization.
```

Issue creation follows the planning rules in
[planning/index.md](../planning/index.md): bounded enough to end in a PR or a
concrete deliverable, and never created merely to fill a milestone.

### Stage H — coding-agent implementation

The agent receives structured context:

```text
GitHub Issue
+
repository
+
UX contract
+
Figma frame
+
design tokens/components
+
domain/API contracts
```

It consumes the design through:

1. **Figma MCP**, when available;
2. otherwise **Figma frame + Dev Mode + the UX contract**.

The agent must not infer missing product behavior from visual appearance alone.

Before implementing, the agent inspects:

- the existing frontend architecture ([architecture.md](architecture.md));
- the existing Vue components and their ownership;
- existing tokens and styles ([styling.md](styling.md));
- the relevant domain and API contracts
  ([contracts/](../../contracts/index.md), [architecture.md](../architecture/index.md)).

Then it identifies reusable components, missing UI primitives, the required
states, any architecture conflict, and the smallest coherent implementation slice
— and only then starts implementing. Gates and test expectations are those in
[quality.md](../workflow/quality.md) and [testing.md](testing.md); the frontend
review checklist in [frontend/index.md](index.md) applies unchanged.

### Stage I — review

Review a frontend PR along at least two independent axes.

**Behavioral conformance** — compared against the UX contract, the Issue
acceptance criteria, and the domain/API contracts.

**Visual conformance** — compared against the Figma frame, the design tokens, and
the component variants/states.

A visually accurate implementation with wrong behavior is **not** complete. A
behaviorally correct implementation that ignores the approved visual design is
**also not** complete. The frontend review checklist in
[frontend/index.md](index.md) remains the code-level checklist for both axes.

### Stage J — reconciliation

If implementation reveals a flaw in the design, do not silently patch the behavior
in code. Reconcile:

```text
Figma
+
UX contract
+
Issue/acceptance criteria
+
implementation
```

The merged implementation and the authoritative design/behavior documentation must
agree. Depending on where the flaw is, that means updating the Figma frame, the
behavior contract, the Issue acceptance criteria, or the code — never leaving code
as the only place the real behavior is recorded.

## Figma MCP and Dev Mode policy

### Preferred

```text
Figma MCP + UX contract + repository context
```

Preferred because the agent reads **structured** design information — components,
variables, layout properties, and state variants — instead of relying on
screenshots.

### Supported fallback

```text
Figma frame + Dev Mode + UX contract
```

This fallback must remain sufficient to implement a feature. The workflow must
**not require** Figma MCP: no step in this document depends on an MCP server, and
an Issue must stay implementable without one.

### Screenshot-only workflow

Screenshots are a fallback/reference mechanism, not the canonical design-to-code
interface. Screenshots lose:

- component identity;
- variables;
- spacing rules;
- variants;
- resize behavior;
- component boundaries;
- design tokens.

A screenshot can therefore never be the authoritative visual input when the frame
is available.

## Design tokens — future direction

Nothing below exists yet; there is no token pipeline, no `design/` directory, and
no generated frontend variables in this repository today.

Current styling already uses semantic `--dp-*` tokens in
`apps/editor/src/styles.css` plus the UnoCSS utility layer, with styling ownership
canonical in [styling.md](styling.md). That is the existing semantic-token
practice, not the design-token pipeline described here.

The desired direction is semantic tokens over arbitrary values:

```text
color/background/canvas
color/background/panel
color/border/default

space/1
space/2
space/3
space/4

radius/small
radius/medium

font/body
font/label
font/code
```

and a flow of the form:

```text
Figma variables
      │
      ▼
versioned design tokens
      │
      ▼
generated/consumed frontend variables
```

Where it eventually lives, a future repository structure might contain:

```text
design/
    tokens/
```

Do not create token infrastructure, a `design/` tree, or a generation step until a
concrete requirement and its ownership are decided. Until then the existing
`--dp-*` tokens in [styling.md](styling.md) are the only token layer.

## Naming and traceability — canonical rule

The same UI concept keeps the same name across design, behavior, Issue, and code,
using the repository's own terminology:

```text
Figma:
PFD Editor / Inspector / Equipment

UX contract:
docs/ui/pfd-editor/equipment-inspector.md

Vue:
EquipmentInspector.vue

GitHub Issue:
Implement Equipment Inspector
```

The goal is semantic traceability:

```text
design
↔
behavior
↔
issue
↔
implementation
```

so that a human or an agent can move from a Figma frame to the behavior contract,
the Issue, and the component without guessing. Two constraints apply:

- **Domain concepts keep their repository names.** `ProcessStep`, `ProcessStream`,
  `Equipment`, `Port`, and `Connection` mean what the contracts say they mean; a
  nicer-sounding UI label does not rename them.
- **UI surface names follow the established interaction vocabulary.**
  [engineering-editor-ux.md](../research/engineering-editor-ux.md) already names
  the permanent surfaces (Engineering Explorer, selection-driven Inspector,
  Problems strip, editor views/tabs). Reuse those names instead of inventing a
  parallel set; in particular, use **Engineering Explorer**, not "Project
  Explorer", because the interaction architecture explicitly requires the explorer
  to expose engineering concepts rather than filesystem structure.

Where a Figma or product name conflicts with an established repository name,
reconcile the name deliberately instead of letting two vocabularies coexist.

## Pilots — future direction

The workflow is proven by real pilots. This document selects them; it does **not
implement** them.

### First pilot — DeepPlant Application Shell

```text
Activity Bar
+ Engineering Explorer
+ Document Tabs
+ empty Engineering Canvas
+ Inspector
+ Bottom Panel
+ Status Bar
```

This is the recommended first pilot because it:

- establishes the major layout primitives;
- exercises information architecture;
- creates reusable UI foundations;
- avoids prematurely implementing complex process-engineering behavior.

**Current state:** only a fraction of this exists. `App.vue` is a thin composition
root that owns the application chrome (identity and the active view) and the
toolbar, and the Process/PFD page renders the canvas, notices, a read-only
Inspector, and a status strip
([architecture.md](architecture.md)). Activity Bar, a full Engineering Explorer
tree, document tabs, a Bottom Panel, and a real status bar are **not implemented**.
The pilot's surface names must be reconciled with the current repository layout in
Stage G before implementation starts.

### Second slice — equipment selection through the whole model

```text
Equipment on canvas
        ↓
select
        ↓
Engineering Explorer synchronized
        ↓
Equipment Inspector
        ↓
edit property
        ↓
model change
        ↓
validation state
```

This slice is the one that eventually validates the entire path:

```text
Figma
→ UX contract
→ GitHub Issue
→ coding agent
→ Vue
→ DeepPlant model
```

It depends on semantic editing and save/mutation, which the current editor slice
deliberately does not have (see [roadmap.md](../planning/roadmap.md)); it is
therefore directional context here, not an authorized next task. The roadmap, not
this document, decides when it becomes `Now`.

## Relationship to Figma Make — canonical rule

- **Figma Design is the default design tool.**
- **Figma Make is not required** for this workflow.
- Figma Make may be used selectively for **interaction experiments or throwaway
  prototypes**.
- Production implementation must still happen in the real DeepPlant frontend
  codebase (`apps/editor/`).
- Do **not** create a parallel implementation architecture in Figma Make, and do
  not treat generated code as a deliverable or as a starting branch.

## Coding-agent prompt template

A reusable shape for an implementation Issue that instructs a coding agent.
Adapt names to the current repository terminology.

```text
Implement <feature>.

Design:
<Figma frame URL>

UX contract:
<repo path>

Relevant domain/API contracts:
<repo paths>

Use the referenced Figma design as the authoritative visual specification.
Use the UX contract as the authoritative behavioral specification.

Prefer Figma MCP when available.
Otherwise use Figma Dev Mode / structured design inspection.

Before implementation:
1. inspect the referenced design,
2. inspect existing frontend components and styles,
3. inspect relevant domain/API contracts,
4. identify reusable components,
5. identify missing primitives,
6. identify any design/architecture conflict.

Do not invent product behavior not defined by the UX contract.
Do not redefine domain semantics in the frontend.
Do not hard-code values that should come from existing design tokens/components.

Implement the smallest coherent slice satisfying the acceptance criteria.
```

## Related

- [index.md](index.md) — the frontend engineering contract this workflow feeds
  into, including the review checklist every frontend PR uses.
- [architecture.md](architecture.md) — the current frontend composition and
  boundaries a design must fit.
- [styling.md](styling.md) — the current semantic-token and styling ownership.
- [engineering-editor-ux.md](../research/engineering-editor-ux.md) — the
  interaction authority and the permanent-surface vocabulary.
- [engineering-editor-reuse-architecture.md](../research/engineering-editor-reuse-architecture.md)
  — the reuse-first stack evidence behind `apps/editor/`.
- [quality.md](../workflow/quality.md) — the gates a frontend PR must pass.
- [contracts/index.md](../../contracts/index.md) — the engineering semantics UI
  consumes and never redefines.
- [planning/index.md](../planning/index.md) — how an implementation Issue is
  scoped and prioritized.
