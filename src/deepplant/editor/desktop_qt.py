# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Qt/WebEngine native host for the shared Engineering Editor SPA (Issue #93).

This is the only DeepPlant module that imports a GUI toolkit. It is a *thin
host*: a native window, a native Open dialog, an embedded ``QWebEngineView``, and
the lifecycle that starts and stops the loopback server. It renders the ordinary
production build of ``apps/editor/`` and never re-implements engineering UI.

Dependency direction (one-way)::

    deepplant.editor.desktop_qt   (this module: PySide6 + Qt WebEngine)
        ↓
    deepplant.editor.api          (FastAPI/Uvicorn transport, EditorServer)
        ↓
    deepplant.editor.application  (framework-independent)
        ↓
    projection / renderer / semantic model

It is imported lazily by :mod:`deepplant.editor.desktop`, only after
:func:`deepplant.editor.require_desktop_dependencies` has succeeded, so the
semantic Core, the ordinary CLI, and the developer/browser host never depend on
it. PySide6 is verified in the native packaging jobs, not in the fast gate.
"""

from __future__ import annotations

import json
import os
import socket
import time
from collections.abc import Callable
from pathlib import Path
from typing import Final

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from deepplant.editor import DEFAULT_HOST, DEFAULT_PORT
from deepplant.editor.api import EditorServer
from deepplant.editor.application import EditorApplication, EditorSetupError
from deepplant.editor.desktop import (
    MODEL_FILE_FILTER,
    WINDOW_TITLE,
    ProjectLoader,
    initial_open_directory,
    is_allowed_navigation,
)
from deepplant.io import PlantLoadError

__all__ = ["run_host"]

DEFAULT_WINDOW_WIDTH: Final[int] = 1280
DEFAULT_WINDOW_HEIGHT: Final[int] = 820

#: Give the SPA a moment to render the graph and the Inspector after load and
#: after a synthetic selection. Bounded and explicit; the probe then reads the
#: real DOM rather than guessing that the application is ready.
POST_LOAD_SETTLE_MS: Final[int] = 1500
POST_SELECTION_SETTLE_MS: Final[int] = 600

#: Hard bound on one self-check run. A GUI process must never be able to hang an
#: automated caller: if a stalled webview, a blocking platform dialog, or any
#: other condition prevents the probe from finishing, the application still
#: writes a report and still exits with a non-zero code.
SELF_CHECK_TIMEOUT_MS: Final[int] = 90_000

#: The realistic fragment's step the packaged desktop workflow selects.
PROBE_STEP_ID: Final[str] = "PS-pump"

_EXPECTED_STEPS: Final[int] = 7
_EXPECTED_STREAMS: Final[int] = 7

_CANVAS_PROBE_JS: Final[str] = f"""
(() => {{
  const text = (el) => (el ? el.textContent.replace(/\\s+/g, ' ').trim() : null);
  const status = document.querySelector('[role="status"]');
  const steps = document.querySelectorAll('[role="group"][aria-label^="Process step "]');
  const streams = document.querySelectorAll('[role="group"][aria-label^="Process stream "]');
  const node = document.querySelector('[role="group"][aria-label="Process step {PROBE_STEP_ID}"]');
  if (node) {{
    const box = node.getBoundingClientRect();
    const init = {{
      bubbles: true,
      cancelable: true,
      view: window,
      clientX: box.left + box.width / 2,
      clientY: box.top + box.height / 2,
    }};
    for (const type of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) {{
      node.dispatchEvent(new MouseEvent(type, init));
    }}
  }}
  return JSON.stringify({{
    statusText: text(status),
    processSteps: steps.length,
    processStreams: streams.length,
    pumpNodeFound: node !== null,
    devEntryPoint: document.documentElement.outerHTML.includes('/src/main.ts'),
  }});
}})()
"""

_INSPECTOR_PROBE_JS: Final[str] = """
(() => {
  const text = (el) => (el ? el.textContent.replace(/\\s+/g, ' ').trim() : null);
  const inspector = document.querySelector('aside[aria-label="Inspector"]');
  const fields = {};
  if (inspector) {
    const terms = [...inspector.querySelectorAll('dt')];
    const definitions = [...inspector.querySelectorAll('dd')];
    terms.forEach((term, index) => {
      fields[text(term)] = definitions[index] ? text(definitions[index]) : null;
    });
  }
  return JSON.stringify({
    heading: inspector ? text(inspector.querySelector('h2')) : null,
    fields,
  });
})()
"""


def _configure_webengine_for_this_process() -> None:
    """Apply the one Qt WebEngine flag this application ever needs to set.

    Qt WebEngine is Chromium, which refuses to start its sandbox as ``root``. A
    containerised Linux CI job runs as root and would otherwise fail before the
    window appears. The flag is applied *only* when the process is actually root,
    so an ordinary user session keeps Chromium's sandbox untouched. The Chromium
    sandbox is never disabled globally, and no other flag is set here.

    Any further environment-specific Chromium flag (for example ``--disable-gpu``
    on a headless runner) is set explicitly by the caller through
    ``QTWEBENGINE_CHROMIUM_FLAGS`` - see docs/dev/workflow/packaging.md.
    """
    if os.name != "posix" or not hasattr(os, "geteuid"):
        return
    if os.geteuid() != 0:
        return
    existing = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
    if "--no-sandbox" not in existing:
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = f"{existing} --no-sandbox".strip()


class _LocalOnlyPage(QWebEnginePage):
    """A page that may only navigate within the local DeepPlant application.

    The embedded view shows the privileged local application, so a link that
    would replace it with an arbitrary external page is refused. The policy is
    the pure, unit-tested :func:`deepplant.editor.desktop.is_allowed_navigation`.
    """

    def acceptNavigationRequest(  # noqa: N802 - Qt API name
        self,
        url: QUrl,
        navigation_type: QWebEnginePage.NavigationType,
        is_main_frame: bool,
    ) -> bool:
        return is_allowed_navigation(url.toString())

    def createWindow(  # noqa: N802 - Qt API name
        self,
        window_type: QWebEnginePage.WebWindowType,
    ) -> QWebEnginePage | None:
        """Refuse pop-ups: the desktop host is not a general-purpose browser."""
        return None


def _bootstrap_page(on_open: Callable[[], None]) -> QWidget:
    """The no-project start page: identity plus the primary Open action.

    Deliberately minimal and native. It is host *bootstrap*, not a second
    frontend: it presents no engineering information and performs no engineering
    semantics. A shared Vue start screen remains possible later without changing
    this host's boundaries (see docs/dev/architecture/index.md).
    """
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.addStretch(1)

    title = QLabel("DeepPlant")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title.setStyleSheet("font-size: 28px; font-weight: 600;")
    layout.addWidget(title)

    subtitle = QLabel("Open a plant model to view its Process / PFD.")
    subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(subtitle)

    button = QPushButton("Open plant…")
    button.setMinimumWidth(200)
    button.setDefault(True)
    button.clicked.connect(on_open)
    layout.addSpacing(16)
    layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignHCenter)

    layout.addStretch(1)
    return page


class _MainWindow(QMainWindow):
    """Native window: menu, bootstrap page, and the embedded web view."""

    def __init__(
        self,
        *,
        on_open: Callable[[], None],
        on_close: Callable[[], None],
        on_page_loaded: Callable[[bool], None],
    ) -> None:
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self._on_close = on_close
        self._on_page_loaded = on_page_loaded
        self._view: QWebEngineView | None = None

        self._stack = QStackedWidget(self)
        self._stack.addWidget(_bootstrap_page(on_open))
        self.setCentralWidget(self._stack)

        file_menu = self.menuBar().addMenu("&File")
        open_action = QAction("&Open…", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(on_open)
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

    @property
    def web_view(self) -> QWebEngineView | None:
        """The embedded view, or ``None`` while no project has been opened."""
        return self._view

    def show_editor(self, base_url: str, project_label: str) -> QWebEngineView:
        """Show the embedded SPA for an already-running local server."""
        if self._view is None:
            view = QWebEngineView(self)
            view.setPage(_LocalOnlyPage(view))
            # Connected exactly once, at view creation, and before the first
            # `setUrl`, so no load can finish before the hook exists.
            view.loadFinished.connect(self._on_page_loaded)
            self._stack.addWidget(view)
            self._view = view
        self._stack.setCurrentWidget(self._view)
        self.setWindowTitle(f"{project_label} — {WINDOW_TITLE}")
        self._view.setUrl(QUrl(base_url))
        return self._view

    def ask_for_model(self, directory: str) -> str | None:
        """Run the operating system's native Open dialog (path selection only)."""
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Open plant model",
            directory,
            MODEL_FILE_FILTER,
        )
        return selected or None

    def show_error(self, message: str) -> None:
        """Report a model/asset failure without a traceback."""
        QMessageBox.critical(self, WINDOW_TITLE, message)

    def closeEvent(self, event: object) -> None:  # noqa: N802 - Qt API name
        """Stop owned resources and terminate the application.

        Closing the main window must end the application: it owns a local server
        and a native window, and leaving either behind would be wrong. The
        application does not rely on the ``quitOnLastWindowClosed`` default, so
        the behaviour is identical however the close was triggered (a user, the
        platform window manager, or an automation probe).
        """
        self._on_close()
        super().closeEvent(event)
        instance = QApplication.instance()
        if instance is not None:
            instance.quit()


