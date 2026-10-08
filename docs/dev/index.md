---
type: navigation
status: active
canonical_for:
  - developer-documentation-navigation
read_when:
  - start-work
  - implement-change
  - architecture-change
  - review-change
update_when:
  - developer-documentation-change
depends_on:
  - docs/index.md
  - docs/dev/workflow/conventions.md
decision:
  - docs/dev/decisions/ADR-0015-documentation-architecture-v2-1.md
  - docs/dev/decisions/ADR-0014-documentation-architecture-v2.md
evidence: []
superseded_by: null
---

# Developer and Agent Documentation

For contributors, maintainers, and agents **changing** DeepPlant. This is a
navigation map, not a content dump. The structure is decided in
[ADR-0015](decisions/ADR-0015-documentation-architecture-v2-1.md)
(Documentation Architecture v2.1), refining
[ADR-0014](decisions/ADR-0014-documentation-architecture-v2.md).

This audience layer is the **physical owner** of developer/agent material:
architecture, workflow/governance, planning, developer-only contracts/reference,
decisions, research/evidence, and history are canonical *and* developer-owned.
The developer-only reference layer moved here first
([reference/](reference/svg-symbols.md)); the architecture and
workflow/governance documents followed in Phase 3A
([architecture/](architecture/index.md), [workflow/](workflow/index.md));
planning followed in Phase 3B ([planning/](planning/index.md)); and decisions,
research/evidence, and history followed in Phase 3C
([decisions/](decisions/index.md), [research/](research/index.md),
[history/](history/implementation-slices.md)). Phase 5 relocated the last root
evidence/prototype documents, and Phase 6 split the standards document into
policy ([workflow/standards.md](workflow/standards.md)), registry
([reference/standards-registry.md](reference/standards-registry.md)), and
evidence
([research/standards-licensing-evidence.md](research/standards-licensing-evidence.md)).
The current → target mapping is in
[documentation-migration.md](workflow/documentation-migration.md).

## Start here

- **Current** — [architecture.md](architecture/index.md): boundary map, module
  boundaries, durable invariants.
- **Governance** — [workflow.md](workflow/index.md): the change loop.
- **Governance** — [quality.md](workflow/quality.md): checks and test expectations.
- **Governance** — [python/index.md](python/index.md): the canonical Python
  engineering contract (architecture, conventions, typing, errors, scientific
  computation, testing, and the size/import-boundary guardrails enforced by
  `make architecture-check`).
- **Governance** — [frontend/index.md](frontend/index.md): the Engineering Editor
  frontend engineering contract (architecture, feature ownership, Vue, TypeScript,
  styling, testing, accessibility, size guardrails).
- **Current** — [roadmap.md](planning/roadmap.md): product milestones and the
  active outcome.
- **Governance** — [strategy.md](planning/strategy.md): product strategy, target
  user, and differentiation.
- **Governance** — [conventions.md](workflow/conventions.md): documentation rules.
- **Governance** — [standards.md](workflow/standards.md): standards usage and
  symbol-provenance policy.

## Smallest relevant context for a task

The `always` set in [.agents/context-map.yaml](../../.agents/context-map.yaml) is
only the universal bootstrap ([AGENTS.md](../../AGENTS.md)); everything else is
selected from the task, the changed files, and the selected skill. Pick the row
that matches the work, then add the matching task and changed-file context from
that map rather than reading the whole repository. This is a lightweight routing
table, not an orchestration engine.

