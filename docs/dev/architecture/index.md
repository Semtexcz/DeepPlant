---
type: architecture
status: active
canonical_for:
  - current-architecture
read_when:
  - architecture-change
  - new-module
  - start-work
depends_on:
  - docs/contracts/index.md
  - docs/dev/workflow/conventions.md
decision:
  - docs/dev/decisions/ADR-0001-baseline.md
  - docs/dev/decisions/ADR-0002-semantic-model-is-the-core.md
  - docs/dev/decisions/ADR-0003-separate-semantic-and-presentation-models.md
  - docs/dev/decisions/ADR-0004-yaml-is-a-serialization-format.md
evidence: []
superseded_by: null
---

# Architecture

Project type: `script`. Runtime level: `shared`. Governance: `lightweight`.

This document is a **boundary map**: what exists, where it lives, and which
document owns each current detail. It is deliberately not a specification. Every
obligation lives in a contract under [contracts/](../../contracts/index.md); reasons
live in [decisions/](../decisions/index.md); long-term direction lives in
[direction.md](../planning/direction.md).

## What exists

DeepPlant is a Python CLI package that implements a semantic engineering model
and a small set of consumers around it (ADR-0002):

```text
tests -> CLI (src/deepplant/__main__.py) -> io.load_plant -> model

YAML file
   ↓  PyYAML
Python data structure (dict)
   ↓  Pydantic validation
PlantModel -> Plant + Equipment[] (+ Port[]) + Connection[]
            + PipingModel?   + ProcessModel?
```

| Component | Location | Contract |
|---|---|---|
| Physical/plant model, validation | `src/deepplant/model.py` | [contracts/plant-model.md](../../contracts/plant-model.md) |
| Process graph model, S1–S4 | `src/deepplant/model.py` | [contracts/process-model.md](../../contracts/process-model.md) |
| Piping realization, C1 + P1–P5 | `src/deepplant/model.py` | [contracts/physical-piping.md](../../contracts/physical-piping.md) |
| YAML load/save boundary | `src/deepplant/io.py` | [contracts/yaml-format.md](../../contracts/yaml-format.md) |
| CLI (`--help`, `version`, `validate`) | `src/deepplant/__main__.py` | [contracts/cli.md](../../contracts/cli.md) |
| Headless process renderer | `src/deepplant/render.py` | [contracts/rendering.md](../../contracts/rendering.md) |
| `basic` SVG symbol pack | `src/deepplant/assets/symbols/process/basic/` | [dev/reference/svg-symbols.md](../reference/svg-symbols.md) |
| DEXPI 2.0.0 Process adapter | `src/deepplant/adapters/dexpi.py` | [dev/reference/dexpi-process-adapter.md](../reference/dexpi-process-adapter.md) |
| Public Python surface | `src/deepplant/__init__.py` | re-exports the contracts above |
| Process/PFD view projection | `src/deepplant/editor/projection.py` | [contracts/rendering.md](../../contracts/rendering.md) |
| Editor application (framework-independent) | `src/deepplant/editor/application.py` | this document (local-only) |
| Editor shared launch primitives | `src/deepplant/editor/launcher.py` | this document (used by both hosts) |
| Editor desktop host (Qt CLI + policy) | `src/deepplant/editor/desktop.py` | this document (host-specific, Qt-free) |
| Editor Qt/WebEngine window | `src/deepplant/editor/desktop_qt.py` | this document (the only GUI-toolkit module) |
| Editor FastAPI/Uvicorn transport and server lifecycle | `src/deepplant/editor/api.py` | this document (local-only, transport-thin) |
| Editor SPA (standalone application) | `apps/editor/` | this document (Vue 3 + TypeScript + Vite + Vue Flow) |
| Standalone Editor packaging | `tools/package_editor.py`, `packaging/windows/` | [workflow/packaging.md](../workflow/packaging.md) |

Runtime and toolchain:

- Python >= 3.12, managed with `uv`.
- Base runtime dependencies: Typer (CLI), Pydantic v2, PyYAML. FastAPI and Uvicorn
  are an explicit installation extra, `deepplant[editor]` (mirrored as a uv
  dependency group), so the semantic Core and the ordinary CLI stay installable
  and importable without the editor transport (Issue #85). The native desktop
  host adds PySide6/Qt WebEngine as the `deepplant[desktop]` extra (group
  `desktop`), which includes the transport. The DEXPI adapter and the rest of the
  core use only the standard library plus the base dependencies.
- Build-only tooling for the standalone application: PyInstaller (dependency
  group `package`), plus Inno Setup on Windows and `appimagetool` on Linux. None
  of it is a runtime dependency of the installed application. The non-Python
  tools are pinned and integrity-checked through `packaging/toolchain.toml` (see
  [workflow/packaging.md](../workflow/packaging.md)).
- Dev toolchain: pytest + pytest-cov, Ruff, Pyright (strict), and `httpx2` for the
  FastAPI/Starlette test client.
- Editor SPA toolchain (`apps/editor/`, ephemeral build output): Vue 3,
  TypeScript, Vite, Vue Flow, UnoCSS, Vitest with `@vue/test-utils` and
  `happy-dom`, Playwright (`@playwright/test`, Chromium only) with `@types/node`
  for the browser E2E suite, `vue-tsc`, and ESLint (flat config). The package
  manager is pinned by `apps/editor/package.json` (`packageManager`) with a
  committed `apps/editor/pnpm-lock.yaml`. The frontend engineering rules and gates
  are canonical in [frontend/](../frontend/index.md), and the browser E2E
  ownership, lifecycle, and selector policy in
  [frontend/testing.md](../frontend/testing.md).

## Module boundaries

| Module | Owns | Must not |
|---|---|---|
| `model.py` | semantic objects, ids, structural and reference rules | import CLI, YAML, file I/O, rendering, adapters, or any consumer concern |
| `io.py` | YAML <-> typed models, `PlantLoadError` / `PlantSaveError` | contain domain rules or presentation logic |
| `__main__.py` | argument parsing and user-facing output | contain domain logic; it delegates to `io.load_plant` |
| `render.py` | presentation policy, symbol-role resolution, layout, routing, SVG output | store presentation data in the semantic model, or require it to validate |
| `adapters/dexpi.py` | DEXPI XML <-> `ProcessModel` conversion and its fail-closed checks | leak DEXPI shapes into the canonical model |
| `editor/projection.py` | the read-only Process/PFD view projection of `ProcessModel` | contain domain rules, import the CLI or a web framework, or leak framework concepts |
| `editor/application.py` | the framework-independent editor application: project loading, projection views, symbol resolution, asset resolution | import FastAPI, Starlette, Uvicorn, or a GUI toolkit, or contain HTTP/runtime concerns |
| `editor/api.py` | the thin, local-only FastAPI/Uvicorn transport, the owned `EditorServer` lifecycle, and loopback binding | contain engineering logic, or claim production/server security |
| `editor/launcher.py` | the shared launch primitives both hosts use (`run_editor`, symbol-role parsing, help text) | import FastAPI, Uvicorn, or a GUI toolkit at import time |
| `editor/desktop.py` | the `deepplant-editor` command surface, the desktop dependency probe, the initial-project load, and the exact-origin embedded-navigation policy | import a GUI toolkit at import time, or hold engineering semantics |
| `editor/desktop_qt.py` | the native window, the embedded webview, the native Open dialog, and the Qt window/server lifecycle | parse DeepPlant YAML, own the semantic model, or become a second frontend |
| `assets/symbols/**` | distributable graphical assets with provenance | encode engineering semantics |
| `apps/editor/` (TypeScript) | application composition, the Process/PFD feature (projection state, selection, canvas/adapter, Inspector), transport and runtime contract narrowing, and styling | re-implement the semantic model, parse YAML, or become project truth (rules: [frontend/](../frontend/index.md)) |

The dependency direction is one-way:

```text
            semantic model (model.py)
                 ▲        ▲        ▲
     io.py ──────┘        │        └────── adapters/dexpi.py
   __main__.py            │
                    render.py  (presentation only)
                          ▲
              editor/projection.py
                          ▲
        editor/application.py  ──►  editor/api.py  ──►  apps/editor/ (shared SPA)
                                        ▲                        ▲
                                        │                        │
                     editor/desktop.py  ──►  editor/desktop_qt.py ┘
```

Consumers depend on the model; the model depends on nothing consumer-specific
(ADR-0002, ADR-0003). Exchange formats and editors are adapters or presentational
views, never the canonical shape.

## Durable invariants

1. **The semantic engineering model is the product core.** CLI, renderer,
   adapter, and future consumers depend on it, never the reverse (ADR-0002).
2. **Semantic data and presentation data stay separate.** No coordinate, symbol,
   role, or layout value is stored in a semantic model (ADR-0003, ADR-0009).
3. **YAML is a serialization format**, validated into typed models at the
   boundary; it is not the domain model (ADR-0004).
4. **Separate graph layers stay separate:** process graph, physical topology, and
   piping realization are distinct, and `Connection` carries adjacency only
   (ADR-0010, ADR-0011).
5. **Input is fail-fast.** Unknown fields, blank semantic strings, duplicate ids,
   and unresolvable references are rejected rather than silently normalized.
6. **Unsupported external content fails by name.** The DEXPI adapter rejects
   anything outside its explicit subset (ADR-0009, ADR-0012).
7. **No abstraction without a current requirement.** No database, queue, cache,
   service, container, plugin system, or generic entity hierarchy exists. A single
   user interface exists — the read-only Process/PFD editor slice — and it is a
   consumer behind an explicit projection/adapter boundary, never a source of
   domain truth (ADR-0001, ADR-0002; see the anti-roadmap in
   [roadmap.md](../planning/roadmap.md)).

## Layer summary

```text
PlantModel                     root aggregate (one plant)
├── Plant                      identity
├── Equipment[] / Port[]       physical inventory and connection points
├── Connection[]               directed, property-free adjacency (identified)
├── PipingModel?               line → segment → realization over connections
└── ProcessModel?              process steps, process ports, process streams
```

`ProcessModel` is independently valid; `PipingModel` is a dependent, cross-layer
validated submodel; neither depends on the other, and no process ↔ physical
mapping is implemented. ADR-0016 decides that any future relationship is owned in
a separate cross-layer realization layer.

## Engineering Editor slice (implemented)

Issues #75 and #79 delivered the first runnable, read-only Process/PFD editor
slice. It is deliberately narrow and Process/PFD-only:

```text
YAML → load_plant → PlantModel → ProcessModel
                                   ↓  projection (src/deepplant/editor/projection.py)
                        DeepPlant-owned read-only Process/PFD projection
                                   ↓  application (EditorApplication, src/deepplant/editor/application.py)
                        FastAPI transport (src/deepplant/editor/api.py) → Uvicorn (loopback only)
                                   ↓  HTTP: JSON projection + canonical symbol assets
                        editor application adapter (apps/editor/src/process-pfd/)
                        Vue Flow nodes/edges  →  interactive read-only canvas
```

### Repository layout and dependency direction

The browser editor is an **application**, not package code or reusable frontend
infrastructure, so it lives outside the Python package under `apps/editor/`:

```text
src/deepplant/          reusable Python package/library and CLI
src/deepplant/editor/   DeepPlant-owned editor application + FastAPI HTTP adapter
apps/editor/            the standalone Engineering Editor SPA (Vue 3 + Vite)
```

The dependency direction is one-way and the HTTP layer is a thin adapter only:

```text
apps/editor/ (Vue SPA)
        ↓  HTTP
FastAPI transport (src/deepplant/editor/api.py)
        ↓
EditorApplication (src/deepplant/editor/application.py)
        ↓
projection → renderer / semantic model
```

`apps/editor/` is the only tree for this application; there is no root-level
`frontend/` directory. Issue #79 selected this layout because the SPA is a
standalone, pinned Vite application with its own dependency graph, while
`src/deepplant/` is the reusable Python surface.

- **Projection.** `deepplant.editor.projection` turns a loaded `PlantModel` into
  `ProcessPfdProjection` and a JSON-ready transport DTO. It carries explicit
  semantic identity (`kind` + authored `id`), the semantic properties the
  Inspector shows, and DeepPlant presentation geometry. It is framework-free:
  nothing Vue-Flow-shaped is transported.
- **Presentation reuse.** The projection delegates symbol-role resolution,
  deterministic placement, and anchor-slot assignment to the renderer
  (`compute_process_pfd_layout`), and reads the canonical packaged symbol assets
  through `read_process_symbol_svg`. There is no second mapping and no second
  symbol pack.
- **Application and transport.** `deepplant.editor.application` owns
  `EditorApplication`, project loading, projection and validation reporting,
  symbol resolution, and asset resolution without importing FastAPI, Starlette,
  or Uvicorn, so it stays usable and testable from plain Python.
  `deepplant.editor.api` exposes that application through the explicit FastAPI
  application factory `create_editor_api(editor)`, run by Uvicorn (Issue #79).
  The route handlers are transport-thin: they receive a request, call
  `EditorApplication`, and map the result to a response. The `api.py` →
  `application.py` direction is one-way. It binds to loopback only and makes no
  production or server-security claim.
- **Launch and failures.** `deepplant ui <path>` and the standalone application
  entry point `deepplant-editor <path>` share one launch path (`run_editor`) and
  serve the built editor application from the assets the application carries,
  from an explicit `--assets-dir`, or from the source-checkout build. A
  successful `load_plant` is the
  semantic validation
  boundary. If the Process/PFD projection or its presentation role resolution
  fails, the local JSON route returns a separate view error (currently HTTP 422)
  with no projection; it does not recast the loaded semantic model as invalid.
- **Frontend.** `apps/editor/` is a Vue 3 + TypeScript + Vite + Vue Flow SPA with
  UnoCSS as the canonical utility layer. `App.vue` is a thin application
  composition root; the Process/PFD feature is owned by `process-pfd/` and
  separates its responsibilities: page composition (`pages/ProcessPfdPage.vue`),
  components (`components/ProcessPfdCanvas.vue`, `components/ProcessNode.vue`,
  `components/InspectorPanel.vue`), composables
  (`composables/useProcessPfd.ts`), transport (`transport/api.ts`,
  `transport/projection-contract.ts`, `transport/dto.ts`), view models
  (`view-models/inspector.ts`), and the framework adapter
  (`adapters/vue-flow.ts`). Vue Flow-specific code is confined to the explicit
  Process/PFD canvas integration surface (`components/ProcessPfdCanvas.vue`,
  `components/ProcessNode.vue`, `adapters/vue-flow.ts`), and its `Node`/`Edge`
  graph shapes appear only in `adapters/vue-flow.ts`: a framework node/edge click
  is translated to a DeepPlant semantic id before the feature resolves it, so the
  Inspector only ever consumes projection objects. Selection is transient UI
  state and nothing is persisted.
  Frontend engineering rules — feature ownership, Vue/TypeScript conventions,
  state ownership, styling ownership, accessibility, testing layers, and
  size/cohesion guardrails — are canonical in [frontend/](../frontend/index.md)
  and enforced by `make frontend-lint` and `make frontend-check`. Verification is
  split by lifecycle: isolated Vitest suites under `apps/editor/tests/` and the
  system/browser Playwright suite under `apps/editor/e2e/`, which starts the real
  `deepplant ui` CLI over the production build and drives real Chromium
  (`make frontend-e2e`).

Explicit non-goals of this slice (unchanged direction, not implemented):
semantic editing, process step/stream creation, deletion, property editing,
save, undo/redo, presentation persistence, P&ID rendering, physical/P&ID
symbols, the ADR-0016 mapping, an automatic layout engine, a plugin system, and
an application-command architecture.

Known limitation: none for frontend asset ownership any more. The built SPA is an
explicit resource of the standalone Editor application: the packaging stage maps
it into the frozen bundle at `deepplant/editor/dist` and the editor application
resolves it through `importlib.resources` before falling back to the
source-checkout build. The base Python wheel deliberately never contains it. See
[workflow/packaging.md](../workflow/packaging.md) and
[research/standalone-editor-distribution.md](../research/standalone-editor-distribution.md).

**Hosts of one frontend.** DeepPlant has **one** engineering frontend implemented
in web technologies. Three surfaces exist and stay distinct:

```text
deepplant <command>          Python API / CLI / automation
deepplant ui <path>          developer/browser host  → system browser (URL printed)
deepplant-editor [path]      native desktop host     → embedded webview, no browser
```

```text
delivered distribution foundation (PR #92)
packaged executable → local FastAPI/Uvicorn → external browser

delivered product (Issue #93, merged by PR #95)
packaged executable → native desktop host → embedded shared Vue SPA
```

The desktop host is a *thin host*, not a second frontend: it owns a window, a
native Open dialog, an embedded `QWebEngineView`, and the server/window
lifecycle. It re-implements no Process/PFD canvas, Inspector, engineering form,
navigation, or validation presentation, and it routes no engineering semantics
through a desktop-only bridge. It loads the ordinary production build of
`apps/editor/`, which a future web deployment would serve unchanged; the
technology evidence is in
[research/editor-desktop-host.md](../research/editor-desktop-host.md).

Two host policies are deliberately strict (Issue #93 review):

- **Exact-origin navigation.** The embedded view may only navigate within the
  specific `scheme://host:port` origin of the running `EditorServer` (plus the
  internal `data:`/`blob:`/`about:`/`qrc:` schemes), never an arbitrary loopback
  port, an external site, or `file:`. This is a webview host policy, not
  authentication.
- **Owned lifecycle.** Closing the window must stop the owned server thread,
  release the loopback socket, exit the Qt event loop, and let the process exit
  naturally; the packaged verification treats a surviving process as a failure.

`deepplant-editor` is the desktop application; it is deliberately not the general
DeepPlant CLI, and `deepplant ui` was deliberately not turned into the desktop
application.

## Not implemented (directional only)

Recorded here for orientation; none of it is authorized by appearing here (see
[direction.md](../planning/direction.md) for the capability progression and the anti-roadmap
for the prohibition):

- full DEXPI (energy/information flows, Plant/P&ID import and export, further
  step classes) and any other vendor adapter (COMOS, AVEVA, simulators);
- instrumentation, signals, and cross-sheet connector semantics;
- engineering rules and a validation engine above the structural layer;
- P&ID rendering, standards-aligned or company symbol packs, and semantic/editing
  capabilities in the editor (the delivered editor is read-only Process/PFD);
- typed engineering quantities, a canonical `Pipe` or `Nozzle`, and the
  process ↔ physical realization mapping implementation (its ownership boundary is
  decided by ADR-0016);
- presentation persistence, services, containers, and deployment.

Do not create packages for speculative concerns until real code needs them.

## Quality gates

```bash
make validate-docs
make validate-agent-skills

make check   # ruff format --check, ruff check, pyright, pytest, frontend-check (one local confidence gate before finalizing a PR)
make frontend-check  # install, eslint, typecheck (vue-tsc + tsc), vitest
make frontend-build  # production SPA bundle (separate, higher-cost verification)
make frontend-lint   # pnpm lint (ESLint correctness + hard size/cohesion limits)
make frontend-e2e    # production build + Playwright/Chromium against the real `deepplant ui`
make build   # uv build (release wheel/sdist, outside `make check`)
```

Run only the focused checks for the changed surface while implementing; run
`make check` once before finalizing a pull request. CI runs the same gate plus the
browser, packaging, and release jobs asynchronously: after the PR is pushed the
implementation session ends and does not wait for or poll CI.

[quality.md](../workflow/quality.md) owns what these gates are expected to prove.

## Related

- [contracts/index.md](../../contracts/index.md) — the current contract set.
- [roadmap.md](../planning/roadmap.md) — current state, next direction, evidence gaps.
- [direction.md](../planning/direction.md) — capability progression (not authorization).
- [product.md](../planning/product.md) — product thesis and long-term position.
- [decisions/index.md](../decisions/index.md) — decision records.
- [conventions.md](../workflow/conventions.md) — document types and linking rules.
