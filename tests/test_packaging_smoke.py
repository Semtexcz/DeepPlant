"""Regression coverage for the self-contained packaged-desktop smoke path (Issue #98).

The packaged verification must reproduce what an ordinary user reaches through
``File -> Open…``: a self-contained fixture that loads, validates, projects and
renders with **no** hidden presentation override. Before Issue #98 the packaged
path injected ``--symbol-role PS-vessel=vessel`` so the realistic process fragment
could be drawn; an ordinary user never receives that override, so the packaged
product could not render the model it was verified against.

These tests are Qt-free on purpose: the fixture, the driver's launch command, and
the driver's default model are checked through plain Python. The real native
window and the rendered Process/PFD stay the evidence of the native packaging
jobs (see docs/dev/workflow/packaging.md).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from deepplant import load_plant, render_process_svg
from deepplant.editor.desktop import (
    EMPTY_WORKSPACE_STATUS_TEXT,
    SELF_CHECK_SCENARIO_TRANSITION,
    SMOKE_EXPECTED_STEPS,
    SMOKE_EXPECTED_STREAMS,
    SMOKE_PROBE_STEP_ID,
    TRANSITION_PROJECT_B_EXPECTED_STEPS,
    TRANSITION_PROJECT_B_EXPECTED_STREAMS,
    TRANSITION_PROJECT_B_PROBE_FUNCTION,
    TRANSITION_PROJECT_B_PROBE_STEP_ID,
)
from deepplant.editor.projection import project_process_pfd
from deepplant.io import PlantLoadError
from deepplant.render import ProcessRenderError
from tools import package_editor as pe

REPO_ROOT = Path(__file__).resolve().parents[1]
REALISTIC_EXAMPLE = REPO_ROOT / "examples" / "realistic-process-fragment" / "plant.yaml"


def _smoke_model():
    """Load the canonical smoke fixture; it must load unmodified."""
    model = load_plant(pe.SMOKE_MODEL)
    assert model.process is not None
    return model


# --- The canonical smoke fixture is self-contained ----------------------------


def test_canonical_smoke_fixture_is_the_self_contained_process_graph() -> None:
    assert pe.SMOKE_MODEL == REPO_ROOT / "examples" / "process-graph" / "plant.yaml"
    assert pe.SMOKE_MODEL.is_file()
    # The realistic fragment is never the packaged happy path: it needs an explicit
    # presentation choice an ordinary user cannot supply (Issue #98).
    assert pe.SMOKE_MODEL != REALISTIC_EXAMPLE


def test_smoke_fixture_loads_and_validates_without_overrides() -> None:
    process = _smoke_model().process
    assert process is not None
    assert len(process.steps) == SMOKE_EXPECTED_STEPS
    assert len(process.streams) == SMOKE_EXPECTED_STREAMS
    # The self-check selects a step that carries a normally resolvable engineering
    # function, so the ordinary presentation policy renders it with no override.
    probe = next(step for step in process.steps if step.id == SMOKE_PROBE_STEP_ID)
    assert probe.function == "pumping"


def test_smoke_fixture_projects_without_symbol_role_overrides() -> None:
    projection = project_process_pfd(load_plant(pe.SMOKE_MODEL))

    assert len(projection.steps) == SMOKE_EXPECTED_STEPS
    assert len(projection.streams) == SMOKE_EXPECTED_STREAMS
    probe = next(step for step in projection.steps if step.id == SMOKE_PROBE_STEP_ID)
    assert probe.function == "pumping"
    assert probe.symbol_role == "pump"


def test_smoke_fixture_renders_without_symbol_role_overrides() -> None:
    process = _smoke_model().process
    assert process is not None

    svg = render_process_svg(process)

    assert svg.startswith("<svg")
    assert svg.rstrip().endswith("</svg>")


# --- The packaged driver no longer injects a presentation override -------------


def test_verify_phase_defaults_to_the_canonical_smoke_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Path] = {}
    monkeypatch.setattr(pe, "project_version", lambda: "0.0.0")

    def fake_smoke_test_artifact(
        artifact: Path, *, work_dir: Path, model_path: Path
    ) -> dict[str, object]:
        captured["model_path"] = model_path
        return {}

    monkeypatch.setattr(pe, "smoke_test_artifact", fake_smoke_test_artifact)

    code = pe.main(
        [
            "verify",
            "--build-dir",
            str(tmp_path / "build"),
            "--dist-dir",
            str(tmp_path / "dist"),
            "--artifact",
            str(tmp_path / "artifact.bin"),
        ]
    )

    assert code == 0
    assert captured["model_path"] == pe.SMOKE_MODEL


def _passing_report() -> dict[str, object]:
    """A minimal report the driver accepts, so the launch command can be inspected.

    It carries the loaded-model checks, the empty-workspace checks (Issue #97) and
    the project-replacement checks (Issue #97 review) the real self-check reports,
    so the driver is exercised against the same shape it validates in the packaged
    product.
    """
    return {
        "verdict": "pass",
        "checks": {
            "productionSpa": True,
            "validationValid": True,
            "processSteps": True,
            "processStreams": True,
            "pumpSelected": True,
            "inspectorFunction": True,
            "workspaceEmpty": True,
            "statusNoProject": True,
            "emptyCanvasMessage": True,
            "noProjectionError": True,
            "emptyAtLaunch": True,
            "projectARendered": True,
            "projectASelected": True,
            "projectBReplacedA": True,
            "projectBSelected": True,
            "selectionResetOnReplacement": True,
            "failedLoadKeptProjectB": True,
            "errorReported": True,
            "windowUnchanged": True,
            "viewUnchanged": True,
            "serverUnchanged": True,
            "originUnchanged": True,
            "portUnchanged": True,
            "singleWindow": True,
            "singleView": True,
            "noAdditionalServingSocket": True,
            "windowVisible": True,
            "windowClosed": True,
            "serverStopRequested": True,
            "serverStopped": True,
            "serverThreadTerminated": True,
            "portReleased": True,
            "eventLoopReturned": True,
        },
        "lifecycle": {
            "windowVisible": True,
            "windowClosed": True,
            "serverStopRequested": True,
            "serverStopped": True,
            "serverThreadAliveAfterClose": False,
            "portReleased": True,
            "eventLoopReturned": True,
        },
    }


def _capture_launch_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    model: Path | None,
    scenario: str | None = None,
    projects: tuple[Path, ...] = (),
    invalid_project: Path | None = None,
) -> list[str]:
    report = tmp_path / "desktop-workflow.json"
    captured: dict[str, list[str]] = {}

    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        captured["command"] = list(command)
        report.write_text(json.dumps(_passing_report()), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(pe.subprocess, "run", fake_run)

    def no_helpers() -> set[int]:
        return set()

    monkeypatch.setattr(pe, "_qtwebengine_helper_pids", no_helpers)

    payload = pe.run_desktop_self_check(
        Path("/opt/deepplant-editor/deepplant-editor"),
        report=report,
        model=model,
        cwd=tmp_path,
        scenario=scenario,
        projects=projects,
        invalid_project=invalid_project,
    )
    assert payload["verdict"] == "pass"
    return captured["command"]


def test_packaged_desktop_self_check_injects_no_presentation_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    command = _capture_launch_command(tmp_path, monkeypatch, model=pe.SMOKE_MODEL)

    # The ordinary `deepplant-editor <path>` launch plus the documented
    # automation-only self-check flags - and nothing else.
    assert str(pe.SMOKE_MODEL) in command
    assert "--self-check" in command
    assert "--self-check-report" in command
    assert "--symbol-role" not in command
    assert not any("PS-vessel" in part for part in command)


def test_packaged_desktop_self_check_no_project_launch_has_no_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The no-argument launch proves the shared Vue SPA's empty workspace.

    Issue #97: the packaged verification must exercise the real shared-SPA
    no-project state, not merely that a native bootstrap widget appeared.
    """
    command = _capture_launch_command(tmp_path, monkeypatch, model=None)

    assert command[0].endswith("deepplant-editor")
    assert "--self-check" in command
    assert "--symbol-role" not in command
    assert not any("PS-vessel" in part for part in command)


def test_packaged_project_replacement_self_check_uses_one_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Issue #97 review: the replacement regression is one session, not two.

    The packaged command launches the application **once** with no positional
    model, hands the Open handler the two projects and the invalid project, and
    still injects no presentation override.
    """
    project_a = tmp_path / "project-a.yaml"
    project_b = tmp_path / "project-b.yaml"
    invalid = tmp_path / "invalid.yaml"

    command = _capture_launch_command(
        tmp_path,
        monkeypatch,
        model=None,
        scenario=SELF_CHECK_SCENARIO_TRANSITION,
        projects=(project_a, project_b),
        invalid_project=invalid,
    )

    assert command[0].endswith("deepplant-editor")
    # No positional model: the scenario opens its own projects in one session.
    assert command[1] == "--self-check"
    assert command[command.index("--self-check-scenario") + 1] == SELF_CHECK_SCENARIO_TRANSITION
    project_flags = [index for index, part in enumerate(command) if part == "--self-check-project"]
    assert [command[index + 1] for index in project_flags] == [str(project_a), str(project_b)]
    assert command[command.index("--self-check-invalid-project") + 1] == str(invalid)
    assert "--symbol-role" not in command
    assert not any("PS-vessel" in part for part in command)


def test_the_empty_workspace_status_text_is_a_single_pinned_value() -> None:
    """The empty-workspace status the probe asserts is authored once (Issue #97).

    It is the same string the shared Vue SPA renders for `active project = none`,
    so renaming it on either side fails this fast Python gate rather than only the
    slow native packaging job.
    """
    assert EMPTY_WORKSPACE_STATUS_TEXT == "No project open"


# --- The realistic fragment's honest boundary is unchanged ---------------------


def test_realistic_fragment_still_needs_an_explicit_presentation_choice() -> None:
    """Issue #98 must not falsify the realistic fragment's engineering semantics.

    ``PS-vessel`` stays ``function: unspecified``: the model is semantically valid
    but has no default presentation role, which is exactly why it is *not* the
    packaged smoke fixture and why its semantics must be left untouched.
    """
    model = load_plant(REALISTIC_EXAMPLE)
    assert model.process is not None
    vessel = next(step for step in model.process.steps if step.id == "PS-vessel")
    assert vessel.function == "unspecified"
    assert not hasattr(vessel, "type")

    with pytest.raises(ProcessRenderError):
        project_process_pfd(model)


# --- The project-replacement fixture is self-contained -------------------------


def test_replacement_fixture_is_a_distinguishable_self_contained_model() -> None:
    """Issue #97 review: the replacement fixture is distinct and needs no override.

    It is the second packaged-smoke process model and must differ from the canonical
    fixture by graph contents (two steps, one stream, no ``PUMP``), so the packaged
    self-check can prove the rendered SPA actually replaced project A.
    """
    assert pe.TRANSITION_MODEL == REPO_ROOT / "examples" / "process-graph" / "replacement.yaml"
    assert pe.TRANSITION_MODEL != pe.SMOKE_MODEL
    assert pe.TRANSITION_MODEL.is_file()

    model = load_plant(pe.TRANSITION_MODEL)
    assert model.process is not None
    assert len(model.process.steps) == TRANSITION_PROJECT_B_EXPECTED_STEPS
    assert len(model.process.streams) == TRANSITION_PROJECT_B_EXPECTED_STREAMS
    assert all(step.id != SMOKE_PROBE_STEP_ID for step in model.process.steps)


def test_replacement_fixture_projects_and_renders_without_overrides() -> None:
    model = load_plant(pe.TRANSITION_MODEL)
    projection = project_process_pfd(model)

    assert len(projection.steps) == TRANSITION_PROJECT_B_EXPECTED_STEPS
    assert len(projection.streams) == TRANSITION_PROJECT_B_EXPECTED_STREAMS
    probe = next(step for step in projection.steps if step.id == TRANSITION_PROJECT_B_PROBE_STEP_ID)
    assert probe.function == TRANSITION_PROJECT_B_PROBE_FUNCTION

    process = model.process
    assert process is not None
    svg = render_process_svg(process)
    assert svg.startswith("<svg")
    assert svg.rstrip().endswith("</svg>")


def test_the_transition_invalid_model_is_rejected_by_the_loader(tmp_path: Path) -> None:
    """The failing open in the replacement scenario is a real loader rejection."""
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text(pe.INVALID_MODEL_TEXT, encoding="utf-8")

    with pytest.raises(PlantLoadError):
        load_plant(invalid)
