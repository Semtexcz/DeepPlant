import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from deepplant import __version__
from deepplant.__main__ import app, main

runner = CliRunner()

EXAMPLE = Path(__file__).parents[1] / "examples" / "minimal-process" / "plant.yaml"


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
  - source:
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
