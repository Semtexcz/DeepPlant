---
type: architecture
status: active
canonical_for:
  - frontend-architecture
  - frontend-feature-ownership
  - frontend-size-guardrails
read_when:
  - frontend-change
  - editor-frontend-work
  - frontend-architecture-change
update_when:
  - frontend-architecture-change
  - frontend-tooling-change
depends_on:
  - docs/dev/frontend/index.md
  - docs/dev/architecture/index.md
  - docs/dev/workflow/quality.md
decision:
  - docs/dev/decisions/ADR-0002-semantic-model-is-the-core.md
  - docs/dev/decisions/ADR-0003-separate-semantic-and-presentation-models.md
  - docs/dev/decisions/ADR-0009-separate-process-function-from-symbol-role.md
evidence:
  - docs/dev/research/engineering-editor-reuse-architecture.md
superseded_by: null
---

# Frontend Architecture

> **Question this document answers:** how must the Engineering Editor frontend be
> composed, how is code owned, where are the DeepPlant boundaries, and which
> dependencies and size limits apply?

The canonical application path is `apps/editor/`. It is not moved or renamed.

## Preferred direction

```text
application composition
        ↓
feature modules
        ↓
components + composables + feature helpers
        ↓
DeepPlant frontend contract / adapters
        ↓
FastAPI transport (src/deepplant/editor/api.py)
        ↓
DeepPlant application / core
```

A future tree may resemble `app/`, `features/`, `shared/`, but matching that
tree is **not** the goal. Issue #81 applied the durable rule **feature first,
responsibility second** inside the existing `process-pfd/` module, and
deliberately did **not** create global technical buckets (`app/`, `shared/`,
`features/`, `components/`, `composables/`, `services/`, `view-models/`), because
no current code is shared across more than one feature:

```text
apps/editor/src/
├── App.vue                        application composition root (shell + toolbar)
├── main.ts                        SPA entry + style layers
├── styles.css                     global only: tokens, reset, root sizing, typography
└── process-pfd/                   the Process/PFD feature
    ├── pages/
    │   └── ProcessPfdPage.vue     page composition: feature state + screen composition
    ├── components/
    │   ├── ProcessPfdCanvas.vue   canvas integration: lifecycle, events, viewport
    │   ├── ProcessNode.vue        canvas integration: custom-node symbol rendering
    │   └── InspectorPanel.vue     read-only Inspector
    ├── composables/
    │   └── useProcessPfd.ts       feature state: workspace, projection, selection, derived
    ├── transport/
    │   ├── api.ts                 transport access
    │   ├── projection-contract.ts unknown -> runtime narrowing -> DTO
    │   └── dto.ts                 read-only projection DTO contract
    ├── view-models/
    │   ├── inspector.ts           selection -> Inspector view model
    │   └── workspace-status.ts    workspace/validation -> status view model
    └── adapters/
        └── vue-flow.ts            canvas integration: the only Node/Edge graph shapes
```

The durable rule is:

> Feature-specific code stays inside its feature. Inside a feature, separate
> page composition, reusable/visual components, composables, transport
> contracts, view models, and external-framework adapters when those
> responsibilities are real. Do not create global technical buckets unless code
> is genuinely shared across multiple features.

Create a responsibility directory inside a feature only when that responsibility
actually exists. The `process-pfd/` layout above is the current set of real
responsibilities, **not** a mandate that every future feature must have all six
directories. Do not over-nest further (`components/canvas/`,
`transport/contracts/`): the selected granularity is feature → responsibility →
file.

`apps/editor/src/` contains production application code only. Automated frontend
tests and their fixtures live under `apps/editor/tests/` (their structure is
documented in [testing.md](testing.md)); fixtures are test-owned and are never
imported by production source.

> **Canonical rule:** production application code lives under
> `apps/editor/src/`. Automated frontend tests live under `apps/editor/tests/`;
> test fixtures are test-owned and must not live in, or be imported by,
> production source code.

The rule is:

> Cohesion and clear ownership matter more than matching a prescribed directory
> tree.

Prefer feature ownership. Do not create generic buckets (`utils/`, `helpers/`,
`services/`, `common/`, `composables/`) that merely collect unrelated code.
Shared code exists only when it is genuinely cross-cutting. The existing
`process-pfd/` folder is already a feature module and remains the model to follow.

