# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Shared launch primitives for the DeepPlant Editor hosts (Issues #85, #93).

Two hosts serve the *same* editor over the *same* transport:

- ``deepplant ui <path>`` - the developer/browser host. It prints the loopback
  URL and serves the built SPA to whatever browser the developer uses.
- ``deepplant-editor [path]`` - the standalone desktop host
  (:mod:`deepplant.editor.desktop`), which embeds the same SPA in a native
  window and starts no external browser.

Both call :func:`run_editor`, which resolves the project through
:func:`deepplant.editor.application.load_editor_application` and serves it
through the FastAPI/Uvicorn transport in :mod:`deepplant.editor.api`. There is no
second editor implementation, and neither host re-implements engineering
semantics.

Importing this module is deliberately cheap: it never imports FastAPI or
Uvicorn. The transport is imported inside :func:`run_editor`, after the editor
dependency probe, which is what keeps ``deepplant version`` and
``deepplant validate`` independent of the editor transport.
"""

from __future__ import annotations

import webbrowser
from collections.abc import Callable, Sequence
from pathlib import Path

from deepplant.editor import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    MissingEditorDependenciesError,
    require_editor_dependencies,
)
from deepplant.editor.application import EditorSetupError, load_editor_application
from deepplant.io import PlantLoadError

__all__ = [
    "ASSETS_DIR_HELP",
    "EditorLaunchError",
    "SYMBOL_ROLE_HELP",
    "parse_symbol_role_overrides",
    "run_editor",
]

SYMBOL_ROLE_HELP = (
    "Per-step presentation symbol role as STEP=ROLE (repeatable). "
    "A presentation override only: it is never written to the model "
    "or to YAML. The realistic fragment needs "
    "'--symbol-role PS-vessel=vessel'."
)

ASSETS_DIR_HELP = (
    "Directory with built editor assets. Defaults to the assets carried by the "
    "application, then the development checkout build."
)


class EditorLaunchError(Exception):
    """User-facing editor launch failure reported without a traceback."""


def parse_symbol_role_overrides(entries: Sequence[str]) -> dict[str, str]:
    """Parse ``--symbol-role STEP=ROLE`` entries into a presentation mapping.

    Raises:
        EditorLaunchError: If an entry is not of the form ``STEP=ROLE``.
    """
    overrides: dict[str, str] = {}
    for entry in entries:
        step_id, separator, role = entry.partition("=")
        if not separator or not step_id.strip() or not role.strip():
            raise EditorLaunchError(f"invalid --symbol-role {entry!r}: expected the form STEP=ROLE")
        overrides[step_id.strip()] = role.strip()
    return overrides


def run_editor(
    project_path: Path,
    *,
    symbol_role_entries: Sequence[str] = (),
    port: int = DEFAULT_PORT,
    host: str = DEFAULT_HOST,
    assets_dir: Path | None = None,
    open_browser: bool = False,
    echo: Callable[[str], None] = print,
    browser_opener: Callable[[str], bool] = webbrowser.open,
) -> None:
    """Load one project and serve the local editor until the process is stopped.

    This is the single launch path shared by ``deepplant ui`` and
    ``deepplant-editor``.

    Raises:
        EditorLaunchError: For a malformed ``--symbol-role`` entry, a missing
            editor installation, an unreadable or invalid plant model, or
            missing editor assets. The message is the user-facing text; a raw
            traceback is never surfaced.
    """
    overrides = parse_symbol_role_overrides(symbol_role_entries)
    try:
        require_editor_dependencies()
    except MissingEditorDependenciesError as exc:
        raise EditorLaunchError(str(exc)) from exc

    # Imported here, not at module import time: the transport is the only part of
    # DeepPlant that needs FastAPI/Uvicorn, and the probe above decides whether
    # importing it is even meaningful.
    from deepplant.editor.api import serve_editor

    try:
        application = load_editor_application(
            project_path,
            symbol_role_overrides=overrides,
            assets_dir=assets_dir,
        )
    except (PlantLoadError, EditorSetupError) as exc:
        raise EditorLaunchError(str(exc)) from exc

    on_listening = (
        _browser_launcher(host, echo=echo, opener=browser_opener) if open_browser else None
    )
    serve_editor(application, host=host, port=port, echo=echo, on_listening=on_listening)


def _browser_launcher(
    host: str,
    *,
    echo: Callable[[str], None],
    opener: Callable[[str], bool],
) -> Callable[[int], None]:
    """Return a readiness callback that opens the editor in the user's browser.

    The browser is a convenience, never a requirement: when it cannot be opened
    (headless session, no default handler) the URL is echoed again so the user
    can open it manually.
    """

    def open_browser(bound_port: int) -> None:
        url = f"http://{host}:{bound_port}/"
        try:
            opened = opener(url)
        except Exception as exc:  # `webbrowser` raises on a broken desktop session
            echo(f"  could not open a browser automatically ({exc}); open {url}")
            return
        if not opened:
            echo(f"  could not open a browser automatically; open {url}")

    return open_browser
