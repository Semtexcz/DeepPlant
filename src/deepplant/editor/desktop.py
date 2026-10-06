# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Standalone desktop host for the shared Engineering Editor SPA (Issue #93).

``deepplant-editor`` is what an end user launches. It is a *thin native host*,
not a second frontend:

    native window + embedded webview
              ↓
    http://127.0.0.1:<ephemeral-port>   (one long-lived origin)
              ↓
    FastAPI / Uvicorn  (deepplant.editor.api)
              ↓
    EditorWorkspace  (deepplant.editor.application)
              ↓
    EditorApplication?  (active document: none | loaded)  →  DeepPlant Core

The embedded page is the ordinary production build of ``apps/editor/`` - the same
Vue SPA the developer/browser host (``deepplant ui``) and any future web
deployment serve. No engineering UI is re-implemented natively.

Since Issue #97 the window opens *directly into that shared Vue editor*: the
application shell exists independently of its active document, so launching with
no argument shows the ordinary editor workspace with ``active project = none``
rather than a native start page. Opening a project changes workspace state
through the same long-lived server and webview; it never swaps in a second UI.

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
from dataclasses import dataclass
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
    create_empty_workspace,
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
    "SELF_CHECK_SCENARIO_EMPTY",
    "SELF_CHECK_SCENARIO_LOADED",
    "SELF_CHECK_SCENARIO_TRANSITION",
    "SELF_CHECK_SCENARIOS",
    "SMOKE_EXPECTED_STEPS",
    "SMOKE_EXPECTED_STREAMS",
    "SMOKE_PROBE_STEP_ID",
    "TRANSITION_PROJECT_B_EXPECTED_STEPS",
    "TRANSITION_PROJECT_B_EXPECTED_STREAMS",
    "TRANSITION_PROJECT_B_PROBE_FUNCTION",
    "TRANSITION_PROJECT_B_PROBE_STEP_ID",
    "TRANSITION_PROJECT_COUNT",
    "WINDOW_TITLE",
    "DesktopHostError",
    "DesktopSelfCheckPlan",
    "EMPTY_WORKSPACE_STATUS_TEXT",
    "MODEL_FILE_FILTER",
    "app",
    "editor_origin",
    "initial_open_directory",
    "is_allowed_navigation",
    "main",
    "plan_self_check",
    "run_desktop_editor",
]

#: Native window title. Also the string the packaging smoke test looks for when
#: it discovers the real top-level window on Linux.
WINDOW_TITLE: str = "DeepPlant Editor"

#: The native Open dialog only *selects a path*; it never parses DeepPlant YAML.
MODEL_FILE_FILTER: str = "DeepPlant plant models (*.yaml *.yml);;All files (*)"

#: The packaged desktop self-check's expected fixture graph (Issue #98). They
#: describe the canonical, self-contained smoke fixture the packaged verification
#: opens - ``tools/package_editor.py``'s ``SMOKE_MODEL``
#: (``examples/process-graph/plant.yaml``): a small model the ordinary
#: ``File -> Open…`` workflow renders with **no** presentation override. They live
#: in this Qt-free half of the host so the fixture and the self-check's
#: expectations can be checked together without a GUI toolkit.
SMOKE_PROBE_STEP_ID: str = "PUMP"
SMOKE_EXPECTED_STEPS: int = 3
SMOKE_EXPECTED_STREAMS: int = 2

#: The packaged desktop *project-replacement* regression (Issue #97 review) opens
#: two self-contained process models in one session. Project A is the canonical
#: smoke fixture above; project B is ``examples/process-graph/replacement.yaml``,
#: which is distinguishable from it by graph contents (two steps, one stream, no
#: ``PUMP``). The distinctions are authored here - the Qt-free half of the host -
#: so the fixture and the probe expectations are checked together in the fast
#: Python gate rather than only in the slow native packaging job.
TRANSITION_PROJECT_B_PROBE_STEP_ID: str = "INLET"
TRANSITION_PROJECT_B_EXPECTED_STEPS: int = 2
TRANSITION_PROJECT_B_EXPECTED_STREAMS: int = 1
TRANSITION_PROJECT_B_PROBE_FUNCTION: str = "source"

