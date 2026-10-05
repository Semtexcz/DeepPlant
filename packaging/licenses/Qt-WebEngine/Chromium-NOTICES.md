# Qt WebEngine / Chromium third-party notices

Qt WebEngine compiles the Chromium engine into `Qt6WebEngineCore`. Distributing Qt
WebEngine therefore means honouring the Qt WebEngine licences **and** the licences
of the Chromium code it contains. This file explains what the DeepPlant Editor
ships for the second obligation and how it is verified; the notice material itself
is [`Chromium-THIRD-PARTY-NOTICES.txt`](Chromium-THIRD-PARTY-NOTICES.txt) in this
same directory. Repository documentation is not artifact evidence, so everything
described here is also shipped inside the installed application.

## What is shipped

| Shipped file | What it is |
|---|---|
| `Chromium-THIRD-PARTY-NOTICES.txt` | The complete Chromium third-party notice set for the exact redistributed engine: every component upstream lists, each with licence identifier, project homepage, and the full notice text. |
| `Chromium-VERSION.txt` | Upstream `CHROMIUM_VERSION` from the exact Qt WebEngine tag: which Chromium revision is compiled into the shipped `Qt6WebEngineCore`. |
| `Chromium-LICENSE-BSD.txt` | The Chromium project's own BSD licence (`LICENSE.Chromium` from the same tag). |
| `LGPL-3.0-only.txt`, `LGPL-2.0-or-later.txt`, `GPL-2.0-only.txt`, `GPL-3.0-only.txt`, `Qt-GPL-exception-1.0.txt` | The Qt WebEngine *parts*' licence texts, taken from the exact `qtwebengine` source tag. |

## Version this artifact matches

- PySide6 / Qt / Qt WebEngine: **6.11.2** — tag `v6.11.2`, commit
  `a33fa2a897e5ee58e385b3f88dc247d99fca56db`.
- Chromium inside Qt WebEngine 6.11.2: **140.0.7339.264** (patched with security
  fixes up to 151.0.7922.71), from the same tag's `CHROMIUM_VERSION`.

The same version relationship is pinned in `packaging/licenses.toml` in the
DeepPlant source repository and re-checked by the packaging job.

## Which upstream mechanism generates this notice set

Upstream does not publish the Chromium third-party notice set as a single
immutable release file. Qt *generates* it during its own build:

```text
qtwebengine/cmake/QtGnCredits.cmake
  -> src/3rdparty/chromium/tools/licenses/licenses.py credits \
       --gn-target :QtWebEngineCore --file-template about_credits.tmpl \
       --entry-template about_credits_entry.tmpl
  -> chromium_attributions.qdoc
  -> the "Qt WebEngine Licensing -> Third-Party Licenses" documentation for the
     exact Qt release
```

`tools/chromium_notices.py` in the DeepPlant repository turns that published,
exact-version output into a deterministic packaging input: it fetches the pinned
publication, extracts every component it lists together with the notice text
upstream publishes for that component, and writes the bundle shipped here. No
component list is written by hand.

## What the running engine does *not* provide

Chrome's `chrome://credits` page is a Chrome-layer feature. Qt WebEngine
implements its own small WebUI set — `chrome://version` (which reports the
Chromium revision compiled into the engine), but **not** `chrome://credits` — and
the PySide6 6.11.2 resources DeepPlant redistributes
(`qtwebengine_resources*.pak`, `qtwebengine_devtools_resources.pak`) contain no
credits payload. A user could therefore not obtain the Chromium notices from the
running application, which is exactly why they are shipped as the plain-text file
above: it needs no browser, no network, and no development tooling.

## How this is verified

- **Build time** (`tools/package_editor.py`, `licenses` phase): the pinned
  publication is fetched and its SHA-256 verified, then
  `tools/chromium_notices.py` proves the bundle enumerates *every* component the
  publication lists and that each entry carries notice text. A partial, stale, or
  digest-mismatched bundle fails the build.
- **Artifact time**: the installed Windows tree / extracted Linux AppImage is
  inspected, and verification fails if the bundle is missing, empty, lacks the
  generated provenance markers, covers a different component count than the
  manifest declares, or has an entry without notice text.

If upstream republishes the Qt 6.11 documentation for a later patch release, the
digest check fails closed, and a maintainer re-runs
`tools/chromium_notices.py generate` and re-pins the publication digest in
`packaging/licenses.toml` together with the engine version it corresponds to.

