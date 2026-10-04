---
type: design-evidence
status: active
canonical_for:
  - standalone-editor-distribution-evidence
read_when:
  - packaging-change
  - distribution-change
  - editor-release-work
update_when:
  - distribution-architecture-change
  - packaging-tool-evidence-change
depends_on:
  - docs/dev/planning/product.md
  - docs/dev/architecture/index.md
  - docs/dev/frontend/index.md
  - docs/contracts/cli.md
decision: []
evidence: []
superseded_by: null
---

# Standalone Editor Distribution

> **Question investigated:** how can the existing read-only DeepPlant Engineering
> Editor become a genuinely installable Windows and Linux application, without
> giving up the local browser-based SPA, the FastAPI/Uvicorn boundary, or the
> independence of DeepPlant Core?

- **Status:** evidence, current for Issue #85. The resulting practice is
  canonical in [workflow/packaging.md](../workflow/packaging.md).
- **Inspection scope and date:** repository `main` at
  `719067b9c881435d15398987d272b2338560ba88`; the current runtime
  (Python 3.12.13, FastAPI 0.142.2, Uvicorn 0.54.0, Typer 0.27.2, Pydantic
  2.13.5, PyYAML 6.0.3, the built Vue SPA, the canonical `basic` symbol pack);
  and the official upstream documentation of PyInstaller, Nuitka, Briefcase,
  Inno Setup, and AppImage `appimagetool`. Evidence gathered **2026-10-04**.
- **Conclusions:**
  1. The Editor is a *local browser application*, so the smallest credible
     distribution keeps that shape: a frozen Python application that serves the
     unchanged SPA over loopback and opens the user's own browser.
  2. **PyInstaller onedir + Inno Setup (Windows) + AppImage (Linux)** is the
     selected stack. It satisfied both #85 artifact requirements with the lowest
     measured build cost and the least new runtime surface.
  3. **Nuitka** is a legitimate integrated alternative (free
     `--windows-create-installer` and `--linux-create-installer`) but was not
     selected: measured build cost is far higher, and its runtime behaviour for
     this application was not verified within the audit window.
  4. **Briefcase** was rejected for this slice on documented upstream evidence
     plus DeepPlant's own dependency profile.
  5. No desktop shell, and no second runtime, is justified today: the product
     direction is already a locally launched browser SPA.
  6. The frontend must become an *application-owned resource*. Package-relative
     `importlib.resources` resolution — the mechanism the canonical symbol pack
     already uses — removes the checkout and working-directory coupling without
     naming any packaging tool in the application or the Core.

## 1. Current runtime inventory (before the change)

```text
command                     what it actually did
deepplant ui <path>         load_editor_application(path)
                            -> resolve_assets_dir(None)
                               -> Path.cwd() / "apps" / "editor" / "dist"
                            -> FastAPI app via create_editor_api()
                            -> pre-bound 127.0.0.1 socket + uvicorn.Server.run()
                            -> SPA and canonical symbols served over loopback
```

| Concern | Observed state before #85 |
|---|---|
| Python runtime | 3.12.13, `requires-python >= 3.12`, managed with `uv` |
| Base Python dependencies | `fastapi`, `uvicorn`, `pydantic`, `pyyaml`, `typer` — **all mandatory** |
| CLI import graph | `import deepplant.__main__` imported `fastapi` **and** `uvicorn` at import time; verified by running the import and inspecting `sys.modules` |
| Built frontend assets | `apps/editor/dist` (Vite output, not committed) |
| Frontend resolution | `Path.cwd() / "apps" / "editor" / "dist"` — a **working-directory** dependency |
| Canonical SVG symbols | `src/deepplant/assets/symbols/process/basic/*.svg`, already resolved through `importlib.resources`; already verified inside the wheel by `tools/verify_wheel_contents.py` |
| Filesystem paths | no other absolute or checkout path in the runtime |
| Process/server lifecycle | single process; binds the loopback socket itself, then runs Uvicorn on that socket |
| Loopback networking | `DEFAULT_HOST = 127.0.0.1`, no `0.0.0.0` option |
| Browser launch behaviour | none; the URL was only printed |
| Windows behaviour | untested; nothing Windows-specific existed |
| Linux behaviour | developed on Linux only |
| CI build environment | `ubuntu-latest` only: fast `check` + source-run Playwright E2E |
| Packaging | none for the application; only a wheel-content check for Core symbol data |

