---
type: governance
status: active
canonical_for:
  - quality-gates
read_when:
  - prepare-task
  - implement-change
  - review-change
update_when:
  - test-strategy-change
  - runtime-level-change
depends_on: []
decision: []
evidence: []
superseded_by: null
---

# Quality

## Baseline

- Formatting and linting run through `make lint`.
- Type checking runs through `make typecheck`. It deliberately excludes
  `src/deepplant/editor/desktop_qt.py`, because the fast environment does not
  install PySide6. The Qt module is still strictly type-checked: the native
  packaging jobs run `make typecheck-desktop`
  (`pyright --project pyrightconfig.desktop.json`), which mirrors the canonical
  strict settings with PySide6 available and keeps every module in scope. There is
  no blanket `type: ignore` for the Qt module.
- Tests run through `make test`.
- Frontend lint runs through `make frontend-lint`: ESLint (flat config in
  `apps/editor/eslint.config.js`) over the editor source (`src/**`), the automated
  tests and their fixtures (`tests/**`), and the frontend configuration. It
  enforces Vue/TypeScript correctness, the explicit-`any` ban, and the hard
  size/cohesion limits from [frontend/architecture.md](../frontend/architecture.md).
- Default frontend checks run through `make frontend-check`: dependency install
  from the committed lockfile, `frontend-lint`, `frontend-typecheck` (browser
  `vue-tsc` over `tsconfig.json` plus Node/tooling `tsc` over
  `tsconfig.node.json`), and Vitest (pure unit plus Vue component and
  feature-integration suites). These are independent gates; no gate replaces
  another, and hard size-limit violations fail `frontend-lint`. The two
  TypeScript runtime environments are canonical in
  [frontend/typescript.md](../frontend/typescript.md).
- The production SPA build runs through `make frontend-build` (`vite build`). It
  is deliberately **not** part of `frontend-check`/`check`: it is a separate
  production-build/artifact verification and is intentionally outside the fast
  default local confidence gate. Beyond the TypeScript contract that
  `frontend-typecheck` already proves, a production build can also catch build
  configuration, module resolution, asset, plugin, or bundling failures. It is
  exercised by `make frontend-e2e` and by the packaging jobs.
- Browser system E2E runs through `make frontend-e2e`: it installs frontend
  dependencies from the committed lockfile, builds the production SPA, and runs
  the Playwright + Chromium suite against the real local `deepplant ui` CLI. It is
  deliberately **not** part of `frontend-check`/`check`, so the fast default gate
  never downloads a browser. Install Chromium once per environment with
  `cd apps/editor && pnpm exec playwright install chromium`. Ownership, lifecycle,
  selector policy, and debugging are canonical in
  [frontend/testing.md](../frontend/testing.md).
- `make check` is the single canonical local confidence gate, run once before
  finalizing a pull request (not after every edit). It is a
  developer-confidence gate, not a release/distribution gate: the production SPA
  build, browser E2E, packaging, the desktop type check, and the wheel build stay
  outside it. It includes `frontend-check`, so Node 22 and `pnpm` (pinned by
  `apps/editor/package.json`) are prerequisites of `make check`.
- Standalone Editor packaging runs through `uv run --group package --group desktop
  python tools/package_editor.py` (or `make package-editor`): production SPA
  build, freeze (PyInstaller + Qt WebEngine), platform package, and a packaged
  **desktop** verification that launches the real native window. It is
  deliberately **not** part of `check`, because it is slow and platform-specific.
  It runs in CI as the native `editor-package-windows` and `editor-package-linux`
  jobs, which install and integrity-check the pinned external toolchain
  (`packaging/toolchain.toml`) before building; the Linux job also runs the
  graphical verification on a virtual display. The Qt/desktop group is never part
  of `make setup`/`check`, so the fast gate stays free of Qt and the Core, CLI,
  and browser host stay provably independent of it. Ownership and debugging are
  canonical in [workflow/packaging.md](packaging.md).
- Base-installation independence verification runs through
  `python tools/verify_base_install.py <wheel>` in the `check` job: it installs
  the base wheel into clean environments and proves the semantic Core works
  without the editor transport while the editor extra still provides it.
- The template repository has a separate full release-candidate gate across
  every generated profile and workflow.

## Validation boundaries

