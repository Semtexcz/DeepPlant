# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Local-only application boundary for the Engineering Editor slice.

The editor is a browser SPA over the existing Python DeepPlant core. This module
is the smallest practical boundary that lets the SPA reach that core without
re-implementing the loader, the semantic model, or the projection in the
browser:

    browser SPA  <->  this local boundary  <->  DeepPlant core

Chosen transport: the Python standard library ``http.server``. For this exact
slice the surface is three read routes (one JSON projection, the canonical symbol
assets, and the built frontend assets), so a small, explicit handler stays
maintenance-cheap and adds no runtime dependency. The boundary is deliberately
replaceable: the CLI uses only :class:`EditorApplication`,
:func:`load_editor_application`, and :func:`serve_editor`, so another transport
can replace this module without touching the projection, the semantic model, or
the frontend contract.

Security scope: this is a local, read-only, unauthenticated developer/product
tool. It binds to loopback by default, serves only the selected project (loaded
through the DeepPlant loader), and serves only the canonical packaged symbol
assets plus the built frontend directory. It makes no production or
server-security claim.

Known limitation of this first slice: the built frontend assets are read from the
checkout (``frontend/dist``); bundling them into the Python wheel is not done
here and is documented as a limitation in the architecture notes.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Final
from urllib.parse import unquote, urlsplit

from deepplant.editor.projection import (
    ProcessPfdProjectionError,
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
    "EditorSetupError",
    "create_editor_server",
    "load_editor_application",
    "resolve_assets_dir",
    "serve_editor",
]

DEFAULT_HOST: str = "127.0.0.1"
DEFAULT_PORT: int = 8765

_PROJECTION_ROUTE: Final[str] = "/api/projection"
_SYMBOL_ROUTE_PREFIX: Final[str] = "/api/symbols/"
_TEXT_CONTENT_TYPE: Final[str] = "text/plain; charset=utf-8"
_JSON_CONTENT_TYPE: Final[str] = "application/json; charset=utf-8"
_SVG_CONTENT_TYPE: Final[str] = "image/svg+xml; charset=utf-8"
_CONTENT_TYPES: Final[dict[str, str]] = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml; charset=utf-8",
    ".map": "application/json; charset=utf-8",
    ".ico": "image/x-icon",
    ".png": "image/png",
    ".woff2": "font/woff2",
}


class EditorSetupError(Exception):
    """Raised when the local editor cannot be started for the selected project."""


@dataclass(frozen=True)
class EditorApplication:
    """Read-only local application state for one loaded DeepPlant project."""

    project_path: Path
    model: PlantModel
    assets_dir: Path
    symbol_pack: str = "basic"
    symbol_role_overrides: Mapping[str, str] | None = None

    def projection_payload(self) -> tuple[int, dict[str, object]]:
        """Return ``(http_status, json_ready_payload)`` for the Process/PFD view.

        Semantic validation truth comes from :func:`load_plant`: this application
        only exists after that loader returned a valid ``PlantModel``. A Process/PFD
        projection or rendering error is therefore reported separately as a
        limitation of this view, never as an invalid semantic model.
        """
        try:
            projection = project_process_pfd(
                self.model,
                symbol_pack=self.symbol_pack,
                symbol_role_overrides=self.symbol_role_overrides,
            )
        except (ProcessPfdProjectionError, ProcessRenderError) as exc:
            return 422, {
                "validation": {"valid": True, "message": "Valid"},
                "projection": None,
                "error": str(exc),
            }
        return 200, {
            "validation": {
                "valid": projection.validation.valid,
                "message": projection.validation.message,
            },
            "projection": projection_to_dict(projection),
        }

    def symbol_svg(self, symbol_role: str) -> str:
        """Return the canonical packaged SVG text for one symbol role."""
        return read_process_symbol_svg(self.symbol_pack, symbol_role)


