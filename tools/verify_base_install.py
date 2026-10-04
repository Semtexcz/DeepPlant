# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Verify that a base DeepPlant installation keeps the Core independent.

Issue #85 requires the semantic Core to stay usable without the editor
application. Stating that in documentation is not evidence, so this stdlib
script builds clean, isolated environments from the built wheel and checks the
real installation:

1. **base only** - the semantic Core, YAML loading, `deepplant validate` and
   `deepplant version` must all work, FastAPI and Uvicorn must *not* be
   importable, and `deepplant ui` must fail with an actionable message instead
   of an ``ImportError`` traceback;
2. **with the editor extra** - `deepplant ui` must be available.

The isolated environments are temporary and always removed. This runs in CI so
contributors never have to do it by hand.

Usage::

    python tools/verify_base_install.py dist/deepplant-0.1.0-py3-none-any.whl
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REALISTIC_EXAMPLE = REPO_ROOT / "examples" / "realistic-process-fragment" / "plant.yaml"

_CORE_PROBE = """
import json
import sys

from deepplant.io import load_plant
from deepplant.model import PlantModel

model = load_plant(sys.argv[1])
assert isinstance(model, PlantModel)

report = {"plant": model.plant.id}
for name in ("fastapi", "uvicorn", "starlette"):
    try:
        __import__(name)
    except ImportError:
        report[name + "_importable"] = False
    else:
        report[name + "_importable"] = True
print(json.dumps(report))
"""


class VerificationError(RuntimeError):
    """Raised when the installation under test does not meet the contract."""


def run(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    """Run one command in a clean environment, capturing output."""
    print("[verify-base-install] run: " + " ".join(command), flush=True)
    env = dict(os.environ)
    env.pop("VIRTUAL_ENV", None)
    env.pop("PYTHONPATH", None)
    return subprocess.run(
        list(command),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _checked(command: Sequence[str]) -> str:
    completed = run(command)
    if completed.returncode != 0:
        raise VerificationError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"{completed.stdout}\n{completed.stderr}"
        )
    return completed.stdout


def venv_python(venv: Path) -> Path:
    """Return the interpreter path inside a virtual environment."""
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def create_venv(venv: Path) -> Path:
    """Create an isolated interpreter and return its Python path."""
    _checked([sys.executable, "-m", "venv", str(venv)])
    return venv_python(venv)


def install(python: Path, requirement: str) -> None:
    """Install a requirement into the isolated environment."""
    _checked(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--quiet",
            "--disable-pip-version-check",
            requirement,
        ]
    )


def verify_base_install(wheel: Path) -> dict[str, object]:
    """Verify the base-only environment, then the editor environment."""
    if not wheel.is_file():
        raise VerificationError(f"no wheel at {wheel}")
    evidence: dict[str, object] = {"wheel": str(wheel)}

    workdir = Path(tempfile.mkdtemp(prefix="deepplant-base-install-"))
    try:
        # --- base installation: semantic Core only ----------------------------
        base = create_venv(workdir / "base")
        install(base, str(wheel))

        report = json.loads(_checked([str(base), "-c", _CORE_PROBE, str(REALISTIC_EXAMPLE)]))
        if report["fastapi_importable"] or report["uvicorn_importable"]:
            raise VerificationError(
                f"the base installation pulled in the editor transport: {report}"
            )
        evidence["base_core"] = report

        version = _checked([str(base), "-m", "deepplant", "version"])
        validate = _checked([str(base), "-m", "deepplant", "validate", str(REALISTIC_EXAMPLE)])
        if "DeepPlant" not in version or "valid DeepPlant model" not in validate:
            raise VerificationError("the base CLI did not report normally")
        evidence["base_cli"] = "version + validate ok"

        ui = run([str(base), "-m", "deepplant", "ui", str(REALISTIC_EXAMPLE)])
        combined = f"{ui.stdout}\n{ui.stderr}"
        if ui.returncode == 0:
            raise VerificationError("`deepplant ui` unexpectedly succeeded without the extra")
        if "deepplant[editor]" not in combined:
            raise VerificationError(f"`deepplant ui` gave no actionable message:\n{combined}")
        if "Traceback" in combined or "ModuleNotFoundError" in combined:
            raise VerificationError(f"`deepplant ui` surfaced a raw traceback:\n{combined}")
        evidence["base_ui"] = "actionable message, no traceback"

        # --- editor-enabled installation --------------------------------------
        editor = create_venv(workdir / "editor")
        install(editor, f"{wheel}[editor]")
        _checked([str(editor), "-c", "import fastapi, uvicorn"])
        _checked([str(editor), "-m", "deepplant", "ui", "--help"])
        evidence["editor_extra"] = "`deepplant ui` available"
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    return evidence


def main(argv: Sequence[str] | None = None) -> int:
    """Run the verification for one wheel and report the evidence."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 1:
        print(
            "usage: python tools/verify_base_install.py dist/deepplant-*.whl",
            file=sys.stderr,
        )
        return 2
    try:
        evidence = verify_base_install(Path(arguments[0]))
    except VerificationError as error:
        print(f"[verify-base-install] FAILED: {error}", file=sys.stderr)
        return 1
    print("[verify-base-install] " + json.dumps(evidence, sort_keys=True))
    print("[verify-base-install] VERIFIED: base install keeps the Core independent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
