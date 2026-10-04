"""Focused tests for the Engineering Editor application and FastAPI boundary.

These exercise the editor transport without a browser: the JSON projection
route, canonical symbol delivery, static asset delivery, honest failure for a
plant that cannot be projected, and the framework-independent application the
routes delegate to (Issues #75, #79).
"""

from __future__ import annotations

import json
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import cast

import httpx2
import pytest
from fastapi.testclient import TestClient

from deepplant import load_plant
from deepplant.editor.app import (
    EditorApplication,
    create_editor_api,
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


@pytest.fixture()
def client(assets_dir: Path) -> Iterator[TestClient]:
    with TestClient(create_editor_api(_application(assets_dir))) as test_client:
        yield test_client


def _envelope(response: httpx2.Response) -> dict[str, object]:
    parsed = json.loads(response.text)
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


def _sequence(value: object) -> Sequence[object]:
    assert isinstance(value, list)
    return cast("Sequence[object]", value)


def test_projection_route_returns_the_deepplant_projection(client: TestClient) -> None:
    response = client.get("/api/projection")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    payload = _envelope(response)
    assert _validation_of(payload) == {"valid": True, "message": "Valid"}
    projection = _projection_of(payload)
    assert len(_sequence(projection["steps"])) == 7
    assert len(_sequence(projection["streams"])) == 7


def test_symbol_route_serves_the_canonical_pack_asset(client: TestClient) -> None:
    response = client.get("/api/symbols/pump.svg")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml; charset=utf-8"
    assert "<svg" in response.text
    # The canonical asset is the packaged one, not a frontend copy.
    assert 'id="deepplant-anchors"' in response.text


def test_symbol_route_rejects_unknown_and_traversing_roles(client: TestClient) -> None:
    unknown = client.get("/api/symbols/not-a-role.svg")
    traversing = client.get("/api/symbols/..%2F..%2Fpyproject.svg")

    assert unknown.status_code == 404
    assert traversing.status_code == 404


def test_static_assets_are_served_from_the_editor_build(client: TestClient) -> None:
    root = client.get("/")
    asset = client.get("/app.js")

    assert root.status_code == 200
    assert "text/html" in root.headers["content-type"]
    assert "DeepPlant" in root.text
    assert asset.status_code == 200
    assert "console.log" in asset.text


def test_static_route_rejects_path_traversal(client: TestClient) -> None:
    response = client.get("/..%2Fpyproject.toml")

    assert response.status_code == 404


def test_head_request_reports_headers_without_a_body(client: TestClient) -> None:
    response = client.request("HEAD", "/api/projection")

    assert response.status_code == 200
    assert response.content == b""
    assert int(response.headers["content-length"]) > 0


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

    with TestClient(create_editor_api(application)) as scoped_client:
        response = scoped_client.get("/api/projection")

    assert response.status_code == 422
    payload = _envelope(response)
    assert _validation_of(payload) == {"valid": True, "message": "Valid"}
    assert payload["projection"] is None
    assert "no process model to project" in str(payload["error"])


def test_projection_route_keeps_a_valid_model_valid_when_its_role_is_unrenderable(
    assets_dir: Path,
) -> None:
    application = load_editor_application(REALISTIC_EXAMPLE, assets_dir=assets_dir)

    with TestClient(create_editor_api(application)) as scoped_client:
        response = scoped_client.get("/api/projection")

    assert response.status_code == 422
    payload = _envelope(response)
    assert _validation_of(payload) == {"valid": True, "message": "Valid"}
    assert payload["projection"] is None
    assert "PS-vessel" in str(payload["error"])


def test_application_projects_without_http(assets_dir: Path) -> None:
    """Engineering behaviour stays usable and testable without the HTTP layer."""
    view = _application(assets_dir).projection_view()

    assert view.projectable is True
    assert view.error is None
    assert view.projection is not None
    assert len(view.projection.steps) == 7
    assert len(view.projection.streams) == 7


def test_load_editor_application_reports_a_missing_project(assets_dir: Path) -> None:
    with pytest.raises(PlantLoadError):
        load_editor_application(
            REPO_ROOT / "examples" / "does-not-exist.yaml", assets_dir=assets_dir
        )


def test_resolve_assets_dir_requires_a_built_editor_app(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.chdir(tmp_path)

    assert resolve_assets_dir(empty) is None
    # No default checkout build is visible from this temporary working directory.
    assert resolve_assets_dir(None) is None

    default_dir = tmp_path / "apps" / "editor" / "dist"
    default_dir.mkdir(parents=True)
    (default_dir / "index.html").write_text("<!doctype html>", encoding="utf-8")
    assert resolve_assets_dir(None) == default_dir
