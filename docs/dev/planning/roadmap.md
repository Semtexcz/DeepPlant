---
type: roadmap
status: active
canonical_for:
  - product-milestones
read_when:
  - feature-planning
  - roadmap-change
  - milestone-progress
update_when:
  - milestone-change
  - priority-change
depends_on:
  - VISION.md
  - docs/dev/planning/strategy.md
  - docs/dev/planning/product.md
  - docs/dev/planning/index.md
  - docs/dev/architecture/index.md
  - docs/contracts/index.md
decision: []
evidence: []
superseded_by: null
---

# Roadmap

> **Primary question:** which **product outcome** is DeepPlant pursuing now, and
> how do we know that outcome is finished?

The roadmap is organized around **product milestones**, not a sequence of
completed Issues. A milestone is an outcome an engineer can experience; its
success criteria describe demonstrable behavior, and a milestone is **not**
complete merely because the Issues linked to it were merged.

```text
VISION.md          why DeepPlant exists            →
strategy.md        who it is for, and the choices  →
product.md         what the first MVP must do       →
roadmap.md         the milestones we build toward   →  (this document)
GitHub Issues      bounded, executable work         →
Pull Requests      delivered, verified capability   →
```

This document contains no dates, deadlines, duration estimates, horizons, or
scheduled review intervals. Historical delivery is recorded in
[history/implementation-slices.md](../history/implementation-slices.md); the
long-term capability progression in [direction.md](direction.md); the product
target in [product.md](product.md); the strategy in [strategy.md](strategy.md);
and planning governance in [index.md](index.md).

## Milestones at a glance

| Milestone | Status |
|---|---|
| Foundation | **Delivered** |
| Integrated Engineering Workspace | **Active** |
| Project Persistence and Bidirectional Authoring | Planned (not authorized) |
| Functional PFD/P&ID Authoring | Planned (not authorized) |
| MVP Acceptance | Planned (not authorized) |

"Delivered" states observable repository facts owned by
[architecture.md](../architecture/index.md) and the [contracts](../../contracts/index.md),
not a roadmap promise. "Planned" means the outcome is the intended direction;
work in it is authorized only by a selected, refined Issue
([index.md](index.md)).

## Foundation — Delivered

**Outcome.** DeepPlant has a semantic core, a headless toolchain, and a runnable,
distributable, read-only editor over it.

Delivered capabilities (facts owned by [architecture.md](../architecture/index.md)
and the [contracts](../../contracts/index.md)):

- the physical/plant model, process graph, and physical piping realization;
- YAML load/save and the `validate` CLI;
- the `basic` SVG symbol pack and the headless read-only process renderer;
- the narrow DEXPI 2.0.0 Process adapter;
- the read-only Process/PFD editor: `deepplant ui <path>`, the framework-independent
  editor application with a loopback-only FastAPI/Uvicorn boundary, and the
  Vue 3 + TypeScript + Vite + Vue Flow SPA under `apps/editor/`;
- the canonical Python and frontend engineering contracts with enforced quality
  and size guardrails;
- standalone Windows/Linux desktop distribution (`deepplant-editor`) and the
  empty shared Editor workspace (`active project = none`).

Detailed slice provenance is in
[history/implementation-slices.md](../history/implementation-slices.md).

## Active Milestone — Integrated Engineering Workspace

**Outcome.** An engineer works inside one coherent, professional desktop
application: a project/engineering explorer, editor tabs that move between the
Process/PFD view and the physical/P&ID view, a YAML surface, a contextual
Inspector, and a Problems/diagnostics area — with explicit application, project,
document, and view states. The editor reads and feels like one application, not
a graph widget beside a text box.

This milestone delivers the **integrated application shell and navigation**,
including the intended PFD/P&ID/YAML workspace structure. It does **not** deliver
a working P&ID or YAML editor. The existing read-only Process/PFD view remains
available; the physical/P&ID and YAML surfaces appear in the shell as explicitly
unavailable or non-editable placeholders whose unsupported capabilities are
clearly communicated. No functional P&ID or YAML authoring is implied or
required, and no premature semantic model, synchronization, or
project-persistence implementation is authorized here.

