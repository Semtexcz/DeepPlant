---
type: contract
status: active
canonical_for:
  - cli-contract
read_when:
  - cli-change
  - user-documentation
depends_on:
  - docs/contracts/yaml-format.md
  - docs/dev/architecture/index.md
decision:
  - docs/decisions/ADR-0002-semantic-model-is-the-core.md
evidence: []
superseded_by: null
---

# CLI Contract

> **Question this document answers:** which commands exist, what do they print,
> and what exit codes do they use?
>
> Implemented in `src/deepplant/__main__.py` (Typer). The CLI is a consumer of
> the semantic model and YAML boundary; it holds no domain logic (ADR-0002).

## Entry points

- Console script: `deepplant`
- Module execution: `python -m deepplant` (equivalent; `make run` / `make dev`
  use it)

Running with no arguments prints help.

## Commands

| Command | Output |
|---|---|
| `deepplant --help` | Typer help text; command list |
| `deepplant version` | `DeepPlant <version>` on stdout, exit code 0 |
| `deepplant validate <path>` | validation summary on stdout, exit code 0 |

### `deepplant validate <path>`

On success it prints exactly:

```text
✓ valid DeepPlant model
✓ plant: <plant id>
✓ equipment: <count>
✓ ports: <count>
✓ connections: <count>
```

- `equipment` counts `PlantModel.equipment`; `ports` counts every port owned by
  every equipment item; `connections` counts `PlantModel.connections`.
- The process graph, piping lines, and any other submodel are **not** reported
  yet.
- On failure it prints `✗ <message>` to **stderr** and exits with code 1. The
  message is the `PlantLoadError` text from
  [yaml-format.md](yaml-format.md), so a user sees the file path, the dotted
  field location, and the reason, but never a traceback.

The command validates structural and reference rules only. Engineering rules
(DN continuity, line-number consistency, and similar) do not exist.

## Deliberately not provided

A render command, a save/format command, a symbol-pack selector, machine-readable
(JSON) output, watch mode, and any configuration file or environment-variable
surface. Each needs its own evidence and Issue; the renderer and loader are
currently library/API-level only.

## Related

- [yaml-format.md](yaml-format.md) — error-message contract behind `validate`.
- [architecture.md](../dev/architecture/index.md) — `tests -> CLI -> io.load_plant -> model`.
