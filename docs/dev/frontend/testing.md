---
type: governance
status: active
canonical_for:
  - frontend-testing-strategy
read_when:
  - frontend-change
  - frontend-test-change
  - editor-frontend-work
update_when:
  - frontend-test-strategy-change
depends_on:
  - docs/dev/frontend/index.md
  - docs/dev/workflow/quality.md
decision: []
evidence: []
superseded_by: null
---

# Frontend Testing

> **Question this document answers:** what layers exist in the frontend test
> pyramid, what does each own, and who implements each layer?

## Pyramid

```text
pure unit
    ↓
Vue component
    ↓
feature integration
    ↓
browser E2E
```

Keep each layer small and purposeful. Do not test framework internals, and avoid
large snapshot suites: they are brittle and rarely express intent.

## Responsibilities

### Pure unit

For example: runtime DTO narrowing, adapters, view-model transformations, and
pure state transformations. No DOM, no Vue runtime.

### Vue component

For example: props/emits, visible state, local interaction, and accessibility
behavior of a single component.

### Feature integration

For example the current workspace chain:

```text
projection → workspace → selection → Inspector
```

Prove the chain works with real modules, without a browser.

### Browser E2E

Only critical real workflows against the actual local DeepPlant boundary. Keep
this layer deliberately tiny.

## Ownership of each layer

- **#80** documented the pyramid.
- **#81** added the component and feature-integration layers, including the Vue
  Test Utils / DOM-environment setup they require.
- **#82** owns browser end-to-end tests (Playwright). No E2E tooling is added
  here.

## Current state (implemented)

Seven Vitest suites, all offline and independent of a running DeepPlant server.

Pure unit (**Node** environment — the default in `apps/editor/vite.config.ts`):

| Suite | Covers |
|---|---|
| `process-pfd/projection-contract.test.ts` | transport payload narrowing and contract errors |
| `process-pfd/api.test.ts` | projection transport, boundary failures, symbol asset URL |
| `process-pfd/inspector-model.test.ts` | selection → Inspector mapping |
| `process-pfd/vue-flow-adapter.test.ts` | DTO → Vue Flow adapter, identity separation, identity narrowing |

Vue component and feature integration (**DOM** environment):

| Suite | Covers |
|---|---|
| `process-pfd/InspectorPanel.test.ts` | empty state, ProcessStep/ProcessStream semantic fields, Inspector landmark |
| `process-pfd/ProcessNode.test.ts` | canonical symbol URL from `symbol_role`, semantic id/name, selected state, anchor-derived non-connectable handles |
| `process-pfd/ProcessPfdWorkspace.test.ts` | loading, load success, step selection → Inspector, stream selection → Inspector, validation vs projection-error |

There is no browser layer yet; it is #82 work.

## Environment convention

The Vitest default environment stays `node`, so the pure suites keep running
without a DOM. Component and feature-integration suites opt in per file with a
docblock on the first line:

```ts
// @vitest-environment happy-dom
```

`happy-dom` is the single DOM environment dependency. Do not add a second one,
and do not move the global default to a DOM environment merely because a
component test exists.

## Expectations

- Frontend tests run through `make frontend-test` and are part of
  `make frontend-check` and `make check`.
- A DTO/contract mismatch must have negative coverage (it fails clearly).
- Pure unit, Vue component, and feature-integration tests run without external
  network access and do not depend on a running DeepPlant server.
- Browser E2E tests may start and use the real local loopback DeepPlant application
  boundary, but must not depend on external network services and should remain
  deterministic and self-contained. Local loopback application traffic is not an
  external network dependency.
