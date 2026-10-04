---
type: governance
status: active
canonical_for:
  - editor-packaging
read_when:
  - packaging-change
  - distribution-change
  - editor-release-work
update_when:
  - packaging-architecture-change
  - distribution-format-change
depends_on:
  - docs/dev/workflow/quality.md
  - docs/dev/architecture/index.md
  - docs/dev/research/standalone-editor-distribution.md
decision: []
evidence:
  - docs/dev/research/standalone-editor-distribution.md
superseded_by: null
---

# Editor Packaging

> **Question this document answers:** how is the standalone DeepPlant Editor
> built, what are the platform build requirements, who owns the bundled
> resources, and how do I reproduce or debug a package build?

The candidate comparison, measurements, and rejection reasons are canonical in
[research/standalone-editor-distribution.md](../research/standalone-editor-distribution.md).
This page records the resulting practice.

## Selected architecture

```text
DeepPlant Core (semantic model, YAML, renderer)          Python package
        ↓
EditorApplication + FastAPI/Uvicorn transport (loopback)  Python package
        ↓
frozen application (PyInstaller onedir, native per OS)    build artifact
        ↓
user artifact: Inno Setup installer (Windows)
               AppImage (Linux)
```

The SPA is a resource of the **standalone application**, not of the Python
wheel, and the packaged application serves it from its own bundle.

One entry point drives all of it:

```bash
python tools/package_editor.py <phase>
```

with the explicit phases `frontend`, `stage`, `freeze`, `package`, `verify`,
`extract`, and `all`. The driver is plain Python because Windows is a
first-class target: the canonical packaging logic must not depend on bash or GNU
Make. `make package-editor` / `make verify-packaged-editor` are convenience
wrappers only.

## Build commands

```bash
python tools/package_editor.py all          # frontend -> stage -> freeze -> package -> verify
python tools/package_editor.py frontend     # production SPA build (pnpm)
python tools/package_editor.py stage        # copy the SPA into the packaging tree
python tools/package_editor.py freeze       # PyInstaller onedir, native OS
python tools/package_editor.py package      # installer (Windows) / AppImage (Linux)
python tools/package_editor.py verify       # install/extract the artifact and smoke-test it
python tools/package_editor.py extract      # install/extract and print the launcher path
```

Artifacts are written to `dist/editor/` with a deterministic name derived from
`[project] version` in `pyproject.toml`:

```text
deepplant-editor-<version>-windows-x86_64-setup.exe
deepplant-editor-<version>-linux-x86_64.AppImage
```

There is no second version string: `tools/package_editor.py` reads the project
version, and the Inno Setup script receives it as a define.

Intermediate state lives under the git-ignored `build/editor-package/`
(`spa/`, `work/`, `frozen/`, `verify/`).

## Platform build requirements (build machines only)

| Platform | Requirements |
|---|---|
| Both | Python 3.12, `uv`, PyInstaller (the `package` dependency group), Node.js 22 + `pnpm` for the SPA build |
| Windows | Inno Setup 6 (`ISCC.exe` on `PATH`, the default install locations, or `ISCC`); `choco install innosetup -y` in CI |
| Linux | `appimagetool` (official upstream release on `PATH` or `APPIMAGETOOL`) |

These are **build-time** requirements. End users need none of them, and the
packaged-artifact smoke test proves that by running the artifact with a
sanitized PATH (see below).

`appimagetool` is MIT-licensed and Inno Setup is free to use; neither is
redistributed inside the artifact. Provenance is recorded in
[THIRD_PARTY_NOTICES.md](../../../THIRD_PARTY_NOTICES.md).

## Resource ownership

```text
production SPA         apps/editor/dist  ->  staged  ->  deepplant/editor/dist in the bundle
canonical SVG symbols  src/deepplant/assets/symbols/**  ->  collected from the DeepPlant package
```

`deepplant.editor.application.resolve_assets_dir()` resolves the built SPA in a
fixed order and knows nothing about packaging tools:

1. an explicit `--assets-dir`;
2. the application's own packaged resource
   (`importlib.resources.files("deepplant.editor") / "dist"`) — the same
   mechanism the canonical symbol pack already uses;
3. the development checkout build, derived from the installed module's location
   rather than the process working directory.

Two consequences are deliberate:

