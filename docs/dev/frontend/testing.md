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

For example the current page chain:

```text
projection → page → selection → Inspector
```

Prove the chain works with real modules, without a browser. The current
`ProcessPfdPage.test.ts` replaces only the two unavoidable boundaries — the
network (`fetch`) and a canvas integration double — while the transport, the
contract narrowing, the feature state, selection, the Inspector and the
validation/error behaviour stay real.

### Browser E2E

Only critical real workflows against the actual local DeepPlant boundary. Keep
this layer deliberately tiny.

## Ownership of each layer

- **#80** documented the pyramid.
- **#81** added the component and feature-integration layers, including the Vue
  Test Utils / DOM-environment setup they require.
- **#82** owns browser end-to-end tests (Playwright). No E2E tooling is added
  here.

## Test root and layout (implemented)

Production application code lives under `apps/editor/src/`. Automated frontend
tests live under `apps/editor/tests/`; test fixtures are test-owned and must not
live in, or be imported by, production source code. Vitest discovers tests only
under that single canonical root (`include: ['tests/**/*.test.ts']` in
`apps/editor/vite.config.ts`), and `vue-tsc` type checks it together with `src/`
(one frontend tsconfig includes `tests/**/*.ts`).

The directory structure makes the test pyramid visible: the test **layer** comes
first, then the feature, then the responsibility being verified — mirroring the
production responsibility the suite covers:

```text
apps/editor/
├── src/                         production application architecture
│   └── process-pfd/             feature
│       ├── pages/ components/ composables/
│       └── transport/ view-models/ adapters/
└── tests/                       verification architecture
    ├── unit/                    pure tests (Node environment, DOM-free)
    │   └── process-pfd/
    │       ├── transport/
    │       ├── view-models/
    │       └── adapters/
    ├── component/               Vue component tests (happy-dom)
    │   └── process-pfd/
    │       └── components/
    ├── integration/             feature-level integration tests (happy-dom)
    │   └── process-pfd/
    │       └── pages/
    └── fixtures/                test-owned fixture data (never imported by src/)
```

Do not flatten feature tests into generic buckets. Feature ownership stays
visible below each layer, and the responsibility directory mirrors the
production module the suite verifies (`unit/process-pfd/transport/`,
`component/process-pfd/components/`, `integration/process-pfd/pages/`).

## Current state (implemented)

Seven Vitest suites, all offline and independent of a running DeepPlant server.

Pure unit — `tests/unit/process-pfd/{transport,view-models,adapters}/`
(**Node** environment, the default in `apps/editor/vite.config.ts`):

| Suite | Covers |
|---|---|
| `transport/api.test.ts` | projection transport, boundary failures, symbol asset URL |
| `transport/projection-contract.test.ts` | transport payload narrowing and contract errors |
| `view-models/inspector.test.ts` | selection → Inspector mapping |
| `adapters/vue-flow.test.ts` | DTO → Vue Flow adapter, identity separation, identity narrowing |

Vue component — `tests/component/process-pfd/components/` — and feature
integration — `tests/integration/process-pfd/pages/` (**DOM** environment):

| Suite | Covers |
|---|---|
| `components/InspectorPanel.test.ts` | empty state, ProcessStep/ProcessStream semantic fields, Inspector landmark |
| `components/ProcessNode.test.ts` | canonical symbol URL from `symbol_role`, semantic id/name, selected state, anchor-derived non-connectable handles |
| `pages/ProcessPfdPage.test.ts` | loading, load success, step selection → Inspector, stream selection → Inspector, validation vs projection-error |

The shared fixtures live in `tests/fixtures/process-pfd.ts` and are imported only
by test suites.

There is no browser layer yet; it is #82 work. #82 decides its own
ownership/layout (`apps/editor/tests/e2e/` or `apps/editor/e2e/`) from the real
server/browser lifecycle requirements; no `tests/e2e/` directory is reserved
here.

## Environment convention

The Vitest default environment stays `node`, so the pure suites under
`tests/unit/` keep running without a DOM. Component and feature-integration
suites opt in per file with a docblock on the first line:

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
