"""Focused plain-Python tests for the Engineering Editor application layer.

These tests exercise the framework-independent application directly, without
constructing FastAPI or going through HTTP: ``EditorApplication.projection_view()``,
``load_editor_application()``, and ``resolve_assets_dir()`` (Issues #75, #79).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from deepplant.editor import application as application_module
from deepplant.editor.application import (
    EditorApplication,
    load_editor_application,
    resolve_assets_dir,
)
from deepplant.io import PlantLoadError, load_plant

REPO_ROOT = Path(__file__).resolve().parents[2]
REALISTIC_EXAMPLE = REPO_ROOT / "examples" / "realistic-process-fragment" / "plant.yaml"
VESSEL_OVERRIDES = {"PS-vessel": "vessel"}


@pytest.fixture()
def assets_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "dist"
    directory.mkdir()
    (directory / "index.html").write_text("<!doctype html><p>DeepPlant</p>", encoding="utf-8")
    return directory


def test_application_projects_without_http(assets_dir: Path) -> None:
    """Engineering behaviour stays usable and testable without the HTTP layer."""
    application = load_editor_application(
        REALISTIC_EXAMPLE,
        symbol_role_overrides=VESSEL_OVERRIDES,
        assets_dir=assets_dir,
    )

    view = application.projection_view()

    assert view.projectable is True
    assert view.error is None
    assert view.projection is not None
    assert len(view.projection.steps) == 7
    assert len(view.projection.streams) == 7


def test_application_keeps_a_valid_but_unprojectable_model_valid(
    assets_dir: Path, tmp_path: Path
) -> None:
    plant_path = tmp_path / "no-process.yaml"
    plant_path.write_text("plant:\n  id: demo\nequipment: []\n", encoding="utf-8")
    application = EditorApplication(
        project_path=plant_path,
        model=load_plant(plant_path),
        assets_dir=assets_dir,
    )

    view = application.projection_view()

    assert view.validation.valid is True
    assert view.projection is None
    assert view.error is not None
    assert "no process model to project" in view.error


def test_load_editor_application_reports_a_missing_project(assets_dir: Path) -> None:
    with pytest.raises(PlantLoadError):
        load_editor_application(
            REPO_ROOT / "examples" / "does-not-exist.yaml", assets_dir=assets_dir
        )


def test_resolve_assets_dir_requires_a_built_editor_app(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()

    assert resolve_assets_dir(empty) is None

    explicit = tmp_path / "explicit" / "dist"
    explicit.mkdir(parents=True)
    (explicit / "index.html").write_text("<!doctype html>", encoding="utf-8")
    assert resolve_assets_dir(explicit) == explicit


def test_resolve_assets_dir_prefers_the_spa_shipped_with_the_application(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A packaged application finds its own SPA and never needs a checkout.

    This is the #85 ownership rule: the built frontend is an explicit resource
    of the editor application, so resolution uses the packaged resource first
    and the development checkout build only as a fallback.
    """
    packaged_root = tmp_path / "bundle" / "deepplant" / "editor"
    packaged_spa = packaged_root / "dist"
    packaged_spa.mkdir(parents=True)
    (packaged_spa / "index.html").write_text("<!doctype html>", encoding="utf-8")

    checkout_spa = tmp_path / "checkout" / "apps" / "editor" / "dist"
    checkout_spa.mkdir(parents=True)
    (checkout_spa / "index.html").write_text("<!doctype html>", encoding="utf-8")

    def fake_files(package: str) -> Path:
        return packaged_root

    monkeypatch.setattr(application_module.resources, "files", fake_files)
    monkeypatch.setattr(application_module, "_checkout_assets_dir", lambda: checkout_spa)

    assert resolve_assets_dir(None) == packaged_spa


def test_resolve_assets_dir_does_not_depend_on_the_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkout_spa = tmp_path / "checkout" / "apps" / "editor" / "dist"
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()

    monkeypatch.setattr(application_module, "_packaged_assets_dir", lambda: None)
    monkeypatch.setattr(application_module, "_checkout_assets_dir", lambda: checkout_spa)
    monkeypatch.chdir(elsewhere)

    assert resolve_assets_dir(None) is None

    checkout_spa.mkdir(parents=True)
    (checkout_spa / "index.html").write_text("<!doctype html>", encoding="utf-8")
    assert resolve_assets_dir(None) == checkout_spa
