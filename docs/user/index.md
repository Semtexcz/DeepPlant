---
type: navigation
status: active
canonical_for:
  - user-documentation-navigation
read_when:
  - start-work
  - authoring-plant-yaml
  - cli-change
update_when:
  - user-documentation-change
depends_on:
  - docs/index.md
  - docs/conventions.md
decision:
  - docs/decisions/ADR-0015-documentation-architecture-v2-1.md
  - docs/decisions/ADR-0014-documentation-architecture-v2.md
evidence: []
superseded_by: null
---

# User Documentation

For people who **use** DeepPlant rather than change its internals. This layer will
eventually own the how-to-use guidance. Today it routes to existing pages;
canonical **cross-audience contracts** stay shared in
[contracts/](../contracts/index.md), while developer-only contracts/reference remain
canonical but developer-owned. Architecture, decisions, planning, and evidence are
also developer-owned and are not required reading for users. The structure is decided in
[ADR-0015](../decisions/ADR-0015-documentation-architecture-v2-1.md), refining
[ADR-0014](../decisions/ADR-0014-documentation-architecture-v2.md).

## Start here

- Install, build, and run: [README.md](../../README.md) (Quick Start).
- Minimal example: [examples/minimal-process/README.md](../../examples/minimal-process/README.md).
- Realistic fragment and its rendered SVG:
  [examples/realistic-process-fragment/README.md](../../examples/realistic-process-fragment/README.md).

## Use the CLI

- **Contract** — [contracts/cli.md](../contracts/cli.md): commands, printed
  output, and exit codes.

## Author a plant model as YAML

- **Contract** — [contracts/yaml-format.md](../contracts/yaml-format.md):
  authored document shape, load/save guarantees, error messages.
- **Contract** — [contracts/plant-model.md](../contracts/plant-model.md):
  equipment, ports, and connections.
- **Contract** — [contracts/process-model.md](../contracts/process-model.md):
  process steps and streams.
- **Contract** — [contracts/physical-piping.md](../contracts/physical-piping.md):
  piping lines, segments, and realizations.

## Understand what DeepPlant is

- **Transitional current link** — [product.md](../product.md): internal
  product/planning thesis and long-term non-goals. After migration, the user-facing
  explanation will be `docs/user/concepts/what-is-deepplant.md`; that page is a
  planned target and is not created by this PR.
- **Current** — [architecture.md](../architecture.md): what exists today. This is
  developer-oriented; read it only if you want the internal boundary map.

A user should not need architecture research, ADRs, planning governance, or
historical spikes to use DeepPlant. The pages above link to contracts, which are
the shared authoritative reference.

## Developer or agent?

If you are changing DeepPlant rather than using it, start from
[../dev/index.md](../dev/index.md). Only the **contracts** above are shared
between audiences; developer/agent material (architecture, decisions, evidence,
planning, history) is canonical but developer-owned, and the audience layer
changes both where you begin and what you should read.
