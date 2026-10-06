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
- Editor application: `deepplant-editor` — the standalone **native desktop host**
  (a graphical window embedding the shared SPA); see
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
- It serves exactly three read routes: the workspace/projection JSON
  (`/api/projection`), the canonical packaged symbol assets
  (`/api/symbols/<role>.svg`), and the built editor assets.
- `/api/projection` reports the explicit **workspace state** first
  (`workspace.state`: `"empty"` or `"loaded"`, with the open document's identity
  when loaded). With no project open it answers HTTP 200 with
  `validation: null`, `projection: null`, and no error: an empty workspace is an
  ordinary state, never an invalid model or a failed projection (Issue #97).
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

`deepplant-editor` is the **native desktop host**: the graphical application an
end user launches. It is the entry point the frozen Windows/Linux artifact runs,
and it embeds the *same* frontend and the *same* application boundary as
`deepplant ui`.

```text
deepplant-editor [path] [--symbol-role STEP=ROLE] [--port <n>]
                        [--assets-dir <dir>]
                        [--self-check --self-check-report <path>]
```

- **The path is optional.** Running it with no argument opens the ordinary shared
  Vue editor with **no project open**: the application chrome, the Process/PFD
  workspace and canvas, the Inspector and the status strip are all present, the
  canvas is empty, and the status clearly says no project is open. There is no
  separate native start page and no second editor UI (Issue #97). It never prints
  help and never demands a path, so normal use requires no terminal and no
  command-line knowledge.
- With a path it opens the same editor with that model already active. This is the
  advanced/diagnostic form, and it supports development, automated checks, and a
  future OS *Open With* association. It is not a separate product mode: the path
  simply activates a document in the normal workspace.
- **`File -> Open…`** activates the selected model in the *existing* session. The
  same window, long-lived server and webview are reused, so opening or replacing a
  project never leaks a server, socket, webview or window, and the previous
  document is released cleanly. A failed open leaves the previously active project
  untouched and reports the normal DeepPlant load error.
- It resolves the project through the same `EditorApplication`, serves it through
  the same FastAPI/Uvicorn transport on `127.0.0.1` with the same ephemeral-port
  behaviour, and renders the same production SPA. There is no second editor
  implementation.
- The native `Open` dialog only selects a `*.yaml`/`*.yml` filesystem path; the
  desktop host never parses DeepPlant YAML. The selected path is loaded through
  the ordinary application/model-loading boundary, exactly like `deepplant ui`.
- It **never** opens an external browser, and it keeps the embedded view on its
  own loopback origin.
- It needs the desktop runtime (`PySide6`/Qt WebEngine, the `deepplant[desktop]`
  extra, which includes the editor transport). Without it, it reports an
  actionable message naming that extra instead of an `ImportError` traceback.
  `deepplant version`, `deepplant validate`, and `deepplant ui` never need it.
- `--self-check --self-check-report <path>` is the documented automation mode
  used by the packaged-artifact verification: it loads the application, probes
  the real rendered page, closes the window, writes a JSON verdict, and exits
  with `0` only when every check passed. With no model argument it probes the
  shared SPA's empty workspace (no project open, no fabricated model); with a
  model it probes the rendered Process/PFD and Inspector. It adds no production
  protocol and is never used in normal operation.

Closing the window stops the local server, releases the loopback socket, and
terminates the helper processes the application owns. Nothing outside the
application is signalled. This holds when the editor never opened a project: an
empty session owns the same server, socket and WebEngine helpers, so it shuts
them down identically (Issue #97).

## Deliberately not provided

A render command, a save/format command, a symbol-pack selector, machine-readable
(JSON) output, watch mode, browser auto-open **in `deepplant ui`**, daemon/service
management, and any configuration file or environment-variable surface. Each
needs its own evidence and Issue; the renderer and loader are currently
library/API-level only. No host opens a browser automatically: `deepplant ui`
prints the loopback URL for you to open, and `deepplant-editor` embeds the SPA in
its own window.

## Related

- [yaml-format.md](yaml-format.md) — error-message contract behind `validate`.
- [architecture.md](../dev/architecture/index.md) — `tests -> CLI -> io.load_plant -> model`.