def _initial_open_directory() -> str:
    """Return a usable starting directory for the native Open dialog.

    This must never raise. A graphical application has to start even when the
    platform cannot report a home directory (a service or locked-down session, a
    hardened CI runner); the Open dialog simply starts somewhere sensible.
    ``Path.home()`` raises ``RuntimeError`` in exactly those cases.
    """
    for candidate in (Path.home, Path.cwd):
        try:
            return str(candidate())
        except (OSError, RuntimeError):
            continue
    return ""


class _DesktopEditor:
    """Owns the window, the open project, and that project's local server.

    Lifecycle (Issue #93)::

        launch -> create window -> (optional) load model -> start local server
               -> show window -> load embedded SPA
               -> user closes the window -> server stops -> Qt exits

    Exactly one loopback :class:`~deepplant.editor.api.EditorServer` is owned at a
    time. Opening another model through the dialog replaces it deliberately, so
    no socket is ever leaked and nothing outside this application is signalled.
    """

    def __init__(
        self,
        *,
        loader: ProjectLoader,
        port: int,
        host: str,
        echo: Callable[[str], None],
    ) -> None:
        self._loader = loader
        self._port = port
        self._host = host
        self._echo = echo
        self._server: EditorServer | None = None
        self._open_directory = initial_open_directory()
        #: Set by the self-check before the first load; harmless when unset.
        self.page_loaded_hook: Callable[[bool], None] | None = None
        self._window = _MainWindow(
            on_open=self.open_from_dialog,
            on_close=self.shutdown,
            on_page_loaded=self._dispatch_page_loaded,
        )

    @property
    def window(self) -> _MainWindow:
        return self._window

    @property
    def server(self) -> EditorServer | None:
        """The currently owned local server, if a project is open."""
        return self._server

    def show(self) -> None:
        self._window.show()

    def open_project(self, application: EditorApplication) -> None:
        """Start the embedded server and show the shared SPA for one project."""
        self._stop_server()
        server = EditorServer(application, host=self._host, port=self._port)
        server.start()
        self._server = server
        self._open_directory = str(application.project_path.parent)
        self._echo(f"DeepPlant Editor: serving {application.project_path} at {server.base_url}")
        self._window.show_editor(server.base_url, application.project_path.name)

    def open_from_dialog(self) -> None:
        """Run the native Open dialog, then load the selected model.

        The dialog selects a *path*; the model is loaded through the ordinary
        DeepPlant application boundary. No YAML is parsed here.
        """
        selected = self._window.ask_for_model(self._open_directory)
        if selected is None:
            return
        selected_path = Path(selected)
        try:
            application = self._loader(selected_path)
        except (PlantLoadError, EditorSetupError) as exc:
            self._window.show_error(str(exc))
            return
        self.open_project(application)

    def shutdown(self) -> None:
        """Stop the owned server (called once, from the window close handler)."""
        self._stop_server()

    def _stop_server(self) -> None:
        server = self._server
        self._server = None
        if server is not None and not server.stop():
            self._echo("warning: the local editor server did not stop cleanly")

    def _dispatch_page_loaded(self, ok: bool) -> None:
        hook = self.page_loaded_hook
        if hook is not None:
            hook(ok)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    """Write one JSON report, creating the parent directory if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _stage_log(report_path: Path, message: str) -> None:
    """Append one diagnostic line next to the self-check report.

    A packaged Windows Editor is a GUI (``--windowed``) executable with no
    console, so stdout/stderr carry nothing. This is the deliberate diagnostics
    path for that case: a small stage log beside the machine-readable report, so
    a stalled or failing run is diagnosable instead of silent.
    """
    log_path = report_path.with_name(report_path.name + ".log")
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{time.monotonic():.3f} {message}\n")
    except OSError:
        # Diagnostics must never break the application under test.
        return


def _port_accepts(port: int) -> bool:
    """Whether the loopback port still accepts connections."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1.0):
            return True
    except OSError:
        return False


