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
- `CORRESPONDING-SOURCE.md` — DeepPlant's distributor-controlled written offer and
  the exact upstream revisions of every redistributed library.
- `BUILD-IDENTITY.md` — generated identifiers for the exact received DeepPlant
  artifact covered by that offer.

Every file under `Qt/` and `Qt-WebEngine/` is fetched from an immutable upstream
URL and verified against a pinned SHA-256 digest before it is staged into the
application (`packaging/licenses.toml`, `tools/package_editor.py`).

## Corresponding-source request mechanism

`BUILD-IDENTITY.md` is generated into each artifact. It records the DeepPlant
version and immutable source revision for the received binary together with the
Qt/Qt WebEngine/Chromium revisions. `CORRESPONDING-SOURCE.md` provides DeepPlant's
three-year written offer for any corresponding source required by applicable
redistributed-component licences. A recipient includes that identity file when
requesting source through the project maintainer named in
`THIRD_PARTY_NOTICES.md`; this is a DeepPlant-controlled request path, not merely a
pointer to upstream downloads.

## Chromium / Qt WebEngine third-party notices

Qt WebEngine compiles Chromium into `Qt6WebEngineCore`, so Chromium's third-party
licences apply to the distributed binaries as well. This directory therefore
ships the complete, version-matched Chromium third-party notice set as
`Qt-WebEngine/Chromium-THIRD-PARTY-NOTICES.txt`, together with
`Qt-WebEngine/Chromium-VERSION.txt` (the Chromium revision inside the shipped
engine) and `Qt-WebEngine/Chromium-LICENSE-BSD.txt` (Chromium's own licence).
`Qt-WebEngine/Chromium-NOTICES.md` records how that notice set is generated
upstream and how the packaging job verifies it against the exact engine version.
