---
type: contract
status: active
canonical_for:
  - engineering-editor-ux-behavior
read_when:
  - frontend-design-work
  - frontend-change
  - editor-frontend-work
  - implement-change
  - review-change
update_when:
  - engineering-editor-ux-behavior-change
  - approved-figma-design-change
depends_on:
  - docs/dev/frontend/index.md
  - docs/dev/frontend/architecture.md
  - docs/dev/frontend/design-to-code.md
  - docs/dev/frontend/accessibility.md
  - docs/dev/research/engineering-editor-ux.md
  - docs/contracts/index.md
decision:
  - docs/dev/decisions/ADR-0002-semantic-model-is-the-core.md
  - docs/dev/decisions/ADR-0003-separate-semantic-and-presentation-models.md
  - docs/dev/decisions/ADR-0004-yaml-is-a-serialization-format.md
  - docs/dev/decisions/ADR-0009-separate-process-function-from-symbol-role.md
  - docs/dev/decisions/ADR-0016-process-physical-realization-boundary.md
evidence:
  - docs/dev/research/engineering-editor-ux.md
  - docs/dev/research/engineering-editor-reuse-architecture.md
superseded_by: null
---

# Engineering Editor UX Contract

> **Question this document answers:** what behavior must the approved DeepPlant
> Engineering Editor UI provide, so that implementation does not have to invent
> undocumented UX behavior and so that Figma geometry never becomes an engineering
> or architectural authority?

This is the canonical, Git-tracked behavioral UX contract for the Engineering
Editor. It records behavior for the approved design; it does not authorize a
capability merely because that capability appears in the design, and it does not
itself change product scope ([roadmap.md](../planning/roadmap.md)).

## Artifact and source-of-truth contract

