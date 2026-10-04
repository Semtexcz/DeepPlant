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
| Windows | Inno Setup 6 (`ISCC.exe` on `PATH`, the default install locations, or `ISCC`). CI installs the pinned Chocolatey package version |
| Linux | `appimagetool` (upstream release on `PATH` or `APPIMAGETOOL`). CI downloads the pinned, checksum-verified release |

These are **build-time** requirements. End users need none of them, and the
packaged-artifact smoke test proves that by running the artifact with a
sanitized PATH (see below).

## Packaging toolchain (pinned and integrity-checked)

Two dependency systems meet here and deliberately stay separate:

```text
uv.lock                     -> the Python dependency graph (PyInstaller included)
packaging/toolchain.toml    -> the pinned external native build tools
```

PyInstaller is a Python package, so it is resolved from the locked graph like any
other build dependency. The other tools are **not** Python packages: they are
native programs distributed by their own upstreams, so they cannot live in
`uv.lock` and are deliberately not vendored into the repository. Their exact
version, immutable upstream URL, and expected SHA-256 are recorded once in
[`packaging/toolchain.toml`](../../../packaging/toolchain.toml), which
`tools/packaging_toolchain.py` reads for CI
(`python tools/packaging_toolchain.py show`).

| Tool | Pinned input |
|---|---|
| PyInstaller | resolved through `uv.lock` (dependency group `package`) |
| Inno Setup | Chocolatey package `innosetup`, version `6.7.1` |
| `appimagetool` | release `1.9.1`, `https://github.com/AppImage/appimagetool/releases/download/1.9.1/appimagetool-x86_64.AppImage`, SHA-256 `ed4ce84f0d9caff66f50bcca6ff6f35aae54ce8135408b3fa33abfc3cb384eb0` |
| AppImage runtime | release `20251108`, `https://github.com/AppImage/type2-runtime/releases/download/20251108/runtime-x86_64`, SHA-256 `2fca8b443c92510f1483a883f60061ad09b46b978b2631c807cd873a47ec260d` |

The AppImage runtime is pinned because `appimagetool` would otherwise download
whatever its own upstream mutable `continuous` release serves at build time and
embed that into the generated `.AppImage` — a mutable input to a user-facing
artifact. CI passes the pinned runtime with `--runtime-file` instead.

Both packaging jobs verify the toolchain **before executing it**:

- Linux downloads the exact `appimagetool` and AppImage runtime named in the
  contract, checks both digests with `sha256sum --check`, and only then makes
  them executable. A mismatch fails the job, so the tool never runs and no
  artifact is produced.
- Windows installs the pinned Chocolatey package version with an explicit
  `--version` and fails unless Chocolatey reports exactly that version as
  installed. The resolved `ISCC.exe` (the Inno Setup 6 install directory is
  preferred over `PATH`, which can be a Chocolatey shim) is exported as `ISCC`,
  so the compiler that builds the installer is that verified one. Because Inno
  Setup 6.7.1 exposes no `--version` and its own `VERSIONINFO` resource is
  `0.0.0.0`, the version that actually built the artifact is then asserted from
  ISCC's own `Compiler engine version: …` banner in the packaging log. A missing
  or different version fails the job; there is no fallback to another installed
  Inno Setup.

Both jobs print the pinned release identity, the verified digest, and the tool's
own reported version, so the CI log shows which toolchain produced the uploaded
artifact. Version and checksum literals live only in `packaging/toolchain.toml`;
`tests/test_packaging_toolchain.py` fails if a mutable locator (`continuous`,
`latest`, `master`, `main`) or a missing SHA-256 is ever reintroduced.

Licences and what actually enters the artifact are recorded in
[THIRD_PARTY_NOTICES.md](../../../THIRD_PARTY_NOTICES.md): the `appimagetool`
and `ISCC` build executables are not distributed with DeepPlant, while the
generated AppImage contains the AppImage runtime and the generated Windows
installer contains Inno Setup installer/runtime components.

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
editor-package-windows   native windows-latest: pinned Inno Setup, build, package,
                         packaged smoke, upload
editor-package-linux     native ubuntu-latest: pinned + checksum-verified
                         appimagetool and AppImage runtime, build, package,
                         packaged smoke, packaged browser E2E, upload
```

Each packaging job builds on its native runner because a frozen application is
OS- and architecture-specific, and each reads `packaging/toolchain.toml` and
verifies its external tools **before** building (see above). Both jobs upload the
artifact plus a `.sha256` companion for reviewer download. Uploaded artifacts are
development/CI artifacts: no GitHub Release, no tag, and no automatic version
bumping is part of this workflow.

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

On Linux, put `appimagetool` on `PATH` (or set `APPIMAGETOOL`); set
`APPIMAGE_RUNTIME` to pin the AppImage runtime embedded into the artifact instead
of letting `appimagetool` fetch its own default. On Windows, install Inno Setup 6
(or set `ISCC`). `python tools/packaging_toolchain.py show` prints the versions
and digests CI pins, and `... export` exposes them as environment variables.

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
