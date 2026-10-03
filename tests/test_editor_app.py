"""Focused tests for the local editor application boundary (Issue #75).

These exercise the transport behaviour without a browser: the JSON projection
route, canonical symbol delivery, static asset delivery, and honest failure for
a plant that cannot be projected.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Generator
from contextlib import contextmanager
from http.client import HTTPConnection
from pathlib import Path
from typing import cast

import pytest

from deepplant import load_plant
from deepplant.editor.app import (
    DEFAULT_HOST,
    EditorApplication,
    create_editor_server,
    load_editor_application,
    resolve_assets_dir,
)
from deepplant.io import PlantLoadError

REPO_ROOT = Path(__file__).resolve().parents[1]
REALISTIC_EXAMPLE = REPO_ROOT / "examples" / "realistic-process-fragment" / "plant.yaml"
VESSEL_OVERRIDES = {"PS-vessel": "vessel"}


@pytest.fixture()
def assets_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "dist"
    directory.mkdir()
    (directory / "index.html").write_text("<!doctype html><p>DeepPlant</p>", encoding="utf-8")
    (directory / "app.js").write_text("console.log('editor');", encoding="utf-8")
    return directory


def _application(assets_dir: Path) -> EditorApplication:
    return load_editor_application(
        REALISTIC_EXAMPLE,
        symbol_role_overrides=VESSEL_OVERRIDES,
        assets_dir=assets_dir,
    )


@contextmanager
def _served(application: EditorApplication) -> Generator[int, None, None]:
    server = create_editor_server(application, host=DEFAULT_HOST, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_port
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@contextmanager
def _connection(port: int) -> Generator[HTTPConnection, None, None]:
    connection = HTTPConnection(DEFAULT_HOST, port, timeout=5)
    try:
        yield connection
    finally:
        connection.close()


def _request(port: int, path: str, *, method: str = "GET") -> tuple[int, dict[str, str], bytes]:
    with _connection(port) as connection:
        connection.request(method, path)
        response = connection.getresponse()
        body = response.read()
        headers = {key.lower(): value for key, value in response.getheaders()}
        return response.status, headers, body


def _json(body: bytes) -> dict[str, object]:
    parsed = json.loads(body.decode("utf-8"))
    assert isinstance(parsed, dict)
    return cast("dict[str, object]", parsed)


def _projection_of(payload: dict[str, object]) -> dict[str, object]:
    projection = payload["projection"]
    assert isinstance(projection, dict)
    return cast("dict[str, object]", projection)


def _validation_of(payload: dict[str, object]) -> dict[str, object]:
    validation = payload["validation"]
    assert isinstance(validation, dict)
    return cast("dict[str, object]", validation)


def test_projection_route_returns_the_deepplant_projection(assets_dir: Path) -> None:
    with _served(_application(assets_dir)) as port:
        status, headers, body = _request(port, "/api/projection")

    assert status == 200
    assert headers["content-type"] == "application/json; charset=utf-8"
    payload = _json(body)
    assert _validation_of(payload) == {"valid": True, "message": "Valid"}
    projection = _projection_of(payload)
    steps = cast("list[object]", projection["steps"])
    streams = cast("list[object]", projection["streams"])
    assert len(steps) == 7
    assert len(streams) == 7


def test_symbol_route_serves_the_canonical_pack_asset(assets_dir: Path) -> None:
    with _served(_application(assets_dir)) as port:
        status, headers, body = _request(port, "/api/symbols/pump.svg")

    assert status == 200
    assert headers["content-type"] == "image/svg+xml; charset=utf-8"
    text = body.decode("utf-8")
    assert "<svg" in text
    # The canonical asset is the packaged one, not a frontend copy.
    assert 'id="deepplant-anchors"' in text


def test_symbol_route_rejects_unknown_and_traversing_roles(assets_dir: Path) -> None:
    with _served(_application(assets_dir)) as port:
        unknown, _, _ = _request(port, "/api/symbols/not-a-role.svg")
        traversing, _, _ = _request(port, "/api/symbols/..%2F..%2Fpyproject.svg")

    assert unknown == 404
    assert traversing == 404


def test_static_assets_are_served_from_the_frontend_build(assets_dir: Path) -> None:
    with _served(_application(assets_dir)) as port:
        root_status, root_headers, root_body = _request(port, "/")
        asset_status, _, asset_body = _request(port, "/app.js")

    assert root_status == 200
    assert "text/html" in root_headers["content-type"]
    assert b"DeepPlant" in root_body
    assert asset_status == 200
    assert b"console.log" in asset_body


def test_static_route_rejects_path_traversal(assets_dir: Path) -> None:
    with _served(_application(assets_dir)) as port:
        status, _, _ = _request(port, "/../pyproject.toml")

    assert status == 404


def test_head_request_reports_headers_without_a_body(assets_dir: Path) -> None:
    with _served(_application(assets_dir)) as port:
        status, headers, body = _request(port, "/api/projection", method="HEAD")

    assert status == 200
    assert body == b""
    assert int(headers["content-length"]) > 0


def test_projection_route_reports_an_honest_failure_without_a_process(
    assets_dir: Path, tmp_path: Path
) -> None:
    plant_path = tmp_path / "no-process.yaml"
    plant_path.write_text("plant:\n  id: demo\nequipment: []\n", encoding="utf-8")
    application = EditorApplication(
        project_path=plant_path,
        model=load_plant(plant_path),
        assets_dir=assets_dir,
    )

    with _served(application) as port:
        status, _, body = _request(port, "/api/projection")

    assert status == 422
    payload = _json(body)
    validation = _validation_of(payload)
    assert validation["valid"] is False
    assert "no process model to project" in str(validation["message"])


def test_load_editor_application_reports_a_missing_project(assets_dir: Path) -> None:
    with pytest.raises(PlantLoadError):
        load_editor_application(
            REPO_ROOT / "examples" / "does-not-exist.yaml", assets_dir=assets_dir
        )


def test_resolve_assets_dir_requires_a_built_frontend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.chdir(tmp_path)

    assert resolve_assets_dir(empty) is None
    # No default checkout build is visible from this temporary working directory.
    assert resolve_assets_dir(None) is None

    default_dir = tmp_path / "frontend" / "dist"
    default_dir.mkdir(parents=True)
    (default_dir / "index.html").write_text("<!doctype html>", encoding="utf-8")
    assert resolve_assets_dir(None) == default_dir
