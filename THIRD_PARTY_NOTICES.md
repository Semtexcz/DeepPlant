# Third-party notices and provenance

This index records known non-original inputs and points to the detailed record
where one exists. It is not a complete inventory of every dependency's licence.
Contributors must disclose new material before it is accepted.

## DEXPI 2.0 fixtures

The synthetic XML fixtures under
[`tests/fixtures/dexpi/2.0.0/`](tests/fixtures/dexpi/2.0.0/) use DEXPI 2.0
class identifiers, enumeration literals, and XML envelope structure reported
under CC BY 4.0. The XML instances themselves were authored for DeepPlant.
The directory's [attribution record](tests/fixtures/dexpi/2.0.0/ATTRIBUTION.md)
identifies the upstream sources, licence, attribution, modifications, and
limitations. Verify any future reuse against the upstream terms; do not infer
that every DEXPI-associated work is covered by CC BY 4.0.

## DeepPlant-original assets

The packaged `basic` process SVG symbols are documented as DeepPlant-original,
non-normative fallback assets in
[`src/deepplant/assets/symbols/process/basic/README.md`](src/deepplant/assets/symbols/process/basic/README.md).
That record is the per-asset provenance source and does not claim standards
compliance.

The brand logo artwork in [`assets/brand/logo/`](assets/brand/logo/) is
project-authored. Its horizontal wordmark paths were generated from Inter Bold,
then converted to vector outlines; the SVGs have no runtime font dependency.
Inter is distributed under the SIL Open Font License 1.1. The [asset
record](assets/brand/logo/README.md) links the Inter project and licence and
states the variants and distribution terms.

## Engineering Editor frontend dependencies (Issue #75)

The local editor SPA under [`apps/editor/`](apps/editor/) is built with the
following direct dependencies. They are build/dev-time dependencies of the SPA;
the Python wheel does not bundle or redistribute any JavaScript, and the built
`apps/editor/dist` output is not committed.