- the base Python wheel never carries the SPA, even if a developer has staged a
  copy (`[tool.hatch.build.targets.wheel] exclude`);
- no candidate depends on the current working directory, so a packaged
  application cannot silently fall back to a checkout.

## CI jobs

`.github/workflows/ci.yml` keeps packaging off the fast gate:

```text
check                    Python + frontend fast gates, wheel build, wheel resource
                         check, base-install independence check
frontend-e2e             production SPA + real `deepplant ui` + real Chromium (source run)
editor-package-windows   native windows-latest: build, package, packaged smoke, upload
editor-package-linux     native ubuntu-latest: build, package, packaged smoke, upload
```

Each packaging job builds on its native runner because a frozen application is
OS- and architecture-specific. Both jobs upload the artifact plus a `.sha256`
companion for reviewer download. Uploaded artifacts are development/CI
artifacts: no GitHub Release, no tag, and no automatic version bumping is part
of this workflow.

## How the packaged-artifact smoke test works

`python tools/package_editor.py verify` does not trust the packaging tool's exit
code. It:

1. installs the Windows installer silently into a temporary directory, or
   extracts the AppImage with `--appimage-extract`;
2. copies `examples/realistic-process-fragment/plant.yaml` to a directory
   outside the repository;
3. **moves the checkout's `apps/editor/dist` out of the way**, so a packaged
   application that secretly relied on it cannot pass;
4. starts the artifact from outside the repository with a *sanitized*
   environment (no virtualenv, and no Python/Node/pnpm entries on `PATH`) using
   `--no-browser --port 0`;
5. waits for the application to announce its own loopback URL;
6. verifies `GET /` (built SPA, not a dev entry point), `GET /api/projection`
   (valid, 7 steps, 7 streams) and canonical symbol requests (`pump`, `vessel`,
   `heat_exchanger`);
7. stops the process, confirms it is gone, uninstalls/removes the temporary
   installation, and restores the checkout SPA.

What this proves: the artifact runs outside the checkout, opens a model outside
the checkout, serves the production SPA and the canonical symbols, and does not
need a separately installed Python or Node toolchain. What it does not prove:
that the operating system's browser or the Linux FUSE 2 runtime is present, so
both are documented as system requirements instead of being assumed.

The packaged-browser E2E boundary: `apps/editor/e2e/support/editor-server.ts`
accepts `DEEPLANT_EDITOR_EXECUTABLE` (and `DEEPLANT_EDITOR_PROJECT`), so the
*existing* Playwright specs run unchanged against either the source launcher or
the packaged launcher. Packaging concerns stay in that one helper.

## Reproducing a build locally

```bash
uv sync --group package
cd apps/editor && pnpm install --frozen-lockfile && cd ../..
python tools/package_editor.py all
```

On Linux, put `appimagetool` on `PATH` first (or set `APPIMAGETOOL`). On
Windows, install Inno Setup 6 (or set `ISCC`).

For ordinary frontend/backend iteration you never need to build an installer:
`make frontend-build` plus `uv run deepplant ui <path>` still works, and now also
works from any working directory.

## Debugging a package failure

| Symptom | Where to look |
|---|---|
| SPA missing from the artifact | the `stage` phase output and `build/editor-package/spa/index.html` |
| Missing module at artifact runtime | the freeze log; add a PyInstaller hook or `--collect-*` option in `tools/package_editor.py` |
| Artifact starts but serves nothing | `verify` output; the launcher's own stdout is echoed as `app:` lines |
| Installer build fails | the `ISCC` command echoed by the driver; compile the `.iss` manually with the same `/D` defines |
| AppImage build fails | rerun `appimagetool` on `build/editor-package/deepplant-editor.AppDir` directly |
| Packaged E2E fails | the CI job uploads Playwright traces/screenshots and the packaging log |

Always verify the **artifact**, not the intermediate tree: a successful fix is
one where `verify` passes with the checkout SPA moved aside.

## Related

- [research/standalone-editor-distribution.md](../research/standalone-editor-distribution.md)
  — measured candidate comparison and selection.
- [quality.md](quality.md) — which gates exist and what each must prove.
- [architecture/index.md](../architecture/index.md) — where the editor
  application boundary sits.
- [frontend/testing.md](../frontend/testing.md) — the browser E2E layer this
  workflow reuses.
