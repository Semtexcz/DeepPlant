"""Evidence that DeepPlant Core stays independent of the editor application.

Issue #85 requires the semantic Core to remain independently usable. A doc
statement is not evidence, so these tests run real subprocesses and assert the
*dependency graph* rather than grepping source text:

- representative Core operations (load, validate, render) work with the editor
  transport, the SPA resources, and any packaging module absent from
  ``sys.modules``;
- the ordinary CLI (``version``, ``validate``) does not import FastAPI/Uvicorn
  merely because ``deepplant ui`` exists;
- an installation without the ``editor`` extra reports an actionable message
  instead of an ``ImportError`` traceback.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
REALISTIC_EXAMPLE = REPO_ROOT / "examples" / "realistic-process-fragment" / "plant.yaml"

#: Modules the Core and the ordinary CLI must never drag in. Only *application
#: technologies* are listed: editor transport, web framework, and packaging
#: tooling. Standard-library modules (for example ``webbrowser``, which the
#: editor launcher uses for its optional browser convenience) are legitimate and
#: deliberately not forbidden.
FORBIDDEN_CORE_IMPORTS = (
    "fastapi",
    "uvicorn",
    "starlette",
    "PyInstaller",
    "nuitka",
    "deepplant.editor.api",
)

# Refuses to import the editor transport, so the probe behaves like an
# installation that never received the `editor` extra. A raising metapath finder
# mirrors a genuinely missing distribution more closely than monkeypatching
# ``sys.modules`` does.
_BLOCK_EDITOR_TRANSPORT_PREAMBLE = """
import sys


class _BlockEditorTransport:
    blocked = ("fastapi", "uvicorn", "starlette")

    def find_spec(self, fullname, path=None, target=None):
        root = fullname.split(".")[0]
        if root in self.blocked:
            raise ModuleNotFoundError(f"No module named {root!r}", name=root)
        return None


sys.meta_path.insert(0, _BlockEditorTransport())
"""


def _run_python(program: str, *args: str) -> subprocess.CompletedProcess[str]:
    """Run ``program`` in a fresh interpreter that can import DeepPlant."""
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(SRC_ROOT), str(REPO_ROOT)])
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-c", program, *args],
        capture_output=True,
        text=True,
        check=False,
        env=env,
        cwd=str(REPO_ROOT),
    )


def test_core_operations_do_not_import_application_technologies() -> None:
    """Representative Core work runs without editor, HTTP, or packaging modules."""
    program = textwrap.dedent(
        """
        import json
        import sys
        from pathlib import Path

        from deepplant.io import load_plant
        from deepplant.model import PlantModel
        from deepplant.render import render_process_svg

        model = load_plant(Path(sys.argv[1]))
        assert isinstance(model, PlantModel)
        assert model.plant.id
        assert model.process is not None

        svg = render_process_svg(
            model.process,
            symbol_pack="basic",
            symbol_role_overrides={"PS-vessel": "vessel"},
        )
        assert svg.startswith("<")

        forbidden = [name for name in sys.argv[2:] if name in sys.modules]
        print(json.dumps({"forbidden": forbidden, "svg_bytes": len(svg)}))
        """
    )
    result = _run_python(program, str(REALISTIC_EXAMPLE), *FORBIDDEN_CORE_IMPORTS)

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["forbidden"] == []
    assert payload["svg_bytes"] > 0


def test_ordinary_cli_commands_do_not_import_the_editor_transport() -> None:
    """``deepplant version``/``validate`` stay usable without the editor extra."""
    program = textwrap.dedent(
        """
        import json
        import sys

        from typer.testing import CliRunner

        from deepplant.__main__ import app

        runner = CliRunner()
        version = runner.invoke(app, ["version"])
        validate = runner.invoke(app, ["validate", sys.argv[1]])
        assert version.exit_code == 0, version.output
        assert validate.exit_code == 0, validate.output

        forbidden = [name for name in sys.argv[2:] if name in sys.modules]
        print(json.dumps({"forbidden": forbidden}))
        """
    )
    result = _run_python(program, str(REALISTIC_EXAMPLE), *FORBIDDEN_CORE_IMPORTS)

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout.strip().splitlines()[-1])["forbidden"] == []


def test_ui_without_the_editor_extra_reports_a_supported_installation() -> None:
    """A missing editor installation is a message, never a raw traceback."""
    program = _BLOCK_EDITOR_TRANSPORT_PREAMBLE + textwrap.dedent(
        """
        from typer.testing import CliRunner

        from deepplant.__main__ import app

        result = CliRunner().invoke(app, ["ui", "plant.yaml"])
        print("exit_code:", result.exit_code)
        print(result.output)
        """
    )
    result = _run_python(program)

    assert result.returncode == 0, result.stderr
    assert "exit_code: 1" in result.stdout
    assert "deepplant[editor]" in result.stdout
    assert "Traceback" not in result.stdout
    assert "ModuleNotFoundError" not in result.stdout


def test_editor_entry_point_without_the_editor_extra_reports_the_same_message() -> None:
    """The application entry point fails as clearly as the CLI does."""
    program = _BLOCK_EDITOR_TRANSPORT_PREAMBLE + textwrap.dedent(
        """
        from typer.testing import CliRunner

        from deepplant.editor.launcher import app

        result = CliRunner().invoke(app, ["plant.yaml", "--no-browser"])
        print("exit_code:", result.exit_code)
        print(result.output)
        """
    )
    result = _run_python(program)

    assert result.returncode == 0, result.stderr
    assert "exit_code: 1" in result.stdout
    assert "deepplant[editor]" in result.stdout
    assert "Traceback" not in result.stdout


def test_editor_entry_point_help_does_not_import_the_editor_transport() -> None:
    """The packaged entry point describes itself without FastAPI/Uvicorn."""
    program = _BLOCK_EDITOR_TRANSPORT_PREAMBLE + textwrap.dedent(
        """
        import json
        import sys

        from typer.testing import CliRunner

        from deepplant.editor.launcher import app

        result = CliRunner().invoke(app, ["--help"])
        assert result.exit_code == 0, result.output
        forbidden = [name for name in sys.argv[1:] if name in sys.modules]
        print(json.dumps({"forbidden": forbidden}))
        """
    )
    result = _run_python(program, *FORBIDDEN_CORE_IMPORTS)

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout.strip().splitlines()[-1])["forbidden"] == []
