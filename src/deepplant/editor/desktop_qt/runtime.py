# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Desktop host lifecycle and runtime: the owned server and `run_host`.

`DesktopEditor` owns the native window, the open project, and exactly one
loopback `EditorServer` at a time; `run_host` starts Qt, shows the window, and
returns its exit code. Closing the window stops the owned server and lets the
process exit naturally. No engineering semantics are decided here.
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
from deepplant.editor.application import EditorApplication, EditorSetupError
from deepplant.editor.desktop import (
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
        """The currently owned local server, if a project is open.

        A still-live server is deliberately retained after a failed stop, so this
        never reports ``None`` for a server whose thread is still running.
        """
        return self._server

    def current_origin(self) -> str | None:
        """The exact origin owned by the current server, or ``None``.

        This is the single value the embedded webview's navigation policy compares
        against, so opening another model - which starts a new server on a possibly
        different ephemeral port - moves the permitted origin to the new one. It is
        a method (not a property) because the page reads it live through a
        callback.
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

    def open_project(self, application: EditorApplication) -> None:
        """Start the embedded server and show the shared SPA for one project."""
        if not self._stop_server():
            self._window.show_error(
                "The previous local editor server did not stop, so this model was "
                "not opened. Close the application and try again."
            )
            return
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
        stage_log(report_path, "host: starting")
    qt_instance = QApplication.instance()
    qt_application = qt_instance if isinstance(qt_instance, QApplication) else QApplication([])
    if report_path is not None:
        stage_log(report_path, "host: Qt application created")

    report: dict[str, object] | None = None
    try:
        editor = DesktopEditor(loader=loader, port=port, host=host, echo=echo)
        if self_check:
            if report_path is None:
                raise RuntimeError("the desktop self-check requires a report path")
            report = start_self_check(
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
