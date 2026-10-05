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

## Distributor-controlled corresponding-source mechanism

The installed artifact includes `BUILD-IDENTITY.md`. It records the DeepPlant
release version and immutable DeepPlant Git revision that produced that exact
package, as well as the Qt, Qt WebEngine and Chromium revisions below. It is
generated while the package is staged; artifact verification rejects a package that
does not carry it or whose version/revision record is malformed.

For any redistributed component whose applicable licence requires corresponding
source, **DeepPlant makes the following written offer for the exact artifact
identified by that file**. This mechanism is controlled by DeepPlant rather than
being a statement that source may happen to remain available at an upstream URL:

> For three years from the date of the DeepPlant release containing this file,
> DeepPlant will provide on request the complete corresponding machine-readable
> source code for the PySide6, Qt and Qt WebEngine binaries redistributed in that
> identified artifact, including the Chromium source required for those binaries.
> Send the request, including `BUILD-IDENTITY.md`, to the project maintainer through
> the repository recorded in `THIRD_PARTY_NOTICES.md`.

DeepPlant redistributes unmodified upstream builds. The immutable revisions below
make a request reproducible and auditable, but they do not replace the offer above.
The offer is supplied without asserting that every bundled component has the same
source-obligation trigger or licence interpretation.

## Exact upstream revisions

The corresponding source for an identified artifact is reproducibly located from
the following immutable upstream revisions:

| Component | Upstream repository | Exact revision |
|---|---|---|
| PySide6 / Qt for Python | `https://code.qt.io/pyside/pyside-setup.git` | tag `v6.11.2` = `24627cd36e1593adf22eb1f2950e4248e7bcc1ec` |
| Qt (qtbase) | `https://code.qt.io/qt/qtbase.git` | tag `v6.11.2` = `ef55f427f2c8b410d34f8a7681020a3000cf6866` |
| Qt WebEngine | `https://code.qt.io/qt/qtwebengine.git` | tag `v6.11.2` = `a33fa2a897e5ee58e385b3f88dc247d99fca56db` |
| Qt Declarative | `https://code.qt.io/qt/qtdeclarative.git` | tag `v6.11.2` = `4e3399c26ec57246c08de019cfcbda8d23604cfa` |
| Chromium inside Qt WebEngine | `https://code.qt.io/qt/qtwebengine-chromium.git` | Qt's Chromium fork at the `src/3rdparty` gitlink of the Qt WebEngine tag: `5170777d28bee1ce92cc693a0dbf2ad01492e5cf` (Chromium 140.0.7339.264) |

Tags in these repositories are immutable: each is a released version tag, not a
branch, and the commit each tag resolves to is recorded above.

## Source delivery

DeepPlant does not publish a companion source archive with every binary artifact.
Instead, the artifact-specific written offer above is the distributor-controlled
request path. The immutable revision table makes the requested source set
reproducible; DeepPlant remains responsible for fulfilling a valid request rather
than directing a recipient to rely only on upstream availability.
