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
  - docs/decisions/ADR-0014-documentation-architecture-v2.md
evidence: []
superseded_by: null
---

# Developer and Agent Documentation

For contributors, maintainers, and agents **changing** DeepPlant. This is a
navigation map, not a content dump. The structure is decided in
[ADR-0014](../decisions/ADR-0014-documentation-architecture-v2.md).

## Start here

- **Current** — [architecture.md](../architecture.md): boundary map, module
  boundaries, durable invariants.
- **Governance** — [workflow.md](../workflow.md): the change loop.
- **Governance** — [quality.md](../quality.md): checks and test expectations.
- **Current** — [roadmap.md](../roadmap.md): current state and next direction.
- **Governance** — [conventions.md](../conventions.md): documentation rules.

## Smallest relevant context for a task

Pick the row that matches the work and read those documents, not the whole
repository. This is a lightweight routing table, not an orchestration engine.

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

- **Contract** — [contracts/index.md](../contracts/index.md): what must hold now.
- **Decision** — [decisions/index.md](../decisions/index.md): why a boundary
  exists.
- **Evidence** — [research/index.md](../research/index.md): what was investigated.
- **History** — [history/implementation-slices.md](../history/implementation-slices.md):
  what shipped, in what order.
- **Governance** — [planning.md](../planning.md), [standards.md](../standards.md),
  [quality.md](../quality.md), [workflow.md](../workflow.md),
  [conventions.md](../conventions.md).
- **Direction** — [direction.md](../direction.md), [product.md](../product.md).

## User-facing material

[../user/index.md](../user/index.md) routes the user audience. Use it to see what
users are told, but keep canonical facts in the shared layer above.