#: The self-check scenario names. ``empty`` is the shared SPA with no document
#: (Issue #97); ``loaded`` is the canonical fixture opened through the ordinary
#: path (Issue #98); ``transition`` is the project-replacement lifecycle (empty
#: session, then project A, then project B, then a failed open, then close).
SELF_CHECK_SCENARIO_EMPTY: str = "empty"
SELF_CHECK_SCENARIO_LOADED: str = "loaded"
SELF_CHECK_SCENARIO_TRANSITION: str = "transition"

#: The scenarios the native host understands, in the order the packaged
#: verification runs them.
SELF_CHECK_SCENARIOS: tuple[str, ...] = (
    SELF_CHECK_SCENARIO_EMPTY,
    SELF_CHECK_SCENARIO_LOADED,
    SELF_CHECK_SCENARIO_TRANSITION,
)

#: Number of projects the transition scenario opens before it attempts the failing
#: open: project A, then project B.
TRANSITION_PROJECT_COUNT: int = 2

#: The neutral status text the shared Vue SPA shows when no project is open (Issue
#: #97). The packaged self-check asserts it, so the no-project launch is proven to
#: be an ordinary editor state rather than a validation ("Invalid") or Process/PFD
#: projection failure. It is authored here - the Qt-free half of the host - so the
#: value the frontend renders and the value the probe asserts can be checked
#: together in the fast Python gate.
EMPTY_WORKSPACE_STATUS_TEXT: str = "No project open"

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


@dataclass(frozen=True)
class DesktopSelfCheckPlan:
    """What the packaged-desktop self-check must verify once the window is up.

    This is the Qt-free description of one automated desktop run, so the
    command-line surface and the native host share one value instead of a growing
    argument list. Issue #97 review added ``transition``: a single long-lived
    session that opens project A, replaces it with project B, then attempts a
    failing open, proving the window, webview, server, port and origin are never
    recreated.
    """

    scenario: str = SELF_CHECK_SCENARIO_LOADED
    #: Projects the ``transition`` scenario opens through the Open handler, in
    #: order (project A, then project B).
    projects: tuple[Path, ...] = ()
    #: A model that must fail to load in the ``transition`` scenario, so the
    #: previous project stays active.
    invalid_project: Path | None = None

    def __post_init__(self) -> None:
        if self.scenario not in SELF_CHECK_SCENARIOS:
            raise ValueError(f"unknown self-check scenario: {self.scenario!r}")
        if self.scenario == SELF_CHECK_SCENARIO_TRANSITION:
            if len(self.projects) != TRANSITION_PROJECT_COUNT:
                raise ValueError(
                    "the transition self-check needs exactly "
                    f"{TRANSITION_PROJECT_COUNT} projects, got {len(self.projects)}"
                )
            if self.invalid_project is None:
                raise ValueError("the transition self-check needs an invalid project")


