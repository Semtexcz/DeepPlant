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
- Type checking runs through `make typecheck`.
- Tests run through `make test`.
- Frontend lint runs through `make frontend-lint`: ESLint (flat config in
  `apps/editor/eslint.config.js`) over the editor source (`src/**`), the automated
  tests and their fixtures (`tests/**`), and the frontend configuration. It
  enforces Vue/TypeScript correctness, the explicit-`any` ban, and the hard
  size/cohesion limits from [frontend/architecture.md](../frontend/architecture.md).
- Frontend checks run through `make frontend-check`: dependency install from the
  committed lockfile, `frontend-lint`, `vue-tsc` type checking, Vitest (pure unit
  plus Vue component and feature-integration suites), and a production build.
  These are four independent gates; no gate replaces another, and hard size-limit
  violations fail `frontend-lint`.
- `make check` is the fast local/pre-review gate for DeepPlant. It includes
  `frontend-check`, so Node 22 and `pnpm` (pinned by `apps/editor/package.json`)
  are prerequisites of `make check`.
- The template repository has a separate full release-candidate gate across
  every generated profile and workflow.

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
- `make check` is the local gate before every commit and pull request.
- The editor slice is tested at its architecture boundaries rather than by
  screenshots: the projection and the local boundary have Python tests, and the
  frontend has pure unit tests for the runtime DTO contract, the transport, the
  DeepPlant DTO → Vue Flow adapter, and the selection → Inspector mapping, plus
  Vue component tests and a Process/PFD feature-integration test for the
  projection → selection → Inspector chain. Frontend runtime data is narrowed to
  the explicit DTO contract so a contract mismatch fails clearly. Browser E2E is
  deferred to #82.
- Frontend work follows the canonical contract in
  [frontend/index.md](../frontend/index.md): feature ownership, the DeepPlant/Vue
  Flow boundary, Vue and composable conventions, state ownership, TypeScript
  safety, styling ownership, accessibility, the testing pyramid, and the
  size/cohesion guardrails. Lint, type checking, tests, and the production build
  are separate gates.

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
