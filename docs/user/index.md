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
  - docs/decisions/ADR-0014-documentation-architecture-v2.md
evidence: []
superseded_by: null
---

# User Documentation

For people who **use** DeepPlant rather than change its internals. The facts stay
in the shared canonical layer and are linked here; this page only routes. The
structure is decided in
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

- **Current** — [product.md](../product.md): product thesis and long-term
  non-goals.
- **Current** — [architecture.md](../architecture.md): what exists today.

## Developer or agent?

If you are changing DeepPlant rather than using it, start from
[../dev/index.md](../dev/index.md). Both audiences share the canonical documents
above; the audience layer only changes where you begin.
