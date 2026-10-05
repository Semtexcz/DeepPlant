# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Standalone desktop host for the shared Engineering Editor SPA (Issue #93).

``deepplant-editor`` is what an end user launches. It is a *thin native host*,
not a second frontend:

    native window + embedded webview
              ↓
    http://127.0.0.1:<ephemeral-port>
              ↓
    FastAPI / Uvicorn  (deepplant.editor.api)
              ↓
    EditorApplication  (deepplant.editor.application)
              ↓
    DeepPlant Core

The embedded page is the ordinary production build of ``apps/editor/`` - the same
Vue SPA the developer/browser host (``deepplant ui``) and any future web
deployment serve. No engineering UI is re-implemented natively.

This module is deliberately **Qt-free**: it owns the command-line surface, the
dependency probe, the initial-project load, and the small navigation policy, so
all of that is testable without installing a GUI toolkit. The Qt machinery lives
in :mod:`deepplant.editor.desktop_qt`, imported lazily and only after
:func:`deepplant.editor.require_desktop_dependencies` succeeds. That is what keeps
``deepplant version``, ``deepplant validate``, and ``deepplant ui`` independent of
the desktop extra.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Annotated
from urllib.parse import urlsplit

import typer

from deepplant.editor import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    MissingEditorDependenciesError,
    require_desktop_dependencies,
)
from deepplant.editor.application import (
    EditorApplication,
    EditorSetupError,
    load_editor_application,
)
from deepplant.editor.launcher import (
    ASSETS_DIR_HELP,
    SYMBOL_ROLE_HELP,
    EditorLaunchError,
    parse_symbol_role_overrides,
)
from deepplant.io import PlantLoadError

__all__ = [
    "DesktopHostError",
    "MODEL_FILE_FILTER",
    "WINDOW_TITLE",
    "app",
    "editor_origin",
    "initial_open_directory",
    "is_allowed_navigation",
    "main",
    "run_desktop_editor",
]

#: Native window title. Also the string the packaging smoke test looks for when
#: it discovers the real top-level window on Linux.
WINDOW_TITLE: str = "DeepPlant Editor"

#: The native Open dialog only *selects a path*; it never parses DeepPlant YAML.
MODEL_FILE_FILTER: str = "DeepPlant plant models (*.yaml *.yml);;All files (*)"

#: Schemes the SPA and Qt itself legitimately use inside the view. They carry no
#: remote authority, so they are allowed alongside the exact active origin. They
#: are the only non-``http(s)`` schemes accepted; ``file:`` is deliberately not one
#: of them.
_INTERNAL_SCHEMES: frozenset[str] = frozenset({"data", "blob", "about", "qrc"})

#: Default ports used when a ``http(s)`` URL omits its port, so origin comparison
#: is exact rather than "any loopback port".
_DEFAULT_PORTS: dict[str, int] = {"http": 80, "https": 443}

#: Native host runner. A small protocol so the command-line wiring stays testable
#: without a GUI toolkit.
HostRunner = Callable[..., int]

#: Project loader the native Open dialog uses.
ProjectLoader = Callable[[Path], EditorApplication]


class DesktopHostError(Exception):
    """User-facing desktop launch failure reported without a traceback."""


def initial_open_directory() -> str:
    """Return a usable starting directory for the native Open dialog.

    This must never raise. A graphical application has to start even when the
    platform cannot report a home directory - a service or locked-down session, a
    hardened CI runner - and ``Path.home()`` raises ``RuntimeError`` in exactly
    those cases. The current working directory is the fallback, and an empty
    string (Qt's own default) the last resort.
    """
    for candidate in (Path.home, Path.cwd):
        try:
            return str(candidate())
        except (OSError, RuntimeError):
            continue
    return ""


def editor_origin(host: str, port: int) -> str:
    """Return the exact ``scheme://host:port`` origin an EditorServer owns.

    The embedded webview is limited to this single origin (Issue #93 review), so
    the value is built in exactly one place and compared as a whole - never by the
    weaker "is this loopback?" test.
    """
    return f"http://{host.lower()}:{int(port)}"


def _origin_of(url: str) -> str | None:
    """Return the normalized ``scheme://host:port`` origin of ``url``, or ``None``.

    Only ``http``/``https`` have a web origin here. A missing port is normalized to
    the scheme default, and the host is lower-cased, so comparison is exact.
    """
    parts = urlsplit(url)
    scheme = parts.scheme.lower()
    if scheme not in _DEFAULT_PORTS:
        return None
    host = (parts.hostname or "").lower()
    if not host:
        return None
    port = parts.port if parts.port is not None else _DEFAULT_PORTS[scheme]
    return f"{scheme}://{host}:{port}"


def is_allowed_navigation(url: str, *, allowed_origin: str | None) -> bool:
    """Whether the embedded webview may navigate to ``url`` (Issue #93 review).

    The policy is *exact origin*: only the ``scheme://host:port`` origin of the
    currently running :class:`~deepplant.editor.api.EditorServer`
    (:func:`editor_origin`) is accepted, plus the internal schemes the SPA and Qt
    themselves use. A different loopback port, a different loopback host name
    (``localhost`` versus ``127.0.0.1``), an external HTTPS site, and ``file:``
    URLs are all refused.

    This is a webview **host policy**, not authentication: the embedded server is
    already loopback-only, single-user, and unauthenticated, and nothing here adds
    tokens, sessions, or CORS.

    Args:
        url: The candidate navigation target.
        allowed_origin: The origin of the active EditorServer, or ``None`` when no
            server is running (only the internal schemes are then accepted).
    """
    scheme = urlsplit(url).scheme.lower()
    if scheme in _INTERNAL_SCHEMES:
        return True
    if allowed_origin is None:
        return False
    origin = _origin_of(url)
    return origin is not None and origin == allowed_origin.lower()


