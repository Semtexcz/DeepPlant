import sys

import pytest
from typer.testing import CliRunner

from deepplant import __version__
from deepplant.__main__ import app, main

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert f"DeepPlant {__version__}" in result.stdout


def test_help_shows_usage() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "version" in result.stdout


def test_bare_invocation_shows_help(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["deepplant"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