### Checkout dependencies found

1. **Frontend assets** — `apps/editor/dist`, resolved from the current working
   directory. The source browser E2E even documented starting the Python process
   from the repository root *because of* this.
2. **Editor transport being a base dependency** — an installation that only
   wanted the semantic Core still pulled in FastAPI and Uvicorn.
3. **CLI-level transport import** — `deepplant version` and `deepplant validate`
   imported the editor transport infrastructure they never use.

No other checkout coupling was found: the semantic model, YAML boundary,
renderer, and symbol resources were already location-independent.

## 2. Candidate stacks

Each candidate is evaluated as a **complete end-user distribution stack**, not as
a freezer alone:

| Candidate | Windows user artifact | Linux user artifact |
|---|---|---|
| **A. PyInstaller stack** | PyInstaller onedir + Inno Setup installer | PyInstaller onedir + `appimagetool` AppImage |
| **B. Nuitka** | Nuitka standalone + `--windows-create-installer` (NSIS) | Nuitka standalone + `--linux-create-installer` (AppImage) |
| **C. Briefcase** | Briefcase Windows MSI (WiX) | Briefcase Linux native packages / AppImage |
| **D. Webview shell** (PyInstaller or Nuitka + a GUI webview) | desktop window | desktop window |
| **E. Tauri/Electron** | desktop runtime bundle | desktop runtime bundle |

A bare ZIP around a frozen directory was **not** considered equivalent to #85's
"normal installer or equivalent installable application package".

## 3. Selection criteria

Windows support; Linux support; self-contained runtime; reuse of the existing
Python Core, `EditorApplication`, FastAPI/Uvicorn transport and the unchanged
Vue SPA; resource bundling; installer/package support; native CI buildability;
licensing; artifact size; startup time; build complexity; process lifecycle;
debuggability; platform-specific complexity; developer workflow; upgrade path;
and future ability to separate Core and applications.

## 4. Measurements

All numbers below come from prototypes run against the **actual DeepPlant
application** on Ubuntu 26.04, x86-64, 12 CPUs, Python 3.12.13.

| Measurement | A. PyInstaller stack | B. Nuitka | C. Briefcase |
|---|---|---|---|
| Frozen tree size | 49 MB (onedir) | not reached | not reached |
| Freeze build time | well under a minute | **> 28 min, still compiling, aborted** | not reached |
| Compiled modules | bytecode only | 768 modules → 772 C translation units | n/a |
| Intermediate build tree | 29 MB | 491 MB | n/a |
| Extra build tooling | none for the freeze | C compiler (gcc), `patchelf` on Linux | Docker (Linux), WiX (Windows) |
| Linux artifact | **AppImage, 21,801,464 bytes** | not reached | documented as unreliable |
| Windows artifact | Inno Setup installer (CI) | NSIS installer (unverified) | MSI (unverified) |
| Startup to announced URL | **0.72 s / 0.77 s** (extracted AppImage) | not reached | not reached |
| Runtime behaviour of this app | **verified end-to-end** | **not verified** | not verified |
| Licences | PyInstaller: GPLv2-or-later **with a bundling exception**; `appimagetool` MIT; Inno Setup free-to-use custom licence | Nuitka: **AGPL-3.0 with a runtime exception** (free tier); NSIS zlib/libpng | Briefcase BSD-3 |

The verified PyInstaller-stack run reported:

```text
artifact:  deepplant-editor-0.1.0-linux-x86_64.AppImage (21801464 bytes)
sha256:    dc759e9f…
checkout_spa_removed: true          <- apps/editor/dist was moved aside first
GET /:                200 (built SPA, no /src/main.ts)
/api/projection:      7 steps, 7 streams, valid
/api/symbols:         pump, vessel, heat_exchanger -> image/svg+xml
shutdown:             process terminated, installation removed, SPA restored
```

