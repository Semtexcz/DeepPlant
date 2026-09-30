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
- `make check` is the fast local/pre-review gate for DeepPlant.
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
