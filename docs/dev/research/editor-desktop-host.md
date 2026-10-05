---
type: design-evidence
status: active
canonical_for:
  - editor-desktop-host-evidence
read_when:
  - packaging-change
  - desktop-host-change
  - editor-release-work
update_when:
  - desktop-host-technology-change
  - packaging-tool-evidence-change
depends_on:
  - docs/dev/research/standalone-editor-distribution.md
  - docs/dev/architecture/index.md
  - docs/dev/frontend/index.md
decision: []
evidence:
  - docs/dev/research/standalone-editor-distribution.md
superseded_by: null
---

# Editor Desktop Host

> **Question investigated:** which native desktop host technology should turn the
> already-packaged DeepPlant Editor into a real graphical desktop application
> while keeping the *same* `apps/editor/` Vue SPA, the same FastAPI/Uvicorn
> application boundary, and an independent DeepPlant Core?

- **Status:** evidence, canonical for Issue #93 (the second and final
  implementation slice of #85). Resulting practice:
  [workflow/packaging.md](../workflow/packaging.md). The distribution-foundation
  evidence remains in
  [standalone-editor-distribution.md](standalone-editor-distribution.md).
- **Inspection scope and date:** repository `main` at
  `532ce03c3df57bbf1943485ba9b9f8ea5c3f52cd` (the #92 merge); the real
  `EditorApplication` + FastAPI/Uvicorn transport + production SPA build; Python
  3.12.13; PyInstaller 6.22.3; PySide6 6.11.2; appimagetool 1.9.1 and the pinned
  AppImage type-2 runtime. Upstream documentation of Qt/Qt WebEngine, Qt for
  Python, pywebview, and Tauri was read at that date. Evidence gathered
  **2026-10-04**.
- **Conclusions:**
  1. **PySide6 + Qt WebEngine is selected.** It is the only candidate in this
     comparison that ships its own webview engine inside the artifact, so the
     packaged Editor needs no separately installed system webview on either
     supported platform.
  2. `pywebview` was rejected for this requirement: its Windows default needs the
     Microsoft WebView2 Runtime, and on Linux it requires either Qt or
     GTK/WebKitGTK from the system, so it cannot make the AppImage
     self-contained by itself.
  3. `Tauri + Python sidecar` was rejected: it preserves the Vue SPA, but adds a
     Rust toolchain, a second process/runtime boundary, and the same platform
     webview dependencies (`WebKitGTK` on Linux, WebView2 on Windows) that Qt
     WebEngine already solves inside one Python-native stack.
  4. Electron was **not** added to the matrix: it would duplicate the Python
     runtime and the SPA's own bundler without changing any deciding constraint.
  5. The pre-existing packaging foundation (PyInstaller onedir, Inno Setup,
     AppImage, `packaging/toolchain.toml`, pinned toolchain, dependency split) is
     preserved; only the frozen bundle and the two artifact shims changed.

## 1. What the product requires

The delivered #92 artifact behaved like a packaged CLI/server launcher: it
started Uvicorn, printed a loopback URL, and opened the user's own browser.
Issue #93 requires a normal graphical application:

```text
launch DeepPlant Editor
        ↓
native desktop window
        ↓
embedded webview
        ↓
same Vue Engineering Editor
        ↓
DeepPlant application/API
        ↓
DeepPlant Core
```

with normal use requiring no terminal, no external browser, no separately
installed Python/Node/pnpm/uv/pip/compiler, and no source checkout.

Two constraints dominate the technology choice:

1. **One engineering frontend.** `apps/editor/` stays the only frontend. The host
   embeds its production build; no engineering UI may be re-implemented natively.
2. **Self-contained artifacts.** Windows and Linux must both work without asking
   the user to install a webview runtime.

## 2. Candidates evaluated against the real application

### Candidate A - PySide6 + Qt WebEngine (selected)

```text
QApplication
→ QMainWindow
→ QWebEngineView
→ existing http://127.0.0.1:<port>/
→ existing Vue SPA
```

Measured on the real application:

- **PyInstaller support:** works. PySide6 lazy imports are declared as hidden
  imports, and the PyInstaller Qt hooks then collect the Qt WebEngine helper
  process, resource packs, ICU data, and locales automatically.
- **Bundled WebEngine resources (verified in the frozen tree):**
  `QtWebEngineProcess`, 57 `*.pak` resource files, a `qtwebengine_locales`
  directory containing 53 locale packs, and `icudtl.dat`.
- **Frozen size:** the `deepplant-editor` onedir tree is **1,012,455,511 bytes**
  (~1.01 GB). The AppImage is **231,950,840 bytes** (~232 MB) after squashfs
  compression.
- **Artifact size change:** the #92 browser-hosted AppImage was
  **21,801,464 bytes**. The desktop artifact is therefore ~10.6x larger. That is
  the direct, honest cost of embedding a Chromium-based webview engine, and it is
  accepted deliberately rather than optimized before correctness.
- **Process lifecycle:** Qt WebEngine is multiprocess. The host owns the
  application window and the loopback server; Qt owns `QtWebEngineProcess`. When
  the main window closes, the host stops the server first and then lets Qt shut
  its own helpers down. No process-killing logic is used, and the successful close
  path returns through the ordinary Python/Qt teardown rather than force-exiting
  the process (see the review hardening section below).
- **Loopback transport:** unchanged. The host starts the *same* `EditorServer` on
  `127.0.0.1`, port `0`.
- **Build-host hazard found and fixed:** PyInstaller resolves each collected
  library's dependencies through the *build* host. A build host with its own Qt 6
  installed produced a bundle that mixed two Qt versions and failed at import
  with an unresolved Qt *private* symbol. The freeze now prefers PySide6's own Qt
  library directory during analysis, so the collected Qt comes from one place on
  any host.
- **Linux runtime requirements:** Qt WebEngine/Chromium needs the ordinary Linux
  desktop graphics/session libraries (X11/Wayland, GL, NSS, fontconfig, xkbcommon,
  …) that a normal desktop already provides. Those are the *host* half of the
  supported baseline: they are not bundled into the artifact, and the CI job
  installs them to emulate a real desktop session. By contrast the Python, Qt and
  Qt WebEngine/Chromium runtimes are bundled, so the end user needs no separately
  installed Python, Qt, webview or browser. The boundary is stated in
  [workflow/packaging.md](../workflow/packaging.md) ("Supported Linux baseline").

### Candidate B - pywebview (rejected)

- **Windows backend:** `pythonnet` plus the **Microsoft WebView2 Runtime** for
  current Chromium ("To use with the latest Chromium you need WebView2 Runtime").
- **Linux backend:** an explicit choice between **Qt** (`pywebview[qt]`,
  PyQt6/PySide6) and **GTK** (`PyGObject` + `WebKit2` 2.22+).
- Therefore pywebview does not by itself make the artifact self-contained: on
  Linux it either requires a system GTK/WebKitGTK stack or pulls in the same Qt
  stack Qt WebEngine already uses, and on Windows it depends on a
  Microsoft-distributed runtime.

### Candidate C - Tauri + Python sidecar (rejected)

- Tauri v2 requires the **Rust** toolchain (and Node.js) and, on Linux,
  `libwebkit2gtk-4.1-dev`; on Windows it uses the system WebView2.
- It preserves the SPA, but it adds a second language toolchain, a second build
  system, and a sidecar lifecycle for a Python application, while still
  depending on a platform webview that is not bundled by DeepPlant.

### Candidate D - Electron (not evaluated)

Electron would add a second runtime next to Python and the SPA bundler without
changing any deciding constraint, so it was deliberately not added to the matrix.

## 3. Comparison

| Criterion | PySide6 + Qt WebEngine | pywebview | Tauri + Python sidecar |
|---|---|---|---|
| Shared Vue SPA | yes - embeds the `apps/editor/` build unchanged | yes | yes |
| Native desktop window | yes (`QMainWindow`) | yes | yes |
| Native Open dialog | yes (`QFileDialog.getOpenFileName`, native by default) | yes (backend dialog) | yes (plugin) |
| Windows packaging | Inno Setup unchanged; windowed `.exe` | Inno Setup; needs WebView2 on the target | WiX/NSIS; needs WebView2 |
| Linux AppImage packaging | unchanged `appimagetool` flow; `Terminal=false` | needs Qt or GTK/WebKitGTK from the system | needs `libwebkit2gtk-4.1` |
| Self-contained end-user runtime | **yes** (engine ships in the artifact) | no (platform webview required) | no (platform webview required) |
| Python/Core compatibility | native (same interpreter) | native | sidecar process boundary |
| FastAPI/Uvicorn compatibility | unchanged loopback server | unchanged | unchanged, but across a process boundary |
| PyInstaller compatibility | yes (hooks collect the WebEngine runtime) | yes, but the webview runtime is not bundled | n/a (Rust packaging) |
| CI testability | self-check via `QWebEnginePage.runJavaScript` on the real page | would need the platform webview in CI | WebDriver, plus the sidecar |
| GUI automation | Qt's own JS engine; real X11 window discoverable with `xdotool` | backend-dependent | WebDriver |
| Startup time | Qt WebEngine initialisation cost (first launch only) | host-webview dependent | host-webview dependent |
| Artifact size | ~232 MB AppImage / ~1.01 GB frozen tree | smaller, but not self-contained | smaller, but not self-contained |
| Platform dependencies | none on the end user's machine | WebView2 (Windows), Qt or WebKitGTK (Linux) | WebView2, WebKitGTK |
| Licensing | `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only` (PySide6); Qt WebEngine adds the Chromium third-party set | BSD-3-Clause; backends bring their own licences | Apache-2.0/MIT plus platform webviews |
| Redistribution obligations | LGPL/Qt notice obligations plus the Qt WebEngine/Chromium third-party set | backend-dependent | platform webview terms |
| Process lifecycle | host owns window + server; Qt owns its helper processes | host-webview dependent | host owns everything, sidecar separate |
| Future web compatibility | same API, same SPA; the browser host is unchanged | same | same |
| Maintenance complexity | one Python stack | small library, backend variability | Rust + Node + Python sidecar |

## 4. Why PySide6 + Qt WebEngine won

It is the smallest architecture that satisfies the actual requirement
*self-contained graphical desktop application on Windows and Linux*:

- it embeds the **existing** SPA unchanged, and the host never parses YAML or
  holds engineering semantics;
- it keeps the **existing** `EditorServer` loopback boundary, so the transport
  stays the same one a future web deployment would use;
- it needs **no** webview runtime on the end user's machine, which is the
  requirement `pywebview` and `Tauri` leave to the platform;
- it adds exactly one runtime stack (Python + Qt) instead of adding Rust and a
  sidecar to a Python application.

The accepted cost is artifact size, which is caused by the correct embedded
engine and is reported honestly in section 2.

## 5. Measured DeepPlant evidence

```text
source-mode host (PySide6 + Qt WebEngine, Linux, Xvfb)
  window visible .................... true
  validation status ................. "Valid"
  ProcessSteps rendered ............. 7
  ProcessStreams rendered ........... 7
  PS-pump selected .................. Inspector heading "PS-pump"
  Inspector fields .................. Function=pumping, ID=PS-pump,
                                      Name="Feed Pumping", Ports="suction, discharge"
  served document is the built SPA .. true (not /src/main.ts)
  window closed / server stopped .... true / true
  loopback port released ............ true

frozen onedir application (same checks) ................. pass
AppImage 0.1.0 (extracted AppRun, no model / with model)  pass / pass
```

The AppImage produced during this investigation was
`deepplant-editor-0.1.0-linux-x86_64.AppImage`, 231,950,840 bytes,
SHA-256 `8ffebf9e6351dc924a67497a1ccd3bd5380a9405a97cafc6cc3ba36da7b0616b`.

The checks are produced by the application's own `--self-check` mode, which is
the narrow, documented test hook described in
[workflow/packaging.md](../workflow/packaging.md): the real host loads the real
application, reads the real rendered page through Qt's JavaScript engine, then
closes the window through the ordinary `closeEvent` and records whether the owned
server and loopback socket went away.

## 6. Licensing and provenance

Verified from current upstream sources at the inspection date; see
[THIRD_PARTY_NOTICES.md](../../../THIRD_PARTY_NOTICES.md) for the recorded
obligations.

- **PySide6 / Qt for Python** is offered under `LGPL-3.0-only OR GPL-2.0-only OR
  GPL-3.0-only` (PyPI project metadata) and additionally under a commercial
  licence; Qt describes LGPLv3 as its primary open-source licence, with some
  parts available only under GPL.
- **Qt WebEngine** ships Chromium as part of `QtWebEngineCore`: "when
  distributing Qt WebEngine, users need to comply to both the licenses of the Qt
  WebEngine part as developed under the Qt Project, as well as the licenses that
  are part of Chromium." The Qt parts are available under commercial, LGPLv3,
  GPLv3, or GPLv2; the Chromium parts carry a large third-party set whose most
  restrictive licence is LGPL 2.1.
- **Redistributed inside the DeepPlant artifacts:** the PySide6 wheels' Qt
  libraries, the Qt WebEngine Core library and its `QtWebEngineProcess` helper,
  Chromium resource/ICU/locale data, and the Python runtime - all unmodified
  upstream binaries. The onedir layout keeps the Qt libraries as separate,
  replaceable files.
- **Build-time only:** `appimagetool`, PyInstaller, and Inno Setup's compiler.
  The AppImage type-2 runtime is build-time *and* redistributed, as recorded in
  [THIRD_PARTY_NOTICES.md](../../../THIRD_PARTY_NOTICES.md).

## 7. Consequences for the product shape

- The standalone application is a **desktop host**, not a second frontend and not
  the general DeepPlant CLI: `deepplant` (Python API/CLI), `deepplant ui`
  (developer/browser host) and `deepplant-editor` (native desktop host) remain
  distinct surfaces.
- The developer/browser host keeps its documented behaviour: it serves the SPA
  and prints the loopback URL; it never opens a browser automatically.
- The desktop host never opens an external browser, and it refuses navigation
  outside the **exact origin** of its own loopback server (`scheme://host:port`) -
  a different loopback port, `localhost` versus `127.0.0.1`, an external site, and
  `file:` are all refused; pop-ups are refused too.
- The Python dependency split is explicit: base (Core/CLI), `editor`
  (FastAPI/Uvicorn), `desktop` (transport + PySide6). None of the desktop
  dependencies reach DeepPlant Core.

## 8. Review hardening (Issue #93 review fix)

A focused review of the first #93 implementation found four evidence/compliance
gaps and one quality gap. The accepted architecture was **not** re-evaluated; only
the following were hardened:

1. **Clean shutdown became a real invariant.** `EditorServer.stop()` now returns
   the *measured* thread state and keeps the thread reference after a timeout, so
   `EditorServer.running` stays truthful and a later `stop()` can still join the
   owned thread. `_DesktopEditor` drops the owned server only when `stop()` reports
   it stopped. `serverStopped` in the packaged self-check is derived from the live
   `EditorServer.running`, never from `editor.server is None`.
2. **The successful desktop lifecycle no longer uses `os._exit()`.** The event loop
   returns, the webview is stopped/detached and its deferred deletion is flushed,
   and `run_host()` returns normally so the interpreter exits on its own.
   `os._exit(1)` remains only in the fatal error handler (bounded emergency
   fallback), and the ordinary close path does not depend on it.
3. **Linux window lifecycle is a hard CI gate.** The packaging job fails if the
   packaged process is still alive after the window is closed through a supported
   user path; forced cleanup runs only after the failure has been recorded.
4. **Redistribution compliance payload shipped in the artifacts.** The PySide6
   wheels ship no licence files, so the version-matched Qt / Qt WebEngine licence
   texts are pinned in `packaging/licenses.toml` (immutable URLs + SHA-256) and
   staged into a `licenses/` directory inside the installed application. The
   packaged verification fails if any required notice is missing.
5. **`desktop_qt.py` is strictly type-checked.** The native packaging jobs run
   `pyright --project pyrightconfig.desktop.json`, which mirrors the canonical
   strict settings but keeps the Qt module in scope, so the fast gate still needs
   no PySide6 and the Qt module is not silenced with blanket ignores.

## 9. Second review fix: Chromium notice evidence and the Linux runtime baseline

The first review round left the Chromium third-party notice set explicitly
unresolved and let the Linux dependency audit treat any non-Qt library as an
allowed host dependency. Both were closed in a second, evidence-based fix.

**Chromium / Qt WebEngine notices.** Qt WebEngine 6.11.2 is based on Chromium
140.0.7339.264 (the `CHROMIUM_VERSION` file at tag `v6.11.2`, commit
`a33fa2a897e5ee58e385b3f88dc247d99fca56db`). Qt *generates* the Chromium
third-party notice set with Chromium's own `tools/licenses/licenses.py credits`,
driven by `qtwebengine/cmake/QtGnCredits.cmake` for the GN target
`:QtWebEngineCore`, and publishes the generated result as the
`qtwebengine-licensing` documentation for the exact release; it is not published
as a single immutable release file. `tools/chromium_notices.py` obtains that
exact-version result and writes a deterministic notice bundle that is committed
and shipped, and the packaging job re-fetches the pinned publication (SHA-256
checked) and fails unless the bundle enumerates every component upstream lists
with notice text. The previously claimed `about:credits` route was **disproved**
for this distribution: Qt WebEngine does not implement Chrome's credits page and
the redistributed PySide6 6.11.2 `.pak` resources contain no credits payload, so
shipping real notice text is the mechanism. Corresponding source is handled by
`licenses/CORRESPONDING-SOURCE.md`, which relies on the LGPL v3 section 4(d)(1)
shared-library option this onedir distribution satisfies and additionally makes a
three-year written offer (LGPL v2.1 section 6(c)) for the LGPL-2.1 Chromium parts.

**Linux runtime baseline.** The audit now inspects `deepplant-editor` itself
alongside `QtWebEngineProcess`, `libQt6WebEngineCore.so*` and `libqxcb.so*`; every
host library must be declared by SONAME in
`packaging/linux-runtime-baseline.toml`, and an undeclared one fails the build.
The full per-target inventory is uploaded as
`dependency-inventory.json` with the Linux desktop evidence, and the Linux job
pins `ubuntu-24.04` so the baseline is reproducible rather than floating.
