# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""FastAPI/Uvicorn transport and local runtime for the Engineering Editor.

This module owns only the HTTP transport and the local server lifecycle. It
depends on the framework-independent application layer
(:mod:`deepplant.editor.application`); the application layer never depends on it.

Transport (Issue #79): FastAPI + Uvicorn. The surface is three read routes (one
JSON projection, the canonical symbol assets, and the built SPA assets). It is
loopback-only, single-user, unauthenticated, and makes no production or
server-security claim. Route handlers only receive a request, call
``EditorApplication``, and map its result to an HTTP response; no engineering
behaviour lives here.

Known limitation: the built SPA assets are read from the checkout
(``apps/editor/dist``); bundling them into the Python wheel is not done yet.
"""

from __future__ import annotations

import socket
from collections.abc import Callable
from typing import Final

import uvicorn
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from deepplant.editor.application import EditorApplication
from deepplant.render import ProcessRenderError

__all__ = [
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "create_editor_api",
    "serve_editor",
]

DEFAULT_HOST: str = "127.0.0.1"
DEFAULT_PORT: int = 8765

_PROJECTION_ROUTE: Final[str] = "/api/projection"
_SYMBOL_ROUTE: Final[str] = "/api/symbols/{symbol_role}"
_SVG_SUFFIX: Final[str] = ".svg"
_TEXT_CONTENT_TYPE: Final[str] = "text/plain; charset=utf-8"
_SVG_CONTENT_TYPE: Final[str] = "image/svg+xml; charset=utf-8"


def create_editor_api(editor: EditorApplication) -> FastAPI:
    """Build the FastAPI transport for one editor session.

    The returned application exposes exactly three read surfaces and holds no
    engineering logic: the projection view, the canonical packaged symbol
    assets, and the built SPA assets. It is an explicit factory rather than
    hidden module-level mutable state, so the HTTP layer is straightforward to
    test.
    """
    api = FastAPI(
        title="DeepPlant Engineering Editor",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    def read_projection() -> Response:
        view = editor.projection_view()
        return JSONResponse(
            status_code=200 if view.projectable else 422,
            content=view.to_envelope(),
        )

    def read_symbol(symbol_role: str) -> Response:
        # The canonical asset is ``<role>.svg``; accept the role with or without
        # the extension so the URL reads naturally.
        role = (
            symbol_role[: -len(_SVG_SUFFIX)] if symbol_role.endswith(_SVG_SUFFIX) else symbol_role
        )
        try:
            svg = editor.symbol_svg(role)
        except ProcessRenderError as exc:
            return Response(
                status_code=404,
                content=f"unknown symbol role: {exc}\n",
                media_type=_TEXT_CONTENT_TYPE,
            )
        return Response(content=svg, media_type=_SVG_CONTENT_TYPE)

    api.add_api_route(_PROJECTION_ROUTE, read_projection, methods=["GET", "HEAD"])
    api.add_api_route(_SYMBOL_ROUTE, read_symbol, methods=["GET", "HEAD"])
    api.mount("/", StaticFiles(directory=editor.assets_dir, html=True), name="editor-spa")
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


def serve_editor(
    application: EditorApplication,
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    echo: Callable[[str], None] = print,
) -> None:
    """Serve the local editor with Uvicorn until interrupted (usually Ctrl+C).

    The bind address defaults to loopback, so the editor is never exposed on
    ``0.0.0.0`` by default.
    """
    api = create_editor_api(application)
    config = uvicorn.Config(api, log_level="warning", access_log=False)
    listener = _bind_loopback_socket(host, port)
    try:
        echo("DeepPlant Engineering Editor (read-only Process/PFD)")
        echo(f"  project: {application.project_path}")
        echo(f"  open:    http://{host}:{listener.getsockname()[1]}/")
        echo("  press Ctrl+C to stop")
        uvicorn.Server(config).run(sockets=[listener])
    finally:
        listener.close()