def _parse_probe(raw: object) -> dict[str, object]:
    """Narrow a JavaScript probe result into a plain mapping (never raise)."""
    if not isinstance(raw, str):
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    return {str(key): value for key, value in parsed.items()}


def _self_check_verdict(
    canvas: dict[str, object],
    inspector: dict[str, object],
) -> tuple[bool, dict[str, object]]:
    """Decide whether the real embedded application matched the expectations.

    The checks are read from the *rendered* page via the webview's JavaScript
    engine - the production host and the production SPA, not a mock.
    """
    fields_raw = inspector.get("fields")
    fields: dict[str, object] = fields_raw if isinstance(fields_raw, dict) else {}
    checks: dict[str, object] = {
        "validationValid": canvas.get("statusText") == "Valid",
        "processSteps": canvas.get("processSteps") == _EXPECTED_STEPS,
        "processStreams": canvas.get("processStreams") == _EXPECTED_STREAMS,
        "pumpSelected": inspector.get("heading") == PROBE_STEP_ID,
        "inspectorFunction": fields.get("Function") == "pumping",
        "productionSpa": canvas.get("devEntryPoint") is False,
    }
    passed = all(value is True for value in checks.values())
    return passed, {
        "verdict": "pass" if passed else "fail",
        "checks": checks,
        "canvas": canvas,
        "inspector": inspector,
    }


