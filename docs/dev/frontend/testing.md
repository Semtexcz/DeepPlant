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
this layer deliberately tiny: it starts a real Python process and a real browser,
so it is the slowest and most expensive layer. It exists to prove that the whole
local product path works together, not to re-assert behaviour the unit,
component, and integration layers already cover.

The specs always drive the developer/browser host: `uv run deepplant ui <path>
--port 0` over the production build. `DEEPLANT_EDITOR_PROJECT` may point them at a
model outside the checkout. They no longer target the packaged product, because
since Issue #93 that product is a native desktop window rather than a browser
target; the packaged product is verified by
[workflow/packaging.md](../workflow/packaging.md). Feature specs stay
packaging-agnostic.

### Desktop host layer (Issue #93)

The standalone product adds two layers that this browser suite does not cover:

- **Host behaviour, without a GUI toolkit** - `tests/test_editor_desktop.py`
  (command-line wiring, the optional-path/self-check hand-off, the initial-model
  load, the embedded-navigation policy) and `tests/test_editor_server.py` (the
  owned `EditorServer` lifecycle: loopback-only bind, real HTTP, and socket
  release on stop).
- **The packaged graphical product** - `tools/package_editor.py verify` launches
  the real frozen application with no model argument and with the realistic
  fragment, reads the real rendered page through Qt's own JavaScript engine, and
  checks the window/server/socket lifecycle. On Linux the CI job additionally
  discovers the real X11 window with `xdotool` on a virtual display.

The layers are deliberately not duplicated: browser behaviour belongs to this
Playwright suite, and the native window belongs to the packaging verification.

## Ownership of each layer

- **#80** documented the pyramid.
- **#81** added the component and feature-integration layers, including the Vue
  Test Utils / DOM-environment setup they require.
