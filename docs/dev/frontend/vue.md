---
type: governance
status: active
canonical_for:
  - vue-component-conventions
  - frontend-state-ownership
  - frontend-effects-and-watchers
read_when:
  - frontend-change
  - vue-component-change
  - editor-frontend-work
update_when:
  - vue-convention-change
depends_on:
  - docs/dev/frontend/index.md
  - docs/dev/frontend/architecture.md
decision:
  - docs/dev/decisions/ADR-0003-separate-semantic-and-presentation-models.md
evidence: []
superseded_by: null
---

# Vue Conventions

> **Question this document answers:** how should Vue components and composables be
> written, and who owns frontend state?

## Default style

- Vue 3 Composition API with `<script setup lang="ts">`.
- Typed props and typed emits. Do not widen a prop to `any` to silence a
  mismatch.
- `computed` for derived state instead of imperative recomputation.
- Explicit loading, error, and empty states for any asynchronous surface.
- Minimal duplicated reactive state; minimal side effects.
- One cohesive responsibility per component.

The existing `process-pfd/` components follow this baseline already.

## Components

Components render; they should not become arbitrary application controllers.
At the same time, do not move all logic out of a component mechanically — a
small, local computation belongs in the component that displays it.

Extract behavior into a module or composable when it is independently
meaningful, for example:

- reusable behavior;
- external I/O (the transport boundary);
- a cohesive stateful workflow;
- independently testable application behavior;
- sufficiently complex reactive coordination.

`src/App.vue` currently owns the workspace composition and transient selection
because that is where the current slice is small. Extracting it is a real,
justified refactor owned by #81 — not by this contract. Do not extract it here.

## Composables

Avoid vague composables such as `useUtils()`, `useHelpers()`, or `useCommon()`.
Prefer domain- or feature-named composables such as `useProcessPfd()` or
`useProcessSelection()`, and only when the behavior is genuinely cohesive and
reused or independently testable.

This contract deliberately creates no composables. `src/process-pfd/` contains
none today; adding them is #81 work justified by real extraction, not by this
document.

## State ownership

Own each mutable state concept exactly once, at the lowest sufficient level:

```text
component-local state
        ↓
feature-level state / composable
        ↓
shared application state
        ↓
global store only when evidence requires it
```

- Do not introduce Pinia, or any global store, in this contract. It requires a
  concrete, current use case with recorded reasoning.
- Avoid `API → global store → copied local refs → synchronization watchers`.
  Every layer in that chain must be justified by evidence, not by convention.

## Effects and watchers

Preferred order:

```text
computed
explicit actions
lifecycle hooks
watch / watchEffect only for actual reactive side effects
```

- Use `computed` for anything that is a pure function of state.
- Use explicit functions/actions for user-driven change.
- Use lifecycle hooks (`onMounted`, `onUnmounted`) for setup and cleanup.
- Use `watch`/`watchEffect` only for a genuine reactive side effect such as a
  subscription, imperative API call, or DOM interaction.
- A watcher used only to synchronize duplicated state is a design smell: fix the
  duplication and keep one owner instead.

Watchers are not banned. `src/App.vue` uses a lifecycle hook (`onMounted`) and a
one-shot `nextTick` + `fitView` after load, which is an imperative framework
interaction — a legitimate use. A watcher added purely to mirror state is not.