## DeepPlant boundary (non-negotiable)

```text
Python semantic model  !=  transport DTO  !=  Vue application state  !=  Vue Flow state
Vue Flow Node          !=  ProcessStep
Vue Flow Edge          !=  ProcessStream
```

The browser must not:

- parse DeepPlant YAML into an independent domain model;
- recreate semantic validation;
- become authoritative for engineering state;
- persist Vue Flow objects as engineering truth;
- infer semantic identity from labels, coordinates, or Vue Flow framework ids;
- leak Vue Flow framework objects/types out of the integration surface into
  feature or application layers.

The direction is one-way and stays replaceable:

```text
DeepPlant semantic / application core
        ↓
projection / transport contract
        ↓
frontend DTO boundary
        ↓
replaceable Vue Flow adapter
```

The current transport contract is **hand-written and explicit**
(`process-pfd/transport/dto.ts` for the shape plus runtime narrowing in
`process-pfd/transport/projection-contract.ts`, reached through the transport in
`process-pfd/transport/api.ts`). That is the documented current state. Generated
OpenAPI clients are deliberately not introduced; if they ever are, that is a
separate, evidence-backed decision.

## Process/PFD Vue Flow integration surface

Vue Flow-specific code is confined to an explicit **integration surface** inside
the Process/PFD feature. This is deliberately coarser than "every framework shape
lives in one file": `ProcessNode.vue` is a legitimate Vue Flow custom node and
imports framework objects (`Handle`, `Position`, `NodeProps`), so the surface has
three members, not two.

```text
Process/PFD feature (process-pfd/)
│
├── framework-independent feature layer
│   ├── pages/ProcessPfdPage.vue            page composition + feature state wiring
│   ├── composables/useProcessPfd.ts        feature state (workspace, projection, selection, derived)
│   ├── components/InspectorPanel.vue       read-only Inspector
│   ├── transport/dto.ts                    projection DTO contract
│   ├── transport/api.ts                    transport access
│   ├── transport/projection-contract.ts    unknown -> narrowed DTO
│   ├── view-models/inspector.ts            selection -> Inspector view model
│   └── view-models/workspace-status.ts     workspace/validation -> status view model
│
└── Vue Flow integration surface (the only place framework code appears)
    ├── components/ProcessPfdCanvas.vue     canvas lifecycle, events, viewport / fit-view
    ├── components/ProcessNode.vue          custom-node framework props, Handle, Position
    └── adapters/vue-flow.ts                Node/Edge graph shapes + DTO -> framework mapping
```

The invariants are:

- Vue Flow `Node`/`Edge` **graph shapes** belong only to `adapters/vue-flow.ts`.
- Vue Flow **framework objects/types** must not cross upward out of the surface
  into `App.vue`, `pages/ProcessPfdPage.vue`, `composables/useProcessPfd.ts`,
  `components/InspectorPanel.vue`, `view-models/inspector.ts`,
  `transport/dto.ts`, `transport/projection-contract.ts`, or `transport/api.ts`.
- `components/ProcessNode.vue` may depend on Vue Flow but never becomes semantic
  or domain state: it renders a projected symbol node and declares its
  non-connectable handles, and it carries no engineering truth of its own.
- Framework interaction leaves the surface as DeepPlant-owned meaning:

```text
framework click  ->  DeepPlant semantic id  ->  feature selection action
```

Never:

```text
Vue Flow Node/Edge  ->  page / feature state / Inspector
```

## Module boundaries (current)

