---
type: how-to
status: active
canonical_for:
  - standalone-editor-installation
read_when:
  - install-the-editor
  - run-the-editor
update_when:
  - distribution-artifact-change
  - supported-platform-change
depends_on:
  - docs/contracts/cli.md
  - docs/dev/research/standalone-editor-distribution.md
  - docs/dev/research/editor-desktop-host.md
decision: []
evidence:
  - docs/dev/research/standalone-editor-distribution.md
  - docs/dev/research/editor-desktop-host.md
superseded_by: null
---

# Install and run the standalone DeepPlant Editor

> **Question this page answers:** which file do I download for my computer, how do
> I install and run it, how do I open a plant model, and what does not exist yet?

The standalone DeepPlant Editor is a self-contained application runtime: you do
**not** need Python, Node.js, `pnpm`, `npm`, `uv`, `pip`, a compiler, a separately
installed Qt or webview/Chromium runtime, or the DeepPlant source code.

"Self-contained" means the application brings its own runtime; it does not mean a
statically linked binary with no system dependencies. On Linux it uses the
ordinary desktop graphics/session libraries that any graphical application uses
(the same ones your file manager and browser already use). On Windows it uses the
standard Windows runtime libraries.

The editor is **read-only**. It displays the current Process/PFD view of a plant
model and the validation status of that model. It never modifies your file.

## Which file do I download?

Pick the artifact for your operating system from the build's uploaded artifacts
(a maintainer provides them; there is no update service yet):

| Your computer | Download |
|---|---|
| Windows 10/11 on x86-64 | `deepplant-editor-<version>-windows-x86_64-setup.exe` |
| Linux on x86-64 | `deepplant-editor-<version>-linux-x86_64.AppImage` |

`<version>` matches the DeepPlant version, for example `0.1.0`.

## Windows

1. Run `deepplant-editor-<version>-windows-x86_64-setup.exe`.
2. Accept the default installation folder, or choose your own.
3. Finish the wizard. This installs the application and creates a **DeepPlant
   Editor** entry in the Start Menu (and on the desktop if you kept that option).

No administrator rights are required; the application installs for your user
account only.

To remove it later, use **Settings → Apps → Installed apps → DeepPlant Editor →
Uninstall**, or run the installer again and choose *Modify*.

## Linux

The Editor is distributed as an AppImage: a single executable file that contains
the whole application.

```bash
chmod +x deepplant-editor-<version>-linux-x86_64.AppImage
./deepplant-editor-<version>-linux-x86_64.AppImage --help
```

AppImages mount themselves through FUSE. If your distribution does not ship the
FUSE 2 runtime, either install it (`libfuse2` on Debian/Ubuntu, or `libfuse2t64`
on Ubuntu 24.04 and newer, `fuse-libs` on Fedora) or run the file in
extract-and-run mode, which needs no FUSE at all:

```bash
./deepplant-editor-<version>-linux-x86_64.AppImage --appimage-extract-and-run --help
```

## Open a plant model

**The normal way — no terminal.** Launch **DeepPlant Editor** (Start Menu on
Windows, or the AppImage on Linux). The editor window opens with a start page:

```text
┌────────────────────────────────────────┐
│ DeepPlant Editor                       │
│                                        │
│               DeepPlant                │
│                                        │
│            [ Open plant… ]             │
│                                        │
└────────────────────────────────────────┘
```

Choose **File → Open…** (or the **Open plant…** button) and pick your DeepPlant
YAML file (`*.yaml` or `*.yml`) in the normal operating-system file chooser. The
model opens inside the application window.

**The advanced way.** You can also pass the model on the command line, which
opens the same window directly on that file:

```bash
deepplant-editor path/to/plant.yaml
```

On Windows the same command is available as
`deepplant-editor.exe path/to/plant.yaml` inside the installation folder.

The realistic example fragment needs one transient **presentation** override,
because its `PS-vessel` step is honestly classified `function: unspecified`:

```bash
deepplant-editor examples/realistic-process-fragment/plant.yaml \
  --symbol-role PS-vessel=vessel
```

That override only changes how the drawing is rendered. It is never written to
your model or to your YAML file.

## What happens when I launch it?

```text
start the application
        ↓
the DeepPlant Editor window opens
        ↓
File → Open…  (or the model you passed on the command line)
        ↓
you see the read-only Process / PFD view inside the window
        ↓
close the window to stop the application
```

No terminal stays open and no browser window appears: the editor runs inside its
own window. Everything the editor needs is inside the application — you do not
need Python, Node.js, a compiler, a web server, or a separately installed
webview.

The editor serves itself only on `127.0.0.1` (your own machine). It is not
reachable from the network, and there is no login because there is no remote
surface to protect.

Useful options (`deepplant-editor --help` lists them):

| Option | Meaning |
|---|---|
| `<path>` | Optional. Open this model immediately instead of the start page. |
| `--port <n>` | Local port for the embedded server; `0` asks the operating system for a free port. |
| `--symbol-role STEP=ROLE` | Repeatable transient presentation override (see above). |

The following are used by our automated packaging checks and are not needed in
normal use: `--self-check`, `--self-check-report <path>`, `--assets-dir <dir>`.

## Licences and third-party notices

The Editor is a desktop application that embeds a Chromium-based webview, so it
redistributes Qt, Qt WebEngine/Chromium and other third-party components. The
applicable licence and notice material ships **inside the installed application**:

- Windows: `<installation folder>\licenses\` (for example
  `%LOCALAPPDATA%\Programs\DeepPlant Editor\licenses\` for a per-user install).
- Linux (AppImage): `usr/bin/deepplant-editor/licenses/` inside the AppDir - run
  `./deepplant-editor-<version>-linux-x86_64.AppImage --appimage-extract` and look
  under `squashfs-root/usr/bin/deepplant-editor/licenses/`.

That directory contains DeepPlant's own licence, the third-party notice index, the
project-authored compliance documents, and the Qt / Qt WebEngine licence texts
matching the exact redistributed versions. See
[THIRD_PARTY_NOTICES.md](../../../THIRD_PARTY_NOTICES.md) for the provenance index.

## What is not implemented yet

- **No editing and no saving.** The editor cannot create, change, delete, or
  save process steps, streams, or properties.
- **No project format.** It opens a single `plant.yaml`. There is no
  `.deepplant` project directory or manifest.
- **No P&ID view.** Only the read-only Process/PFD projection exists.
- **No automatic updates.** Download a newer artifact to upgrade.
- **No macOS build.** Windows and Linux are the supported platforms.

## Related

- [contracts/cli.md](../../contracts/cli.md) — the canonical `deepplant ui`
  contract the standalone application shares, and the standalone application's
  own contract.
- [dev/research/editor-desktop-host.md](../../dev/research/editor-desktop-host.md)
  — the evidence behind the native desktop host.
- [dev/research/standalone-editor-distribution.md](../../dev/research/standalone-editor-distribution.md)
  — the evidence behind the chosen distribution format.
- [getting-started.md](../getting-started.md) — using DeepPlant from a source
  checkout (contributors).