def plan_self_check(
    scenario: str,
    *,
    projects: Sequence[Path] = (),
    invalid_project: Path | None = None,
) -> DesktopSelfCheckPlan:
    """Build a validated :class:`DesktopSelfCheckPlan`, or raise ``DesktopHostError``.

    The command line accepts a free-form scenario string, so the mapping from a
    bad value to a user-facing message lives here rather than as an unhandled
    ``ValueError``.
    """
    try:
        return DesktopSelfCheckPlan(
            scenario=scenario,
            projects=tuple(Path(project) for project in projects),
            invalid_project=None if invalid_project is None else Path(invalid_project),
        )
    except ValueError as exc:
        raise DesktopHostError(str(exc)) from exc


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
    self_check_scenario: str | None = None,
    self_check_projects: Sequence[Path] = (),
    self_check_invalid_project: Path | None = None,
    echo: Callable[[str], None] = print,
    host_runner: HostRunner | None = None,
) -> int:
    """Launch the native DeepPlant Editor window and return its exit code.

    ``project_path`` is optional: the window always opens directly into the
    ordinary shared Vue editor workspace (Issue #97), so with no path that
    workspace simply has no active document. The initial project is loaded
    *before* the window is created, so an invalid or missing model is a clear
    message instead of a window that appears and then fails; the Open dialog's
    selections are loaded through the same boundary.

    ``self_check`` runs the automated packaged-desktop verification instead of
    waiting for the user (see docs/dev/workflow/packaging.md). Its scenario is
    ``empty`` (no document), ``loaded`` (the canonical fixture, the default with a
    path), or ``transition`` - the project-replacement lifecycle, which opens
    ``self_check_projects`` in order and then attempts ``self_check_invalid_project``.

    Raises:
        DesktopHostError: If the desktop extra is missing, the built editor assets
            cannot be found, the initial model cannot be loaded, or the self-check
            scenario is inconsistent. The message is user-facing; no traceback.
    """
    try:
        overrides = parse_symbol_role_overrides(symbol_role_entries)
    except EditorLaunchError as exc:
        raise DesktopHostError(str(exc)) from exc

    if self_check and report_path is None:
        raise DesktopHostError("--self-check requires --self-check-report <path>")
    if self_check_scenario is not None and not self_check:
        raise DesktopHostError("--self-check-scenario requires --self-check")

    plan = _resolve_self_check_plan(
        self_check=self_check,
        project_path=project_path,
        scenario=self_check_scenario,
        projects=self_check_projects,
        invalid_project=self_check_invalid_project,
    )

    runner = host_runner if host_runner is not None else _load_qt_host_runner()

    # The workspace serves the shared SPA whether or not a document is open, so the
    # built assets must resolve before any window appears. An empty workspace is a
    # real, first-class state - not a fallback that hides a missing build.
    try:
        workspace = create_empty_workspace(assets_dir)
    except EditorSetupError as exc:
        raise DesktopHostError(str(exc)) from exc

    def load(selected: Path) -> EditorApplication:
        return load_editor_application(
            selected,
            symbol_role_overrides=overrides,
            assets_dir=workspace.assets_dir,
        )

    return runner(
        assets_dir=workspace.assets_dir,
        initial_application=_load_initial_application(load, project_path),
        loader=load,
        port=port,
        host=host,
        echo=echo,
        self_check=self_check,
        report_path=report_path,
        self_check_plan=plan,
    )


def _load_initial_application(
    load: Callable[[Path], EditorApplication], project_path: Path | None
) -> EditorApplication | None:
    """Load the optional initial document, reporting a bad path as a message."""
    if project_path is None:
        return None
    try:
        return load(project_path)
    except (PlantLoadError, EditorSetupError) as exc:
        raise DesktopHostError(str(exc)) from exc


def _resolve_self_check_plan(
    *,
    self_check: bool,
    project_path: Path | None,
    scenario: str | None,
    projects: Sequence[Path],
    invalid_project: Path | None,
) -> DesktopSelfCheckPlan | None:
    """Return the validated self-check plan, or ``None`` when not self-checking.

    With no explicit scenario the behaviour is the Issue #97/#98 default: the
    ``loaded`` scenario when an initial path was given, ``empty`` otherwise. The
    ``transition`` scenario opens its own projects, so an initial path is
    contradictory and is rejected rather than silently ignored.
    """
    if not self_check:
        return None
    if scenario is None:
        scenario = (
            SELF_CHECK_SCENARIO_LOADED if project_path is not None else SELF_CHECK_SCENARIO_EMPTY
        )
    if scenario == SELF_CHECK_SCENARIO_TRANSITION and project_path is not None:
        raise DesktopHostError(
            "the transition self-check opens its own projects; do not pass a project path"
        )
    return plan_self_check(scenario, projects=projects, invalid_project=invalid_project)


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
            help="Automated packaged-desktop verification: probe the real page and exit.",
        ),
    ] = False,
    self_check_report: Annotated[
        Path | None,
        typer.Option("--self-check-report", help="Report path for --self-check."),
    ] = None,
    self_check_scenario: Annotated[
        str | None,
        typer.Option(
            "--self-check-scenario",
            help="empty | loaded | transition (defaults from the presence of a path).",
        ),
    ] = None,
    self_check_project: Annotated[
        list[Path] | None,
        typer.Option(
            "--self-check-project",
            help="For transition: a project to open, in order (repeat once per project).",
        ),
    ] = None,
    self_check_invalid_project: Annotated[
        Path | None,
        typer.Option(
            "--self-check-invalid-project",
            help="For transition: a model that must fail to load.",
        ),
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
            self_check_scenario=self_check_scenario,
            self_check_projects=tuple(self_check_project or ()),
            self_check_invalid_project=self_check_invalid_project,
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
