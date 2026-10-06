# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Native Qt window, embedded webview, and the local-only page policy.

The native presentation of the standalone Editor host: the menu, the
no-project bootstrap page, and the embedded `QWebEngineView` that renders the
ordinary production build of `apps/editor/`. The embedded page may only
navigate within the exact active `EditorServer` origin (a webview host policy,
not authentication). This module decides no engineering semantics and parses
no DeepPlant YAML.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Final

from PySide6.QtCore import QObject, Qt, QUrl
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
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

from deepplant.editor.desktop import (
    MODEL_FILE_FILTER,
    SMOKE_EXPECTED_STEPS,
    SMOKE_EXPECTED_STREAMS,
    SMOKE_PROBE_STEP_ID,
    WINDOW_TITLE,
    is_allowed_navigation,
)

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

#: The packaged self-check expectations describe the canonical, self-contained
#: smoke fixture (Issue #98). They are authored once in the Qt-free host module
#: (:mod:`deepplant.editor.desktop`) so the fixture and these values can be checked
#: together in the fast Python gate; the probe step resolves to a symbol role
#: through the ordinary engineering ``function`` -> role policy, so no presentation
#: override is needed.
PROBE_STEP_ID: Final[str] = SMOKE_PROBE_STEP_ID

EXPECTED_STEPS: Final[int] = SMOKE_EXPECTED_STEPS
EXPECTED_STREAMS: Final[int] = SMOKE_EXPECTED_STREAMS

CANVAS_PROBE_JS: Final[str] = f"""
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

INSPECTOR_PROBE_JS: Final[str] = """
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


class _LocalOnlyPage(QWebEnginePage):
    """A page that may only navigate within the active EditorServer origin.

    The embedded view shows the privileged local application, so a navigation that
    would replace it with another origin is refused. The policy is the pure,
    unit-tested :func:`deepplant.editor.desktop.is_allowed_navigation`, and the
    allowed origin is read *live* from the host so that opening another model -
    which replaces the server and may bind a different ephemeral port - moves the
    permitted origin to the new one (Issue #93 review).
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


class MainWindow(QMainWindow):
    """Native window: menu, bootstrap page, and the embedded web view."""

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
            view.setPage(_LocalOnlyPage(view, self._origin_provider))
            # Connected exactly once, at view creation, and before the first
            # `setUrl`, so no load can finish before the hook exists.
            view.loadFinished.connect(self._on_page_loaded)
            self._stack.addWidget(view)
            self._view = view
        self._stack.setCurrentWidget(self._view)
        self.setWindowTitle(f"{project_label} — {WINDOW_TITLE}")
        self._view.setUrl(QUrl(base_url))
        return self._view

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
            self._stack.removeWidget(view)

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
