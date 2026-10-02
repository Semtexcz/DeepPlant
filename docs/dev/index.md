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
  - docs/decisions/ADR-0015-documentation-architecture-v2-1.md
  - docs/decisions/ADR-0014-documentation-architecture-v2.md
evidence: []
superseded_by: null
---

# Developer and Agent Documentation

For contributors, maintainers, and agents **changing** DeepPlant. This is a
navigation map, not a content dump. The structure is decided in
[ADR-0015](../decisions/ADR-0015-documentation-architecture-v2-1.md)
(Documentation Architecture v2.1), refining
[ADR-0014](../decisions/ADR-0014-documentation-architecture-v2.md).

This audience layer is the **physical owner** of developer/agent material:
architecture, workflow/governance, planning, developer-only contracts/reference,
decisions, research/evidence, and history are canonical *and* developer-owned.
The developer-only reference layer moved here first
([reference/](reference/svg-symbols.md)); the architecture and
workflow/governance documents followed in Phase 3A
([architecture/](architecture/index.md), [workflow/](workflow/index.md)), and
planning followed in Phase 3B ([planning/](planning/index.md)). Decisions,
research/evidence, and history are still reached from the `docs/` root until
their own slices, and stay canonical after their move. The current → target
mapping is in
[documentation-migration.md](workflow/documentation-migration.md).

## Start here

- **Current** — [architecture.md](architecture/index.md): boundary map, module
  boundaries, durable invariants.
- **Governance** — [workflow.md](workflow/index.md): the change loop.
- **Governance** — [quality.md](workflow/quality.md): checks and test expectations.
- **Current** — [roadmap.md](planning/roadmap.md): current state and next direction.
- **Governance** — [conventions.md](workflow/conventions.md): documentation rules.

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
| Change the plant / process / piping model | [contracts/index.md](../contracts/index.md), then the specific contract |
| Change the CLI | [contracts/cli.md](../contracts/cli.md), [contracts/yaml-format.md](../contracts/yaml-format.md) |
| Change YAML load/save | [contracts/yaml-format.md](../contracts/yaml-format.md) |
| Change the renderer | [contracts/rendering.md](../contracts/rendering.md) — the shared headless process-renderer contract |
| Change symbols or the symbol pack | [reference/svg-symbols.md](reference/svg-symbols.md) — the developer-only SVG + anchor contract |
| Change the DEXPI adapter | [reference/dexpi-process-adapter.md](reference/dexpi-process-adapter.md) — the developer-only DEXPI Process adapter contract |
| Decide or record an architecture boundary | [decisions/index.md](../decisions/index.md), [conventions.md](workflow/conventions.md) |
| Add or change evidence | [research/index.md](../research/index.md) |
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
- **Developer-only contract/reference** (developer-owned) —
  [reference/svg-symbols.md](reference/svg-symbols.md),
  [reference/dexpi-process-adapter.md](reference/dexpi-process-adapter.md).
- **Decision** (developer-owned) — [decisions/index.md](../decisions/index.md):
  why a boundary exists.
- **Evidence** (developer-owned) — [research/index.md](../research/index.md): what
  was investigated.
- **History** (developer-owned) —
  [history/implementation-slices.md](../history/implementation-slices.md): what
  shipped, in what order.
- **Governance** (developer-owned) — [planning.md](planning/index.md),
  [standards.md](../standards.md), [quality.md](workflow/quality.md),
  [workflow.md](workflow/index.md), [conventions.md](workflow/conventions.md).
- **Direction** (developer-owned) — [direction.md](planning/direction.md),
  [product.md](planning/product.md).

## User-facing material

[../user/index.md](../user/index.md) routes the user audience. Use it to see what
users are told. Do not move canonical *developer* facts into the user layer, and
do not treat the shared `contracts/` layer as the only place authoritative content
may live: canonical does not mean shared directory.
