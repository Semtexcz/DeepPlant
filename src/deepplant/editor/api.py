# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""FastAPI/Uvicorn transport and local runtime for the Engineering Editor.

This module owns only the HTTP transport and the local server lifecycle. It
depends on the framework-independent application layer
(:mod:`deepplant.editor.application`); the application layer never depends on it.

Transport (Issue #79): FastAPI + Uvicorn. The surface is three read routes (the
workspace/projection JSON, the canonical symbol assets, and the built SPA
assets). It is loopback-only, single-user, unauthenticated, and makes no
production or server-security claim. Route handlers only receive a request, call
an ``EditorWorkspace``, and map its result to an HTTP response; no engineering
behaviour lives here.

This is the only DeepPlant module that imports FastAPI and Uvicorn. Those are an
explicit installation extra (``deepplant[editor]``, Issue #85); callers probe
:func:`deepplant.editor.require_editor_dependencies` before importing this
module, and the standalone Editor distribution always contains them.

The SPA is served from whichever directory
:func:`deepplant.editor.application.resolve_assets_dir` resolved: the packaged
application's own resource directory, or the development checkout build. This
module does not know or care which.
"""

from __future__ import annotations

import socket
import sys
import threading
import time
from collections.abc import Callable
from typing import Final

import uvicorn
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from deepplant.editor import DEFAULT_HOST, DEFAULT_PORT
from deepplant.editor.application import WORKSPACE_STATE_EMPTY, EditorWorkspace
from deepplant.render import ProcessRenderError

__all__ = [
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "EditorServer",
    "create_editor_api",
    "serve_editor",
]

_PROJECTION_ROUTE: Final[str] = "/api/projection"
_SYMBOL_ROUTE: Final[str] = "/api/symbols/{symbol_role}"
_SVG_SUFFIX: Final[str] = ".svg"
_TEXT_CONTENT_TYPE: Final[str] = "text/plain; charset=utf-8"
_SVG_CONTENT_TYPE: Final[str] = "image/svg+xml; charset=utf-8"

# Bounded readiness probe used only when a caller wants to act on the moment the
# editor starts accepting connections (for example opening a browser).
_LISTENING_POLL_INTERVAL_S: Final[float] = 0.1
_LISTENING_TIMEOUT_S: Final[float] = 20.0

#: Bounded wait for a graceful Uvicorn shutdown before the caller gives up.
_SHUTDOWN_TIMEOUT_S: Final[float] = 10.0


def create_editor_api(workspace: EditorWorkspace) -> FastAPI:
    """Build the FastAPI transport for one editor session.

    The returned application exposes exactly three read surfaces and holds no
    engineering logic: the workspace/projection view, the canonical packaged
    symbol assets, and the built SPA assets. It is an explicit factory rather than
    hidden module-level mutable state, so the HTTP layer is straightforward to
    test.

    The transport reads the *live* workspace (Issue #97): activating a document
    changes what ``/api/projection`` reports, so opening a project is a state
    change rather than a new server.
    """
    api = FastAPI(
        title="DeepPlant Engineering Editor",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    def read_projection() -> Response:
        view = workspace.view()
        # An empty workspace is a successful, ordinary state (HTTP 200): no
        # document is open, so there is nothing to validate or project. HTTP 422
        # is reserved for a loaded document whose *current Process/PFD view*
        # cannot be produced - a view limitation, never the absence of a document.
        status_code = 200 if view.state == WORKSPACE_STATE_EMPTY or view.projectable else 422
        return JSONResponse(status_code=status_code, content=view.to_envelope())

    def read_symbol(symbol_role: str) -> Response:
        # The canonical asset is ``<role>.svg``; accept the role with or without
        # the extension so the URL reads naturally.
        role = (
            symbol_role[: -len(_SVG_SUFFIX)] if symbol_role.endswith(_SVG_SUFFIX) else symbol_role
        )
        try:
            svg = workspace.symbol_svg(role)
        except ProcessRenderError as exc:
            return Response(
                status_code=404,
                content=f"process symbol role is not available: {exc}\n",
                media_type=_TEXT_CONTENT_TYPE,
            )
        return Response(content=svg, media_type=_SVG_CONTENT_TYPE)

    api.add_api_route(_PROJECTION_ROUTE, read_projection, methods=["GET", "HEAD"])
    api.add_api_route(_SYMBOL_ROUTE, read_symbol, methods=["GET", "HEAD"])
    api.mount("/", StaticFiles(directory=workspace.assets_dir, html=True), name="editor-spa")
    return api


def _bind_loopback_socket(host: str, port: int) -> socket.socket:
    """Bind the listening socket so loopback-only binding stays explicit.

    Binding here (instead of letting Uvicorn bind internally) keeps the
    loopback-only guarantee visible and lets ``port=0`` report the real assigned
    port in the launch message.
    """
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind((host, port))
    return listener


def _await_listening(host: str, port: int, *, timeout: float) -> None:
    """Block until the loopback address accepts a connection, or raise.

    Readiness is proved by connecting to the kernel through the same loopback
    address the user is given, rather than by sleeping for a guessed interval.

    Raises:
        TimeoutError: If nothing accepts a connection within ``timeout`` seconds.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=_LISTENING_POLL_INTERVAL_S):
                return
        except OSError:
            time.sleep(_LISTENING_POLL_INTERVAL_S)
    raise TimeoutError(f"the editor server never accepted connections on {host}:{port}")


class EditorServer:
    """Owns the local loopback editor server for one editor workspace.

    Issue #93 needs a server the caller *owns*: the native desktop host starts it,
    shows the window, and must stop it deterministically when the window closes.
    The blocking :func:`serve_editor` (the terminal shape of ``deepplant ui``) is
    implemented on top of this class, so there is exactly one server lifecycle.

    Since Issue #97 the server is bound to an :class:`EditorWorkspace` rather than
    to one loaded document, so a single long-lived server keeps serving the same
    shared SPA while the workspace moves between "no project open" and "project
    open".

    The socket is bound in the constructor - before Uvicorn starts - so the real
    loopback URL is known (and can be embedded in the native window) *before* the
    server begins accepting. Only the given host is ever bound; the default is
    loopback, and there is no ``0.0.0.0`` path.
    """

    def __init__(
        self,
        workspace: EditorWorkspace,
        *,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
    ) -> None:
        self._host = host
        self._workspace = workspace
        self._config = uvicorn.Config(
            create_editor_api(workspace), log_level="warning", access_log=False
        )
        self._server = uvicorn.Server(self._config)
        self._listener = _bind_loopback_socket(host, port)
        self._bound_port = int(self._listener.getsockname()[1])
        self._thread: threading.Thread | None = None
        #: Whether a graceful stop has ever been requested. Kept separate from the
        #: thread state so a caller can distinguish "no stop was asked for" from
        #: "a stop was asked for and the thread is still alive" (Issue #93 review).
        self._stop_requested = False

    @property
    def workspace(self) -> EditorWorkspace:
        """The editor workspace this server exposes."""
        return self._workspace

    @property
    def host(self) -> str:
        """The bind host (loopback by default)."""
        return self._host

    @property
    def port(self) -> int:
        """The real bound port (resolved when ``port=0`` was requested)."""
        return self._bound_port

    @property
    def base_url(self) -> str:
        """The loopback URL a browser or embedded webview loads."""
        return f"http://{self._host}:{self._bound_port}/"

    @property
    def running(self) -> bool:
        """Whether the serving thread is currently alive.

        This stays truthful after a failed or timed-out :meth:`stop`: while the
        owned thread is alive it is still retained, so ``running`` reports ``True``
        rather than silently forgetting a live server (Issue #93 review).
        """
        return self._thread is not None and self._thread.is_alive()

    @property
    def stop_requested(self) -> bool:
        """Whether a graceful stop has been requested at least once."""
        return self._stop_requested

    def start(self, *, timeout: float = _LISTENING_TIMEOUT_S) -> None:
        """Start serving in a background thread and wait until it accepts.

        Raises:
            RuntimeError: If the server was already started.
            TimeoutError: If the loopback address does not accept in time. A
                partially started server is stopped before the error propagates.
        """
        if self._thread is not None:
            raise RuntimeError("the editor server has already been started")
        self._thread = threading.Thread(
            target=self._server.run,
            kwargs={"sockets": [self._listener]},
            name="deepplant-editor-server",
            daemon=True,
        )
        self._thread.start()
        try:
            _await_listening(self._host, self._bound_port, timeout=timeout)
        except TimeoutError:
            self.stop()
            raise

    def wait(self) -> None:
        """Block until the serving thread stops (the terminal ``ui`` shape)."""
        thread = self._thread
        if thread is not None:
            thread.join()

    def stop(self, *, timeout: float = _SHUTDOWN_TIMEOUT_S) -> bool:
        """Ask Uvicorn to exit, join the thread, and release the loopback socket.

        Deliberately non-raising: shutdown runs from a window-close handler and
        from ``finally`` blocks, so it must never mask the real reason the
        application is ending. It is idempotent - calling it twice, or on a
        server that never started, is safe - and bounded by ``timeout`` so a
        stalled server can never hang the caller.

        The return value is the *measured* truth about the owned thread, not a
        bookkeeping flag: ``True`` means the serving thread has actually
        terminated (or never ran), ``False`` means it was still alive when
        ``timeout`` elapsed. A timed-out stop deliberately **keeps** the thread
        reference and leaves the listener open, so :attr:`running` stays ``True``
        and a later ``stop()`` can still join the same owned thread instead of
        leaking the evidence of a live server (Issue #93 review).

        Returns:
            ``True`` when the serving thread has exited (or never ran),
            ``False`` when it was still alive after ``timeout`` seconds.
        """
        self._stop_requested = True
        self._server.should_exit = True
        thread = self._thread
        if thread is not None:
            thread.join(timeout=timeout)
            if thread.is_alive():
                # Still ours and still running: retain the reference so `running`
                # remains truthful and a later stop() can join it. The listener is
                # left open because the live thread still owns it.
                return False
            self._thread = None
        self._listener.close()
        return True


def serve_editor(
    workspace: EditorWorkspace,
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    echo: Callable[[str], None] = print,
    on_listening: Callable[[int], None] | None = None,
) -> None:
    """Serve the local editor workspace with Uvicorn until interrupted (Ctrl+C).

    The bind address defaults to loopback, so the editor is never exposed on
    ``0.0.0.0`` by default.

    ``on_listening`` is an optional readiness hook called once with the actual
    bound port after the server starts accepting connections. It is only a
    readiness notification; it is never used to change what the server serves.
    """
    server = EditorServer(workspace, host=host, port=port)
    echo("DeepPlant Engineering Editor (read-only Process/PFD)")
    document = workspace.active_document
    echo(f"  project: {document.project_path if document is not None else '(none)'}")
    echo(f"  open:    {server.base_url}")
    echo("  press Ctrl+C to stop")
    _flush_standard_streams()
    try:
        server.start()
        if on_listening is not None:
            on_listening(server.port)
        server.wait()
    finally:
        server.stop()


def _flush_standard_streams() -> None:
    """Flush the launch banner so a piped consumer sees the URL immediately.

    The announced URL is the readiness boundary for a user in a terminal and for
    automation. When stdout is a pipe rather than a terminal it is block
    buffered, so without this the banner can stay invisible until the process
    exits - which would make a packaged application look like it never started.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.flush()
        except (OSError, ValueError):
            continue