Ordinary implementation runs only the checks relevant to the changed surface. Do
not run exhaustive validation after every edit; the broader gate is deliberately
run once per finalization/review cycle.

| Changed surface | Focused check |
|---|---|
| documentation | `make validate-docs` |
| agent skills / context map | `make validate-agent-skills` |
| Python / Core | `make format-check`, `make lint`, `make typecheck`, then a targeted `uv run pytest <relevant test paths>` selection |
| frontend | `make frontend-lint`, `make frontend-typecheck`, `make frontend-test` |
| desktop host (PySide6) | `make typecheck-desktop` when relevant |
| packaging / distribution | `make package-editor` / `make verify-packaged-editor` when relevant |

Focused iteration selects only the tests a change can affect, for example
`uv run pytest tests/test_cli.py` or a `-k` selection. `make test` always runs the
complete Python suite, so it belongs to the broader gate rather than to per-edit
iteration:

```text
focused iteration        -> targeted `uv run pytest <relevant test paths>`
broader local confidence -> `make check` -> includes the full `make test` suite
```

Then exactly one broader local confidence gate runs before the pull request is
finalized:

```bash
make check
```

After the PR is pushed the implementation session ends: do not wait for or poll
GitHub Actions.

> CI is authoritative where required but runs asynchronously. If CI later fails,
> repair it in a fresh focused session on the same branch and pull request.

There is one normal broader local gate per finalization/review cycle. Do not
follow focused checks with `make check`, another equivalent full local check, a
push, and then CI polling.

## Test Expectations

- Domain rules are unit-tested independently of the CLI and any transport.
- Every fail-closed rule has negative coverage: unknown fields, blank semantic
  strings, duplicate ids, unresolvable references, unsupported external content.
- Deterministic outputs (canonical YAML, rendered SVG, exported DEXPI XML) are
  pinned by determinism or golden tests.
- External systems appear only as repository fixtures; the suite runs offline
  with no network access at test time.
- Infrastructure that does not exist yet (databases, migrations, authorization
  boundaries, front-end runtimes, external services) gains test expectations
  only when it exists.

## DeepPlant Expectations

- Domain rules must be unit-tested independently of the CLI and any transport.
- Validation behavior is exercised through the public Python API and the CLI
  entry point once the domain model exists.
- `make check` is the single canonical local confidence gate, run once before
  finalizing a pull request; it is not repeated per commit, and the GitHub Actions
  CI that runs afterwards is asynchronous.
- The editor slice is tested at its architecture boundaries rather than by
  screenshots: the projection and the local boundary have Python tests, and the
  frontend has pure unit tests for the runtime DTO contract, the transport, the
  DeepPlant DTO → Vue Flow adapter, and the selection → Inspector mapping, plus
  Vue component tests and a Process/PFD feature-integration test for the
  projection → selection → Inspector chain. Frontend runtime data is narrowed to
  the explicit DTO contract so a contract mismatch fails clearly. A small
  Playwright + Chromium browser E2E layer proves the critical workflow across the
  real local product path (production build + real `deepplant ui` CLI + real
  browser); it is a separate gate (`make frontend-e2e`) and its ownership is
  canonical in [frontend/testing.md](../frontend/testing.md).
- Frontend work follows the canonical contract in
  [frontend/index.md](../frontend/index.md): feature ownership, the DeepPlant/Vue
  Flow boundary, Vue and composable conventions, state ownership, TypeScript
  safety, styling ownership, accessibility, the testing pyramid, and the
  size/cohesion guardrails. Lint, type checking, and tests are the default
  frontend gates; the production build is a separate, higher-cost verification.

## Security Baseline

- No committed secrets.
- No destructive data action without explicit human approval.
- Dependencies are updated intentionally.
- Sensitive data handling requires explicit requirements.

## Observability

Critical operations should be diagnosable. Production projects require logs, readiness checks, rollback, incident workflow, and tested restore for stateful systems.

## Production Runtime Checks

DeepPlant is a `script` project at runtime level `shared`: there is no container
image, no production service, and no deployment surface. The template's
full-stack production gates (image build/inspect, compose up/status/smoke,
production E2E) therefore do not apply and are intentionally absent from the
Makefile. If DeepPlant ever gains a deployment surface, this section must be
replaced with the applicable gates before that work merges.
