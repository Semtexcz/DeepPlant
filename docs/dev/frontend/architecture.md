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
tree is **not** the goal. Issue #81 applied feature ownership inside the existing
`process-pfd/` module and deliberately did **not** create `app/`, `shared/`, or
`features/`, because no current responsibility required those directories:

```text
apps/editor/src/
├── App.vue                        application composition root
├── main.ts                        SPA entry + style layers
├── styles.css                     global only: tokens, reset, root sizing, typography
└── process-pfd/                   the Process/PFD feature module
    ├── ProcessPfdWorkspace.vue    feature composition + feature state wiring
    ├── ProcessPfdCanvas.vue       canvas integration: lifecycle, events, viewport
    ├── InspectorPanel.vue         read-only Inspector
    ├── ProcessNode.vue            canvas integration: custom-node symbol rendering
    ├── useProcessPfd.ts           feature state: projection, selection, derived Inspector
    ├── api.ts                     transport access
    ├── projection-contract.ts     unknown -> runtime narrowing -> DTO
    ├── dto.ts                     read-only projection DTO contract
    ├── inspector-model.ts         selection -> Inspector view model
    └── vue-flow-adapter.ts        canvas integration: the only Node/Edge graph shapes
```

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
(`process-pfd/dto.ts` for the shape plus runtime narrowing in
`process-pfd/projection-contract.ts`, reached through the transport in
`process-pfd/api.ts`). That is the documented current state. Generated OpenAPI
clients are deliberately not introduced; if they ever are, that is a separate,
evidence-backed decision.

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
│   ├── ProcessPfdWorkspace.vue     feature composition + feature state wiring
│   ├── useProcessPfd.ts            feature state (projection, selection, derived)
│   ├── InspectorPanel.vue          read-only Inspector
│   ├── dto.ts                      projection DTO contract
│   ├── api.ts                      transport access
│   ├── projection-contract.ts      unknown -> narrowed DTO
│   └── inspector-model.ts          selection -> Inspector view model
│
└── Vue Flow integration surface (the only place framework code appears)
    ├── ProcessPfdCanvas.vue        canvas lifecycle, events, viewport / fit-view
    ├── ProcessNode.vue             custom-node framework props, Handle, Position
    └── vue-flow-adapter.ts         Node/Edge graph shapes + DTO -> framework mapping
```

The invariants are:

- Vue Flow `Node`/`Edge` **graph shapes** belong only to `vue-flow-adapter.ts`.
- Vue Flow **framework objects/types** must not cross upward out of the surface
  into `App.vue`, `ProcessPfdWorkspace.vue`, `useProcessPfd.ts`,
  `InspectorPanel.vue`, `inspector-model.ts`, `dto.ts`,
  `projection-contract.ts`, or `api.ts`.
- `ProcessNode.vue` may depend on Vue Flow but never becomes semantic or domain
  state: it renders a projected symbol node and declares its non-connectable
  handles, and it carries no engineering truth of its own.
- Framework interaction leaves the surface as DeepPlant-owned meaning:

```text
framework click  ->  DeepPlant semantic id  ->  feature selection action
```

Never:

```text
Vue Flow Node/Edge  ->  workspace / feature state / Inspector
```

## Module boundaries (current)

| Module | Owns | Must not |
|---|---|---|
| `src/App.vue` | application composition: shell, application chrome, active view, toolbar wiring | own projection, selection, Inspector, or framework state |
| `src/process-pfd/ProcessPfdWorkspace.vue` | feature composition: binds feature state to the canvas, notices, Inspector, and status strip | reach into Vue Flow or parse transport data |
| `src/process-pfd/useProcessPfd.ts` | feature state: remote/projection state, selection state, loading lifecycle, derived Inspector and status | hold Vue Flow state or perform I/O directly |
| `src/process-pfd/ProcessPfdCanvas.vue` | Process/PFD integration surface: Vue Flow canvas, node-type registration, view projection, framework events, viewport / fit-view | emit Vue Flow `Node`/`Edge` or framework objects upwards |
| `src/process-pfd/ProcessNode.vue` | Process/PFD integration surface: Vue Flow custom-node presentation (`NodeProps`, `Handle`, `Position`, engineering symbol node rendering) | own engineering truth or hold semantic state |
| `src/process-pfd/dto.ts` | the read-only projection DTO contract | contain a domain model or framework shapes |
| `src/process-pfd/api.ts` | transport access to the local boundary (projection route, symbol asset URL) | interpret or validate payload shape |
| `src/process-pfd/projection-contract.ts` | `unknown` -> runtime narrowing -> typed DTO | define a second semantic model |
| `src/process-pfd/vue-flow-adapter.ts` | Process/PFD integration surface: the only Vue Flow `Node`/`Edge` graph shapes, framework ids, handle ids, DTO -> graph conversion, and DeepPlant identity carried in framework `data` | leak `Node`/`Edge` or framework objects outside the integration surface |
| `src/process-pfd/inspector-model.ts` | selection → read-only Inspector view mapping | inspect framework objects or labels |
| `src/process-pfd/InspectorPanel.vue` | rendering the read-only Inspector view model | own engineering truth or touch framework objects |
| `src/styles.css` | semantic tokens, minimal reset, root sizing, global typography | own feature/component selectors |

The application path is one-way:

```text
App.vue
    ↓
ProcessPfdWorkspace.vue  (feature state + feature UI)
    ├── Vue Flow integration surface
    │   ├── ProcessPfdCanvas.vue  (canvas lifecycle, events, viewport)
    │   ├── ProcessNode.vue       (custom-node presentation)
    │   └── vue-flow-adapter.ts   (Node/Edge shapes, DTO mapping)
    └── InspectorPanel.vue
```

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
- Vue Flow stays behind its adapter; a future canvas replacement must be possible
  without touching the DTOs or the semantic core.

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