def _load_qt_host_runner() -> HostRunner:
    """Return the native host runner, or fail with an actionable message."""
    try:
        require_desktop_dependencies()
    except MissingEditorDependenciesError as exc:
        raise DesktopHostError(str(exc)) from exc
    # Imported here, not at module import time: Qt WebEngine is the desktop
    # extra, and nothing else in DeepPlant may depend on it.
    from deepplant.editor.desktop_qt import run_host

    return run_host


def run_desktop_editor(
    project_path: Path | None = None,
    *,
    symbol_role_entries: Sequence[str] = (),
    port: int = DEFAULT_PORT,
    assets_dir: Path | None = None,
    host: str = DEFAULT_HOST,
    self_check: bool = False,
    report_path: Path | None = None,
    echo: Callable[[str], None] = print,
    host_runner: HostRunner | None = None,
) -> int:
    """Launch the native DeepPlant Editor window and return its exit code.

    ``project_path`` is *optional*: with no path the window opens with a minimal
    native bootstrap (``File -> Open...``), which is the primary end-user
    workflow. With a path the same window opens directly on that model, which is
    the advanced/diagnostic workflow.

    The initial project is loaded *before* the window is created, so an invalid
    or missing model is a clear message instead of a window that appears and then
    fails. The Open dialog's selections are loaded through the same boundary.

    Args:
        project_path: Optional DeepPlant plant model to open immediately.
        symbol_role_entries: Repeatable ``STEP=ROLE`` presentation overrides.
        port: Local loopback port; ``0`` asks the OS for a free one.
        assets_dir: Optional explicit built-SPA directory.
        host: Bind host; loopback by default and never ``0.0.0.0``.
        self_check: Run the automated packaged-desktop verification instead of
            waiting for the user (see docs/dev/workflow/packaging.md).
        report_path: Where ``self_check`` writes its JSON report. Required by the
            packaged Windows build, which is a GUI executable with no console.
        echo: Diagnostic sink.
        host_runner: Test seam; defaults to the real Qt host.

    Raises:
        DesktopHostError: If the desktop extra is missing or the initial model
            cannot be loaded. The message is user-facing; no traceback.
    """
    try:
        overrides = parse_symbol_role_overrides(symbol_role_entries)
    except EditorLaunchError as exc:
        raise DesktopHostError(str(exc)) from exc

    if self_check and report_path is None:
        raise DesktopHostError("--self-check requires --self-check-report <path>")

    runner = host_runner if host_runner is not None else _load_qt_host_runner()

    def load(selected: Path) -> EditorApplication:
        return load_editor_application(
            selected,
            symbol_role_overrides=overrides,
            assets_dir=assets_dir,
        )

    initial_application: EditorApplication | None = None
    if project_path is not None:
        try:
            initial_application = load(project_path)
        except (PlantLoadError, EditorSetupError) as exc:
            raise DesktopHostError(str(exc)) from exc

    return runner(
        initial_application=initial_application,
        loader=load,
        port=port,
        host=host,
        echo=echo,
        self_check=self_check,
        report_path=report_path,
    )


def _ensure_standard_streams() -> None:
    """Give a windowed build usable standard streams.

    The packaged Windows application is a GUI executable (PyInstaller
    ``--windowed``), so it has no console and ``sys.stdout``/``sys.stderr`` are
    ``None``. Writing to them then raises, which would turn an ordinary message
    into a crash. A null stream keeps diagnostics from breaking the application;
    the deliberate diagnostics path for automation is ``--self-check-report``
    (see docs/dev/workflow/packaging.md).
    """
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")


app = typer.Typer(
    help=(
        "DeepPlant Editor - standalone graphical editor for a DeepPlant plant model. "
        "Run it without arguments to open the editor window and choose a model with "
        "File -> Open."
    ),
    # No arguments must launch the window, never print help or demand a path.
    no_args_is_help=False,
    add_completion=False,
)


@app.command()
def open_editor(
    path: Annotated[
        Path | None,
        typer.Argument(help="Optional DeepPlant plant model YAML file (advanced use)."),
    ] = None,
    symbol_role: Annotated[
        list[str] | None,
        typer.Option("--symbol-role", help=SYMBOL_ROLE_HELP),
    ] = None,
    port: Annotated[
        int,
        typer.Option(help="Local port for the embedded server (0 picks a free port)."),
    ] = DEFAULT_PORT,
    assets_dir: Annotated[
        Path | None,
        typer.Option("--assets-dir", help=ASSETS_DIR_HELP),
    ] = None,
    self_check: Annotated[
        bool,
        typer.Option(
            "--self-check",
            help=(
                "Automated verification: load the embedded application, probe the real "
                "page, write a JSON report, and exit. Used by packaged desktop tests."
            ),
        ),
    ] = False,
    self_check_report: Annotated[
        Path | None,
        typer.Option("--self-check-report", help="Report path for --self-check."),
    ] = None,
) -> None:
    """Open the standalone DeepPlant Editor window."""
    try:
        code = run_desktop_editor(
            path,
            symbol_role_entries=symbol_role or [],
            port=port,
            assets_dir=assets_dir,
            self_check=self_check,
            report_path=self_check_report,
        )
    except DesktopHostError as exc:
        typer.echo(f"✗ {exc}", err=True)
        raise typer.Exit(code=1) from exc
    if code != 0:
        raise typer.Exit(code=code)


def main() -> None:
    """Console-script entry point for the standalone DeepPlant Editor."""
    _ensure_standard_streams()
    app()


if __name__ == "__main__":
    main()