def resolve_assets_dir(explicit: Path | None) -> Path | None:
    """Return the directory holding the built editor assets, or ``None``.

    Resolution order: an explicit ``--assets-dir`` path, otherwise the checkout's
    ``frontend/dist`` relative to the current directory. A directory only counts
    when it actually contains ``index.html``, so a missing build is reported
    honestly instead of serving an empty canvas.
    """
    candidate = explicit if explicit is not None else Path.cwd() / "frontend" / "dist"
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
        EditorSetupError: If the built frontend assets cannot be found.
    """
    model = load_plant(project_path)
    resolved_assets = resolve_assets_dir(assets_dir)
    if resolved_assets is None:
        raise EditorSetupError(
            "editor frontend assets were not found; build them first with "
            "`make frontend-build` (or `cd frontend && pnpm build`), or pass an "
            "explicit --assets-dir"
        )
    return EditorApplication(
        project_path=Path(project_path),
        model=model,
        assets_dir=resolved_assets,
        symbol_pack=symbol_pack,
        symbol_role_overrides=symbol_role_overrides,
    )


def _content_type_for(path: Path) -> str:
    return _CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream")


def _is_within(candidate: Path, directory: Path) -> bool:
    try:
        candidate.relative_to(directory)
    except ValueError:
        return False
    return True


def _build_handler(application: EditorApplication) -> type[BaseHTTPRequestHandler]:
    """Build the request handler bound to one editor application."""
    assets_dir = application.assets_dir
    resolved_assets = assets_dir.resolve()

    class EditorRequestHandler(BaseHTTPRequestHandler):
        server_version = "DeepPlantEditor/0.1"
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *args: Any) -> None:
            # Stay quiet by default: the CLI prints the launch URL, and the local
            # tool should not emit a log line for every asset request.
            del format, args

        def do_GET(self) -> None:
            self._dispatch(head_only=False)

        def do_HEAD(self) -> None:
            self._dispatch(head_only=True)

        def _dispatch(self, *, head_only: bool) -> None:
            path = unquote(urlsplit(self.path).path)
            if path == _PROJECTION_ROUTE:
                status, payload = application.projection_payload()
                self._send_json(status, payload, head_only=head_only)
                return
            if path.startswith(_SYMBOL_ROUTE_PREFIX):
                self._send_symbol(path[len(_SYMBOL_ROUTE_PREFIX) :], head_only=head_only)
                return
            self._send_static(path, head_only=head_only)

        def _send_json(self, status: int, payload: dict[str, object], *, head_only: bool) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self._send_bytes(
                status,
                _JSON_CONTENT_TYPE,
                body,
                head_only=head_only,
                cache_control="no-store",
            )

        def _send_symbol(self, symbol_role: str, *, head_only: bool) -> None:
            # The canonical asset is ``<role>.svg``; accept the role with or
            # without the extension so the URL reads naturally.
            if symbol_role.endswith(".svg"):
                symbol_role = symbol_role[: -len(".svg")]
            try:
                svg = application.symbol_svg(symbol_role)
            except ProcessRenderError as exc:
                self._send_bytes(
                    404,
                    _TEXT_CONTENT_TYPE,
                    f"unknown symbol role: {exc}\n".encode(),
                    head_only=head_only,
                )
                return
            self._send_bytes(200, _SVG_CONTENT_TYPE, svg.encode("utf-8"), head_only=head_only)

        def _send_static(self, path: str, *, head_only: bool) -> None:
            relative = "index.html" if path in {"", "/"} else path.lstrip("/")
            candidate = (assets_dir / relative).resolve()
            if not _is_within(candidate, resolved_assets) or not candidate.is_file():
                self._send_bytes(404, _TEXT_CONTENT_TYPE, b"not found\n", head_only=head_only)
                return
            self._send_bytes(
                200,
                _content_type_for(candidate),
                candidate.read_bytes(),
                head_only=head_only,
            )

        def _send_bytes(
            self,
            status: int,
            content_type: str,
            body: bytes,
            *,
            head_only: bool,
            cache_control: str | None = None,
        ) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            if cache_control is not None:
                self.send_header("Cache-Control", cache_control)
            self.end_headers()
            if not head_only:
                self.wfile.write(body)

    return EditorRequestHandler


def create_editor_server(
    application: EditorApplication,
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> ThreadingHTTPServer:
    """Create, but do not start, the local editor server."""
    return ThreadingHTTPServer((host, port), _build_handler(application))


def serve_editor(
    application: EditorApplication,
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    echo: Callable[[str], None] = print,
) -> None:
    """Serve the local editor until interrupted (typically Ctrl+C).

    The bind address defaults to loopback, so the server is never exposed on
    ``0.0.0.0`` by default.
    """
    server = create_editor_server(application, host=host, port=port)
    echo("DeepPlant Engineering Editor (read-only Process/PFD)")
    echo(f"  project: {application.project_path}")
    echo(f"  open:    http://{host}:{server.server_port}/")
    echo("  press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
