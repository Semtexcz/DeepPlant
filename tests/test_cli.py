import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from deepplant import __version__
from deepplant.__main__ import app, main
from deepplant.editor.application import EditorApplication

runner = CliRunner()

EXAMPLE = Path(__file__).parents[1] / "examples" / "minimal-process" / "plant.yaml"
PROCESS_EXAMPLE = Path(__file__).parents[1] / "examples" / "process-graph" / "plant.yaml"
REALISTIC_EXAMPLE = (
    Path(__file__).parents[1] / "examples" / "realistic-process-fragment" / "plant.yaml"
)


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert f"DeepPlant {__version__}" in result.stdout


def test_help_shows_usage() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "version" in result.stdout
    assert "validate" in result.stdout


def test_bare_invocation_shows_help(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["deepplant"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0


def test_validate_succeeds_for_example() -> None:
    result = runner.invoke(app, ["validate", str(EXAMPLE)])

    assert result.exit_code == 0
    assert "✓ valid DeepPlant model" in result.output
    assert "✓ plant: demo" in result.output
    assert "✓ equipment: 2" in result.output
    assert "✓ ports: 3" in result.output
    assert "✓ connections: 1" in result.output


def test_validate_succeeds_for_process_graph_example() -> None:
    result = runner.invoke(app, ["validate", str(PROCESS_EXAMPLE)])

    assert result.exit_code == 0
    assert "✓ valid DeepPlant model" in result.output
    assert "✓ plant: demo" in result.output
    assert "✓ equipment: 0" in result.output
    assert "✓ ports: 0" in result.output
    assert "✓ connections: 0" in result.output


def test_validate_succeeds_for_realistic_process_fragment_example() -> None:
    result = runner.invoke(app, ["validate", str(REALISTIC_EXAMPLE)])

    assert result.exit_code == 0
    assert "✓ valid DeepPlant model" in result.output
    assert "✓ plant: demo" in result.output
    assert "✓ equipment: 5" in result.output
    assert "✓ ports: 9" in result.output
    assert "✓ connections: 2" in result.output


def test_validate_returns_nonzero_for_invalid_model(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text(
        "plant:\n  id: demo\nequipment:\n  - id: T-101\n    type: tank\n"
        "  - id: T-101\n    type: pump\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", str(invalid)])

    assert result.exit_code == 1
    assert "duplicate equipment id" in result.output


def test_validate_returns_nonzero_for_invalid_port_reference(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid-reference.yaml"
    invalid.write_text(
        """\
plant:
  id: demo
equipment:
  - id: T-101
    type: tank
    ports:
      - id: outlet
  - id: P-101
    type: pump
    ports:
      - id: suction
connections:
  - id: C-001
    source:
      component: T-101
      port: nope
    target:
      component: P-101
      port: suction
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", str(invalid)])

    assert result.exit_code == 1
    assert "has no port 'nope'" in result.output
    assert "Traceback" not in result.output


def test_validate_reports_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist.yaml"

    result = runner.invoke(app, ["validate", str(missing)])

    assert result.exit_code == 1
    assert "cannot read plant file" in result.output


def test_validate_returns_nonzero_for_unknown_field(tmp_path: Path) -> None:
    invalid = tmp_path / "typo.yaml"
    invalid.write_text(
        "plant:\n  id: demo\n  unknown_field: value\nequipment: []\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", str(invalid)])

    assert result.exit_code == 1
    assert "not permitted" in result.output


# --- ui: local read-only Engineering Editor launcher (Issues #75, #79) --------


def _built_editor_app(tmp_path: Path) -> Path:
    directory = tmp_path / "dist"
    directory.mkdir()
    (directory / "index.html").write_text("<!doctype html>", encoding="utf-8")
    return directory


def test_help_lists_the_ui_command() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "ui" in result.stdout


def test_ui_refuses_a_missing_project(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "ui",
            str(tmp_path / "missing.yaml"),
            "--assets-dir",
            str(_built_editor_app(tmp_path)),
        ],
    )

    assert result.exit_code == 1
    assert "cannot read plant file" in result.output
    assert "Traceback" not in result.output


def test_ui_refuses_a_malformed_symbol_role_override() -> None:
    result = runner.invoke(app, ["ui", str(REALISTIC_EXAMPLE), "--symbol-role", "PS-vessel"])

    assert result.exit_code == 1
    assert "expected the form STEP=ROLE" in result.output


def test_ui_requires_built_editor_assets(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()

    result = runner.invoke(app, ["ui", str(REALISTIC_EXAMPLE), "--assets-dir", str(empty)])

    assert result.exit_code == 1
    assert "frontend assets were not found" in result.output


def test_ui_loads_the_project_through_the_python_core(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, object] = {}

    def fake_serve(application: object, *, port: int, echo: object) -> None:
        captured["application"] = application
        captured["port"] = port

    monkeypatch.setattr("deepplant.__main__.serve_editor", fake_serve)

    result = runner.invoke(
        app,
        [
            "ui",
            str(REALISTIC_EXAMPLE),
            "--symbol-role",
            "PS-vessel=vessel",
            "--assets-dir",
            str(_built_editor_app(tmp_path)),
            "--port",
            "0",
        ],
    )

    assert result.exit_code == 0
    application = captured["application"]
    assert isinstance(application, EditorApplication)
    assert application.model.process is not None
    assert len(application.model.process.steps) == 7
    assert application.symbol_role_overrides == {"PS-vessel": "vessel"}
    assert captured["port"] == 0