def _start_self_check(
    editor: _DesktopEditor,
    report_path: Path,
    *,
    echo: Callable[[str], None],
    finish: Callable[[int], None],
    has_project: bool,
) -> None:
    """Drive the packaged-desktop verification through the real application.

    Issue #93 requires the packaged Windows/Linux artifacts to prove the actual
    graphical product, not merely that an HTTP endpoint answered. This narrow,
    documented test hook launches the ordinary application, shows the real native
    window, drives the real embedded SPA through Qt's own JavaScript engine, then
    closes the window through the same ``closeEvent`` a user triggers and records
    whether the owned server and socket went away.

    It adds no production protocol: normal builds never enter it, and the state it
    reads is the state the application already has.
    """
    results: dict[str, object] = {}
    finished = False

    def finish_once(code: int) -> None:
        """Finish exactly once, so a late timer cannot restart the loop exit."""
        nonlocal finished
        if finished:
            return
        finished = True
        _stage_log(report_path, f"finish: exit code {code}")
        finish(code)

    def fail(message: str) -> None:
        _stage_log(report_path, f"fail: {message}")
        _write_json(report_path, {"verdict": "fail", "error": message})
        echo(f"self-check failed: {message}")
        finish_once(1)

    def failed_guard(step: str, work: Callable[[], None]) -> None:
        """Run one probe step, reporting an unexpected error instead of hanging.

        An exception raised inside a Qt callback would otherwise be printed to a
        stream a GUI build may not have and would leave the event loop running
        forever, which is exactly the failure mode automated callers cannot
        diagnose.
        """
        try:
            work()
        except Exception as exc:  # noqa: BLE001 - reported, never swallowed
            fail(f"{step} raised {type(exc).__name__}: {exc}")

    def finalize() -> None:
        _stage_log(report_path, "finalize: begin")
        window = editor.window
        visible_before_close = window.isVisible()
        server = editor.server
        port_before_close = server.port if server is not None else None

        # The real close path: `closeEvent` -> stop the owned server -> Qt quits.
        window.close()
        window_closed = not window.isVisible()
        server_stopped = editor.server is None
        port_released = port_before_close is None or not _port_accepts(port_before_close)

        canvas = results.get("canvas")
        inspector = results.get("inspector")
        if has_project:
            content_passed, report = _self_check_verdict(canvas, inspector)
        else:
            content_passed, report = True, {"checks": {}}

        checks: dict[str, object] = dict(report["checks"])
        checks["windowVisible"] = visible_before_close
        checks["windowClosed"] = window_closed
        checks["serverStopped"] = server_stopped
        checks["portReleased"] = port_released
        lifecycle_passed = (
            visible_before_close and window_closed and server_stopped and port_released
        )
        passed = bool(content_passed and lifecycle_passed)
        report["checks"] = checks
        report["verdict"] = "pass" if passed else "fail"
        report["windowTitle"] = WINDOW_TITLE
        _write_json(report_path, report)
        echo(f"self-check verdict: {report['verdict']}")
        finish_once(0 if passed else 1)

    def probe_canvas() -> None:
        _stage_log(report_path, "probe: canvas")
        view = editor.window.web_view
        if view is None:
            fail("the native window never created an embedded view")
            return
        view.page().runJavaScript(_CANVAS_PROBE_JS, after_canvas)

    def after_canvas(raw: object) -> None:
        def handle() -> None:
            canvas = _parse_probe(raw)
            _stage_log(report_path, f"probe: canvas result {bool(canvas)}")
            if not canvas:
                fail("the canvas probe returned no usable result")
                return
            results["canvas"] = canvas
            QTimer.singleShot(POST_SELECTION_SETTLE_MS, lambda: probe_inspector(canvas))

        failed_guard("the canvas probe", handle)

    def probe_inspector(canvas: dict[str, object]) -> None:
        view = editor.window.web_view
        if view is None:
            fail("the embedded view disappeared")
            return
        view.page().runJavaScript(
            _INSPECTOR_PROBE_JS,
            lambda raw: after_inspector(canvas, raw),
        )

    def after_inspector(canvas: dict[str, object], raw: object) -> None:
        del canvas

        def handle() -> None:
            results["inspector"] = _parse_probe(raw)
            _stage_log(report_path, "probe: inspector done")
            finalize()

        failed_guard("the inspector probe", handle)

    def on_loaded(ok: bool) -> None:
        _stage_log(report_path, f"page loaded: {ok}")
        if not ok:
            fail("the embedded page did not finish loading")
            return
        QTimer.singleShot(
            POST_LOAD_SETTLE_MS, lambda: failed_guard("the canvas probe", probe_canvas)
        )

    # The watchdog is armed before anything else, so no probe, dialog, or stalled
    # webview can keep the process alive past the caller's patience.
    _stage_log(report_path, "self-check: watchdog armed")
    QTimer.singleShot(
        SELF_CHECK_TIMEOUT_MS,
        lambda: fail(f"the self-check did not finish within {SELF_CHECK_TIMEOUT_MS} ms"),
    )

    if not has_project:
        # No model was supplied: the bootstrap window is the thing under test.
        QTimer.singleShot(POST_LOAD_SETTLE_MS, lambda: failed_guard("the window check", finalize))
        return

    editor.page_loaded_hook = on_loaded


