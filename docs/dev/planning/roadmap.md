---
type: roadmap
status: active
canonical_for:
  - current-implementation-roadmap
read_when:
  - roadmap-change
  - feature-planning
  - next-task-selection
depends_on:
  - docs/contracts/index.md
  - docs/dev/architecture/index.md
  - docs/dev/planning/index.md
decision: []
evidence: []
superseded_by: null
---

# Roadmap

> **Primary question:** What is DeepPlant's current execution-planning state?

It answers that question through three aspects:

1. **Current state** — a short summary; canonical facts live in
   [contracts/](../../contracts/index.md) and [architecture.md](../architecture/index.md).
2. **Immediate operational sequence** — the authorized next work and its order.
3. **Unresolved evidence gaps** — questions whose evidence must precede another
   executable task.

It contains no dates, estimates, release promises, fixed sequence commitments, or
completion percentages; GitHub Issues remain the place for executable tasks.
Detailed completion records live in
[history/implementation-slices.md](../history/implementation-slices.md), the
long-term capability progression in [direction.md](direction.md), and planning
governance in [planning.md](index.md). This document is the canonical source for
current operational priority and horizons; GitHub Issues own detailed scope for
concrete executable work.

## Current State

DeepPlant ships a Python CLI package (`src/deepplant/`) implementing:

- the physical/plant model and its validation contract
  ([contracts/plant-model.md](../../contracts/plant-model.md));
- the process graph ([contracts/process-model.md](../../contracts/process-model.md));
- physical piping realization over identified connections
  ([contracts/physical-piping.md](../../contracts/physical-piping.md));
- YAML load/save ([contracts/yaml-format.md](../../contracts/yaml-format.md)) and the
  `validate` CLI ([contracts/cli.md](../../contracts/cli.md));
- the basic headless read-only process renderer ([contracts/rendering.md](../../contracts/rendering.md))
  and the `basic` SVG symbol-pack contract ([dev/reference/svg-symbols.md](../reference/svg-symbols.md));
- the narrow DEXPI 2.0.0 Process adapter
  ([dev/reference/dexpi-process-adapter.md](../reference/dexpi-process-adapter.md));
