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
desktop host (PySide6 / Qt WebEngine) + embedded SPA      application code
        ↓
frozen application (PyInstaller onedir, native per OS)    build artifact
        ↓
user artifact: Inno Setup installer (Windows)
               AppImage (Linux)
```

The SPA is a resource of the **standalone application**, not of the Python
wheel. The desktop host serves it from the application's own loopback server and
embeds it in a native window; the built SPA is mapped into the frozen bundle at
`deepplant/editor/dist` and is never part of the base wheel.

The technology investigation and the measured selection (PySide6 + Qt WebEngine)
are canonical in
[research/editor-desktop-host.md](../research/editor-desktop-host.md); this page
records the resulting practice. The first #85 slice (PR #92) established the
self-contained packaging foundation with a browser host
([research/standalone-editor-distribution.md](../research/standalone-editor-distribution.md));
Issue #93 replaced only the host:

```text
distribution foundation (PR #92)
packaged executable → local FastAPI/Uvicorn → external browser

delivered product (Issue #93, merged by PR #95)
packaged executable → native desktop window → embedded shared Vue SPA
```

### The desktop host

- `deepplant-editor` launches a `QMainWindow` with an embedded
  `QWebEngineView`. It never opens an external browser.
- The initial model path is **optional**. With no argument the window opens with
  a minimal native bootstrap (`File -> Open…` and an `Open plant…` button);
  a native `QFileDialog` then selects a `*.yaml`/`*.yml` path, which is loaded
  through the ordinary DeepPlant application boundary. The shell never parses
  YAML.
- With a path argument the same window opens directly on that model.
- The embedded view may only navigate within the local application origin; other
  schemes and remote hosts are refused.
- Closing the window stops the owned `EditorServer`, which closes the loopback
  socket and joins the serving thread, and then Qt shuts down its own
  `QtWebEngineProcess` helpers. Nothing is force-killed and no process outside
  the application is signalled.
- On Windows the frozen executable is built `--windowed`, so the Start Menu
  shortcut does not open a console window. Diagnostics for automation are
  deliberately routed to `--self-check-report <path>` rather than to stdout,
  which a GUI executable does not have.

One entry point drives all of it:

```bash
python tools/package_editor.py <phase>
```

with the explicit phases `frontend`, `stage`, `licenses`, `freeze`, `package`,
`verify`, `extract`, and `all`. The driver is plain Python because Windows is a
first-class target: the canonical packaging logic must not depend on bash or GNU
Make. `make package-editor` / `make verify-packaged-editor` are convenience
wrappers only.

## Build commands

```bash
uv run --group package --group desktop python tools/package_editor.py all
uv run --group package --group desktop python tools/package_editor.py frontend   # production SPA build (pnpm)
uv run --group package --group desktop python tools/package_editor.py stage      # copy the SPA into the packaging tree
uv run --group package --group desktop python tools/package_editor.py licenses   # assemble the compliance payload (digest-verified)
uv run --group package --group desktop python tools/package_editor.py freeze     # PyInstaller onedir, native OS
uv run --group package --group desktop python tools/package_editor.py package    # installer (Windows) / AppImage (Linux)
uv run --group package --group desktop python tools/package_editor.py verify     # install/extract the artifact and verify the desktop product
uv run --group package --group desktop python tools/package_editor.py extract    # install/extract and print the launcher path
```

The `desktop` group supplies PySide6/Qt WebEngine. It is **not** part of
`make setup`/`make check`: the fast gate must never download the Qt runtime, and
the semantic Core, the ordinary CLI, and `deepplant ui` must stay provably free
of it.

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
| Both | Python 3.12, `uv`, PyInstaller (the `package` dependency group), **PySide6 / Qt WebEngine** (the `desktop` dependency group), Node.js 22 + `pnpm` for the SPA build |
| Windows | Inno Setup 6 (`ISCC.exe` on `PATH`, the default install locations, or `ISCC`). CI installs the pinned Chocolatey package version |
| Linux | `appimagetool` (upstream release on `PATH` or `APPIMAGETOOL`). CI downloads the pinned, checksum-verified release. The **desktop verification** additionally needs a display (CI uses Xvfb) and the ordinary Linux desktop graphics/session libraries Qt WebEngine/Chromium uses on an end user's machine (see "Supported Linux baseline" below) |

These are **build-time** requirements for the build machine. End users need none of
them: the Python, Qt and Qt WebEngine/Chromium runtimes are inside the artifact,
and the packaged-artifact verification proves that by running it with a sanitized
environment (see below). The one thing the artifact does not bundle is the
ordinary Linux desktop graphics/userspace stack, which every Qt application uses;
that boundary is stated explicitly under "Supported Linux baseline".

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

`.github/workflows/ci.yml` keeps packaging off the fast gate and off
unrelated pull requests. The native jobs run only when the change classifier
decides the packaged desktop product can be affected, and they always run on
`main` and `workflow_dispatch`:

```text
docs-validation          documentation / agent metadata only (no build, no browser)
python-checks            format, lint, typecheck, full pytest
wheel-verification       wheel build, wheel resource check, base-install independence check
frontend-checks          frontend lint/typecheck/tests + production SPA build
frontend-e2e             production SPA + real `deepplant ui` + real Chromium (source run)
editor-package-windows   native windows-latest: pinned Inno Setup, desktop group,
                         strict type-check of the Qt host, build, package, real-window
                         desktop verification, helper/notice/exit assertions, upload
editor-package-linux     native ubuntu-24.04: pinned + checksum-verified
                         appimagetool and AppImage runtime, Xvfb + Qt WebEngine
                         host libraries, desktop group, strict type-check of the Qt
                         host, build, package, real-window desktop verification,
                         Linux dependency audit, xdotool window discovery and a
                         hard process-exit gate on the virtual display, upload
ci-gate                  stable aggregate required result (branch protection)
```

The full routing matrix, and the surfaces that select each native job, are
canonical in [quality.md](quality.md#change-aware-ci). For packaging those
surfaces are the desktop host, `packaging/**`, the packaging tooling, the
packaged brand assets, the canonical `src/deepplant/assets/**` symbols, the
desktop/package dependency groups, the desktop type-check configuration
(`pyrightconfig.desktop.json`), the embedded SPA and editor application, and the
bundled compliance payload (`LICENSE`, `THIRD_PARTY_NOTICES.md`). The packaged
smoke test also loads the self-contained `examples/process-graph/plant.yaml`
fixture at runtime, so changing that fixture selects both native jobs as well.
The `examples/realistic-process-fragment/**` browser E2E fixture is **not** used
by the packaged path, so it selects only the browser E2E job. Routing never
weakens a step: when a packaging job runs, it still performs the complete
verification listed below.

Each packaging job builds on its native runner because a frozen application is
OS- and architecture-specific, and each reads `packaging/toolchain.toml` and
verifies its external tools **before** building (see above). Both jobs upload the
artifact plus a `.sha256` companion for reviewer download, and both upload the
desktop verification reports. Uploaded artifacts are development/CI artifacts: no
GitHub Release, no tag, and no automatic version bumping is part of this
workflow.

Because the fast `check` gate deliberately does not install PySide6, it excludes
`src/deepplant/editor/desktop_qt.py` from Pyright. Both native jobs therefore run
the desktop-specific strict check as well:

```bash
uv run --group dev --group desktop pyright --project pyrightconfig.desktop.json
make typecheck-desktop   # developer convenience wrapper
```

`pyrightconfig.desktop.json` mirrors the canonical strict settings in
`[tool.pyright]` but keeps every module - including `desktop_qt.py` - in scope,
with PySide6's stubs available. There is no blanket `type: ignore` for the Qt
module.

`frontend-e2e` stays a separate job and keeps verifying the *shared frontend* as
a browser/web deployment through `deepplant ui`. It no longer targets the
packaged application, because that product is now a native window rather than a
browser target; the desktop jobs cover it.

## How the packaged desktop verification works

`uv run --group package --group desktop python tools/package_editor.py verify`
does not trust the packaging tool's exit code. It:

1. installs the Windows installer silently into a temporary directory, or
   extracts the AppImage with `--appimage-extract`;
2. copies the canonical **self-contained smoke fixture**
   (`examples/process-graph/plant.yaml`, `SMOKE_MODEL` in the driver) to a
   directory outside the repository;
3. **moves the checkout's `apps/editor/dist` out of the way**, so a packaged
   application that secretly relied on it cannot pass;
4. asserts the frozen bundle actually carries the built SPA, the canonical
   symbols, and the Qt WebEngine runtime (`QtWebEngineProcess`, resource packs,
   ICU data, and a locale pack directory);
5. starts the artifact from outside the repository with a *sanitized*
   environment (no virtualenv, and no Python/Node/pnpm entries on `PATH` - the
   graphical session variables an end user's desktop provides are deliberately
   kept) **twice**:
   - **no model argument** - proves the primary end-user workflow opens a real
     window instead of demanding a path;
   - `plant.yaml` - proves the packaged editor workflow renders the
     self-contained fixture, selects a known step, and shows its semantics, with
     **no** `--symbol-role` or other hidden presentation override;
6. reads each launch's JSON report and requires every check to be true;
7. restores the checkout SPA and removes the temporary installation.

### The canonical packaged smoke fixture

The packaged verification must use the same model-loading and presentation
semantics an ordinary user reaches through `File -> Open…`, so the fixture it
loads is **self-contained**: it loads, validates, projects and renders through the
ordinary application boundary with no `--symbol-role`, no environment-variable
presentation injection, no test-only application state, and no source-checkout
dependency.

The automation and the manual workflow differ only in **how the path is
supplied**; both cross the same application loading boundary and neither carries
hidden presentation state:

```text
automation            deepplant-editor <path>            (no native dialog driven)
manual user workflow  launch editor -> File -> Open… -> choose the same fixture
```

```text
examples/process-graph/plant.yaml     (driver constant `SMOKE_MODEL`)
```

It is the smallest example that still exercises meaningful Editor behaviour -
three `ProcessStep`s, two `ProcessStream`s, and a step (`PUMP`, `function:
pumping`) that resolves to a symbol role through the ordinary engineering
`function` -> role policy - so the packaged path proves semantic validation,
Process/PFD projection, real rendering, node selection, and Inspector content end
to end. `tests/test_packaging_smoke.py` holds the regression: it proves the
fixture renders with no overrides, that the driver's default model is that
fixture, and that the launch command never injects a presentation override.

`examples/realistic-process-fragment/plant.yaml` is deliberately **not** the
packaged smoke fixture. Its `PS-vessel` step is honestly `function: unspecified`
(ADR-0009): the drawing shows a vessel, but that is a presentation choice, and the
fragment carries no engineering evidence for the vessel's process function.
Rendering it therefore requires an explicit per-step presentation override that an
ordinary user never receives, so it stays unrenderable through the plain
`File -> Open…` path. It remains useful evidence of a semantically valid model
whose current presentation role cannot be resolved (`tests/test_render.py`,
`tests/test_editor_projection.py`), and it stays the browser E2E fixture; this
packaging slice must not falsify it by inventing a process function or adding a
global `unspecified -> vessel` mapping.

### Manual parity check

The automated verification supplies the fixture path on launch
(`deepplant-editor <path>`); it does **not** click through the native file dialog.
Issue #98 also requires a reproducible manual path, so a developer or user can
reach the *same meaningful result* by hand through the native workflow.

The installed artifact does **not** bundle the `examples/` directory, so copy the
fixture to a location outside the repository before opening it in a packaged
application (a source checkout can open the file in place):

```bash
cp examples/process-graph/plant.yaml /tmp/deepplant-smoke.yaml
```

1. Launch the Editor **without a model** and wait for the start page:
   - source checkout: `uv run --group desktop deepplant-editor`;
   - installed artifact: the Start Menu shortcut (Windows) or the AppImage
     (Linux).
2. Use **File -> Open…** and select the model in the native dialog:
   - source checkout: `examples/process-graph/plant.yaml`;
   - installed artifact: the copied standalone file, e.g.
     `/tmp/deepplant-smoke.yaml`.
3. Confirm the rendered result:
   - the model status is **Valid**;
   - 3 `ProcessStep`s are rendered;
   - 2 `ProcessStream`s are rendered;
   - **PUMP** is visible;
   - selecting **PUMP** shows `ID = PUMP`, `Name = Transfer Pump`,
     `Function = pumping`, `Ports = suction, discharge`.
4. Close the application normally (no forced kill).

These are exactly the expectations the automated self-check asserts
(`SMOKE_PROBE_STEP_ID`/`SMOKE_EXPECTED_STEPS`/`SMOKE_EXPECTED_STREAMS` in
`deepplant.editor.desktop`), reached through the native workflow instead of a
launch argument. On Windows the same recipe works with `deepplant-editor.exe`
from the installation folder.

### The desktop self-check hook

Both launches use `--self-check --self-check-report <path>`. This is the narrow,
documented test hook Issue #93 requires, and it exists for a specific reason: a
GUI application has no browser target, and on Windows it is a `--windowed`
executable with no console, so stdout cannot carry the evidence.

What it does — and deliberately does **not** do:

- it launches the ordinary application, shows the real native window, and loads
  the real production SPA from the real loopback server;
- it reads the real rendered page through Qt's own JavaScript engine
  (`QWebEnginePage.runJavaScript`), not a mock: validation status, the rendered
  `ProcessStep`/`ProcessStream` counts, the selection of `PUMP`, and the
  Inspector's semantic fields (the canonical self-contained smoke fixture; see
  "The canonical packaged smoke fixture" above);
- it then closes the window through the ordinary `closeEvent` a user triggers and
  records whether the owned server stopped and the loopback socket was released;
- it adds **no** production protocol, introduces no behavioural branch in normal
  use, and can be ignored by any normal build.

The report is a small JSON object. Every value in `checks` must be `true`;
`lifecycle` records the raw measured facts (a `false` there is what makes the run
fail):

```json
{
  "checks": {
    "validationValid": true, "processSteps": true, "processStreams": true,
    "pumpSelected": true, "inspectorFunction": true, "productionSpa": true,
    "windowVisible": true, "windowClosed": true,
    "serverStopRequested": true, "serverStopped": true,
    "serverThreadTerminated": true, "portReleased": true,
    "eventLoopReturned": true
  },
  "lifecycle": {
    "windowVisible": true, "windowClosed": true,
    "serverStopRequested": true, "serverStopped": true,
    "serverThreadAliveAfterClose": false, "portReleased": true,
    "eventLoopReturned": true
  },
  "verdict": "pass",
  "windowTitle": "DeepPlant Editor"
}
```

The driver also rejects a report whose `checks` omit any required lifecycle key,
so an older artifact cannot pass by sending a shorter report.

What this proves: the artifact runs outside the checkout, opens a model outside
the checkout, renders the production SPA in a real native window, stops its owned
server thread and releases the loopback socket when the window closes, and lets
the application exit through the ordinary lifecycle. The process is **not**
force-terminated to make the report look clean: `eventLoopReturned` is only
recorded after `QApplication.exec()` returns in the normal path.

### Shutdown is a hard invariant

```text
user closes the main window
        ↓
EditorServer stops  (the serving thread must actually terminate)
        ↓
loopback socket is released
        ↓
Qt event loop exits
        ↓
owned QtWebEngineProcess helpers exit
        ↓
DeepPlant Editor process exits naturally
```

Three pieces enforce it, and none trusts a bookkeeping flag:

- `EditorServer.stop()` returns the *measured* thread state. A timed-out stop keeps
  the thread reference instead of erasing it, so `EditorServer.running` stays
  truthful (`False` only once the thread is really gone) and a later `stop()` can
  still join the same owned thread. Unit coverage is in
  `tests/test_editor_server.py` (success, idempotency, timeout/still-live,
  eventual shutdown, socket release) using a controlled thread seam, not real
  sleeps.
- `_DesktopEditor` drops the owned server reference only when `stop()` reports it
  stopped; otherwise the still-live server is retained and reported. The
  self-check derives `serverStopped` from `EditorServer.running`, never from
  `editor.server is None`.
- the Linux packaging job launches the packaged application with no model
  argument, closes the real window through the session close request (and the
  standard `alt+F4` gesture), and **fails the job** if the process is still alive
  afterwards. Forced cleanup runs only after that failure has been recorded.

`os._exit()` remains only in the fatal error handler of
`deepplant.editor.desktop_qt`: a half-constructed Qt/WebEngine application must
not be allowed to hang an automated caller. The ordinary successful close path
returns from `run_host()` and lets Python exit normally - nothing in the success
path depends on `os._exit()`.

### Owned Qt WebEngine helpers must not leak

Qt WebEngine is multiprocess. Before each self-check launch the driver snapshots
the running `QtWebEngineProcess` PIDs, and after the application exits it requires
that none *added by that run* is still alive (within a bounded grace period). The
evidence is tied to the application run: the assertion is not "the OS has zero
`QtWebEngineProcess` processes", and it never uses a broad `pkill`.

### Redistribution compliance payload

The artifact redistributes PySide6, Qt, Qt WebEngine and Chromium. Repository
documentation is not artifact evidence, so a `licenses/` directory is staged into
the installed application (Windows: `<install dir>\licenses\`; Linux AppImage:
`usr/bin/deepplant-editor/licenses/`). It carries DeepPlant's own licence, the
third-party notice index, the project-authored compliance documents, the
corresponding-source record, the Qt / Qt WebEngine licence texts, and the Chromium
third-party notice set matched to the exact redistributed Qt version.

The Qt texts come from the exact Qt source tag the PySide6 wheels were built from
and are pinned by immutable URL and SHA-256 in
[`packaging/licenses.toml`](../../../packaging/licenses.toml) - the PySide6 wheels
themselves ship **no** licence files, which is why the material is staged from
upstream at build time. `tests/test_packaging_licenses.py` protects that contract,
and `verify` fails if any required notice file is missing or empty in the built
artifact.

### Chromium third-party notices

Qt WebEngine compiles Chromium into `Qt6WebEngineCore`, and Qt states that
distributing it requires complying with the Chromium licences as well. Qt
*generates* that notice set during its own build with Chromium's
`tools/licenses/licenses.py credits`, driven by `qtwebengine/cmake/QtGnCredits.cmake`
for the GN target `:QtWebEngineCore`; it is not published as a single immutable
release file.

`tools/chromium_notices.py` turns the published exact-version result into a
deterministic packaging input:

```text
generate   fetch the pinned publication + every component page it links to,
           write the notice bundle (committed, shipped in licenses/)
check      fetch the pinned publication, verify its SHA-256, and fail unless the
           shipped bundle enumerates *every* component it lists, with notice text
```

`packaging/licenses.toml` declares the pinned publication
(`[chromium]`: versioned URL, SHA-256, engine version, generator, component count)
and the bundle to ship. The `licenses` phase runs the completeness check, and
artifact verification re-checks the shipped bundle offline (presence, provenance
markers, component count, notice text present). A file of links cannot pass.
`tests/test_chromium_notices.py` covers the parser, the completeness failures, and
that the shipped bundle is real notice material.

Chrome's `chrome://credits` page is not a substitute: Qt WebEngine does not
implement it and the redistributed PySide6 resources contain no credits payload,
so the notices are shipped as a plain-text file instead. The corresponding-source
mechanism is a three-year distributor-controlled written offer recorded in
`licenses/CORRESPONDING-SOURCE.md`; every artifact also carries generated
`licenses/BUILD-IDENTITY.md` with its DeepPlant version and immutable source revision
so a request is tied to the received build.

### Supported Linux baseline

```text
bundled in the artifact   Python, DeepPlant, FastAPI/Uvicorn, PySide6, Qt,
                          Qt WebEngine/Chromium, the production SPA, the canonical
                          DeepPlant symbols, the compliance payload
provided by the host OS   the kernel, the display/session environment, glibc and
                          standard platform libraries, the X11/Wayland and
                          graphics/audio/font/NSS libraries a normal desktop
                          already provides, FUSE (or `--appimage-extract-and-run`)
                          to mount the AppImage
```

"Self-contained" means the user needs **no** separately installed Python, Qt,
webview/Chromium runtime, Node.js, package manager or source checkout. It does
**not** mean the binary is statically linked with zero Linux system libraries: a
Qt/PyInstaller/AppImage application legitimately depends on the ordinary Linux
graphics/userspace stack. The Linux job installs those host libraries
(`libnss3`, `libxkbcommon`, `libgl1`, …) because they are what a real desktop
provides, not because they are "CI only"; `xvfb`, `xdotool`, `openbox` and
`x11-utils` are the CI harness for the virtual display and scripted input.

The canonical, machine-readable statement of that host half is
[`packaging/linux-runtime-baseline.toml`](../../../packaging/linux-runtime-baseline.toml):
it declares, **by SONAME**, every host library the packaged application may resolve
(currently 77 entries - glibc and the compiler runtime, X11/xcb/keyboard, OpenGL/
EGL/GBM, fonts, NSS/Kerberos, D-Bus/systemd, compression, and the few GLib/PNG/ALSA
helpers Qt and Chromium use). The audit (below) fails on an undeclared host
library, so the file is the reviewable contract and it must stay in step with the
job's `apt-get install` list. Because the baseline is what makes the job
reproducible, the Linux packaging job pins its runner image (`ubuntu-24.04`)
instead of tracking `ubuntu-latest`.

### Linux dynamic-dependency audit

`verify` runs `ldd` over the launcher itself (`deepplant-editor`) and the packaged
`QtWebEngineProcess`, `libQt6WebEngineCore` and Qt platform plugin (`libqxcb.so`),
and classifies every resolved dependency as bundled (inside the application tree),
host, checkout, or uv-environment. The build **fails** when:

- a required audited target is missing from the artifact (the audit can only prove
  what it actually inspected);
- a dependency is `not found`;
- any dependency resolves into the repository checkout or the uv environment - the
  mixed-host-Qt / accidental-checkout failure mode this repository hit before;
- a Qt library resolves outside the bundle;
- a host library is resolved that `packaging/linux-runtime-baseline.toml` does not
  declare. A genuinely new host dependency therefore arrives as a CI failure that a
  maintainer reviews and then adds to the baseline deliberately; CI never rewrites
  the baseline.

Declared-but-unused baseline entries are reported (not fatal), which is how
platform variation between images shows up for review. The full per-target
inventory - every bundled and host library per audited binary, plus the resolved
path of each host library - is written to
`build/editor-package/verify/dependency-inventory.json` and uploaded with the
`editor-package-linux-desktop-evidence` artifact, so counts alone are never the
evidence. `tests/test_linux_runtime_baseline.py` covers the parser, the
classifier, the baseline comparison, and every failure listed above with
synthetic `ldd` output; the native job remains the system evidence.

The analysis is deliberately run with `LD_LIBRARY_PATH`, `LD_PRELOAD` and
`LD_AUDIT` removed from the environment. `ldd` searches `LD_LIBRARY_PATH` *before*
an object's own `DT_RUNPATH`, so an ambient value (common in developer shells that
source a platform SDK or a virtual environment) would make the audit report the
build host's libraries instead of the artifact's own contract - and on a runner
that happened to set one, it could mask a real host dependency. Removing them
makes the inventory a property of the artifact and the pinned baseline image, so
the same AppImage produces the same result on any machine; a difference that
remains (for example a host library pulled in transitively by a different
distribution's system libraries) is a real review signal, not an environment
artefact.

### Exact-origin webview policy

The embedded view is limited to the **exact origin** of the running
`EditorServer` (`scheme://host:port`), plus the internal `data:`/`blob:`/`about:`/
`qrc:` schemes the SPA and Qt use. A different loopback port, `localhost` versus
`127.0.0.1`, an external HTTPS site and `file:` are all refused, and pop-ups are
refused. When another model is opened the server is replaced - possibly on a
different ephemeral port - and the permitted origin moves to the new one. This is
a webview host policy, not authentication: the loopback server stays single-user
and unauthenticated, and no tokens, sessions, CORS or TLS are introduced. The pure
policy is `deepplant.editor.desktop.is_allowed_navigation`, covered by
`tests/test_editor_desktop.py`.

On Linux the packaging job additionally launches the packaged application with
**no** model argument on a virtual display (Xvfb) under a session window manager
(openbox) and discovers the real X11 window with `xdotool`, proving the graphical
product exists outside the application's own report. It then requests an ordinary
session close - the EWMH `_NET_CLOSE_WINDOW` request (`wmctrl -c`) and the
standard `alt+F4` gesture delivered through the window manager - and **fails the
job** if the process is still alive. `xdotool windowclose` is deliberately not
used: it destroys the X window out of band and leaves the client running, which is
neither a user action nor a session close request. A window that disappears while
the process lingers is a failure, not a note.

### Browser E2E boundary

`apps/editor/e2e/support/editor-server.ts` drives only the developer/browser host
(`uv run deepplant ui <path> --port 0`) over the production build, so the existing
Playwright specs verify the shared frontend unchanged. `DEEPLANT_EDITOR_PROJECT`
may point the specs at a model outside the repository. The packaged desktop
product is verified by the self-check above.

## Reproducing a build locally

```bash
uv sync --group package --group desktop
cd apps/editor && pnpm install --frozen-lockfile && cd ../..
uv run --group package --group desktop python tools/package_editor.py all
```

On Linux, put `appimagetool` on `PATH` (or set `APPIMAGETOOL`); set
`APPIMAGE_RUNTIME` to pin the AppImage runtime embedded into the artifact instead
of letting `appimagetool` fetch its own default. On Windows, install Inno Setup 6
(or set `ISCC`). `python tools/packaging_toolchain.py show` prints the versions
and digests CI pins, and `... export` exposes them as environment variables.

The `licenses` phase downloads the pinned Qt / Qt WebEngine licence texts from
their immutable upstream URLs and verifies each SHA-256 before staging, so it
needs network access (or set `DEEPLANT_LICENSE_CACHE` to a directory of
digest-named blobs). Nothing mutable is ever fetched: the manifest forbids a
`latest`/`continuous`/`master`/`main` locator, and a digest mismatch fails the
build.

The Linux verification needs a display; without a desktop session use a virtual
one (`Xvfb`). If the build machine has its own Qt 6 runtime installed, the freeze
still produces a self-consistent bundle: it prefers PySide6's own Qt libraries
during dependency analysis.

For ordinary frontend/backend iteration you never need to build an installer:
`make frontend-build` plus `uv run deepplant ui <path>` still works, and now also
works from any working directory.

## Debugging a package failure

| Symptom | Where to look |
|---|---|
| SPA missing from the artifact | the `stage` phase output and `build/editor-package/spa/index.html` |
| Missing module at artifact runtime | the freeze log; add a PyInstaller hidden import or `--collect-*` option in `tools/package_editor.py` |
| `undefined symbol: … version Qt_6_PRIVATE_API` | two Qt versions in the bundle; check that the freeze ran with `qt_build_environment()` so PySide6's own Qt libraries win |
| `could not connect to display` / `no Qt platform plugin could be initialized` | the verification has no display, or the Qt X11 libraries are missing (CI installs both) |
| `the packaged application carries no Qt WebEngine …` | the frozen bundle is incomplete; check that the PyInstaller Qt hooks ran (`QT_HIDDEN_IMPORTS`) |
| Desktop self-check reports a failed check | the report names the failing checks; the launcher's own stdout/stderr is echoed as `app:`/`app!:` lines |
| Installer build fails | the `ISCC` command echoed by the driver; compile the `.iss` manually with the same `/D` defines |
| AppImage build fails | rerun `appimagetool` on `build/editor-package/deepplant-editor.AppDir` directly |

Always verify the **artifact**, not the intermediate tree: a successful fix is
one where `verify` passes with the checkout SPA moved aside.

## Related

- [research/editor-desktop-host.md](../research/editor-desktop-host.md)
  — the desktop-host candidate comparison, selection, and measured evidence.
- [research/standalone-editor-distribution.md](../research/standalone-editor-distribution.md)
  — the distribution-foundation candidate comparison and selection.
- [quality.md](quality.md) — which gates exist and what each must prove.
- [architecture/index.md](../architecture/index.md) — where the editor
  application boundary sits.
- [frontend/testing.md](../frontend/testing.md) — the browser E2E layer this
  workflow uses for the shared frontend.
