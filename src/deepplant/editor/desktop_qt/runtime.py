# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Desktop host lifecycle and runtime: the owned workspace/server and `run_host`.

`DesktopEditor` owns the native window, the editor workspace (an optional active
document), and exactly one long-lived loopback `EditorServer`; `run_host` starts
Qt, shows the window, and returns its exit code. Closing the window stops the
owned server and lets the process exit naturally. No engineering semantics are
decided here.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QUrl
from PySide6.QtWidgets import QApplication

from deepplant.editor import DEFAULT_HOST, DEFAULT_PORT
from deepplant.editor.api import EditorServer
from deepplant.editor.application import EditorApplication, EditorSetupError, EditorWorkspace
from deepplant.editor.desktop import (
    SELF_CHECK_SCENARIO_EMPTY,
    SELF_CHECK_SCENARIO_LOADED,
    DesktopSelfCheckPlan,
    ProjectLoader,
    editor_origin,
    initial_open_directory,
)
from deepplant.editor.desktop_qt.self_check import (
    finalize_self_check_after_loop,
    stage_log,
    start_self_check,
    write_json,
)
from deepplant.editor.desktop_qt.window import MainWindow
from deepplant.io import PlantLoadError


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


@dataclass(frozen=True)
class _ServerShutdown:
    """Truthful outcome of stopping the owned server (Issue #93 review).

    ``requested``/``stopped``/``thread_alive`` are *measured* facts, so the
    packaged self-check can distinguish "no server exists", "stop requested",
    "stopped successfully", and "stop timed out / still alive" instead of treating
    a cleared reference as proof that the serving thread exited.
    """

    requested: bool
    stopped: bool
    thread_alive: bool


class DesktopEditor:
    """Owns the window, the workspace, and the workspace's local server.

    Lifecycle (Issues #93, #97)::

        launch -> create window + empty workspace (optional initial document)
               -> start one long-lived local server
               -> show window -> load the shared SPA (workspace may be empty)
               -> File -> Open… -> activate a document -> reload the same SPA
               -> user closes the window -> server stops -> Qt exits

    Exactly one loopback :class:`~deepplant.editor.api.EditorServer` is owned for
    the life of the application, and it is bound to the workspace rather than to a
    single document, so opening or replacing a project is a workspace state change:
    the server, its listening socket, the native window and the embedded webview are
    never recreated.
    """

    def __init__(
        self,
        *,
        assets_dir: Path,
        loader: ProjectLoader,
        port: int,
        host: str,
        echo: Callable[[str], None],
    ) -> None:
        self._workspace = EditorWorkspace(assets_dir=assets_dir)
        self._loader = loader
        self._port = port
        self._host = host
        self._echo = echo
        self._server: EditorServer | None = None
        self._server_shutdown = _ServerShutdown(requested=False, stopped=False, thread_alive=False)
        self._open_directory = initial_open_directory()
        #: Set by the self-check before the first load; harmless when unset.
        self.page_loaded_hook: Callable[[bool], None] | None = None
        self._window = MainWindow(
            on_open=self.open_from_dialog,
            on_close=self.shutdown,
            on_page_loaded=self._dispatch_page_loaded,
            origin_provider=self.current_origin,
        )

    @property
    def window(self) -> MainWindow:
        return self._window

    @property
    def server(self) -> EditorServer | None:
        """The currently owned local server, or ``None`` before the session starts.

        A still-live server is deliberately retained after a failed stop, so this
        never reports ``None`` for a server whose thread is still running.
        """
        return self._server

    def current_origin(self) -> str | None:
        """The exact origin owned by the current server, or ``None``.

        This is the single value the webview's navigation policy compares against.
        Since Issue #97 the session keeps one long-lived server, so the origin stays
        stable while the workspace changes document. It is a method (not a property)
        because the page reads it live through a callback.
        """
        server = self._server
        if server is None:
            return None
        return editor_origin(server.host, server.port)

    @property
    def server_shutdown(self) -> _ServerShutdown:
        """The measured outcome of the most recent ``_stop_server`` call."""
        return self._server_shutdown

    def show(self) -> None:
        self._window.show()

    def start_session(self) -> None:
        """Start the long-lived server and show the shared SPA.

        Called once, before the event loop runs, for both the empty and the loaded
        workspace: either way it serves the *same* shared Vue editor.
        """
        server = EditorServer(self._workspace, host=self._host, port=self._port)
        server.start()
        self._server = server
        document_name = self._workspace.document_name
        self._echo(f"DeepPlant Editor: {document_name or 'no project open'} at {server.base_url}")
        self._window.show_editor(server.base_url, document_name)

    def open_project(self, application: EditorApplication) -> None:
        """Open (or replace) the active document in the existing editor session.

        This is a workspace *state* change: the same server, socket, window and
        webview are reused and the shared SPA is reloaded, so nothing leaks and no
        stale selection survives. The document is loaded through the ordinary
        application boundary *before* this call, so a failed load never reaches
        here and the previous document stays active.
        """
        self._workspace.activate(application)
        self._open_directory = str(application.project_path.parent)
        if self._server is None:
            self.start_session()
            return
        self._echo(f"DeepPlant Editor: opened {application.project_path}")
        self._window.reload_editor(self._workspace.document_name)

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

    def _stop_server(self) -> bool:
        """Stop the owned server and keep a truthful record of the outcome.

        A cleared ``self._server`` is **not** evidence that the serving thread
        exited. The reference is dropped only when :meth:`EditorServer.stop`
        reports that the thread actually terminated; otherwise the still-live
        server is retained so it stays discoverable and reportable, and ``False``
        is returned (Issue #93 review).

        Returns:
            ``True`` when the owned server is not running any more.
        """
        server = self._server
        if server is None:
            self._server_shutdown = _ServerShutdown(
                requested=True, stopped=True, thread_alive=False
            )
            return True
        stopped = server.stop()
        thread_alive = server.running
        self._server_shutdown = _ServerShutdown(
            requested=server.stop_requested, stopped=stopped, thread_alive=thread_alive
        )
        if stopped:
            self._server = None
            return True
        # Keep the owned server: it is still alive, and forgetting it would be the
        # false positive this invariant exists to prevent.
        self._echo("warning: the local editor server did not stop cleanly; it is still running")
        return False

    def _dispatch_page_loaded(self, ok: bool) -> None:
        hook = self.page_loaded_hook
        if hook is not None:
            hook(ok)


