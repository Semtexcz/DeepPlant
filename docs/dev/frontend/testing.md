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

- **This contract (#80)** documents the pyramid. It does not add component or
  integration coverage.
- **#81** owns component tests and feature-integration tests, including the
  Vue Test Utils / DOM-environment setup they require (Vitest currently runs in a
  `node` environment, so component tests need that setup added there).
- **#82** owns browser end-to-end tests (Playwright). No E2E tooling is added
  here.

## Current state (implemented)

Three Vitest suites, all **pure unit**:

| Suite | Covers |
|---|---|
| `process-pfd/api.test.ts` | transport payload narrowing and contract errors |
| `process-pfd/inspector-model.test.ts` | selection → Inspector mapping |
| `process-pfd/vue-flow-adapter.test.ts` | DTO → Vue Flow adapter and identity separation |

There is no component, integration, or browser layer yet. That is expected; it is
#81/#82 work, not a gap in this contract.

## Expectations

- Frontend tests run through `make frontend-test` and are part of
  `make frontend-check` and `make check`.
- A DTO/contract mismatch must have negative coverage (it fails clearly).
- Tests must run offline, with no network access and no dependency on a running
  DeepPlant boundary.