The approved visual artifact is
[DeepPlant Editor in Figma](https://www.figma.com/design/2Y9J76cXBYEIMvDymF8npl/DeepPlant-Editor).

| Authority | Owns |
|---|---|
| [DeepPlant Editor in Figma](https://www.figma.com/design/2Y9J76cXBYEIMvDymF8npl/DeepPlant-Editor) | visual intent, visual states, component appearance, responsive composition, and representative prototype paths |
| This document (Git) | behavioral UX contract: what the UI does, which states exist, and how surfaces interact |
| Repository architecture and frontend governance | code ownership, dependency direction, framework containment, and implementation conventions |
| Domain and API contracts | engineering semantics, data boundaries, validation rules, commands, and transport |

The Figma screen and component hierarchy does **not** prescribe the implementation
hierarchy:

- a Figma component does not automatically become a Vue component;
- a Figma screen does not automatically become a route or page;
- a Figma variant does not automatically become a Vue prop; and
- a Figma fixture or prototype hotspot is not a production component.

Figma demonstrates representative interactions; it is not executable product logic.
If the design conflicts with this contract, repository architecture, or the
engineering contracts, the conflict is reconciled before implementation rather
than silently resolved toward a visual approximation
([design-to-code.md](design-to-code.md#precedence--repository-governance-constrains-figma)).

## Application shell behavior

The shell provides the following regions:

- **Activity Bar** — primary global workspaces and entry points.
- **Optional left sidebar** — contextual navigation such as the Engineering
  Explorer; collapsible, and its absence never makes the central workspace
  unusable.
- **Central editor workspace** — the open engineering views and the controls that
  belong to the active view.
- **Right Inspector, and a future Copilot surface** — the Inspector is
  selection-driven; Copilot is a future contextual surface, never a second
  mutation path ([future interaction layer](../research/engineering-editor-ux.md)).
- **Global Status Bar** — always-available compact workspace, validity, and
  project status; it remains present when detail surfaces are hidden.
- **Bottom Panel** — a contextual surface (including Problems) that can open,
  collapse to its compact status indication, and close.

Behavioral invariants:

- Opening, collapsing, or closing a secondary surface never discards the accepted
  project state, diagnostics, or semantic selection.
- Exactly one editor view is active at a time; switching the active view changes
  the projection and its view-specific controls, not the semantic model.
- Responsive behavior preserves access to the central workspace and the Status
  Bar. At narrower widths, optional sidebars and secondary surfaces collapse,
  hide behind an explicit affordance, or become on-demand surfaces; they may not
  silently remove the capability they represent.

Pixel measurements, breakpoints, spacing, and colour composition are visual intent
owned by Figma. Only behavior that must hold regardless of layout is a rule here.

## Representation and ownership boundaries

PFD, P&ID and YAML are **representations/views** over engineering information, not
global application modes:

```text
Process/PFD  !=  Physical/P&ID  !=  Simulation
```

- Switching the active editor view changes the projection, never the canonical
  engineering state or the Process/Physical boundary.
- Graphical-only controls belong only to graphical editors. A YAML or other text
  editor must not inherit canvas instrument controls (zoom, pan, fit, placement).
- Control availability follows the **active view**, not a global application mode.
- The Engineering Explorer navigates engineering concepts and views; it is not a
  filesystem-first replacement for the semantic model.

These boundaries are established by
[ADR-0002](../decisions/ADR-0002-semantic-model-is-the-core.md),
[ADR-0003](../decisions/ADR-0003-separate-semantic-and-presentation-models.md),
[ADR-0004](../decisions/ADR-0004-yaml-is-a-serialization-format.md) and
[ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md), and
must not be relaxed to match a design frame.

## Selection and navigation

Selection is **semantic application state**: it identifies an engineering object
(or a set of them) independently of where it is displayed. Keyboard focus is a
separate, transient UI concern ([Focus and semantic state](#focus-and-semantic-state)).

The same selection is shared by the surfaces that can represent it:

| Selection origin | Required behavior |
|---|---|
| Graphical editor | selects the semantic object; Explorer and Inspector reflect the same selection |
| Engineering Explorer | selects the semantic object and reveals it in a compatible open view when one exists |
| Inspector | shows the current selection; with no selection it shows a neutral hint rather than stale content |
| Problems / diagnostics | selecting a diagnostic makes it the current diagnostic and exposes its relevant Inspector context |

Synchronization rules:

- **Reveal** opens or focuses a compatible view, brings the target representation
  into view, and selects the semantic target.
- **Source** navigation moves to source/YAML context **only** when such context is
  truthfully available; otherwise the action is unavailable and explains why.
- Navigation never fabricates an engineering relationship. In particular it must
  not invent a Process-to-Physical realization, a source location, or a view that
  cannot honestly represent the target
  ([ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md)).
- Inspector content is semantic, plus explicitly labelled presentation facts. It
  never exposes framework fields such as canvas coordinates, node/edge ids, or
  handles ([architecture.md](architecture.md)).

## Add Object and placement

Opening **Add Object** presents a searchable library/result surface. Search and
keyboard navigation may focus every matching result row. A result that cannot be
used in the current project may remain discoverable, focusable, and may explain
its limitation, but it is **not activatable**; focusing it never activates it.

Selecting an available library/result item enters **single-shot placement**:

1. the originating tile/result remains visually selected while placement is
   pending, so the pending intent stays identifiable;
2. the user indicates a permitted location in a compatible graphical editor;
3. the corresponding application command performs semantic creation; then
4. placement completes and the single-shot state ends.

Cancellation (`Esc`, closing the surface, or another explicit cancel action) exits
pending placement **without** issuing a creation command. Completion likewise ends
pending placement, so a second placement requires a new selection. Placement is a
presentation act; the semantic creation is the command, and the accepted model
changes only when that command succeeds
([semantic source-of-truth direction](../research/engineering-editor-ux.md)).

This contract never implies that a currently unavailable object type, its
engineering semantics, or its backend behavior is implemented.

## YAML editing and reconciliation

YAML is a serialization format, not a second domain model
([ADR-0004](../decisions/ADR-0004-yaml-is-a-serialization-format.md)). The UI
distinguishes these states and must not collapse them:

| State | Meaning |
|---|---|
| **Accepted model** | The validated semantic state that projections and other accepted views represent. |
| **Editable YAML draft/source** | User-editable text that may differ from the accepted model. |
| **Invalid draft** | The draft cannot be accepted because syntax or semantic validation fails. |
| **Reconciliation required** | The draft and the accepted model differ and require an explicit review/decision. |
| **Conflict review** | Competing changes must be reviewed explicitly before a reconciliation choice is made. |

Behavioral rules:

- The accepted model remains **unchanged** until an explicit apply/reconcile
  decision succeeds. An invalid, reconciliation-required, or conflict-review draft
  never silently replaces, partially merges into, or degrades the accepted model.
- The UI must not imply automatic or hidden merge/synchronization. Reconciliation
  is an explicit, user-visible decision, and its outcome is stated after the
  decision.
- Editing a draft is not a mutation. A YAML surface submits through the same
  semantic/application-command boundary as every other editing surface; a UI
  surface must never bypass that boundary to mutate canonical YAML or model state
  directly.
- Unsaved/dirty state is distinguishable from invalid and from
  reconciliation-required state.

This contract specifies behavior only: it does not assert that a full YAML
editing/reconciliation backend exists today. Draft persistence, diffing
mechanism, and the reconciliation implementation remain unimplemented until a
selected Issue delivers them.

## Problems and validation

Diagnostics are navigable items, not dead-end text.

- **Diagnostics list** — all current diagnostics for the loaded project, each with
  its severity, the failing object, and the rule/source it originates from.
- **Selected diagnostic** — the current diagnostic, distinct from keyboard focus
  and from the semantic selection of an engineering object.
- **Reveal** — opens or focuses a compatible view, brings the diagnostic's object
  into view, and selects that semantic target.
- **Source navigation** — moves to the diagnostic's source location only when that
  context is truthfully available; otherwise the action is unavailable and
  explains why.
- **Validation state** — the global validity state stays visible in the Status Bar
  even when the detailed list is hidden.
- **Unavailable navigation** — a diagnostic whose target cannot be represented or
  resolved shows an explained unavailable state rather than a silent no-op.

Bottom Panel lifecycle:

| Action | Required behavior |
|---|---|
| Open | Shows the panel for its current content (for example Problems) without changing validation or selection. |
| Collapse | Hides the detail while leaving the compact validation/status indication visible. |
| Close | Dismisses the panel; diagnostics, semantic selection, and accepted model state are retained and can be restored. |

Severity vocabulary is bounded by the engineering contracts: only the severities
those contracts define may be presented as current.

## Command Palette

The Command Palette is an on-demand command-discovery surface, never permanent
chrome:

- **Invocation** opens the palette and moves input focus into its search field.
- **Up/Down** moves focus between command rows; search results and row focus are
  distinct from the engineering selection.
- **Enter** activates the focused command **when it is available**.
- **Unavailable** commands remain discoverable and focusable so the user can learn
  that the capability exists, but they cannot be activated; the palette states why
  the command is unavailable rather than failing silently.
- **Esc** dismisses the palette without executing a command.
- After dismissal, focus returns to the control that invoked the palette, so the
  keyboard path continues from where it started.

The design represents these rows with a canonical command-row component. That
component is the visual evidence for the interaction; the production component
structure and the command surface remain implementation concerns governed by this
contract and the frontend architecture.

## Focus and semantic state

Keyboard focus is **orthogonal** to semantic state. Focus is where keyboard input
currently goes; semantic state describes what the component means. The same
semantic state must remain expressible while focused, for example:

```text
Selected + Focus
Active + Focus
Dirty + Focus
Invalid + Focus
Error + Focus
Future/Unavailable + Focus
```

Focus must never erase the semantic meaning of the component: a focused control
keeps its selected/active/dirty/invalid/error/future cue, and a focus indicator
must not be the only distinction where the semantic state also matters
([accessibility.md](accessibility.md)).

Implementation-level details remain implementation responsibilities where they are
not yet specified: ARIA roles and exact screen-reader text, final tab order, and
native-desktop window-region behavior.

## Capability and deferred states

These states are distinct; a single visual treatment must not merge them, and each
must be conveyable without relying on colour alone:

| State | Meaning |
|---|---|
| **Disabled** | The action is not applicable in the current context. |
| **Unavailable** | The action cannot be performed because truthful data, a target, or a capability is missing. |
| **Future** | Designed direction that is not implemented and not authorized by this contract. |
| **Loading** | Required data or a view is being obtained. |
| **Dirty** | The current editable state differs from its accepted/saved baseline. |
| **Invalid** | Current input fails syntactic or semantic acceptance. |
| **Error** | An operation or the current view failed and requires an explicit outcome. |

A designed **Future** or **Unavailable** state is **not** implementation
authorization. In particular, none of the following may be presented as
implemented merely because it appears in the design:

- Copilot backend or LLM runtime;
- extensions;
- persistence;
- advanced P&ID editing;
- a full YAML editing/reconciliation backend;
- Output/Terminal behavior;
- future symbol fidelity;
- any other deferred capability recorded in the
  [anti-roadmap](../planning/roadmap.md#anti-roadmap--what-must-not-be-implemented-prematurely).

Where such a capability appears in the design, it is represented as future or
unavailable and labelled as such.

## Representative prototype flows

The Figma prototype is representative interaction evidence, not executable product
logic; its geometry and exact visual composition are not part of this contract.
The flows establish the following behavioral intent:

| Flow | Intent |
|---|---|
| **F01 — primary navigation / shell** | Navigate the shell while the central workspace and global Status Bar remain usable. |
| **F02 — PFD inspection and selection/deselection** | Select and deselect a representation; Explorer and Inspector reflect the same semantic selection. |
| **F03 — diagnostics navigation** | Select a diagnostic, reveal a truthful target, and show the associated Inspector context. |
| **F04 — YAML reconciliation / conflict** | Keep draft/source states separate from the accepted model until an explicit review and apply/reconcile decision resolves them. |
| **F05 — Bottom Panel lifecycle** | Open, collapse, and close the panel without losing diagnostics, selection, or accepted model state. |
| **F06 — Command Palette invoke/dismiss/activate** | Invoke, search, move row focus, activate an available command, and dismiss back to the invoker. |
| **F07 — responsive shell** | Collapse secondary shell regions at narrower widths while retaining deliberate access to their capabilities. |

A prototype hotspot is interaction evidence only. It does not create a command, a
route, a component boundary, or an engineering relationship.

## Design-to-code ownership constraints

The implementation target is unchanged: a Vue 3 + TypeScript + Vite SPA under
`apps/editor/` ([index.md](index.md)). This contract adds no directory tree, and
the Figma hierarchy does not prescribe one.

- Preserve **feature first, responsibility second** ownership inside the existing
  feature modules ([architecture.md](architecture.md)).
- The current Process/PFD implementation stays owned by `process-pfd/`. A screen in
  the design does not by itself justify a new feature module.
- Vue Flow integration stays isolated behind the existing feature
  adapter/component boundary; the framework `Node`/`Edge` graph shapes remain
  confined there.
- Framework objects must not leak into application- or domain-facing state: a
  framework interaction is translated into a DeepPlant semantic identity at the
  integration surface before the rest of the feature observes it.
- Shared UI is extracted only when real code reuse justifies it. A component that
  Figma reuses is not yet a shared frontend component.
- Do not create global technical buckets (`app/`, `shared/`, `components/`) for
  surfaces the design implies but no current code shares.

## Related

- [index.md](index.md) — frontend engineering contract, topics, and review checklist.
- [design-to-code.md](design-to-code.md) — the Figma → behavior → Issue →
  implementation workflow and its source-of-truth rules.
- [architecture.md](architecture.md) — current frontend ownership and the Vue Flow
  containment boundary.
- [accessibility.md](accessibility.md) — the accessibility baseline this contract's
  focus and state rules must honor.
- [engineering-editor-ux.md](../research/engineering-editor-ux.md) — the
  interaction architecture and rationale this contract operationalizes.
- [engineering-editor-reuse-architecture.md](../research/engineering-editor-reuse-architecture.md)
  — the reuse-first stack evidence behind `apps/editor/`.
- [contracts/index.md](../../contracts/index.md) — the engineering semantics this
  UI consumes and never redefines.
- [roadmap.md](../planning/roadmap.md) — milestones and the anti-roadmap that
  governs deferred capabilities.