### Why Nuitka is not the selected tool (evidence, not prejudice)

Nuitka's free tier genuinely provides both artifact kinds directly
(`--windows-create-installer` → NSIS, `--linux-create-installer` → AppImage), and
its AGPL-3.0 licence is compatible with this AGPL-3.0-only project. That is a
real advantage: one fewer vendor, and it was verified from `--help-all` rather
than assumed.

It was not selected because of measured and unmeasured costs:

- it compiles the entire dependency graph to C — 768 modules, 772 C translation
  units, a 491 MB intermediate tree — because Typer pulls in Rich and Pygments;
- on a 12-core workstation it had not produced an artifact after ~28 minutes,
  whereas the whole PyInstaller stack (freeze, package, verify) completes in
  minutes. GitHub-hosted runners have far fewer cores, so this directly affects
  the native-CI buildability criterion;
- its runtime behaviour for *this* application (Pydantic v2 models, the FastAPI
  lifespan, `importlib.resources` over the frozen package tree) was never
  verified inside the audit window, and the C-compilation path is a much larger
  surface to debug than collecting bytecode;
- it needs a compiler toolchain on both platforms plus `patchelf` on Linux.

The compiler requirement by itself was explicitly **not** treated as a
disqualifier: #85 forbids toolchain requirements for *end users*, not for CI or
build machines.

### Why Briefcase is not the selected tool

- Its own current documentation says the Linux **AppImage** backend is
  "best effort" support, "strongly discourage[s]" AppImages for distribution,
  and states it is *incompatible with the use of binary wheels* while also
  fighting modern GUI frameworks over base-image age. DeepPlant's runtime is
  exactly that profile: `pydantic_core` and PyYAML ship compiled extension
  modules (`_pydantic_core…so`, `_yaml…so`) as binary wheels. Working around
  that requires `--no-binary` source builds, i.e. a Rust toolchain and
  development headers, for the *default* configuration.
- Its Linux **native package** backend requires Docker and an identified Linux
  vendor, and produces `.deb`/`.rpm`/`.pkg.tar.zst`: per-distribution artifacts
  rather than the single low-friction artifact #85 prefers.
- Adopting it would mean restructuring the repository into a Briefcase
  application layout, i.e. reshaping the project for the packaging tool. #85
  explicitly warns against reorganizing the package to satisfy the wording of
  the Issue.

### Why the webview/Tauri/Electron candidates are not selected

The product direction already describes the editor as a local-first,
browser-based SPA launched locally. A dedicated native shell would add a second
runtime (WebView2/WKWebView, Chromium, Node, or Rust), a second process model,
another application framework, and — for Electron/Tauri — a redistributed
browser engine with its own licence and size consequences, without adding a
capability the user asked for. Adding one "merely to make the product look more
desktop" is exactly what #85 forbids. Using the user's own browser also avoids
redistributing a browser runtime at all, which is a deliberate architectural
trade-off rather than a shortcoming.

## 5. Selected architecture

```text
deepplant-editor  (application entry point, PyInstaller-frozen)
        |
        |  bundled: CPython 3.12, FastAPI, Uvicorn, Pydantic, PyYAML, Typer,
        |           DeepPlant package, canonical SVG symbols, built Vue SPA
        v
loopback-only FastAPI/Uvicorn server on 127.0.0.1
        v
user's default browser  (auto-opened; --no-browser suppresses it)
```

| Aspect | Decision |
|---|---|
| Runtime shape | frozen Python application; one process; loopback server; user's own browser |
| Resource ownership | SPA staged into the bundle as `deepplant/editor/dist`, resolved by `importlib.resources` |
| Application entry point | `deepplant-editor` console script, frozen by `tools/editor_entry.py`; the developer `deepplant ui` command shares the same launch path |
| Browser/native-shell choice | user's browser, no shell |
| Windows package format | Inno Setup installer (`…-windows-x86_64-setup.exe`) |
| Linux package format | AppImage (`…-linux-x86_64.AppImage`) |
| Build entry point | `python tools/package_editor.py <phase>` (cross-platform, explicit phases) |

