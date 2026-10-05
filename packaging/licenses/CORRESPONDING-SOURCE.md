# Corresponding source for the redistributed Qt / Qt WebEngine binaries

The DeepPlant Editor redistributes unmodified upstream builds of PySide6, the Qt
libraries, and Qt WebEngine (which contains Chromium). This file states the
mechanism DeepPlant relies on to satisfy the corresponding-source obligations of
those licences, and the exact upstream revisions the shipped binaries correspond
to. It ships inside the installed application.

## What is redistributed and under which licence

| Component | Licence option used by DeepPlant | Source of the statement |
|---|---|---|
| PySide6 (Qt for Python) | LGPL v3 | PySide6 wheel metadata / Qt licensing |
| Qt 6 libraries | LGPL v3 | Qt licensing |
| Qt WebEngine (Qt-specific parts) | LGPL v3 | <https://doc.qt.io/qt-6/qtwebengine-licensing.html> |
| Chromium inside Qt WebEngine | "various licenses, with the most restrictive license being the GNU Lesser General Public License v2.1 (LGPL 2.1)" | same page, quoted verbatim |

Qt states: "The Qt WebEngine module uses Chromium to provide most of its
functionality. During the build process, Chromium becomes a part of the Qt WebEngine
Core library. Therefore, when distributing Qt WebEngine, users need to comply to
both the licenses of the Qt WebEngine part as developed under the Qt Project, as
well as the licenses that are part of Chromium."

## The mechanism DeepPlant uses (LGPL v3 section 4)

The licence text that governs this is shipped next to this file
(`LGPL-3.0-only.txt`). Its section 4, "Combined Works", permits conveying a work
that links a covered library provided the distributor does each of the following;
the operationally decisive part is paragraph (d):

```text
d) Do one of the following:

    0) Convey the Minimal Corresponding Source under the terms of this License, and
    the Corresponding Application Code in a form suitable for, and under terms that
    permit, the user to recombine or relink the Application with a modified version
    of the Linked Version ...

    1) Use a suitable shared library mechanism for linking with the Library.  A
    suitable mechanism is one that (a) uses at run time a copy of the Library
    already present on the user's computer system, and (b) will operate properly
    with a modified version of the Library that is interface-compatible with the
    Linked Version.
```

**DeepPlant uses option 4(d)(1).** The application is distributed as a PyInstaller
**onedir** tree, so Qt, Qt WebEngine and PySide6 remain ordinary, separate shared
libraries (`libQt6*.so.6`, `libqxcb.so`, `QtWebEngineProcess`, and the `.dll`
equivalents on Windows) inside the installation. They are loaded by the dynamic
loader at start-up, and a user may replace any of them with an interface-compatible
modified build without relinking DeepPlant code. Under option 4(d)(1) the licence
does not require DeepPlant to convey the libraries' Minimal Corresponding Source,
and DeepPlant does not modify the libraries.

The remaining paragraphs are satisfied as follows:

- **4(a) prominent notice that the library is used and covered by this licence** —
  this directory and `THIRD_PARTY_NOTICES.md` name every redistributed library, its
  licence, and its role in the application.
- **4(b) a copy of the GNU GPL and this licence document** — `LGPL-3.0-only.txt`
  and `GPL-3.0-only.txt` (plus `GPL-2.0-only.txt`, `LGPL-2.0-or-later.txt` and
  `Qt-GPL-exception-1.0.txt` for the alternatives Qt offers) are shipped here.
- **4(c) copyright notice where the work displays notices during execution** — the
  application displays no copyright notices during execution; attribution is
  therefore carried by the shipped files instead.
- **4(e) Installation Information** — only required for object code conveyed in a
  "User Product" (a consumer device). The Editor is desktop software distributed to
  end users, and the onedir tree needs no special installation step for a replaced
  library to be picked up.

DeepPlant's own source (the "Corresponding Application Code" under option 4(d)(0),
which this mechanism does not require) is public under AGPL-3.0-only at the
repository recorded in `THIRD_PARTY_NOTICES.md`.

## Supplementary: written offer and exact upstream revisions

Because the most restrictive licence inside Qt WebEngine is LGPL 2.1, DeepPlant
additionally offers the corresponding source in the manner LGPL 2.1 section 6(c)
permits ("a written offer, valid for at least three years"), so a recipient never
has to rely on an upstream URL continuing to exist:

> DeepPlant offers, valid for three years from the date of the release that
> contains this file, to provide on request the complete corresponding
> machine-readable source code for the PySide6, Qt and Qt WebEngine binaries
> redistributed with that release. Write to the project maintainer through the
> repository recorded in `THIRD_PARTY_NOTICES.md`.

The shipped binaries are unmodified upstream builds. Their corresponding source is
identified by these immutable upstream revisions:

| Component | Upstream repository | Exact revision |
|---|---|---|
| PySide6 / Qt for Python | `https://code.qt.io/pyside/pyside-setup.git` | tag `v6.11.2` = `24627cd36e1593adf22eb1f2950e4248e7bcc1ec` |
| Qt (qtbase) | `https://code.qt.io/qt/qtbase.git` | tag `v6.11.2` = `ef55f427f2c8b410d34f8a7681020a3000cf6866` |
| Qt WebEngine | `https://code.qt.io/qt/qtwebengine.git` | tag `v6.11.2` = `a33fa2a897e5ee58e385b3f88dc247d99fca56db` |
| Qt Declarative | `https://code.qt.io/qt/qtdeclarative.git` | tag `v6.11.2` = `4e3399c26ec57246c08de019cfcbda8d23604cfa` |
| Chromium inside Qt WebEngine | `https://code.qt.io/qt/qtwebengine-chromium.git` | Qt's Chromium fork at the `src/3rdparty` gitlink of the Qt WebEngine tag: `5170777d28bee1ce92cc693a0dbf2ad01492e5cf` (Chromium 140.0.7339.264) |

Tags in these repositories are immutable: each is a released version tag, not a
branch, and the commit each tag resolves to is recorded above.

## Why no source bundle is uploaded with the artifacts

LGPL v3 option 4(d)(1) — the shared-library mechanism this distribution uses —
does not require conveying (or mirroring) the libraries' source, so DeepPlant does
not produce companion source archives: they would be hundreds of megabytes of
upstream code that the applicable licence option does not require. The immutable
revisions above plus the three-year written offer keep source availability under
DeepPlant's control without duplicating upstream source trees.
