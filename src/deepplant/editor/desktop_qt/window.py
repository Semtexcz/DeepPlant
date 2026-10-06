# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Native Qt window, embedded webview, and the local-only page policy.

The native presentation of the standalone Editor host: the File menu and the
single embedded `QWebEngineView` that renders the ordinary production build of
`apps/editor/`. The window always hosts that shared SPA - there is no native
start page and no second editor UI (Issue #97); the editor's own workspace state
is either empty or carries a loaded project. The embedded page may only navigate
within the exact active `EditorServer` origin (a webview host policy, not
authentication). This module decides no engineering semantics and parses no
DeepPlant YAML.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Final

from PySide6.QtCore import QObject, QUrl
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from deepplant.editor.desktop import MODEL_FILE_FILTER, WINDOW_TITLE, is_allowed_navigation

DEFAULT_WINDOW_WIDTH: Final[int] = 1280
DEFAULT_WINDOW_HEIGHT: Final[int] = 820


class _LocalOnlyPage(QWebEnginePage):
    """A page that may only navigate within the active EditorServer origin.

    The embedded view shows the privileged local application, so a navigation that
    would replace it with another origin is refused. The policy is the pure,
    unit-tested :func:`deepplant.editor.desktop.is_allowed_navigation`, and the
    allowed origin is read *live* from the host (Issue #93 review). Since Issue #97
    the session keeps one long-lived server, so the origin stays stable while the
    workspace opens or replaces a document.
    """

    def __init__(self, parent: QObject, origin_provider: Callable[[], str | None]) -> None:
        super().__init__(parent)
        self._origin_provider = origin_provider

    def acceptNavigationRequest(  # noqa: N802 - Qt API name
        self,
        url: QUrl | str,
        navigation_type: QWebEnginePage.NavigationType,
        is_main_frame: bool,
    ) -> bool:
        target = url.toString() if isinstance(url, QUrl) else url
        return is_allowed_navigation(target, allowed_origin=self._origin_provider())

    def createWindow(  # noqa: N802  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        window_type: QWebEnginePage.WebWindowType,
    ) -> QWebEnginePage | None:
        """Refuse pop-ups: the desktop host is not a general-purpose browser.

        Qt's C++ contract lets ``createWindow`` return ``nullptr`` to refuse the
        pop-up, which is exactly what this host wants; PySide6's stub types the
        return as non-optional, so this single override is annotated narrowly
        rather than the whole module being silenced.
        """
        return None


class MainWindow(QMainWindow):
    """Native window: the File menu and the single embedded web view.

    Issue #97 removed the native bootstrap page. The window always hosts the
    ordinary shared Vue editor, whose own workspace state is either empty (no
    project open) or carries a loaded project. Exactly one ``QWebEngineView`` is
    created and reused for the life of the application, so opening or replacing a
    project reloads the same view against the same long-lived server origin
    instead of creating a second window or webview.
    """

    def __init__(
        self,
        *,
        on_open: Callable[[], None],
        on_close: Callable[[], None],
        on_page_loaded: Callable[[bool], None],
        origin_provider: Callable[[], str | None],
    ) -> None:
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self._on_close = on_close
        self._on_page_loaded = on_page_loaded
        self._origin_provider = origin_provider
        self._view: QWebEngineView | None = None

        #: Automation seams used only by the packaged desktop self-check. Both are
        #: ``None`` in an ordinary session, so the native Open dialog and the
        #: blocking error message box remain the real user paths. The self-check
        #: points ``open_path_provider`` at a controlled path (bypassing the native
        #: file chooser) and records ``error_reporter`` instead of opening a modal
        #: dialog it cannot dismiss. The Open *implementation* - load through the
        #: ordinary boundary, then replace the document in the existing session -
        #: is identical either way.
        self.open_path_provider: Callable[[str], str | None] | None = None
        self.error_reporter: Callable[[str], None] | None = None

        # A plain container holds the single webview. It is not a second UI: it
        # only lets teardown detach the view without deleting it, preserving the
        # ownership semantics the earlier stacked widget provided.
        container = QWidget(self)
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(container)

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
        """The single embedded view, or ``None`` before the first page load."""
        return self._view

    def show_editor(self, base_url: str, project_label: str | None) -> QWebEngineView:
        """Create (once) and load the embedded SPA for the running server.

        ``project_label`` is the active document's file name, or ``None`` when no
        project is open; it only affects the window title.
        """
        view = self._ensure_view()
        self._set_window_label(project_label)
        view.setUrl(QUrl(base_url))
        return view

    def reload_editor(self, project_label: str | None) -> None:
        """Reload the shared SPA in the existing view after a workspace change.

        Opening or replacing a project is a workspace state change, not a new
        application: the same window, the same long-lived server and the same
        webview are reused, and a reload re-runs the SPA so it reads the new
        workspace state and drops any stale selection. A full reload also discards
        the previous page's JavaScript context, so an in-flight response for the
        previous document can never overwrite the new one.
        """
        view = self._view
        if view is None:
            return
        self._set_window_label(project_label)
        view.reload()

    def _ensure_view(self) -> QWebEngineView:
        """Create the single embedded view on first use and reuse it afterwards."""
        if self._view is None:
            view = QWebEngineView(self)
            view.setPage(_LocalOnlyPage(view, self._origin_provider))
            # Connected exactly once, at view creation, and before the first
            # `setUrl`, so no load can finish before the hook exists.
            view.loadFinished.connect(self._on_page_loaded)
            self._layout.addWidget(view)
            self._view = view
        return self._view

    def _set_window_label(self, project_label: str | None) -> None:
        self.setWindowTitle(
            WINDOW_TITLE if not project_label else f"{project_label} — {WINDOW_TITLE}"
        )

    def clear_web_view(self) -> None:
        """Drop the host's reference to the embedded view during teardown.

        Deleting the view alone is not enough for a deterministic shutdown: Qt
        WebEngine is multiprocess, and an interpreter that still holds the view (or
        its page) at exit can block while Chromium's helper threads unwind.
        Removing the reference here, together with the deferred deletion scheduled
        by :func:`_teardown_qt`, lets the page and its profile be destroyed before
        the interpreter starts to exit (Issue #93 review).
        """
        view = self._view
        self._view = None
        if view is not None:
            self._layout.removeWidget(view)
            view.setParent(None)

    def ask_for_model(self, directory: str) -> str | None:
        """Return the path the user chose for a model.

        In an ordinary session this runs the operating system's native Open
        dialog (path selection only). The packaged self-check may install a
        controlled path through :attr:`open_path_provider` instead, so the
        document-replacement lifecycle can be verified without brittle GUI mouse
        automation; the returned value is still loaded through the ordinary
        boundary.
        """
        provider = self.open_path_provider
        if provider is not None:
            return provider(directory)
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Open plant model",
            directory,
            MODEL_FILE_FILTER,
        )
        return selected or None

    def show_error(self, message: str) -> None:
        """Report a model/asset failure without a traceback.

        The real user path is a modal message box. The packaged self-check may
        install :attr:`error_reporter` instead of a dialog it cannot dismiss, so
        it can still assert that the failure was reported through this one
        user-facing mechanism.
        """
        reporter = self.error_reporter
        if reporter is not None:
            reporter(message)
            return
        QMessageBox.critical(self, WINDOW_TITLE, message)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 - Qt API name
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