- **#82** added the browser end-to-end layer (Playwright + Chromium); see
  [Browser E2E](#browser-e2e-implemented-issue-82) below.

## Test root and layout (implemented)

Production application code lives under `apps/editor/src/`. Automated frontend
tests live under `apps/editor/tests/`; test fixtures are test-owned and must not
live in, or be imported by, production source code. Vitest discovers tests only
under that single canonical root (`include: ['tests/**/*.test.ts']` in
`apps/editor/vite.config.ts`), and the browser `vue-tsc` config
(`apps/editor/tsconfig.json`) type checks them together with `src/`. The
Playwright E2E tree under `apps/editor/e2e/` is type checked separately by the
Node/tooling config (`apps/editor/tsconfig.node.json`); see
[typescript.md](typescript.md#runtime-type-environments-implemented).

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

Browser E2E is a separate root, not a layer inside `tests/`:

```text
apps/editor/
├── tests/                       isolated frontend verification (Vitest)
│   ├── unit/ component/ integration/
│   └── fixtures/
├── e2e/                         whole local product verification (Playwright)
│   ├── process-pfd.spec.ts
│   └── support/editor-server.ts
└── playwright.config.ts
```

`tests/` verifies the frontend in isolation and never starts a DeepPlant server.
`e2e/` verifies the local product and always does: a real Python process, real
HTTP, the real production build, and a real browser.

Do not flatten feature tests into generic buckets. Feature ownership stays
visible below each layer, and the responsibility directory mirrors the
production module the suite verifies (`unit/process-pfd/transport/`,
`component/process-pfd/components/`, `integration/process-pfd/pages/`).

## Current state (implemented)

Seven Vitest suites (49 tests), all offline and independent of a running
DeepPlant server, plus two Playwright browser E2E tests that run the real local
product.

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

## Browser E2E (implemented, Issue #82)

Two Playwright + Chromium tests in `apps/editor/e2e/` are the only system/browser
tests. They prove the critical Engineering Editor workflow across the whole local
product path:

```text
production SPA build (`apps/editor/dist`)
        ↓
real `deepplant ui --port 0` CLI  (loopback FastAPI/Uvicorn)
        ↓
real Chromium browser  →  Vue  →  Vue Flow  →  real pointer interaction
```

Nothing is mocked: no Vite dev/preview server, no `page.route()`/`fetch` stub, no
injected DTO, no direct `create_editor_api()` call, and no Vue component mount.
Removing exactly those test doubles from the critical path is the point of this
layer; the lower layers keep them.

### Why `e2e/` is not inside `tests/`

`tests/` and `e2e/` have different lifecycle responsibilities, so they stay
separate trees and are discovered by different runners:

| | `tests/` (Vitest) | `e2e/` (Playwright) |
|---|---|---|
| Scope | isolated frontend verification | whole local product verification |
| Server | none | real Python/Uvicorn process + real HTTP |
| Build | source modules | the production build |
| Browser | `happy-dom` or none | real Chromium |
| Cost | milliseconds | seconds, with process and browser artifacts |

Vitest therefore keeps discovering only `include: ['tests/**/*.test.ts']` in
`apps/editor/vite.config.ts`; Playwright discovers only `apps/editor/e2e/`
through `testDir: './e2e'` in `apps/editor/playwright.config.ts`. Do not mix the
two, and do not re-assert a component or integration behaviour in the browser
layer.

### Server lifecycle

The suite starts the real user-facing CLI, not a test-only application:

```bash
uv run deepplant ui \
  examples/realistic-process-fragment/plant.yaml \
  --symbol-role PS-vessel=vessel \
  --port 0
```

- `e2e/support/editor-server.ts` spawns that command with the repository root as
  the Python process `cwd`, because `uv run` discovers the project from there.
  Asset resolution no longer depends on the working directory (Issue #85): the
  editor application resolves the packaged SPA resource first and the
  source-checkout build from its own module location.
- `--port 0` lets the OS pick a free port, so the suite never depends on port
  `8765` being unused and never collides in CI. Port allocation stays owned by
  the CLI; the helper only parses the URL the CLI prints.
- Readiness is the CLI's own announcement
  (`open:    http://127.0.0.1:<port>/`), followed by a short bounded poll that
  confirms Uvicorn is accepting connections. There is no arbitrary readiness
  sleep and no duplicated port logic in TypeScript.
- The helper fails clearly when the process exits before startup, when no URL
  appears within a bounded timeout, or when startup reports a setup error — and
  it includes the captured CLI log in the thrown error.
- Cleanup terminates only the process group the test started: `SIGTERM` first,
  then `SIGKILL` only after a bounded grace period, using a detached process
  group so the whole `uv` → python → uvicorn tree is stopped on Linux. A
  last-resort `process.on('exit')` handler force-kills any group still alive.
  There is never a broad `pkill python`/`pkill uvicorn`.

### Production path

The suite runs the built application, never a dev server:

```text
pnpm build  →  apps/editor/dist  →  deepplant ui  →  FastAPI/Uvicorn  →  Chromium
```

The happy-path test additionally asserts that the served document does not
reference `/src/main.ts`, so an accidental dev-server path fails loudly instead
of silently passing.

### Fixture

The happy path uses exactly `examples/realistic-process-fragment/plant.yaml` with
the required presentation override `--symbol-role PS-vessel=vessel`; no E2E-only
simplified model is introduced. The error path starts the same project and the
same YAML *without* that override, which is the stable valid-but-unprojectable
case (`semantic validity != Process/PFD projectability`).

### Selector policy

Preferred order, matching the [frontend contract](index.md):

1. role + accessible name;
2. visible semantic text;
3. DeepPlant-owned stable accessibility metadata;
4. a minimal explicit test selector.

The canvas test hooks are production accessibility metadata supplied by the
adapter (`process-pfd/adapters/vue-flow.ts`), not test-only attributes: Vue Flow
renders focusable nodes and edges as `group`s, so each carries a DeepPlant-owned
`ariaLabel` of the form `Process step <id>` / `Process stream <id>`. That is the
semantic identity, never the framework id, and it also fixes the previous default
edge name, which leaked `vue-flow-node:…` ids. The E2E suite therefore selects
`getByRole('group', { name: … })` and never generated CSS classes, Vue scope
attributes, `nth-child`, coordinates, or DOM position.

One documented framework coupling remains: selecting a `ProcessStream` uses
`click({ force: true })`. A perfectly straight SVG edge path has an in-page
`getBoundingClientRect()` height of `0`, so Playwright's `visible` heuristic
(`width > 0 && height > 0`) rejects a stroke that is genuinely hit-testable. The
click is still a real browser click dispatched by Playwright at the framework
element's own centre, and the following Inspector assertion proves the click
reached the edge.

### Local setup and commands

Install Chromium once per environment (browser binaries are an environment setup
step, not part of the normal gate):

```bash
cd apps/editor
pnpm exec playwright install chromium
```

Then run the suite from the repository root:

```bash
make frontend-e2e
```

`make frontend-e2e` installs frontend dependencies from the committed lockfile,
builds the production SPA, and runs the Playwright suite. It does not install
browser binaries on every run, and neither `make frontend-check` nor `make check`
downloads a browser or runs the production build:

```text
make frontend-check → lint/type/unit/component/integration baseline (fast)
make frontend-build → production SPA bundle (separate, higher-cost verification)
make frontend-e2e   → production build + real-browser system tests (slow)
```

All run in CI. Running the suite directly is equivalent to
`cd apps/editor && pnpm e2e` after a build.

### Debugging and failure artifacts

- The Playwright config keeps `trace: 'retain-on-failure'` and
  `screenshot: 'only-on-failure'` and never records video, so a failing run keeps
  a trace and a screenshot in `test-results/`; the HTML report in
  `playwright-report/` is written each run. Both directories are git-ignored.
- The captured `deepplant ui` stdout/stderr is attached to a failing test as
  `deepplant-ui-server-log` once the server has started. A startup failure (the
  helper throws before returning an `EditorServer`) includes the same bounded log
  directly in the thrown error instead, because there is no server object to
  attach from. A successful run does not print the server log.
- The happy path fails on any unexpected `pageerror` or `console.error`, and is
  currently clean on both. The error path allows exactly one documented message:
  the resource-load `console.error` the browser emits for the deliberate HTTP 422
  from `/api/projection`. Narrow that allowlist rather than broadening it.

### No external-network dependency

The suite binds loopback only. Local loopback application traffic is not an
external network dependency, and the browser suite requires no external service.


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
- The production SPA build runs through `make frontend-build` and is deliberately
  outside `frontend-check`/`make check`: it is a production-artifact
  verification, not part of the fast default gate.
- Browser E2E runs through `make frontend-e2e` (or `pnpm e2e` after a build) and
  is deliberately outside `make check`, so the fast default gate never downloads
  a browser.
- A DTO/contract mismatch must have negative coverage (it fails clearly).
- Pure unit, Vue component, and feature-integration tests run without external
  network access and do not depend on a running DeepPlant server.
- Browser E2E tests start and use the real local loopback DeepPlant application
  boundary over the production build, but must not depend on external network
  services and should remain deterministic and self-contained. Local loopback
  application traffic is not an external network dependency.
