---
type: navigation
status: active
canonical_for:
  - frontend-engineering-contract-navigation
read_when:
  - frontend-change
  - editor-frontend-work
  - implement-change
  - review-change
update_when:
  - frontend-engineering-contract-change
depends_on:
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

# Frontend Engineering Contract

> **Question this document answers:** how must the DeepPlant Engineering Editor
> frontend (`apps/editor/`) be architected, typed, styled, tested, and reviewed,
> so that frontend quality does not depend on individual agent judgment?

This is the canonical, repository-owned frontend engineering contract for the
Vue 3 + TypeScript + Vite SPA under `apps/editor/`. It is developer-owned
governance, not a product feature, and it is tool-neutral: it must be usable from
any agent harness and by a human.

## Status vocabulary

| State | Meaning |
|---|---|
| **Implemented** | Already true or already enforced in the repository today. |
| **Canonical rule** | Required for future frontend work. |
| **Deferred** | Direction decided here, applied by a later Issue. |

The #81 refactor and the #82 browser E2E slice have both been applied, including
the explicit production (`apps/editor/src/`), isolated-verification
(`apps/editor/tests/`), and system/browser (`apps/editor/e2e/`) split. This
contract states the rules those slices must follow and does not itself change
editor product behavior.

## Topics

| Topic | Document |
|---|---|
| Application composition, feature ownership, boundaries, dependencies, size guardrails | [architecture.md](architecture.md) |
| Vue components, composables, state ownership, effects and watchers | [vue.md](vue.md) |
| TypeScript safety and assertion policy | [typescript.md](typescript.md) |
| Styling architecture and ownership | [styling.md](styling.md) |
| Frontend testing pyramid and its ownership | [testing.md](testing.md) |
| Accessibility baseline | [accessibility.md](accessibility.md) |
| Commands and the enforced gates | [quality.md](../workflow/quality.md) |

## Current vs canonical vs deferred

- **Implemented:** `apps/editor/` is a Vue 3 + TypeScript + Vite SPA with Vue Flow
  confined to the explicit Process/PFD canvas integration surface
  (`components/ProcessPfdCanvas.vue`, `components/ProcessNode.vue`,
  `adapters/vue-flow.ts`), whose `Node`/`Edge` graph shapes stay in
  `adapters/vue-flow.ts`; the Process/PFD feature separates page composition
  (`pages/ProcessPfdPage.vue`), components, composables, transport, view models,
  and framework adapters, and the transport contract is a hand-written,
  explicitly validated DTO boundary (`process-pfd/transport/dto.ts`,
  `transport/projection-contract.ts`, `transport/api.ts`); feature state lives in
  `process-pfd/composables/useProcessPfd.ts` and ordinary UI uses the canonical
  UnoCSS utility layer over semantic tokens. Production code lives under
  `apps/editor/src/` and automated tests under `apps/editor/tests/` (`unit/`,
  `component/`, `integration/`, `fixtures/`, with feature ownership and the
  verified responsibility below each layer); Vitest covers the pure modules, the
  Vue components, and the Process/PFD feature integration; ESLint (this
  contract), `vue-tsc`, Vitest, and a production build are enforced. Browser
  system tests live in the separate `apps/editor/e2e/` root and run the real
  local product (production build + real `deepplant ui` CLI + real Chromium).
- **Canonical rule:** everything below is binding for new frontend work.
- **Deferred:** none for the current frontend-engineering baseline; the #82
  browser E2E slice is delivered and the next product capability is decided at
  the [roadmap](../planning/roadmap.md) re-evaluation gate.

## Frontend review checklist

Use this for any change under `apps/editor/`. It is the single canonical copy;
the `frontend-engineering` skill points here rather than duplicating it.

- Is feature-specific code owned by its feature rather than a generic bucket?
- Does the component have one cohesive responsibility?
- Is application behavior trapped unnecessarily inside rendering code?
- Is a composable actually cohesive, and named for its domain?
- Is global state genuinely justified, and is mutable state owned once?
- Are Vue Flow concepts contained behind the explicit Process/PFD integration boundary?
- Is untrusted transport input narrowed from `unknown` before being trusted?
- Is an assertion hiding a type-design problem?
- Are watchers synchronizing duplicated state instead of an owned source?
- Are loading, error, and empty states explicit?
- Is accessibility preserved (semantics, names, keyboard, focus, non-color cues)?
- Is every new dependency justified and recorded?
- Are the size/cohesion hard limits crossed?
- Is the abstraction solving a current problem rather than a hypothetical one?
- Is documentation semantic (invariants, side effects, workarounds) and not stale?
- Is feature styling locally owned rather than added to a global bucket?

## Related

- [architecture.md](../architecture/index.md) — current technical shape and boundaries.
- [quality.md](../workflow/quality.md) — the quality gates this contract is part of.
- [roadmap.md](../planning/roadmap.md) — current state and next direction.
- [engineering-editor-reuse-architecture.md](../research/engineering-editor-reuse-architecture.md)
  — the reuse-first evidence behind the selected stack.
