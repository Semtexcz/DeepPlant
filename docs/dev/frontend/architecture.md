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
tree is **not** the goal, and this contract does not reorganize the current
frontend. The rule is:

> Cohesion and clear ownership matter more than matching a prescribed directory
> tree.

Prefer feature ownership. Do not create generic buckets (`utils/`, `helpers/`,
`services/`, `common/`, `composables/`) that merely collect unrelated code.
Shared code exists only when it is genuinely cross-cutting. The existing
`process-pfd/` folder is already a feature module and is the model to follow.

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
- leak Vue Flow types across unrelated application boundaries.

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
(`process-pfd/dto.ts` plus runtime narrowing in `process-pfd/api.ts`). That is
the documented current state. Generated OpenAPI clients are deliberately not
introduced; if they ever are, that is a separate, evidence-backed decision.

## Module boundaries (current)

| Module | Owns | Must not |
|---|---|---|
| `src/process-pfd/dto.ts` | the read-only projection DTO contract | contain a domain model or framework shapes |
| `src/process-pfd/api.ts` | browser access to the local boundary and `unknown` narrowing | re-implement semantics or trust raw JSON |
| `src/process-pfd/vue-flow-adapter.ts` | the only place Vue Flow `Node`/`Edge` shapes appear | leak `Node`/`Edge` outside the adapter |
| `src/process-pfd/inspector-model.ts` | selection → read-only Inspector view mapping | inspect framework objects or labels |
| `src/process-pfd/*.vue` | Vue Flow nodes and the read-only Inspector | own engineering truth |
| `src/App.vue` | current workspace composition and transient selection | grow into the permanent application controller (see [vue.md](vue.md)) |

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
