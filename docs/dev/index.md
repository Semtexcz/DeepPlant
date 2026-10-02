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
  - docs/conventions.md
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

This audience layer is the eventual **physical owner** of developer/agent
material: architecture, workflow/governance, planning, decisions, research/
evidence, and history are canonical *and* developer-owned, and will move from the
`docs/` root into this tree. They remain canonical after the move. Until then the
links below still resolve from the root; the current → target mapping is in
[documentation-migration.md](../documentation-migration.md).

## Start here

- **Current** — [architecture.md](../architecture.md): boundary map, module
  boundaries, durable invariants.
- **Governance** — [workflow.md](../workflow.md): the change loop.
- **Governance** — [quality.md](../quality.md): checks and test expectations.
- **Current** — [roadmap.md](../roadmap.md): current state and next direction.
- **Governance** — [conventions.md](../conventions.md): documentation rules.

## Smallest relevant context for a task

The `always` set in [.agents/context-map.yaml](../../.agents/context-map.yaml) is
only the universal bootstrap ([AGENTS.md](../../AGENTS.md)); everything else is
selected from the task, the changed files, and the selected skill. Pick the row
that matches the work, then add the matching task and changed-file context from
that map rather than reading the whole repository. This is a lightweight routing
table, not an orchestration engine.

| Task / change | Read |
|---|---|
| Orient in the repository | [architecture.md](../architecture.md), [roadmap.md](../roadmap.md) |
| Change the plant / process / piping model | [contracts/index.md](../contracts/index.md), then the specific contract |
| Change the CLI | [contracts/cli.md](../contracts/cli.md), [contracts/yaml-format.md](../contracts/yaml-format.md) |
| Change YAML load/save | [contracts/yaml-format.md](../contracts/yaml-format.md) |
| Change the renderer or symbols | [rendering.md](../rendering.md), [svg-symbols.md](../svg-symbols.md) |
| Change the DEXPI adapter | [contracts/dexpi-process-adapter.md](../contracts/dexpi-process-adapter.md) |
| Decide or record an architecture boundary | [decisions/index.md](../decisions/index.md), [conventions.md](../conventions.md) |
| Add or change evidence | [research/index.md](../research/index.md) |
| Change documentation | [conventions.md](../conventions.md), [documentation-migration.md](../documentation-migration.md) |

Machine-readable agent context selection lives in
[.agents/context-map.yaml](../../.agents/context-map.yaml); [AGENTS.md](../../AGENTS.md)
is the agent bootstrap entry point.

## Authority layers

These are canonical for their authority type. Only the **contract** layer is
shared with users; decisions, evidence, history, and governance are
developer/agent-owned even though they are authoritative.

- **Contract** (shared) — [contracts/index.md](../contracts/index.md): what must
  hold now.
- **Decision** (developer-owned) — [decisions/index.md](../decisions/index.md):
  why a boundary exists.
- **Evidence** (developer-owned) — [research/index.md](../research/index.md): what
  was investigated.
- **History** (developer-owned) —
  [history/implementation-slices.md](../history/implementation-slices.md): what
  shipped, in what order.
- **Governance** (developer-owned) — [planning.md](../planning.md),
  [standards.md](../standards.md), [quality.md](../quality.md),
  [workflow.md](../workflow.md), [conventions.md](../conventions.md).
- **Direction** (developer-owned) — [direction.md](../direction.md),
  [product.md](../product.md).

## User-facing material

[../user/index.md](../user/index.md) routes the user audience. Use it to see what
users are told. Do not move canonical *developer* facts into the user layer, and
do not treat the shared `contracts/` layer as the only place authoritative content
may live: canonical does not mean shared directory.