def _teardown_qt(editor: DesktopEditor, qt_application: QApplication) -> None:
    """Dispose the owned Qt/WebEngine objects before the interpreter exits.

    Closing the window ends the event loop; the remaining job is to let the process
    exit *naturally* instead of terminating it. Qt WebEngine is multiprocess and
    keeps a profile and helper threads alive, so the embedded view is stopped,
    detached from the now-closed server, and scheduled for deletion, and the
    deferred deletion is flushed before ``run_host`` returns and Python unwinds.

    This is deliberately small and destroys only what DeepPlant created. Qt owns its
    own ``QtWebEngineProcess`` helpers and reaps them once the page and profile are
    gone, so nothing is force-killed here.
    """
    window = editor.window
    view = window.web_view
    if view is not None:
        try:
            # Stop any in-flight load and detach from the closed server before the
            # object is destroyed, so Chromium does not chase a socket that is gone.
            view.stop()
            view.setUrl(QUrl("about:blank"))
        except RuntimeError:
            # The C++ object may already be gone during a platform-driven close.
            pass
        view.deleteLater()
    window.clear_web_view()
    window.close()
    qt_application.processEvents()
    # Flush the deferred deletion now, while there is still an event loop to run it,
    # rather than leaving the webview (and its engine profile) alive until the
    # interpreter tears globals down in an arbitrary order.
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qt_application.processEvents()


def run_host(
    *,
    assets_dir: Path,
    initial_application: EditorApplication | None,
    loader: ProjectLoader,
    port: int = DEFAULT_PORT,
    host: str = DEFAULT_HOST,
    echo: Callable[[str], None] = print,
    self_check: bool = False,
    report_path: Path | None = None,
    self_check_plan: DesktopSelfCheckPlan | None = None,
) -> int:
    """Start the Qt application, show the window, and return its exit code.

    Qt is configured, then used; nothing here decides engineering semantics. The
    window always shows the ordinary shared Vue editor (Issue #97): the workspace
    starts empty unless ``initial_application`` was supplied, in which case that
    document is activated before the single long-lived server starts.
    """
    _configure_webengine_for_this_process()
    if report_path is not None:
        stage_log(report_path, "host: starting")
    qt_instance = QApplication.instance()
    qt_application = qt_instance if isinstance(qt_instance, QApplication) else QApplication([])
    if report_path is not None:
        stage_log(report_path, "host: Qt application created")

    report: dict[str, object] | None = None
    try:
        editor = DesktopEditor(
            assets_dir=assets_dir, loader=loader, port=port, host=host, echo=echo
        )
        if self_check:
            if report_path is None:
                raise RuntimeError("the desktop self-check requires a report path")
            # Issue #97/#98 default when the caller gave no explicit plan: the
            # canonical fixture is the `loaded` scenario, no project the `empty`
            # one, and the project-replacement lifecycle is always explicit.
            plan = self_check_plan or DesktopSelfCheckPlan(
                scenario=(
                    SELF_CHECK_SCENARIO_LOADED
                    if initial_application is not None
                    else SELF_CHECK_SCENARIO_EMPTY
                )
            )
            # Armed before the first page load, so the hook is installed before the
            # embedded SPA can finish loading.
            report = start_self_check(
                editor,
                Path(report_path),
                echo=echo,
                finish=qt_application.exit,
                scenario=plan.scenario,
                projects=plan.projects,
                invalid_project=plan.invalid_project,
            )

        # One long-lived session for both the empty and the loaded workspace: the
        # server and the webview are not recreated when a project is opened. An
        # initial document is activated before the first page load, so the SPA's
        # first read already sees the requested workspace state.
        if initial_application is not None:
            editor.open_project(initial_application)
        else:
            editor.start_session()
        editor.show()
        if report_path is not None:
            stage_log(report_path, "host: window shown, entering the event loop")

        exit_code = int(qt_application.exec())
        if report_path is not None:
            stage_log(report_path, f"host: event loop returned {exit_code}")

        # Normal, successful lifecycle: the event loop has returned, so dispose the
        # owned Qt objects explicitly and let the interpreter finish and exit
        # naturally. The process is *not* force-terminated on this path - a close
        # that cannot unwind is a real product defect and must surface as one
        # (Issue #93 review).
        _teardown_qt(editor, qt_application)
        if report is not None and report_path is not None:
            finalize_self_check_after_loop(Path(report_path), report, editor)
        return exit_code
    except BaseException as exc:
        # Fatal/emergency fallback only. A failure while the Qt application already
        # exists must still be bounded and reported: tearing a half-constructed Qt
        # WebEngine application down at interpreter exit can block, which would
        # leave an automated caller waiting instead of receiving the reason. This is
        # never the successful close path - that path returns normally above.
        if report_path is None:
            raise
        stage_log(report_path, f"host: fatal {type(exc).__name__}: {exc}")
        write_json(
            report_path,
            {"verdict": "fail", "error": f"{type(exc).__name__}: {exc}"},
        )
        echo(f"self-check failed: {type(exc).__name__}: {exc}")
        os._exit(1)
        raise  # unreachable; keeps the return type honest for static analysis
