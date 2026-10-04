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
decision: []
evidence:
  - docs/dev/research/standalone-editor-distribution.md
superseded_by: null
---

# Install and run the standalone DeepPlant Editor

> **Question this page answers:** which file do I download for my computer, how do
> I install and run it, how do I open a plant model, and what does not exist yet?

The standalone DeepPlant Editor is a self-contained application. You do **not**
need Python, Node.js, `pnpm`, `npm`, `uv`, `pip`, a compiler, or the DeepPlant
source code.

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

Point the application at a DeepPlant YAML file, exactly the input the developer
command `deepplant ui` accepts:

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
it prints the loopback address and opens your default browser
        ↓
you see the read-only Process / PFD view
        ↓
press Ctrl+C in the terminal window (or close it) to stop
```

The editor serves itself only on `127.0.0.1` (your own machine). It is not
reachable from the network, and there is no login because there is no remote
surface to protect.

> **Status — distribution foundation.** This is the current
> *distribution-foundation* behavior: the packaged application starts the local
> editor and opens it in your system browser. It is **not** the final standalone
> desktop experience. A native desktop window that embeds the same Vue frontend —
> requiring no terminal and no external browser for the normal workflow — is not
> implemented yet and is tracked by
> [Issue #93](https://github.com/Semtexcz/DeepPlant/issues/93).

Useful options:

| Option | Meaning |
|---|---|
| `--port <n>` | Local port to use; `0` asks the operating system for a free port (the default). |
| `--no-browser` | Do not open a browser; just print the address. Use this on a headless machine or in scripts. |
| `--symbol-role STEP=ROLE` | Repeatable transient presentation override (see above). |

If the browser cannot be opened (for example in a remote session), the address is
printed again so you can open it yourself.

## What is not implemented yet

- **No editing and no saving.** The editor cannot create, change, delete, or
  save process steps, streams, or properties.
- **No project format.** It opens a single `plant.yaml`. There is no
  `.deepplant` project directory or manifest.
- **No native desktop window.** Today the packaged application opens your system
  browser. A native desktop host embedding the same frontend — no terminal or
  external browser required — is tracked by
  [Issue #93](https://github.com/Semtexcz/DeepPlant/issues/93).
- **No P&ID view.** Only the read-only Process/PFD projection exists.
- **No automatic updates.** Download a newer artifact to upgrade.
- **No macOS build.** Windows and Linux are the supported platforms.

## Related

- [contracts/cli.md](../../contracts/cli.md) — the canonical `deepplant ui`
  contract the standalone application shares.
- [dev/research/standalone-editor-distribution.md](../../dev/research/standalone-editor-distribution.md)
  — the evidence behind the chosen distribution format.
- [getting-started.md](../getting-started.md) — using DeepPlant from a source
  checkout (contributors).