| Module | Owns | Must not |
|---|---|---|
| `src/App.vue` | application composition: shell, application chrome, active view, toolbar wiring; `Fit view` is delegated to the page and disabled while no project is open | own projection, selection, Inspector, or framework state |
| `src/process-pfd/pages/ProcessPfdPage.vue` | page/screen composition: binds feature state to the canvas, notices, empty-workspace notice, Inspector, and status strip | reach into Vue Flow or parse transport data |
| `src/process-pfd/composables/useProcessPfd.ts` | feature state: workspace state (project or none), remote/projection state, selection state, loading lifecycle, derived Inspector and status, stale-response protection | hold Vue Flow state or perform I/O directly |
| `src/process-pfd/components/ProcessPfdCanvas.vue` | Process/PFD integration surface: Vue Flow canvas, node-type registration, view projection, framework events, viewport / fit-view | emit Vue Flow `Node`/`Edge` or framework objects upwards |
| `src/process-pfd/components/ProcessNode.vue` | Process/PFD integration surface: Vue Flow custom-node presentation (`NodeProps`, `Handle`, `Position`, engineering symbol node rendering) | own engineering truth or hold semantic state |
| `src/process-pfd/components/InspectorPanel.vue` | rendering the read-only Inspector view model, including its neutral no-project empty state | own engineering truth or touch framework objects |
| `src/process-pfd/transport/dto.ts` | the read-only projection + workspace DTO contract | contain a domain model or framework shapes |
| `src/process-pfd/transport/api.ts` | transport access to the local boundary (projection route, symbol asset URL) | interpret or validate payload shape |
| `src/process-pfd/transport/projection-contract.ts` | `unknown` -> runtime narrowing -> typed DTO (workspace state first, then projection) | define a second semantic model |
| `src/process-pfd/view-models/inspector.ts` | selection → read-only Inspector view mapping | inspect framework objects or labels, or become engineering truth |
| `src/process-pfd/view-models/workspace-status.ts` | workspace/projection/error → status text and tone (empty ≠ invalid) | inspect framework objects or hold feature state |
| `src/process-pfd/adapters/vue-flow.ts` | Process/PFD integration surface: the only Vue Flow `Node`/`Edge` graph shapes, framework ids, handle ids, DTO -> graph conversion, and DeepPlant identity carried in framework `data` | leak `Node`/`Edge` or framework objects outside the integration surface |
| `src/styles.css` | semantic tokens, minimal reset, root sizing, global typography | own feature/component selectors |

The dependency direction inside the feature is one-way:

```text
App.vue
    ↓
pages/ProcessPfdPage.vue
    │
    ├── composables/useProcessPfd.ts
    │   ├── transport/api.ts
    │   │   └── transport/projection-contract.ts
    │   │       └── transport/dto.ts
    │   │
    │   ├── view-models/inspector.ts
    │   │   └── transport/dto.ts
    │   └── view-models/workspace-status.ts
    │       └── transport/dto.ts
    │
    ├── components/ProcessPfdCanvas.vue
    │   ├── adapters/vue-flow.ts
    │   │   └── transport/dto.ts
    │   └── components/ProcessNode.vue
    │
    └── components/InspectorPanel.vue
        └── view-models/inspector.ts
```

This direction is a documented invariant, not a separate enforcement system: no
custom tooling validates directory imports. The structure and the current
TypeScript boundaries are enough for this slice.

Framework interaction is translated before it leaves the integration surface: a
Vue Flow node/edge click becomes a DeepPlant semantic id, and the feature state
resolves that id to a projected object. The Inspector therefore consumes
projection objects only, never framework objects.

## Dependencies

- Prefer existing dependencies and local helpers.
- A new dependency must solve a current problem, be recorded with its purpose,
  runtime/build/dev role, and licence in
  [THIRD_PARTY_NOTICES.md](../../../THIRD_PARTY_NOTICES.md), and be removable.
- Do not add a package merely to record a decision that another Issue will apply.
- Vue Flow-specific code stays inside the explicit Process/PFD integration
  surface; `Node`/`Edge` graph shapes remain confined to `adapters/vue-flow.ts`.
  A future canvas replacement must be possible without touching the transport
  DTOs or the semantic core.

## Size and cohesion guardrails

Logical LOC excludes blank lines and comments. Soft limits are review signals;
only hard limits fail a gate.

| Scope | Soft | Hard |
|---|---:|---:|
| TypeScript module | 250 | 500 |
| Vue SFC | 300 | 600 |
| Composable (`use*.ts`, `composables/**`) | 120 | 250 |
| Function | 40 | 80 |
| Test module | 400 | 800 |

The hard limits are enforced by `max-lines` and `max-lines-per-function` in
`apps/editor/eslint.config.js`, so `make frontend-lint` (and therefore
`make frontend-check` and `make check`) fails deterministically when one is
crossed. There are **no per-file size exemptions**: a limit change is made
centrally in the ESLint config, not loosened by an inline suppression.

Do not mechanically split cohesive code to satisfy a line count. The purpose is
to detect loss of cohesion, not to optimize for tiny files. If a hard limit is
genuinely wrong for a class of file, change the centralized config with recorded
reasoning instead of adding a suppression.
