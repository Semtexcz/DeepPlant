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
| Local editor application boundary | `src/deepplant/editor/app.py` | this document (local-only, replaceable) |
| Editor SPA | `frontend/` | this document (Vue 3 + TypeScript + Vite + Vue Flow) |

Runtime and toolchain:

- Python >= 3.12, managed with `uv`.
- Runtime dependencies: Typer (CLI), Pydantic v2, PyYAML. The DEXPI adapter and
  the local editor boundary use only the standard library.
- Dev toolchain: pytest + pytest-cov, Ruff, Pyright (strict).
- Frontend toolchain (`frontend/`, ephemeral build output): Vue 3, TypeScript,
  Vite, Vue Flow, Vitest, `vue-tsc`. The package manager is pinned by
  `frontend/package.json` (`packageManager`) with a committed
  `frontend/pnpm-lock.yaml`.

## Module boundaries

| Module | Owns | Must not |
|---|---|---|
| `model.py` | semantic objects, ids, structural and reference rules | import CLI, YAML, file I/O, rendering, adapters, or any consumer concern |
| `io.py` | YAML <-> typed models, `PlantLoadError` / `PlantSaveError` | contain domain rules or presentation logic |
| `__main__.py` | argument parsing and user-facing output | contain domain logic; it delegates to `io.load_plant` |
| `render.py` | presentation policy, symbol-role resolution, layout, routing, SVG output | store presentation data in the semantic model, or require it to validate |
| `adapters/dexpi.py` | DEXPI XML <-> `ProcessModel` conversion and its fail-closed checks | leak DEXPI shapes into the canonical model |
| `editor/projection.py` | the read-only Process/PFD view projection of `ProcessModel` | contain domain rules, import the CLI or a web framework, or leak framework concepts |
| `editor/app.py` | the small, local-only, replaceable editor transport boundary | contain domain or projection logic, or claim production/server security |
| `assets/symbols/**` | distributable graphical assets with provenance | encode engineering semantics |
| `frontend/` (TypeScript) | browser view state, the Vue Flow adapter, and the read-only Inspector | re-implement the semantic model, parse YAML, or become project truth |

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
                  editor/app.py   ──►  frontend/ (browser)
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

Issue #75 delivered the first runnable, read-only Process/PFD editor slice. It is
deliberately narrow and Process/PFD-only:

```text
YAML → load_plant → PlantModel → ProcessModel
                                   ↓  projection (src/deepplant/editor/projection.py)
                        DeepPlant-owned read-only Process/PFD projection
                                   ↓  local boundary (src/deepplant/editor/app.py)
                        JSON + canonical symbol assets + built SPA assets
                                   ↓  frontend adapter (frontend/src/process-pfd/)
                        Vue Flow nodes/edges  →  interactive read-only canvas
```

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
- **Transport.** `deepplant.editor.app` is a small, local-only boundary built on
  the Python standard library `http.server`. For this slice (one JSON route, the
  canonical symbol assets, and the built SPA assets) a compact explicit handler
  is maintenance-cheap and adds **no Python runtime dependency**; it also keeps
  the boundary replaceable, since only `EditorApplication`,
  `load_editor_application`, and `serve_editor` are used by the CLI. It binds to
  loopback only and makes no production or server-security claim.
- **Launch.** `deepplant ui <path>` loads the project through the ordinary
  DeepPlant loader and serves the built frontend from `frontend/dist`
  (or `--assets-dir`).
- **Frontend.** `frontend/` is a Vue 3 + TypeScript + Vite + Vue Flow SPA. The
  adapter (`process-pfd/vue-flow-adapter.ts`) is the only place Vue Flow shapes
  appear. Selection is transient UI state, translated back to DeepPlant identity
  before the Inspector renders anything.

Explicit non-goals of this slice (unchanged direction, not implemented):
semantic editing, process step/stream creation, deletion, property editing,
save, undo/redo, presentation persistence, P&ID rendering, physical/P&ID
symbols, the ADR-0016 mapping, an automatic layout engine, a plugin system, and
an application-command architecture.

Known limitation: the built frontend assets are read from the checkout
(`frontend/dist`); bundling them into the Python wheel is not done in this slice.
A checkout run is a complete user path (`make frontend-build`, then
`deepplant ui <path>`); wheel packaging of the SPA assets remains a future step.

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

make check   # ruff format --check, ruff check, pyright, pytest, frontend-check
make frontend-check  # pnpm install --frozen-lockfile, vue-tsc, vitest, vite build
make build   # uv build
```

[quality.md](../workflow/quality.md) owns what these gates are expected to prove.

## Related

- [contracts/index.md](../../contracts/index.md) — the current contract set.
- [roadmap.md](../planning/roadmap.md) — current state, next direction, evidence gaps.
- [direction.md](../planning/direction.md) — capability progression (not authorization).
- [product.md](../planning/product.md) — product thesis and long-term position.
- [decisions/index.md](../decisions/index.md) — decision records.
- [conventions.md](../workflow/conventions.md) — document types and linking rules.