def run_host(
    *,
    initial_application: EditorApplication | None,
    loader: ProjectLoader,
    port: int = DEFAULT_PORT,
    host: str = DEFAULT_HOST,
    echo: Callable[[str], None] = print,
    self_check: bool = False,
    report_path: Path | None = None,
) -> int:
    """Start the Qt application, show the window, and return its exit code.

    Qt is configured, then used; nothing here decides engineering semantics. The
    window is shown with the bootstrap page when no project was supplied, which is
    the primary end-user workflow.
    """
    _configure_webengine_for_this_process()
    if report_path is not None:
        _stage_log(report_path, "host: starting")
    qt_instance = QApplication.instance()
    qt_application = qt_instance if isinstance(qt_instance, QApplication) else QApplication([])
    if report_path is not None:
        _stage_log(report_path, "host: Qt application created")

    try:
        editor = _DesktopEditor(loader=loader, port=port, host=host, echo=echo)
        if self_check:
            if report_path is None:
                raise RuntimeError("the desktop self-check requires a report path")
            _start_self_check(
                editor,
                Path(report_path),
                echo=echo,
                finish=qt_application.exit,
                has_project=initial_application is not None,
            )

        if initial_application is not None:
            editor.open_project(initial_application)
        editor.show()
        if report_path is not None:
            _stage_log(report_path, "host: window shown, entering the event loop")

        exit_code = int(qt_application.exec())
        if report_path is not None:
            _stage_log(report_path, f"host: event loop returned {exit_code}")
        # Terminate the process directly. Qt WebEngine keeps global state that can
        # block interpreter shutdown even when no page was ever created, and a
        # desktop application whose window has closed must not linger: the
        # requirement is that closing the window ends the application and the
        # helpers it owns, not that Python's finalizers happen to run.
        os._exit(exit_code)
    except BaseException as exc:
        # A failure while the Qt application already exists must still be bounded
        # and reported: tearing a half-constructed Qt application down at
        # interpreter exit can block, which would leave an automated caller
        # waiting instead of receiving the reason.
        if report_path is None:
            raise
        _stage_log(report_path, f"host: fatal {type(exc).__name__}: {exc}")
        _write_json(
            report_path,
            {"verdict": "fail", "error": f"{type(exc).__name__}: {exc}"},
        )
        echo(f"self-check failed: {type(exc).__name__}: {exc}")
        os._exit(1)
        raise  # unreachable; keeps the return type honest for static analysis
