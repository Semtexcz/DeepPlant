"""Focused plain-Python tests for the Engineering Editor application layer.

These tests exercise the framework-independent application directly, without
constructing FastAPI or going through HTTP: ``EditorApplication.projection_view()``,
the ``EditorWorkspace`` session with and without an active document (Issue #97),
``load_editor_application()``, and ``resolve_assets_dir()`` (Issues #75, #79).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from deepplant.editor import application as application_module
from deepplant.editor.application import (
    EditorApplication,
    EditorSetupError,
    create_empty_workspace,
    load_editor_application,
    resolve_assets_dir,
)
from deepplant.io import PlantLoadError, load_plant
from deepplant.render import ProcessRenderError

REPO_ROOT = Path(__file__).resolve().parents[2]
REALISTIC_EXAMPLE = REPO_ROOT / "examples" / "realistic-process-fragment" / "plant.yaml"
#: The canonical self-contained smoke fixture: it projects with no override.
SMOKE_EXAMPLE = REPO_ROOT / "examples" / "process-graph" / "plant.yaml"
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


# --- The editor workspace exists independently of an active document (Issue #97) --


def test_an_empty_workspace_is_a_first_class_state_with_no_model(assets_dir: Path) -> None:
    """No project open is an ordinary state that carries no fabricated model.

    The empty state reports no validation verdict and no Process/PFD projection, so
    it can never be mistaken for invalid engineering data or a failed projection.
    """
    workspace = create_empty_workspace(assets_dir)

    view = workspace.view()

    assert view.state == "empty"
    assert view.has_document is False
    assert view.document is None
    assert view.validation is None
    assert view.projection is None
    assert view.error is None
    assert view.projectable is False


def test_an_empty_workspace_never_fabricates_a_symbol(assets_dir: Path) -> None:
    workspace = create_empty_workspace(assets_dir)

    with pytest.raises(ProcessRenderError):
        workspace.symbol_svg("pump")


def test_create_empty_workspace_requires_built_assets(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()

    with pytest.raises(EditorSetupError):
        create_empty_workspace(empty)


def test_activating_a_document_loads_it_and_clearing_returns_to_empty(assets_dir: Path) -> None:
    workspace = create_empty_workspace(assets_dir)
    assert workspace.view().state == "empty"

    workspace.activate(load_editor_application(SMOKE_EXAMPLE, assets_dir=assets_dir))

    loaded = workspace.view()
    assert loaded.state == "loaded"
    assert loaded.has_document is True
    assert loaded.document is not None
    assert loaded.document.name == SMOKE_EXAMPLE.name
    assert loaded.validation is not None
    assert loaded.validation.valid is True
    assert loaded.projectable is True

    workspace.clear()

    assert workspace.view().state == "empty"
    assert workspace.active_document is None


def test_a_loaded_but_unprojectable_document_is_still_loaded(assets_dir: Path) -> None:
    """A valid model whose Process/PFD view cannot be produced stays *loaded*.

    Workspace presence and view availability are separate (Issue #97): the model is
    semantically valid, so the workspace reports a loaded document while only the
    projection is missing. Distinguishing that for the user is Issue #99 and is not
    changed here.
    """
    workspace = create_empty_workspace(assets_dir)

    workspace.activate(load_editor_application(REALISTIC_EXAMPLE, assets_dir=assets_dir))

    view = workspace.view()
    assert view.state == "loaded"
    assert view.has_document is True
    assert view.validation is not None
    assert view.validation.valid is True
    assert view.projection is None
    assert view.error is not None


def test_a_failed_load_never_reaches_activation_so_the_workspace_stays_intact(
    assets_dir: Path,
) -> None:
    """Replacement loads through the boundary first, so a failure cannot corrupt it.

    The workspace is only mutated by :meth:`EditorWorkspace.activate`, which is
    reached after a successful load. A failed load raises at the ordinary loader
    boundary, leaving the currently active document exactly as it was.
    """
    workspace = create_empty_workspace(assets_dir)
    workspace.activate(load_editor_application(REALISTIC_EXAMPLE, assets_dir=assets_dir))

    with pytest.raises(PlantLoadError):
        load_editor_application(
            REPO_ROOT / "examples" / "does-not-exist.yaml", assets_dir=assets_dir
        )

    current = workspace.active_document
    assert current is not None
    assert current.project_path == REALISTIC_EXAMPLE
    assert workspace.view().state == "loaded"


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
