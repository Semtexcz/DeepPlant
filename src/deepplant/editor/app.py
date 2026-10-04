# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Engineering Editor application and HTTP boundary (Issues #75, #79).

The Engineering Editor is a standalone Vue SPA in ``apps/editor/`` that renders a
read-only Process/PFD view of one loaded DeepPlant project. This module owns the
framework-independent application state and the thin FastAPI transport that
exposes it to the browser::

    Vue SPA (apps/editor/)
        ↓  HTTP
    FastAPI adapter (create_editor_api)
        ↓
    EditorApplication (projection + symbol resolution)
        ↓
    DeepPlant semantic core, loader, and renderer

Engineering behaviour stays in :class:`EditorApplication` and below it
(``deepplant.editor.projection``, ``deepplant.render``, the semantic model); it is
never moved into a route handler. Route handlers only receive a request, call the
application, and map its result to an HTTP response. The application is usable and
testable from plain Python without FastAPI, and the semantic core never depends on
this module or on the GUI.

Transport (Issue #79): FastAPI + Uvicorn. The surface is still three read routes
(one JSON projection, the canonical symbol assets, and the built SPA assets). It
is loopback-only, single-user, unauthenticated, and makes no production or
server-security claim.

Known limitation: the built SPA assets are read from the checkout
(``apps/editor/dist``); bundling them into the Python wheel is not done yet.
"""

from __future__ import annotations

import socket
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import uvicorn
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from deepplant.editor.projection import (
    ProcessPfdProjection,
    ProcessPfdProjectionError,
    ValidationStatus,
    project_process_pfd,
    projection_to_dict,
)
from deepplant.io import load_plant
from deepplant.model import PlantModel
from deepplant.render import ProcessRenderError, read_process_symbol_svg

__all__ = [
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "EditorApplication",
    "EditorProjectionView",
    "EditorSetupError",
    "create_editor_api",
    "load_editor_application",
    "resolve_assets_dir",
    "serve_editor",
]

DEFAULT_HOST: str = "127.0.0.1"
DEFAULT_PORT: int = 8765

_PROJECTION_ROUTE: Final[str] = "/api/projection"
_SYMBOL_ROUTE: Final[str] = "/api/symbols/{symbol_role}"
_SVG_SUFFIX: Final[str] = ".svg"
_TEXT_CONTENT_TYPE: Final[str] = "text/plain; charset=utf-8"
_SVG_CONTENT_TYPE: Final[str] = "image/svg+xml; charset=utf-8"


class EditorSetupError(Exception):
    """Raised when the local editor cannot be started for the selected project."""


@dataclass(frozen=True)
class EditorProjectionView:
    """Transport-neutral result of projecting one model to a Process/PFD view.

    ``validation`` always reflects the semantic verdict from the ordinary
    DeepPlant loader. A missing ``projection`` is therefore a limitation of this
    view only: it never recasts a semantically valid model as invalid, and the
    separate ``error`` carries the presentation failure text.
    """

    validation: ValidationStatus
    projection: ProcessPfdProjection | None
    error: str | None

    @property
    def projectable(self) -> bool:
        return self.projection is not None

    def to_envelope(self) -> dict[str, object]:
        """JSON-ready response envelope shared by every transport."""
        envelope: dict[str, object] = {
            "validation": {
                "valid": self.validation.valid,
                "message": self.validation.message,
            },
            "projection": None if self.projection is None else projection_to_dict(self.projection),
        }
        if self.error is not None:
            envelope["error"] = self.error
        return envelope


@dataclass(frozen=True)
class EditorApplication:
    """Read-only local application state for one loaded DeepPlant project."""

    project_path: Path
    model: PlantModel
    assets_dir: Path
    symbol_pack: str = "basic"
    symbol_role_overrides: Mapping[str, str] | None = None

    def projection_view(self) -> EditorProjectionView:
        """Project the loaded model to a Process/PFD view result.

        Semantic validation truth comes from :func:`load_plant`: this application
        only exists after that loader returned a valid ``PlantModel``. A
        Process/PFD projection or rendering error is therefore reported
        separately, as a limitation of this view.
        """
        try:
            projection = project_process_pfd(
                self.model,
                symbol_pack=self.symbol_pack,
                symbol_role_overrides=self.symbol_role_overrides,
            )
        except (ProcessPfdProjectionError, ProcessRenderError) as exc:
            return EditorProjectionView(
                validation=ValidationStatus(valid=True, message="Valid"),
                projection=None,
                error=str(exc),
            )
        return EditorProjectionView(
            validation=projection.validation,
            projection=projection,
            error=None,
        )

    def symbol_svg(self, symbol_role: str) -> str:
        """Return the canonical packaged SVG text for one symbol role."""
        return read_process_symbol_svg(self.symbol_pack, symbol_role)


def resolve_assets_dir(explicit: Path | None) -> Path | None:
    """Return the directory holding the built editor assets, or ``None``.

    Resolution order: an explicit ``--assets-dir`` path, otherwise the checkout's
    ``apps/editor/dist`` relative to the current directory. A directory only
    counts when it actually contains ``index.html``, so a missing build is
    reported honestly instead of serving an empty canvas.
    """
    candidate = explicit if explicit is not None else Path.cwd() / "apps" / "editor" / "dist"
    return candidate if (candidate / "index.html").is_file() else None


def load_editor_application(
    project_path: Path,
    *,
    symbol_role_overrides: Mapping[str, str] | None = None,
    symbol_pack: str = "basic",
    assets_dir: Path | None = None,
) -> EditorApplication:
    """Load one project through the DeepPlant loader and resolve editor assets.

    Raises:
        PlantLoadError: If the project file cannot be read or validated. The
            message is the normal DeepPlant user-facing error text.
        EditorSetupError: If the built editor assets cannot be found.
    """
    model = load_plant(project_path)
    resolved_assets = resolve_assets_dir(assets_dir)
    if resolved_assets is None:
        raise EditorSetupError(
            "editor frontend assets were not found; build them first with "
            "`make frontend-build` (or `cd apps/editor && pnpm build`), or pass "
            "an explicit --assets-dir"
        )
    return EditorApplication(
        project_path=Path(project_path),
        model=model,
        assets_dir=resolved_assets,
        symbol_pack=symbol_pack,
        symbol_role_overrides=symbol_role_overrides,
    )


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