| Task / change | Read |
|---|---|
| Orient in the repository | [architecture.md](architecture/index.md), [roadmap.md](planning/roadmap.md) |
| Plan or pick the next slice | [planning/roadmap.md](planning/roadmap.md), [planning/index.md](planning/index.md) |
| Understand the product strategy or triage an idea | [planning/strategy.md](planning/strategy.md), [planning/product.md](planning/product.md), [planning/index.md](planning/index.md) |
| Change Python source or tests | [python/index.md](python/index.md), then the matching topic document in [python/](python/index.md); run `make architecture-check` for the size and import-boundary guardrails |
| Change the plant / process / piping model | [contracts/index.md](../contracts/index.md), then the specific contract |
| Change the CLI | [contracts/cli.md](../contracts/cli.md), [contracts/yaml-format.md](../contracts/yaml-format.md) |
| Change the editor frontend or the local application boundary | [frontend/index.md](frontend/index.md), [architecture.md](architecture/index.md), [contracts/rendering.md](../contracts/rendering.md), [workflow/quality.md](workflow/quality.md) |
| Change editor Vue components, composables, TypeScript, styling, tests, or accessibility | [frontend/index.md](frontend/index.md), then the matching topic document in [frontend/](frontend/index.md) |
| Design a frontend change in Figma and implement it with a coding agent | [frontend/design-to-code.md](frontend/design-to-code.md), [frontend/index.md](frontend/index.md) |
| Package, distribute, or release the standalone Editor | [workflow/packaging.md](workflow/packaging.md), [research/editor-desktop-host.md](research/editor-desktop-host.md), [research/standalone-editor-distribution.md](research/standalone-editor-distribution.md) |
| Change YAML load/save | [contracts/yaml-format.md](../contracts/yaml-format.md) |
| Change the renderer | [contracts/rendering.md](../contracts/rendering.md) — the shared headless process-renderer contract |
| Change symbols or the symbol pack | [reference/svg-symbols.md](reference/svg-symbols.md) — the developer-only SVG + anchor contract |
| Add or change a standard PFD/P&ID symbol | [reference/symbol-library.md](reference/symbol-library.md) — the machine-rendered symbol library contract; then [reference/mvp-symbol-coverage.md](reference/mvp-symbol-coverage.md) — coverage matrix and per-concept status; the implemented geometry is authored from [reference/symbol-seed-geometry.md](reference/symbol-seed-geometry.md) |
| Change the DEXPI adapter | [reference/dexpi-process-adapter.md](reference/dexpi-process-adapter.md) — the developer-only DEXPI Process adapter contract |
| Work with standards material or symbol assets | [workflow/standards.md](workflow/standards.md), then [reference/standards-registry.md](reference/standards-registry.md) |
| Investigate a symbol-asset source or licence | [research/standards-licensing-evidence.md](research/standards-licensing-evidence.md) |
| Decide or record an architecture boundary | [decisions/index.md](decisions/index.md), [conventions.md](workflow/conventions.md) |
| Add or change evidence | [research/index.md](research/index.md) |
| Review implementation history | [history/implementation-slices.md](history/implementation-slices.md) |
| Change documentation | [conventions.md](workflow/conventions.md), [documentation-migration.md](workflow/documentation-migration.md) |

Machine-readable agent context selection lives in
[.agents/context-map.yaml](../../.agents/context-map.yaml); [AGENTS.md](../../AGENTS.md)
is the agent bootstrap entry point.

## Authority layers

These are canonical for their authority type. A contract is shared only when
users and developers both need it; decisions, evidence, history, governance, and
developer-only contracts/reference are developer/agent-owned even though they are
authoritative.

- **Cross-audience contract** (shared) — [contracts/index.md](../contracts/index.md):
  what users and developers must both rely on.
- **Developer-only contract** (developer-owned) —
  [reference/svg-symbols.md](reference/svg-symbols.md) and
  [reference/dexpi-process-adapter.md](reference/dexpi-process-adapter.md).
- **Decision** (developer-owned) — [decisions/index.md](decisions/index.md):
  why a boundary exists.
- **Evidence** (developer-owned) — [research/index.md](research/index.md): what
  was investigated.
- **History** (developer-owned) —
  [history/implementation-slices.md](history/implementation-slices.md) and
  [history/gate-decisions.md](history/gate-decisions.md): what
  shipped, in what order.
- **Governance** (developer-owned) — [planning.md](planning/index.md),
  [standards.md](workflow/standards.md), [quality.md](workflow/quality.md),
  [workflow.md](workflow/index.md), [conventions.md](workflow/conventions.md),
  [python/](python/index.md), [frontend/](frontend/index.md).
- **Reference** (developer-owned) —
  [standards-registry.md](reference/standards-registry.md): current standards
  lookup data (not policy).
- **Direction** (developer-owned) — [strategy.md](planning/strategy.md),
  [direction.md](planning/direction.md), [product.md](planning/product.md),
  [roadmap.md](planning/roadmap.md).

## User-facing material

[../user/index.md](../user/index.md) routes the user audience. Use it to see what
users are told. Do not move canonical *developer* facts into the user layer, and
do not treat the shared `contracts/` layer as the only place authoritative content
may live: canonical does not mean shared directory.
