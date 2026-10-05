# DeepPlant Editor — third-party licence and compliance materials

This directory is shipped **inside** the installed DeepPlant Editor application
(Windows: `<install dir>\licenses\`; Linux AppImage: `usr/bin/deepplant-editor/licenses/`
inside the mounted/extracted AppDir). It is not a source-tree-only document.

## What this application redistributes

The DeepPlant Editor is a native desktop application that embeds a Chromium-based
webview. The distributed artifact therefore contains, unmodified, the following
upstream components:

| Component | Licence (as offered by upstream) | Role |
|---|---|---|
| DeepPlant | AGPL-3.0-only | The application and its semantic engineering model |
| CPython runtime | PSF-2.0 | Bundled interpreter (PyInstaller) |
| PySide6 / Qt for Python | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only, and a commercial licence | Python bindings for Qt |
| Qt 6 libraries (`Qt6Core`, `Qt6Gui`, `Qt6Widgets`, `Qt6Network`, `Qt6Qml`, …) | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only (some parts GPL-only) | Native window, widget and platform layer |
| Qt WebEngine (`Qt6WebEngineCore`, `QtWebEngineProcess`) | Qt WebEngine parts as above; Chromium third-party set as upstream lists | Embedded webview engine and renderer |
| Chromium resource/ICU/locale data (`*.pak`, `icudtl.dat`, locales) | Chromium third-party set (see `Qt-WebEngine/Chromium-NOTICES.md`) | Webview runtime data |

The exact redistributed versions are recorded below and in
`packaging/licenses.toml` in the DeepPlant source repository.

## Version this artifact was built against

- **PySide6 / Qt for Python:** 6.11.2
- **Qt:** 6.11.2 (`v6.11.2`)
- The Qt libraries, Qt WebEngine, the `QtWebEngineProcess` helper, Chromium and the
  Python runtime are redistributed exactly as their upstreams ship them. DeepPlant
  does not modify them.

## Where the applicable licence texts are

- `DEEPLANT-AGPL-3.0.txt` — DeepPlant's own licence.
- `THIRD_PARTY_NOTICES.md` — the DeepPlant third-party provenance index.
- `Qt/` — the licence texts from the exact Qt `v6.11.2` source tag for the Qt
  libraries (LGPL-3.0-only, LGPL-2.1-or-later, GPL-2.0-only, GPL-3.0-only, and the
  Qt GPL exception).
- `Qt-WebEngine/` — the licence texts from the exact Qt WebEngine `v6.11.2` source
  tag, plus `Chromium-VERSION.txt` and `Chromium-LICENSE-BSD.txt` from that same
  tag, plus `Chromium-THIRD-PARTY-NOTICES.txt` — the generated, version-matched
  Chromium third-party notice set — and `Chromium-NOTICES.md`, which records how
  that set is generated and verified.
- `CORRESPONDING-SOURCE.md` — how the corresponding-source obligations of those
  licences are met, quoting the licence clause relied on, with the exact upstream
  revisions of every redistributed library.

Every file under `Qt/` and `Qt-WebEngine/` is fetched from an immutable upstream
URL and verified against a pinned SHA-256 digest before it is staged into the
application (`packaging/licenses.toml`, `tools/package_editor.py`).

## LGPL compliance mechanism used by DeepPlant

Qt and Qt WebEngine are used under the **LGPL v3** (the primary open-source
option); DeepPlant does not statically link them and does not modify them. The
selected mechanism is:

1. **Notice texts.** The applicable Qt LGPL/GPL texts and the Qt GPL exception are
   shipped in this directory (above), together with attribution.
2. **Replaceability / relinking.** The application is distributed as a PyInstaller
   **onedir** tree, so the Qt shared libraries remain separate, ordinary `.so`/`.dll`
   files inside the installation. A user may substitute a compatible modified build
   of an LGPL-covered Qt library (or of PySide6) by replacing that file in the
   installed application; no relinking of DeepPlant code is required. The dynamic
   loader resolves the replaced library at start-up.
3. **Corresponding source.** DeepPlant relies on the shared-library option of
   LGPL v3 section 4(d)(1) — the redistributed libraries are dynamically loaded
   and can be replaced by the user — and additionally makes a written offer valid
   for three years for the corresponding source of the exact binaries, following
   LGPL v2.1 section 6(c) for the Chromium parts (the most restrictive licence
   inside Qt WebEngine is LGPL 2.1). The clause text relied on, the resulting
   obligations, and the immutable upstream revision of every redistributed library
   are recorded in `CORRESPONDING-SOURCE.md` in this directory.

## Chromium / Qt WebEngine third-party notices

Qt WebEngine compiles Chromium into `Qt6WebEngineCore`, so Chromium's third-party
licences apply to the distributed binaries as well. This directory therefore
ships the complete, version-matched Chromium third-party notice set as
`Qt-WebEngine/Chromium-THIRD-PARTY-NOTICES.txt`, together with
`Qt-WebEngine/Chromium-VERSION.txt` (the Chromium revision inside the shipped
engine) and `Qt-WebEngine/Chromium-LICENSE-BSD.txt` (Chromium's own licence).
`Qt-WebEngine/Chromium-NOTICES.md` records how that notice set is generated
upstream and how the packaging job verifies it against the exact engine version.