| Dependency | Declared range | Licence | Why it is needed now |
|---|---|---|---|
| `vue` | `^3.5.43` | MIT | SPA foundation selected by the reuse-first frontend architecture (Issue #70). |
| `@vue-flow/core` | `^1.48.2` | MIT | Interactive canvas candidate selected by Issue #70; used only behind the DeepPlant projection/adapter boundary. |
| `vite` | `^8.3.2` | MIT | Frontend dev server and production bundler. |
| `typescript` | `~5.9.3` | Apache-2.0 | Strict TypeScript checking. Pinned to the 5.x line because `vue-tsc` does not support the TypeScript 7 package layout yet. |
| `vue-tsc` | `^3.3.12` | MIT | Type checking of `.vue` single-file components. |
| `vitest` | `^5.0.3` | MIT | Frontend unit tests for the adapter and the selection → Inspector mapping. |
| `@vitejs/plugin-vue` | `^6.0.9` | MIT | Vue SFC support for Vite. |
| `pnpm` | pinned `10.20.0` in `apps/editor/package.json` | MIT | Package manager; a build-time tool, not distributed or linked. |

Deliberately **not** added: Reka UI, Dockview, Monaco, ELK/elkjs, Pinia,
shadcn-vue, Tailwind, jsdom, or any third-party engineering symbol asset. The
engineering symbols remain the DeepPlant-original `basic` pack (see above),
served from the Python package. (A browser E2E framework was also deliberately not
added by #75; Issue #82 later added Playwright — see below.)

## Engineering Editor frontend lint tooling (Issue #80)

The canonical frontend lint gate (`apps/editor/eslint.config.js`, run by
`pnpm lint` / `make frontend-lint`) is built from the following direct
**dev-only** dependencies. Like the SPA dependencies above, they are build/dev
time only: the Python wheel bundles no JavaScript and `apps/editor/dist` is not
committed.

| Dependency | Declared range | Licence | Why it is needed now |
|---|---|---|---|
| `eslint` | `^10.12.0` | MIT | The lint engine; flat-config based, one of the four independent frontend gates. |
| `@eslint/js` | `^10.0.1` | MIT | ESLint's own recommended JavaScript correctness rules. |
| `typescript-eslint` | `^8.71.0` | MIT | TypeScript parser plus lint rules; enforces the explicit-`any` ban and unused-code checks. |
| `eslint-plugin-vue` | `^10.11.1` | MIT | Vue 3 SFC correctness rules (`flat/essential`); also brings the Vue parser. |
| `globals` | `^17.13.0` | MIT | Standard browser and node global definitions for the linted files. |

`eslint-plugin-vue` requires `vue-eslint-parser` (MIT) and
`@typescript-eslint/parser` (MIT, provided by `typescript-eslint`) as peers; they
are resolved transitively and are not separately declared.

Deliberately **not** added by Issue #80: Prettier (the gate enforces correctness,
not a second formatter). UnoCSS was selected as the canonical styling direction
(see [`docs/dev/frontend/styling.md`](docs/dev/frontend/styling.md)) but
deliberately not installed by #80, because an unused package must not be added
merely to record a decision; #81 integrated it (see below).

## Engineering Editor frontend styling and test tooling (Issue #81)

Issue #81 applied the #80 contract to the existing editor frontend. It added the
following direct **dev-only** dependencies. They are build/dev/integration-test
time only: the Python wheel bundles no JavaScript and `apps/editor/dist` is not
committed.

| Dependency | Declared range | Licence | Why it is needed now |
|---|---|---|---|
| `unocss` | `^66.10.5` | MIT | The canonical utility-first styling layer selected by the #80 frontend contract; generates only the utilities the editor uses. Configured in `apps/editor/uno.config.ts`. It also exposes the maintained official UnoCSS Vite integration as `unocss/vite`, wired into `apps/editor/vite.config.ts` (`UnoCSS()`). |
| `@vue/test-utils` | `^2.5.1` | MIT | The official Vue 3 component test utility; mounts `InspectorPanel.vue`, `ProcessNode.vue` and the Process/PFD workspace in the component and feature-integration suites. |
| `happy-dom` | `^20.14.5` | MIT | The single DOM environment for the component and feature-integration suites (`@vitest-environment happy-dom`). Chosen over `jsdom` as the one maintained DOM environment: it is actively maintained and its declared Node `>=20` engine range covers the pinned Node `>=22.12 <23`. |

`unocss` re-exports the official `@unocss/vite` plugin as `unocss/vite` and depends
on `@unocss/vite` transitively, so `@unocss/vite` is resolved through `unocss` and
is deliberately **not** declared as a separate direct dependency.

`happy-dom` is the only DOM environment added; `jsdom` was deliberately **not**
added. Cypress, Storybook and Testing Library were deliberately **not** added;
#82 later added Playwright and Chromium only (see below). No second utility
framework, no CSS reset package and no
component framework were added: the UnoCSS preset's only preflight output is its
own transform variables, so the minimal global reset stays explicit in
`apps/editor/src/styles.css`.

## Engineering Editor frontend browser E2E tooling (Issue #82)

Issue #82 added the real-browser system/browser verification layer for the
editor: Playwright driving Chromium against the real local `deepplant ui` CLI and
the production SPA build. It added the following direct **dev-only** dependencies.
Like the tooling above, they are build/dev/test time only: the Python wheel bundles
no JavaScript and `apps/editor/dist` is not committed.

| Dependency | Declared range | Licence | Why it is needed now |
|---|---|---|---|
| `@playwright/test` | `^1.63.0` | Apache-2.0 | The maintained browser automation and test runner used for the two critical-system E2E workflows. Chromium is the only browser configured; there is no browser matrix. |
| `@types/node` | `^22.20.0` | MIT | Dev-only Node API typings for the Node-executed frontend tooling and the Playwright E2E launch helper (`node:child_process`, `node:timers/promises`, `node:url`, `node:path`). They are confined to the Node/tooling TypeScript config (`apps/editor/tsconfig.node.json`, `types: ["node"]`); the browser application config (`apps/editor/tsconfig.json`) deliberately does **not** expose Node globals, so Node APIs are never available to the browser application. The range tracks the pinned `engines.node` `>=22.12.0 <23` and cannot cross into Node 23+. Already present transitively via `vite`/`vitest`/`happy-dom`; declared directly so it is publicly resolvable for the Node/tooling typecheck. |

Playwright downloads Chromium browser binaries at install time
(`pnpm exec playwright install chromium`). Those binaries are **not** npm
dependencies, are not committed, and are not redistributed by DeepPlant; they are
fetched into the local Playwright browser cache
(`~/.cache/ms-playwright`) under Playwright's own redistribution terms. The
maintained Playwright installation mechanism is used, so no separate browser
provenance tracking is required here.

Deliberately **not** added by Issue #82: a Firefox or WebKit browser matrix,
Cypress, Storybook, Testing Library, a visual-regression service, a browser-test
abstraction layer, or video recording. No mock server, Vite dev/preview E2E path,
or Page Object framework was introduced.

## Standalone Editor packaging tooling (Issue #85)

Issue #85 made the Engineering Editor distributable as a standalone Windows/Linux
application. It added the following **build-time-only** tooling. None of it is a
runtime dependency of the installed Python package, and the base Python wheel
still bundles no JavaScript and no built SPA.

The non-Python tools are pinned — version, immutable upstream URL, SHA-256 — in
[`packaging/toolchain.toml`](packaging/toolchain.toml), and CI verifies them
before they run; see
[`docs/dev/workflow/packaging.md`](docs/dev/workflow/packaging.md). The
distinction below matters: a *build tool executable* is not distributed with
DeepPlant, but the artifact that tool generates can still contain upstream
runtime/bootstrap components.

| Dependency | Pinned input | Licence | Contributes | Distributed with DeepPlant? |
|---|---|---|---|---|
| `pyinstaller` | `uv.lock` (dependency group `package`) | GPL-2.0-or-later **with a special exception** that permits using PyInstaller to build and distribute applications under any licence, without an attribution requirement, as long as the bundled dependencies' own licences are respected | Freezes the Editor (bundled CPython, the DeepPlant package, its runtime dependencies, the canonical SVG symbols, and the built SPA) into a self-contained onedir application | Yes — PyInstaller's bootloader code is part of the frozen launcher; the exception permits that without an attribution requirement |
| `Inno Setup` (`ISCC.exe`) | Chocolatey package `innosetup`, pinned version | Inno Setup License: free to use, including commercially; binary redistributions must retain the existing copyright notices and web site addresses; an acknowledgment in product documentation is appreciated but not required | Compiles the Windows installer the end user downloads | **The `ISCC.exe` compiler executable is not distributed with DeepPlant.** The generated setup `.exe` does contain Inno Setup installer/runtime components and stays subject to the applicable Inno Setup terms — including the copyright notices and web site addresses Inno Setup embeds in what it produces |
| `appimagetool` | immutable upstream release, pinned with SHA-256 | MIT (AppImage project) | Assembles the Linux AppImage from the plain AppDir layout the packaging driver creates | **The `appimagetool` build executable is not distributed with DeepPlant** |
| AppImage type-2 runtime | immutable upstream release, pinned with SHA-256 | MIT (AppImage project, `AppImage/type2-runtime`); the statically linked runtime additionally contains musl libc, libfuse (LGPL-2.0), squashfuse, libzstd, and zlib, as listed in its upstream `LICENSE` | The bootstrap executable of a type-2 AppImage; it is passed to `appimagetool` with `--runtime-file` and prepended to the AppDir | Yes — every generated `.AppImage` contains it. The runtime binary is redistributed unmodified and carries its own upstream licence/notice text, and the same licence is recorded here |

The frozen artifacts also contain the project's own runtime dependencies
(FastAPI, Starlette, Uvicorn, Pydantic, Pydantic-Core, PyYAML, Typer, Click,
Rich, Pygments, `typing-extensions`, `annotated-doc`, `shellingham`,
`h11`/`httptools`/`uvloop` where applicable) under their own licences (MIT,
BSD-3-Clause, Apache-2.0 family) plus the CPython runtime (PSF-2.0). They were
already declared project dependencies; freeze tooling changed only how they are
distributed.

Deliberately **not** added: Nuitka, Briefcase, Electron, or Tauri. The decision
record and the measured comparison are in
[`docs/dev/research/standalone-editor-distribution.md`](docs/dev/research/standalone-editor-distribution.md).

## Standalone Editor desktop host (Issue #93)

Issue #93 turned the packaged Editor into a native graphical desktop application.
It added one redistributed runtime stack, recorded here separately because it
enters the shipped Windows and Linux artifacts.

| Dependency | Pinned input | Licence | Contributes | Distributed with DeepPlant? |
|---|---|---|---|---|
| `PySide6` (Qt for Python) | `uv.lock` (optional extra `desktop`, uv dependency group `desktop`) | `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only`, and additionally a commercial licence (PyPI project metadata; Qt describes LGPLv3 as its primary open-source licence, with some parts available only under GPL) | The native window, the native Open dialog, and the `QWebEngineView` that embeds the shared Vue SPA; a build/dev toolchain for `apps/editor/dist` is unaffected | Yes — the PySide6 wheels' Qt libraries and the Python bindings are frozen into the artifact |
| Qt WebEngine (Chromium) | shipped inside the `PySide6` wheels (no separate pin) | Qt-specific parts: commercial, LGPL-3.0, GPL-3.0, or GPL-2.0. Chromium parts carry a large third-party set whose most restrictive licence is LGPL-2.1. Qt states that distributing Qt WebEngine requires complying with **both** the Qt WebEngine licences and Chromium's licences | The embedded webview engine and its multiprocess renderer | Yes — `QtWebEngineCore`, the `QtWebEngineProcess` helper, Chromium resource packs (`.pak`), ICU data (`icudtl.dat`), and the locale packs are all inside the artifact. They are redistributed unmodified, and the PyInstaller onedir layout keeps the Qt libraries as separate, replaceable files |
| `PyInstaller` | *(see the packaging-tooling table above)* | | Also freezes the Qt/WebEngine runtime | Yes |

Sources verified at the time of writing:
[Qt WebEngine Licensing](https://doc.qt.io/qt-6/qtwebengine-licensing.html),
[Obligations of the GPL and LGPL](https://www.qt.io/licensing/open-source-lgpl-obligations),
and the [PySide6 PyPI project metadata](https://pypi.org/project/PySide6/).

What this changed for distribution:

- the base Python/Core installation still redistributes **no** desktop or GUI
  dependency; PySide6 lives only in the optional `deepplant[desktop]` extra, the
  `desktop` uv group, and the frozen application;
- a webview engine and a Chromium-based renderer are now redistributed by
  DeepPlant, which is why the artifact is roughly an order of magnitude larger
  than the #92 browser-hosted artifact;
- the obligations above (Qt/Qt WebEngine notices plus Chromium's third-party set)
  apply to the shipped artifacts and must be honoured with the redistributed
  components. Conformance that depends on the applicable upstream notices
  requires checking them against the actual redistributed files, not inferring
  them from this summary.

### Redistribution compliance payload (Issue #93 review fix)

This repository's documentation is not artifact evidence, so the applicable
licence and notice texts are packaged **into** the installed application, in a
`licenses/` directory next to the executable:

- `licenses/DEEPLANT-AGPL-3.0.txt` — DeepPlant's own licence;
- `licenses/THIRD_PARTY_NOTICES.md` — this file;
- `licenses/README.md` — the compliance mechanism: the redistributed versions, the
  replaceable onedir Qt libraries, corresponding-source pointers and the source
  offer;
- `licenses/Qt/*` and `licenses/Qt-WebEngine/*` — the LGPL/GPL/Qt-exception texts
  taken from the exact `v6.11.2` Qt and Qt WebEngine source tags and pinned by
  immutable URL and SHA-256 in `packaging/licenses.toml`;
- `licenses/Qt-WebEngine/Chromium-NOTICES.md` — authoritative upstream pointers for
  the Chromium third-party notice set and the corresponding-source offer.

The PySide6 wheels ship **no** licence files (only the METADATA `License:`
expression), which is why the Qt texts are staged from upstream at build time.
`tools/package_editor.py` verifies every digest before staging, and the packaged
verification fails if any required notice file is missing from the built artifact.

**Unresolved compliance action:** the complete, version-matched **Chromium**
third-party notice set is generated by upstream tooling and is not published as a
single immutable file for a given Qt release. DeepPlant does **not** claim that
obligation is fully satisfied in the artifacts: it ships the Qt WebEngine licence
texts plus the authoritative upstream pointers and the source offer, and tracks
full Chromium third-party notice reproduction as open work. Do not describe the
standalone Editor distribution as fully redistribution-compliant for the Chromium
notice set until that is resolved.

Evaluated and **not** adopted:
[`pywebview`](https://pywebview.flowrl.com/guide/installation.html) (Windows needs
the Microsoft WebView2 runtime; Linux needs system Qt or GTK/WebKitGTK, so the
artifact would not be self-contained) and
[Tauri v2](https://v2.tauri.app/start/prerequisites/) (adds the Rust toolchain and
a Python sidecar, and still depends on `libwebkit2gtk-4.1`/WebView2). Electron was
not added to the matrix. The full reasoning is in
[`docs/dev/research/editor-desktop-host.md`](docs/dev/research/editor-desktop-host.md).

## Standards, vendors, and unresolved boundaries

The repository contains project-authored standards summaries and references;
it does not redistribute restricted ISO, IEC, or ISA standards content. DEXPI,
COMOS, and AVEVA are mentioned as interoperability references or future
integration targets. No COMOS or AVEVA proprietary files are included here.

Future schemas, symbols, vendor formats, industrial project material,
documentation, screenshots, datasets, generated data, or copied examples need
item-level provenance and a redistribution-compatible licence before inclusion.
Where ownership, licence scope, or derivation is unclear, the item remains
unresolved and must not be described as owned by DeepPlant or its maintainer.
