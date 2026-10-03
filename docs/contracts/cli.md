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
  - docs/dev/decisions/ADR-0002-semantic-model-is-the-core.md
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
| `deepplant ui <path>` | local editor launch message on stdout; the command then serves until interrupted |

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

### `deepplant ui <path>`

Launches the local, read-only Engineering Editor (Issue #75). It loads the
project through the same DeepPlant loader as `validate`, so the browser never
parses YAML and the semantic model stays authoritative.

```text
DeepPlant Engineering Editor (read-only Process/PFD)
  project: <path>
  open:    http://127.0.0.1:<port>/
  press Ctrl+C to stop
```

Options:

| Option | Meaning |
|---|---|
| `--symbol-role STEP=ROLE` | Repeatable transient presentation override for one `ProcessStep` id. Presentation only: it is never written to the model or YAML. The realistic fragment needs `--symbol-role PS-vessel=vessel` because `PS-vessel.function` is honestly `unspecified` (ADR-0009). |
| `--port <n>` | Local port; `0` picks a free port. Defaults to `8765`. |
| `--assets-dir <dir>` | Directory containing the built editor assets. Defaults to `./frontend/dist`. |

Behavior:

- The server binds to **loopback only** (`127.0.0.1`); there is no option to
  expose it on `0.0.0.0`. This is a local developer/product tool with no
  authentication and no production or server-security claim.
- It serves exactly three read routes: the Process/PFD projection JSON
  (`/api/projection`), the canonical packaged symbol assets
  (`/api/symbols/<role>.svg`), and the built frontend assets.
- The built frontend must exist first: `make frontend-build` (or
  `cd frontend && pnpm build`). If it is missing, the command exits 1 with a
  concise message and no traceback.
- Project path, YAML, and model errors reuse the `PlantLoadError` text from
  [yaml-format.md](yaml-format.md) and exit 1.
- A valid model without a `process` section starts the editor, and the
  projection route reports the honest DeepPlant message as an invalid status.

## Deliberately not provided

A render command, a save/format command, a symbol-pack selector, machine-readable
(JSON) output, watch mode, browser auto-open, daemon/service management, and any
configuration file or environment-variable surface. Each needs its own evidence
and Issue; the renderer and loader are currently library/API-level only.

## Related

- [yaml-format.md](yaml-format.md) — error-message contract behind `validate`.
- [architecture.md](../dev/architecture/index.md) — `tests -> CLI -> io.load_plant -> model`.