## 6. Why this is the smallest architecture that satisfies #85

- It reuses **everything already delivered**: `EditorApplication`, the
  FastAPI/Uvicorn transport, the DeepPlant projection, the canonical symbol
  pack, and the unchanged production Vue SPA. No editor implementation was
  duplicated and no framework was replaced.
- It adds exactly one runtime dependency (PyInstaller) and two build-time-only
  tools that ship nothing inside the artifact.
- It introduces no new process model: the frozen application is the same single
  process that already served the editor, so lifecycle, loopback binding and
  automation stay identical to the source path.
- It removes the need for a browser *runtime* to be redistributed at all.
- The alternative "one tool does both artifacts" option (Nuitka) was measured
  and found materially more expensive to build, which matters more for a
  cross-platform CI gate than vendor count.

## 7. Licence and provenance notes

| Component | Role | Licence | Redistributed in the artifact? |
|---|---|---|---|
| PyInstaller | freeze/bundle (build-time) | GPLv2-or-later **with an exception** that permits bundling and distributing applications under any licence, with no attribution requirement | its bootloader code is part of the frozen launcher |
| `appimagetool` | AppImage assembly (build-time) | MIT | no; only the AppImage runtime it adds is |
| Inno Setup | Windows installer compilation (build-time) | free-of-charge custom licence (commercial users are asked to purchase); source-available | no; the produced installer is the user artifact |
| CPython | language runtime | PSF-2.0 | yes (bundled interpreter) |
| FastAPI / Starlette / Uvicorn / Pydantic / PyYAML / Typer / Rich / Pygments / Click | application runtime dependencies | MIT / BSD-3 / Apache-2.0 family, all already recorded project dependencies | yes |
| Chromium / WebView2 / Qt / Tauri / Electron | desktop shell runtime | — | **no**: deliberately not adopted |

No new runtime dependency was added to the *installed Python package* by #85.
The DeepPlant project licence is unchanged (`AGPL-3.0-only`).

## 8. Known platform limitations

| Limitation | Status |
|---|---|
| The artifact is OS- **and** architecture-specific | by design: each platform builds on its own native CI runner |
| Linux AppImage needs the FUSE 2 runtime | documented user requirement; `--appimage-extract-and-run` is the documented no-FUSE fallback |
| A web browser must exist on the machine | documented OS-level dependency; the URL is always printed so any browser can be used |
| Windows installer is not code-signed | explicitly out of scope for #85; users see the standard unknown-publisher prompt |
| No automatic updates, tags, or GitHub Releases | explicitly out of scope (#88) |
| macOS unsupported | explicitly out of scope |
| The Editor is still read-only | unchanged product scope; this slice changed distribution, not features |
| Metadata is not a project format | the application still opens a single `plant.yaml`; `.deepplant`/project manifests are #89 |

## 9. Core boundary outcome

The Core boundary was already architecturally correct; #85 made it *true at the
dependency level* and verifiable:

```text
                DeepPlant Core
                     ^
        +------------+------------+
        |            |            |
       CLI        Editor    (future integrations)
```

- `deepplant.model`, `deepplant.io`, `deepplant.render`, and the canonical
  symbols import no application technology. Verified by a subprocess test that
  performs a real load/render and then asserts that `fastapi`, `uvicorn`,
  `starlette`, `PyInstaller`, `nuitka`, and `deepplant.editor.api` are absent
  from `sys.modules`.
- FastAPI and Uvicorn moved from mandatory base dependencies to an explicit
  `editor` extra (mirrored as a uv dependency group). `deepplant version` and
  `deepplant validate` no longer import the transport at all.
- Requesting the editor without the extra produces a concise, actionable message
  (which installation provides the extra) instead of an `ImportError` traceback.
- No `deepplant-core` distribution, no repository split, and no new `core/`
  package hierarchy was introduced: the dependency *direction* was the point,
  and the existing distribution preserves it.