- the first runnable, read-only Process/PFD editor slice
  ([architecture.md](../architecture/index.md#engineering-editor-slice-implemented)):
  a DeepPlant-owned Process/PFD projection (`src/deepplant/editor/projection.py`),
  a framework-independent editor application
  (`src/deepplant/editor/application.py`) with a thin, loopback-only FastAPI/Uvicorn
  boundary (`src/deepplant/editor/api.py`), the `deepplant ui <path>` launcher,
  and a Vue 3 + TypeScript + Vite + Vue Flow SPA under `apps/editor/` that serves
  pan, zoom, fit view, single selection, a read-only semantic Inspector, and the
  current validation status;
- the canonical frontend engineering contract and quality gates for that SPA
  ([dev/frontend/](../frontend/index.md)), enforced by an ESLint flat-config gate
  as part of `make frontend-check` and `make check`, and applied to the existing
  frontend by the #81 refactor: a thin application composition root
  (`apps/editor/src/App.vue`), a feature-owned Process/PFD page and canvas
  boundary, explicit feature state ownership
  (`process-pfd/composables/useProcessPfd.ts`), UnoCSS over semantic tokens, and
  Vue component plus feature-integration tests;
- a small Playwright + Chromium browser E2E layer (`apps/editor/e2e/`, `make
  frontend-e2e`) that proves the critical editor workflow across the real local
  product path: the production SPA build, the real `deepplant ui --port 0` CLI
  over loopback FastAPI/Uvicorn, and real pointer interaction in the browser;
- a standalone Editor **graphical desktop application** (Issue #85, delivered
  through its two child slices): PR #92 established the self-contained
  distribution foundation — the `deepplant-editor` entry point, packaging of the
  unchanged editor as a self-contained Windows installer and a Linux AppImage
  through the cross-platform `tools/package_editor.py` driver, native
  packaged-artifact verification that runs outside the checkout with a sanitized
  environment, native Windows/Linux CI packaging jobs, an application-owned built
  SPA (`deepplant/editor/dist` inside the bundle) rather than a checkout
  dependency, and the editor transport (FastAPI/Uvicorn) as an optional
  `deepplant[editor]` extra so the semantic Core stays installable without it.
  PR #93 (Issue #93) then delivered the native desktop host: PySide6 + Qt WebEngine
  in the optional `deepplant[desktop]` extra, a native window embedding the same
  `apps/editor/` SPA over the same loopback `EditorServer`, a native Open dialog
  for `*.yaml`/`*.yml`, launch with no model argument, an optional model path, and
  a window lifecycle that stops the owned server and releases the loopback socket.
  The evidence and candidate comparison are in
  [research/editor-desktop-host.md](../research/editor-desktop-host.md). The
  browser host `deepplant ui` and the Python CLI remain separate surfaces.

Not implemented: a DeepPlant project format (canonical project directory, manifest,
or portable `.deepplant` package); semantic editing and any semantic mutation
command; presentation persistence; undo/redo; P&ID rendering and physical/P&ID
symbols; automatic updates, code signing, release automation, store/package
publishing, and macOS distribution; full DEXPI and Plant/P&ID import/export;
other vendor adapters (COMOS, AVEVA); instrumentation and signal semantics;
engineering rules; and the process ↔ physical realization mapping. The
authoritative boundary map, including directional-but-unimplemented components,
is [architecture.md](../architecture/index.md).

## Completed

Delivered slices are recorded in
[history/implementation-slices.md](../history/implementation-slices.md) and, for
evidence-heavy slices, in the linked spike/decision documents.

## Operational Roadmap

### Now

**Re-evaluate after #85.** No product capability is currently selected.

[#85 — Establish independent DeepPlant Core and standalone editor distribution](https://github.com/Semtexcz/DeepPlant/issues/85)
is **complete**. Both of its child slices are delivered and recorded in
[history/implementation-slices.md](../history/implementation-slices.md):

- the self-contained distribution foundation (PR #92) — Windows installer, Linux
  AppImage, bundled SPA/runtime, Core independence; and
- the native desktop host
  ([#93](https://github.com/Semtexcz/DeepPlant/issues/93), PR #93) — the packaged
  runtime is now a real graphical application embedding the same `apps/editor/`
  Vue SPA.

The #93 implementation then went through a focused review that hardened clean
shutdown, exact-origin webview navigation, the packaged self-check evidence, the
Linux window-lifecycle CI gate, artifact licence/compliance payloads, and the
desktop static type-check. One redistribution item remains **open** and is tracked
in [THIRD_PARTY_NOTICES.md](../../../THIRD_PARTY_NOTICES.md): the complete,
version-matched Chromium third-party notice set is generated by upstream tooling
and is not published as a single immutable file for a given Qt release, so the
artifact ships the Qt WebEngine licence texts plus authoritative upstream pointers
and the source offer rather than a fabricated partial list. That is a compliance
follow-up, not a new product capability, so it does not change the operational
sequence below.

Because #85 is complete, the next capability must come from an explicit
re-evaluation against the current repository state. **Do not preselect a
successor** — in particular do not preselect #89 — and do not mechanically
promote a backlog row.

Candidate evidence inputs (strong future candidates, not commitments):

```text
#89 project format / portable package
first semantic mutation
save / persistence
presentation state persistence
#88 automated release infrastructure
P&ID
process ↔ physical realization
```

Re-evaluation criteria include:

- what standalone packaging and the desktop-host slice exposed about hidden
  coupling and the application/host/frontend boundary (answered for the delivered
  slices: the checkout-relative SPA path, the CLI-level transport import, and the
  absence of an owned server lifecycle were the real coupling, and all three are
  fixed and covered by tests);
- whether the project/persistence contract (#89) is now the right next step
  before richer Open/Save semantics, or whether a different evidence-supported
  slice comes first;
- whether the first semantic-mutation + Save slice is now authorized, and where
  the minimum application-command machinery Issue #69 describes and undo/redo
  belong;
- whether presentation state (diagram positions, per-view overrides) now needs
  a concrete persisted schema;
- what release/version automation (#88) needs to consume from the now
  distributable artifacts, and what the new desktop runtime means for artifact
  size and release packaging.

### Next

- **Unselected pending the post-#85 re-evaluation.** No successor capability may
  be selected until that re-evaluation produces evidence.

### Re-evaluation Gate

The previous re-evaluation gate was executed after #39, #69, and #70 were
delivered.

Outcome:
[#75 — Engineering Editor: first interactive Process/PFD vertical slice](https://github.com/Semtexcz/DeepPlant/issues/75)
was selected as the smallest executable slice and is delivered.

Process/PFD had the strongest complete executable substrate:

- `ProcessModel`
- structural validation
- realistic process example
- deterministic headless renderer
- Process/PFD SVG symbol/anchor contract
- completed UX architecture (Issue #69,
  [engineering-editor-ux.md](../research/engineering-editor-ux.md))
- completed reuse-first GUI architecture (Issue #70,
  [engineering-editor-reuse-architecture.md](../research/engineering-editor-reuse-architecture.md))

The physical/P&ID side does not yet have an equivalent physical presentation /
symbol contract, so the first GUI slice remains Process/PFD-only.

The process ↔ physical realization boundary evidence that preceded this gate is
[process-physical-realization-boundary.md](../research/process-physical-realization-boundary.md)
and [ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md).
Quantity implementation, DEXPI 2.0.1, port kinds, physical/P&ID GUI,
rules, and semantic diff remain unpromoted. No successor is preselected; selection follows
from the current repository state and the delivered evidence, not from a backlog
row.

The re-evaluation from the #75 implementation evidence identified that the
delivered read-only slice needed foundation hardening before more product
functionality was layered on it. Its outcome selected
[#79 — Bug: Engineering Editor architecture is inconsistent with the existing
DeepPlant application structure](https://github.com/Semtexcz/DeepPlant/issues/79)
as the next executable slice, followed by the dependency-ordered
frontend-engineering work #80 → #81 → #82. #79, #80, #81 and #82 are now
delivered, so the quality-hardening sequence is complete.

#### Re-evaluation after #82 (executed)

The gate that opened after #82 is now executed. It selects exactly one product
capability:

[#85 — Establish independent DeepPlant Core and standalone editor distribution](https://github.com/Semtexcz/DeepPlant/issues/85)

This outcome corrects an earlier draft of this same gate. That draft selected #89
(project format + portable package) and classified #85 as a strategic later
capability. Review found that this deferred #85 despite #85's explicit
requirement that standalone distribution be proven before the editor grows
further. The decision was therefore re-evaluated against Issue #85 itself and the
then-current checkout-dependent editor runtime: the delivered editor was verified
through `production SPA → real deepplant ui → FastAPI/Uvicorn → Chromium`, but it
ran only from a development checkout (`uv run deepplant ui ...`) and resolved the
built SPA assets from `apps/editor/dist` inside that checkout. The strongest
missing evidence was therefore standalone distributability, not project
persistence. Both #85 implementation slices are now delivered — the self-contained
distribution foundation and the native desktop host (see
[history/implementation-slices.md](../history/implementation-slices.md)); the
checkout coupling described here was the gap the first slice closed, and #85 is
complete.

Reasoning: the delivered editor (#75 → #79 → #80 → #81 → #82) proves the read
path `load → semantic model → application/projection boundary → FastAPI →
production SPA → Vue Flow → browser interaction`. That establishes the
application architecture well enough to test the next architectural claim: can
this actually be shipped to an engineering user without a development checkout?
The missing product path is

```text
download
  ↓
install / launch
  ↓
open current supported model
  ↓
use editor
  ↓
close
```

without requiring the user to install Python, Node.js, pnpm/npm, uv/pip,
compilers, or development SDKs. Packaging problems often expose hidden coupling —
repository-relative frontend paths, Python runtime assumptions,
package-data/resource discovery, frontend asset location, subprocess/process
lifecycle assumptions, filesystem/current-working-directory assumptions,
platform-specific launcher behavior, desktop-shell requirements, Windows process
behavior, Linux runtime dependencies — and those problems are cheaper to
discover while the application is still small, read-only, well tested, and
architecturally bounded than after adding semantic mutation, persistent
presentation state, multi-file projects, P&ID, and larger editor infrastructure.
That is why #85 is selected now: packaging is an application-architecture test,
not release polish.

Issue #85 contains two related concerns, and the gate re-evaluates them
separately against the current repository state:

- **A. Independent Core boundary — verify and preserve, not redesign.** Much of
  this is already supported by the delivered architecture: the semantic model
  (`src/deepplant/`) stays usable from Python and CLI without the GUI, and the
  dependency direction is `Vue → FastAPI transport → EditorApplication →
  DeepPlant semantic/core code`. The #85 implementation must verify and preserve
  that boundary (for example a test importing representative Core behavior
  without the editor), **not** create a large Core refactor merely because #85
  mentions Core independence.
- **B. Standalone distribution — the major unresolved evidence gap.** The first
  #85 implementation answers: can today's real read-only editor be built and run
  as a self-contained Windows and Linux application? That is the capability that
  justifies selecting #85.

`deepplant ui <plant.yaml>` already gives the standalone distribution slice a
sufficient input contract: it can open today's supported YAML model. The slice
does not depend on the final project format, and standalone application
packaging must not be made to depend on it merely because a later editor will
need richer Open/Save semantics.

Candidate classification (evidence-based; not issue number or recency):

- **#85 independent Core boundary + standalone editor distribution — selected
  product Now.** The repository now exposes a standalone-distributability
  evidence gap that #85 explicitly requires closing early.
- **#77 product philosophy — not product Now.** Valuable independent
  governance/documentation work and a decision framework; not a prerequisite for
  #85 and not itself the next product capability.
- **#84 Python engineering standards — not product Now.**
  Engineering-maintenance / developer-quality work; useful before substantial new
  Python code, but it answers a developer-quality question rather than a
  user/product one and does not block #85.
- **#88 versioning / changelog / releases — not product Now.** Release
  infrastructure; it becomes valuable before mature automated publishing of the
  artifacts #85 makes possible, but it is not a prerequisite for the first
  standalone build.
- **#89 project format + portable package — strong later product candidate.**
  Strategically important before richer mutation/Open/Save and persistence work,
  but application distribution and project serialization produce evidence
  independently; #89 is not a prerequisite for the first standalone build and is
  not preselected as the successor.

Dependencies supported by current evidence (not a fabricated serial chain):

```text
#85 (standalone distribution)
      proves standalone build / distribution architecture
      preserves the already-established Core boundary
      consumes today's supported input: plant.yaml

#88 (release / version contract)
      later provides automated release / version orchestration
      for the distributable artifacts #85 makes possible

#89 (project contract)
      later defines the durable engineering project representation
      that richer Open/Save operates on

later editor capabilities
      consume evidence from both #85 and #89
```

`#88 → #85` and `#89 → #85` are **not** hard dependencies: the repository already
carries an application version (`0.1.0`) sufficient for versioned development
artifacts, and today's `plant.yaml` input is sufficient to verify the standalone
application architecture. #85 may later feed #88 (publishing the artifacts #85
makes possible) and #89 may later define what richer Open/Save operates on, but
neither blocks the first #85 implementation. #77 and #84 remain independent
governance/maintenance work and are also not prerequisites of #85.

Unresolved future concern recorded by this gate (belongs to #89/future
persistence evidence, not to #85): a DeepPlant project will eventually need to
store presentation state (diagram positions, layout, per-view overrides, possibly
multiple diagrams/views). Presentation state is **not** semantic engineering
state; that must not become a reason to block #85. #89 must create a
project-level place where such state can later live **without** forcing the exact
presentation schema now.

#### #85 child slices (decomposition)

Recorded for the #85 implementation; **not** implemented by this planning fix.
#85 is one umbrella capability, not one mandatory PR, and it is decomposed into
child implementation slices:

```text
#85 — Establish independent DeepPlant Core and standalone editor distribution
  ├── distribution foundation        delivered by PR #92
  │     independent Core boundary
  │     editor dependency boundary
  │     bundled Python runtime
  │     bundled Vue SPA
  │     checkout-independent resources
  │     Windows installer
  │     Linux AppImage
  │     native packaging CI
  │     packaged smoke/E2E
  └── native desktop host            delivered by PR #93
        graphical application window
        embedded shared Vue frontend
        native Open workflow
        no required external browser
        desktop lifecycle
```

The first slice preserved the existing browser-hosted runtime, because its
immediate goal was to prove self-contained Windows/Linux packaging without
changing the product UI host. The second slice then changed only the host:

```text
distribution foundation (PR #92)
packaged executable → local FastAPI/Uvicorn → external browser

delivered product (PR #93)
packaged executable → native desktop host → embedded shared Vue SPA
```

Both slices carry automated evidence proving the packaged product. #85 is
complete.

Deliberately excluded from the first slice (and from this selection): automatic
updates, code signing, Microsoft Store / Flatpak / Snap publishing, PyPI
publishing, commercial licensing, repository separation, complete public Python
API stabilization, complete editor functionality, semantic editing, Save, and the
project format. The product capability being selected is: *prove the standalone
application architecture now, while the editor is still small.*

The exact packaging technology is deliberately **not** selected here. No current
repository evidence decides it; technology selection belongs to the #85
implementation investigation (potential candidates may be evaluated there).

No successor product capability after #85 is preselected, and no successor Issue
is created by this gate (see **Now** and **Next**).

### Completed Context

- **Issue #82 is delivered (browser E2E):** the Engineering Editor now has a real
  browser system/browser test layer. A minimal Playwright (`@playwright/test`,
  Chromium only) suite lives in the new `apps/editor/e2e/` root — deliberately
  outside the Vitest `tests/` tree — and runs through `make frontend-e2e`
  (`pnpm e2e`), which installs from the committed lockfile, builds the production
  SPA, and then starts the real user-facing `uv run deepplant ui
  examples/realistic-process-fragment/plant.yaml --symbol-role PS-vessel=vessel
  --port 0` CLI. Readiness is the CLI's own announced loopback URL (no fixed port,
  no readiness sleep), and the started process group is always stopped (SIGTERM
  then bounded SIGKILL). Two tests prove (1) the realistic fragment renders 7
  `ProcessStep`s and 7 `ProcessStream`s with `Valid` semantics, `Fit view` works,
  and selecting `PS-pump` then `S-004` through the real rendered graph yields the
  correct semantic Inspector fields, and (2) a semantically valid model whose
  `PS-vessel` presentation role is unresolvable still reports `Valid` while
  showing the projection error as a separate alert. The suite uses DeepPlant-owned
  accessible names (`Process step <id>` / `Process stream <id>`, supplied by the
  adapter) as resilient selectors, adds no mocks, and touches no transport,
  domain, or architecture. `make check` still never downloads a browser; a
  dedicated CI job installs Chromium and runs the suite, uploading trace,
  screenshot, and server-log artifacts only on failure. See
  [frontend/testing.md](../frontend/testing.md).
- **Issue #81 is delivered (frontend refactor, unocss, component and integration
  tests):** the #80 contract was applied to the existing editor frontend without
  changing product behaviour. `App.vue` is now a thin application composition
  root; the Process/PFD feature separates page composition, components,
  composables, transport and view models inside its own module, owning feature
  state (`process-pfd/composables/useProcessPfd.ts`), transport
  (`transport/api.ts`) and runtime contract narrowing
  (`transport/projection-contract.ts`); Vue Flow stays behind the canvas
  and adapter boundaries and emits semantic ids only; UnoCSS over semantic
  `--dp-*` tokens replaced broad global feature CSS; and Vue component plus
  feature-integration tests were added alongside the DOM-free pure suites. See
  [history/implementation-slices.md](../history/implementation-slices.md).
- **Issue #80 is delivered (frontend engineering contract and quality gates):**
  the canonical, repository-owned frontend engineering contract now lives in
  [docs/dev/frontend/](../frontend/index.md) (architecture and feature ownership,
  Vue/component/composable conventions, state ownership, effects and watchers,
  TypeScript safety, the selected UnoCSS styling direction, the testing pyramid,
  and accessibility), with a single canonical review checklist. It is enforced by
  a real ESLint flat-config gate (`apps/editor/eslint.config.js`, `make
  frontend-lint`) that is part of `make frontend-check` and therefore `make
  check`, and that implements the hard size/cohesion limits. A tool-neutral
  `frontend-engineering` agent skill routes to the contract. No editor product
  behaviour was intentionally changed and no #81 refactor was performed. See
  [history/implementation-slices.md](../history/implementation-slices.md).
- **Issue #79 is delivered (foundation hardening):** the Engineering Editor
  architecture now matches the repository structure. The browser editor is an
  explicit standalone application under `apps/editor/` instead of an
  unclassified root-level `frontend/` tree, and the custom `http.server` editor
  adapter was replaced by a thin FastAPI application factory
  (`create_editor_api`) served by Uvicorn on loopback only. Engineering behaviour
  stayed in `EditorApplication` and below it — now factored into the
  framework-independent `src/deepplant/editor/application.py` with the transport
  in `src/deepplant/editor/api.py` — so the semantic core and the CLI
  remain usable without the GUI, and no editor capability was added. See
  [history/implementation-slices.md](../history/implementation-slices.md) and
  [architecture.md](../architecture/index.md#engineering-editor-slice-implemented).
- **Issue #75 is delivered:** the first runnable, read-only Process/PFD editor
  slice shipped — a DeepPlant-owned Process/PFD projection
  (`src/deepplant/editor/projection.py`), a loopback-only local application
  boundary (`src/deepplant/editor/app.py`, later split into the
  framework-independent `src/deepplant/editor/application.py` and the
  FastAPI/Uvicorn `src/deepplant/editor/api.py` in Issue #79), the
  `deepplant ui <path>` launcher, and a Vue 3 +
  TypeScript + Vite + Vue Flow SPA under `apps/editor/`. It is read-only
  (pan/zoom/fit/selection/Inspector/validation status) and delivered no semantic
  editing, presentation persistence, undo/redo, P&ID rendering, or process ↔
  physical realization. See
  [history/implementation-slices.md](../history/implementation-slices.md).
- **Issue #68 is delivered:** the Engineering Editor MVP v0.1 is bounded in
  [product.md](product.md), including the PFD/P&ID subsets, semantic
  source-of-truth interaction direction, user journey, non-goals, and Issue
  #39 relationship. It authorized no GUI implementation; the first GUI slice was
  later authorized by Issue #75.
- **Issue #69 delivered design/evidence:** the minimalist Engineering Editor
  UI/UX interaction architecture is recorded in
  [research/engineering-editor-ux.md](../research/engineering-editor-ux.md)
  (canvas-dominant minimum permanent chrome, one command direction, four
  separated state kinds, engineering-concept explorer, PFD/P&ID editor views,
  cardinality-neutral related-object navigation, shared command surface, and the
  MVP/later/not-now UX matrix). It created no ADR and authorized no GUI
  implementation, dependency, or `frontend/` directory; Issue #75 later
  introduced them within its own narrow scope.
- **Issue #70 delivered design/evidence:** the reuse-first Engineering Editor
  frontend architecture is recorded in
  [research/engineering-editor-reuse-architecture.md](../research/engineering-editor-reuse-architecture.md).
  It selects a small replaceable stack (Vue 3 + TypeScript + Vite foundation; Vue
  Flow as the preferred canvas candidate behind a DeepPlant projection/adapter;
  Reka UI primitives) and defers/rejects docking (Dockview), text editing (Monaco),
  layout/routing (ELK/elkjs), a state manager (Pinia), general utilities (VueUse),
  and the shadcn-vue / X6 / Cytoscape.js alternatives, each with a recorded
  adoption trigger. It keeps semantic/presentation/framework state separated,
  places undo/redo at the application-command boundary, reuses the existing
  renderer and SVG symbol contract, created no ADR, and authorized no GUI
  implementation, dependency, or `frontend/` directory; Issue #75 later
  introduced those within its own narrow, read-only scope.
- **Issue #39 delivered decision/evidence:** the process ↔ physical realization
  ownership boundary is decided by
  [process-physical-realization-boundary.md](../research/process-physical-realization-boundary.md)
  and [ADR-0016](../decisions/ADR-0016-process-physical-realization-boundary.md);
  no process ↔ physical realization implementation slice or successor is
  selected.
- **Issue #20 is delivered:** the auditable DEXPI 2.0.0 supported-subset and
  semantic round-trip contract is published in
  [dev/reference/dexpi-process-adapter.md](../reference/dexpi-process-adapter.md).
- **Issue #32 delivered decision/evidence:** the separate qualified-engineering
  quantity boundary is decided in
  [research/qualified-engineering-quantities.md](../research/qualified-engineering-quantities.md)
  and [ADR-0013](../decisions/ADR-0013-qualified-engineering-quantity-boundary.md).
- **Issue #21 is closed:** its `StoringMaterial` topic remains historical or
  deferred strategic/evidence context, not an open executable Issue.

### Scope Discipline

- No hosted/cloud backend, authentication, database, ORM, collaboration
  service, containers, or production server infrastructure before a concrete
  requirement justifies them.
- A minimal local application/transport/API boundary is introduced only when the
  selected standalone SPA vertical slice authorizes it. #75 introduced exactly one
  and #79 corrected it: an explicit FastAPI application factory run by Uvicorn,
  loopback-only, read-only, and single-user. It is not a hosted, authenticated,
  production, containerized, or database-backed service surface, and it adds no
  WebSockets, authentication, background jobs, or persistence infrastructure.
- No empty architecture trees, application directories, or GUI dependencies
  before a current executable slice requires them. The only application tree is
  `apps/editor/`, which Issue #79 created by relocating the delivered SPA.
- No full instrumentation, simulation, 3D, complete DEXPI, HAZOP/SIS, or all
  EPC disciplines in the Engineering Editor MVP v0.1.
- Semantic state remains distinct from presentation/layout state and
  frontend-framework state; YAML remains serialization, not the domain model.
- `Connection` is topology only; do not attach pipe/stream/signal engineering
  semantics until a real requirement justifies them.
- #85 authorized a bounded standalone-distribution and desktop-host vertical
  slice and the preservation of the Core boundary, not a Core redesign. DeepPlant
  Core must not acquire desktop, GUI, FastAPI-application, or packaging
  dependencies; the dependency direction stays `applications → Core`, and the CLI
  and editor continue to consume the same Core. Packaging and desktop-host
  tooling was introduced only within the two #85 child slices (PR #92 distribution
  foundation; PR #93 native desktop host) and is confined to the optional
  `deepplant[editor]`/`deepplant[desktop]` extras, the `package`/`desktop` uv
  groups, and the packaging stages — never the base Core installation.
- A future project/persistence contract (#89) will own the home for presentation
  state (diagram positions, layout, per-view overrides, multiple views). That is
  not semantic engineering state, it is not required for #85, and defining it must
  not become a reason to block standalone distribution.

## Directional Capability Roadmap

The long-term capability progression (stages, goals, dependencies, and their
deliberately open questions) is recorded in [direction.md](direction.md). It is
product context, not implementation authorization; the anti-roadmap below
governs what may be built now.

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
- GUI implementation, editor application structure, and GUI dependencies are
  authorized only within the explicitly selected Engineering Editor slices. The
  hardening sequence is #79 (delivered: application layout + FastAPI boundary) →
  #80 (delivered: frontend engineering contract + quality gates) → #81
  (delivered: frontend refactor + component/integration tests) → #82 (delivered:
  browser E2E); that sequence does not authorize semantic editing, presentation
  persistence, a GUI redesign, P&ID, or broader Engineering Editor infrastructure
- desktop/packaging tooling (desktop framework, webview host, bundlers,
  installers, CI packaging jobs) was authorized only within the two #85 child
  slices (PR #92 distribution foundation; PR #93 native desktop host) — it is
  confined to those slices and the `package`/`desktop` build groups, and is not
  release polish for other work
- the multi-discipline stage does not justify generic entity hierarchies now
- the DEXPI stage does not justify DEXPI-shaped domain objects now
- the physical-piping realization question and the separate process ↔ physical
  realization question do not justify attaching pipe or process-stream semantics
  to `Connection` now — and the decided piping layer (ADR-0011) honours that by
  referencing identified connections instead of widening `Connection`
- selecting #85 authorized only the bounded standalone-distribution and
  desktop-host slices: it does not authorize automatic updates, code signing,
  Microsoft Store / Flatpak / Snap or PyPI publishing, commercial licensing,
  repository separation, complete public Python API stabilization, complete
  editor functionality, semantic editing, Save, or the project format
- defining the project format (#89) does not authorize semantic editing,
  Save/mutation, or presentation persistence by itself; the first #89 slice is the
  smallest project/persistence vertical slice, not the full project architecture

Think broadly about the destination. Build narrowly in the current iteration.