**User value.** Today the editor exposes a single read-only Process/PFD
projection. Before authoring capability is layered on, the user needs a real
application surface: somewhere to navigate a project, see what is open, tell
valid-but-unrenderable states apart from errors, and reach the surfaces the
later milestones will make editable. Without this, persistence and bidirectional
authoring would be added to a screen that cannot yet present them coherently.

**Demonstrable success criteria** (each must be observable in the running
application, not inferred from merged Issues):

1. The application presents a coherent shell with an engineering explorer,
   editor tabs, the existing Process/PFD view, a physical/P&ID view surface, a
   YAML surface, an Inspector, and a Problems area. The physical/P&ID and YAML
   surfaces are present as explicit placeholders that state they are not yet
   editable — they are not working editors.
2. Navigation between surfaces keeps one active project/document context; the
   user can tell what project and what document are open.
3. Application, project, and view states are explicit: empty/no project, loading,
   loaded, error, and unsaved are distinguishable.
4. Semantic validity and Process/PFD view availability are shown as **distinct**
   states, so a valid-but-unprojectable model is not presented as an error
   (Issue #99).
5. The workspace remains local-first and read-consistent with the semantic core;
   no surface becomes a second engineering model.

**Status of the criteria.** None of these are implemented today; they describe
the outcome the milestone must demonstrate. The Process/PFD canvas, the
Inspector, and the status strip already exist. The physical/P&ID and YAML
surfaces do not yet exist even as placeholders, and this milestone adds them only
as explicitly unavailable/non-editable surfaces: criterion 1 requires the
placeholder to be present and to communicate that it is not yet editable, not
that it works.

**Genuine dependencies.** The delivered read-only editor slice, its
`EditorWorkspace`/`EditorServer` session model, the frontend engineering contract
([frontend/index.md](../frontend/index.md)), the interaction architecture
(Issue #69, [engineering-editor-ux.md](../research/engineering-editor-ux.md)),
the reuse-first frontend architecture (Issue #70,
[engineering-editor-reuse-architecture.md](../research/engineering-editor-reuse-architecture.md)),
and the design-to-code workflow (PR #96,
[design-to-code.md](../frontend/design-to-code.md)). None of these has to be
redone; the milestone applies them.

**Relevant existing Issues.**

- [#99 — distinguish semantic validity from Process/PFD view availability](https://github.com/Semtexcz/DeepPlant/issues/99)
  directly supplies criterion 4 and is the clearest bounded starter slice.

**Evidence gaps.**

- The professional application shell and its states are not yet designed; the
  visual specification is a separate implementation concern (the design-to-code
  workflow is the route, not this milestone).
- The physical/P&ID and YAML surfaces are in scope as explicit placeholders only.
  This milestone fixes that boundary: they are present in the shell and clearly
  marked as not yet editable. Making them functional is authorized only by the
  later authoring milestones.
- Presentation-state persistence is explicitly out of this milestone; it belongs
  to the persistence milestone.

**Why this milestone is active (justification).** The Foundation milestone is
delivered, and the remaining MVP work — persistence, bidirectional authoring,
and graphical PFD/P&ID editing — all require a surface to live in. Selecting the
**workspace** first makes the subsequent milestones additive rather than
speculative, and it is the smallest outcome that produces a usable application
rather than more backend capability. Issue #89 (project format) is a strong and
necessary capability, but it is an **enabling** concern for persistence, not the
product outcome; selecting it as the strategic objective would optimize a format
before the application that consumes it is coherent. The active milestone is
therefore the workspace, and #99 is its natural first refinement.

## Planned Milestones

These are intended directions. Nothing here is authorized: work begins only when
a refined, Ready Issue is selected ([index.md](index.md)). Order reflects
dependencies and evidence, not a fixed schedule.

### Project Persistence and Bidirectional Authoring

**Outcome.** A DeepPlant project can be created, opened, edited, saved, closed,
and reopened without losing supported semantic or presentation state; and YAML
and the graphical editors are two views of one accepted model, where a YAML edit
updates the accepted graph and a graphical edit is reflected in YAML.

The synchronization and persistence architecture is proven with **one real
vertical workflow**: one supported Process/PFD semantic mutation, performed
graphically, represented in YAML, propagated bidirectionally through the accepted
canonical `ProcessModel`, and verified by save/reload. This milestone proves the
mechanism with that single command; it does **not** claim the full PFD/P&ID
editing set, which the next milestone expands.

**User value.** This is what makes the "one model, many surfaces" proposition
real and Git-reviewable. It is the core strategic bet of the MVP.

**Demonstrable success criteria.**

- Create/Open/Edit/Save/Close/Reopen works for a real project, and a reopened
  project matches what was saved (no silent loss of supported semantic state or
  presentation state).
- A YAML edit that is accepted updates the graphical view of the accepted model.
- A graphical engineering change is reflected in YAML.
- The single bounded vertical slice is demonstrated end to end: creating one
  supported process step — a `ProcessStep` with an authored `id` and a supported
  `function` — is performed through the UI, appears as the corresponding
  `process.steps` entry in YAML, propagates bidirectionally through the accepted
  `ProcessModel`, and survives save/reload.
- Invalid YAML can exist as a temporary editing draft and does **not** corrupt
  the last accepted model.
- Unsaved state and synchronization conflicts are communicated clearly.
- Serialized changes are meaningful and reviewable in Git.

**Genuine dependencies.** Project Persistence and Bidirectional Authoring
depends on the Integrated Engineering Workspace (the surfaces it authorizes) and
on a project/persistence contract. It does **not** depend on Functional PFD/P&ID
Authoring: it introduces the one bounded graphical mutation it needs directly, so
the two milestones are not circular.

**Relevant existing Issues.**

- [#89 — Define the DeepPlant project format and portable package](https://github.com/Semtexcz/DeepPlant/issues/89)
  is the existing project-format initiative. The canonical directory-first
  format and any portable package stay conceptually distinct from the
  application's own distribution format.

**Evidence gaps.** Comment preservation, formatting fidelity, key ordering,
stable identifiers, and Git-diff quality must be investigated **before** a YAML
synchronization implementation is chosen (see
[product.md](product.md#bidirectional-yaml-editing)). No generic synchronization
framework is designed here.

### Functional PFD/P&ID Authoring

**Outcome.** Building on the single Process/PFD command demonstrated by Project
Persistence and Bidirectional Authoring, an engineer can create, connect, select,
modify, validate, and persist bounded `ProcessModel` objects in the PFD and a
small supported physical subset (equipment, ports, connections, piping, a minimal
valve concept) in the P&ID, without collapsing process intent into physical
realization. This milestone **expands** the demonstrated mutation → YAML →
save/reload mechanism into the bounded MVP editing set; it does not retroactively
supply a prerequisite the earlier milestone lacked.

**User value.** This is the editing capability the product thesis promises; it
turns the workspace into a real engineering editor.

**Scope.** On top of the single mutation proven by the persistence milestone,
this milestone adds:

- additional Process/PFD commands (create/delete steps, connect/disconnect
  streams, edit properties);
- physical equipment editing;
- physical ports and connections;
- basic piping;
- bounded P&ID interactions;
- the relevant validation and persistence.

**Demonstrable success criteria.**

- The bounded PFD workflow (create/delete steps, connect/disconnect streams,
  select, move, edit properties, validate) modifies the canonical `ProcessModel`
  and survives save/reload.
- The bounded P&ID workflow modifies the physical/piping model and survives
  save/reload.
- The process and physical layers remain separate
  (`ProcessStep != Equipment`, `ProcessStream != physical piping`,
  `ProcessPort != physical Port/Nozzle`), with no merged source of truth.

**Genuine dependencies.** Project Persistence and Bidirectional Authoring, which
demonstrates the mutation → YAML → save/reload mechanism with one command, and
the integrated workspace. This milestone expands that demonstrated mechanism; it
is not a prerequisite the earlier milestone waits on.

**Relevant existing Issues.**

- [#94 — Guided P&ID Design](https://github.com/Semtexcz/DeepPlant/issues/94)
  is broader rule-driven P&ID work; it is context for what lies beyond the MVP,
  **not** a milestone-defining requirement. The MVP P&ID subset remains
  intentionally narrow.

**Evidence gaps.** The precise supported P&ID symbol subset and the valve
concept must follow the existing semantic model and ADR-0016; no new semantic
concepts are introduced to make editing easier.

### MVP Acceptance

**Outcome.** The complete end-to-end engineering workflow is demonstrated in the
real application: create/open a project, edit a PFD, edit YAML and observe the
accepted graphical change, edit a bounded P&ID, validate the model, save, close
and reopen DeepPlant, verify semantic and presentation persistence, and inspect
meaningful Git changes.

**User value.** This is the first point at which DeepPlant is a usable product
rather than a set of capabilities, and the point at which the strategy
hypotheses in [strategy.md](strategy.md) receive real evidence.

**Demonstrable success criteria.** The full scenario above, performed in the
running application, with the acceptance scenario in
[product.md](product.md#end-to-end-mvp-acceptance) as the canonical definition.

**Genuine dependencies.** All prior milestones.

**Relevant existing Issues.** None required to define it; acceptance is the
demonstration, and supporting Issues are selected during refinement.

**Evidence gaps.** Real-user usability of the workflow is the assumption under
test; until then, acceptance is an internal demonstration, not validated demand.

## Milestone → relevant existing Issues

| Milestone | Relevant existing Issues |
|---|---|
| Foundation — Delivered | #68 (MVP definition, closed), #69 (UX architecture, closed), #70 (reuse architecture, closed), PR #96 (design-to-code) |
| Integrated Engineering Workspace (active) | #99 (validity vs view availability) |
| Project Persistence and Bidirectional Authoring | #89 (project format and portable package) |
| Functional PFD/P&ID Authoring | #94 (guided P&ID design — broader context only) |
| MVP Acceptance | — |

This is a mapping of existing relevant work, not an authorization. An Issue in
this table is implemented only when it is refined to Ready and selected
([index.md](index.md)).

## Retired planning mechanisms

The earlier roadmap was organized around issue-driven `Now`/`Next` horizons and
mandatory **re-evaluation gates** triggered when a small number of Issues
completed. That mechanism is retired: milestone progress is now the organizing
unit, and the next Issue is chosen during ordinary refinement without a planning
ceremony ([index.md](index.md)). The unique decision evidence from those
historical gates (for example the choice and later correction that led to
standalone distribution before the empty workspace) is preserved in
[history/implementation-slices.md](../history/implementation-slices.md) and
[history/gate-decisions.md](../history/gate-decisions.md); it is historical
record, not current governance.

## Anti-Roadmap — What Must Not Be Implemented Prematurely

> The milestones provide product context, not implementation authorization.
> Implement only the currently scoped vertical slice.
>
> A milestone or a planned capability appearing here is not sufficient
> justification to introduce its architecture today.
>
> Do not add abstractions, dependencies, or infrastructure for a future
> milestone until a selected Issue requires them.

Concrete examples:

- the AI-assisted and simulation directions do not justify agent or simulator
  interfaces now;
- GUI implementation, editor structure, and GUI dependencies are authorized only
  within the currently selected Engineering Editor milestone slice;
- the multi-discipline direction does not justify generic entity hierarchies now;
- the DEXPI direction does not justify DEXPI-shaped domain objects now;
- the physical-piping and process ↔ physical realization questions do not justify
  widening `Connection` — ADR-0011 and ADR-0016 define the boundaries;
- the persistence milestone authorizes only the single bounded semantic mutation
  that proves bidirectional synchronization, together with the persistence it
  requires; it does not authorize general semantic editing or a generic
  synchronization framework;
- the MVP containing a P&ID editing outcome does not authorize full
  instrumentation, control loops, or advanced P&ID engineering.

Think broadly about the destination. Build narrowly in the current iteration.

## Related

- [strategy.md](strategy.md) — who the product is for and the deliberate choices.
- [product.md](product.md) — product definition and the MVP acceptance scenario.
- [index.md](index.md) — idea intake, triage, refinement, and Issue selection.
- [direction.md](direction.md) — long-term capability progression (context only).
- [implementation-slices.md](../history/implementation-slices.md) — delivered
  work and historical gate decisions.
- [architecture.md](../architecture/index.md) — what exists, and its boundaries.
- [contracts/index.md](../../contracts/index.md) — current obligations.


