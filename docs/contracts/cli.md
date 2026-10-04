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
- Editor application: `deepplant-editor` — the same editor with an
  application-oriented identity; see
  [The standalone Editor application](#the-standalone-editor-application)

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

Launches the local, read-only Engineering Editor (Issues #75, #79). It loads the
project through the same DeepPlant loader as `validate`, so the browser never
parses YAML and the semantic model stays authoritative. The local HTTP boundary
is a thin FastAPI adapter served by Uvicorn (Issue #79); the served surface is
unchanged.

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
| `--assets-dir <dir>` | Directory containing the built editor assets. Defaults to the assets the application itself carries, then the development checkout build (see below). |

Built-asset resolution (Issue #85) is working-directory independent and names no
packaging tool:

1. an explicit `--assets-dir`;
2. the packaged resource `deepplant/editor/dist` inside the application bundle;
3. the source-checkout build `<repository root>/apps/editor/dist`, derived from
   the installed module's location.

The base Python wheel never contains the SPA: it is owned by the standalone
Editor packaging stage. See
[workflow/packaging.md](../dev/workflow/packaging.md).

Behavior:

- The server binds to **loopback only** (`127.0.0.1`); there is no option to
  expose it on `0.0.0.0`. This is a local developer/product tool with no
  authentication and no production or server-security claim.
- It serves exactly three read routes: the Process/PFD projection JSON
  (`/api/projection`), the canonical packaged symbol assets
  (`/api/symbols/<role>.svg`), and the built editor assets.
- The built editor application must exist first in a source checkout:
  `make frontend-build` (or `cd apps/editor && pnpm build`). A standalone
  application always carries it. If it is missing, the command exits 1 with a
  concise message and no traceback.
- The editor transport needs FastAPI and Uvicorn, which are the `deepplant[editor]`
  extra. Without it, the command exits 1 with a message naming that extra instead
  of an `ImportError` traceback. `deepplant version` and `deepplant validate`
  never import the transport.
- Project path, YAML, and model errors reuse the `PlantLoadError` text from
  [yaml-format.md](yaml-format.md) and exit 1.
- Semantic validation comes from `load_plant`. A valid model without a
  `process` section, or one whose current Process/PFD presentation role cannot be
  resolved, still starts the editor; `/api/projection` returns HTTP 422 with
  `validation.valid: true`, `projection: null`, and a separate projection error.
  Load, YAML, and semantic-reference failures remain `PlantLoadError` failures.

### The standalone Editor application

`deepplant-editor` is the same editor under the identity an end user runs. It is
the entry point the frozen Windows/Linux artifact launches.

```text
deepplant-editor <path> [--symbol-role STEP=ROLE] [--port <n>]
                        [--assets-dir <dir>] [--browser | --no-browser]
```

- It accepts the same `path`, `--symbol-role`, `--port`, and `--assets-dir`
  arguments, resolves the project through the same
  `EditorApplication`, serves through the same FastAPI/Uvicorn transport, and
  prints the same launch message. There is no second editor implementation.
- It additionally opens the user's default browser once the loopback server is
  actually accepting connections (`--browser`, the default). `--no-browser`
  suppresses that for automation and headless use; the URL is always printed, and
  if no browser can be opened the URL is printed again.
- It is installed by the base distribution but only *runs* with the editor
  transport available; without it, it reports the same actionable message as
  `deepplant ui`.

## Deliberately not provided

A render command, a save/format command, a symbol-pack selector, machine-readable
(JSON) output, watch mode, browser auto-open **in `deepplant ui`**, daemon/service
management, and any configuration file or environment-variable surface. Each
needs its own evidence and Issue; the renderer and loader are currently
library/API-level only. Browser auto-open exists only in the application entry
point `deepplant-editor`, not in the developer command.

## Related

- [yaml-format.md](yaml-format.md) — error-message contract behind `validate`.
- [architecture.md](../dev/architecture/index.md) — `tests -> CLI -> io.load_plant -> model`.
