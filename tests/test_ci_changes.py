"""Deterministic coverage for the change-aware CI routing logic.

The CI workflow must run only the validation that can provide relevant evidence
for a pull request, and must never let a skipped job mask the failure of a job
the change actually requires. That decision lives in a small, reviewable,
dependency-free Python module (``tools/ci_changes.py``) instead of opaque
workflow expressions, so it is unit-tested here:

- representative changed surfaces select exactly the expected evidence jobs;
- documentation-only changes never select a production build, browser E2E,
  wheel, or native packaging job;
- an unrecognized path, a build/CI tooling change, and a non-pull-request
  lifecycle boundary all select the conservative full matrix;
- the aggregate gate fails when a required job failed, was cancelled, or never
  ran, and only tolerates skipped jobs the classifier did not select.

A few structural assertions pin the workflow itself to the classifier, so the
guarantees the classifier expresses cannot drift away from ``ci.yml``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools import ci_changes

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"

NON_DOCUMENTATION_SURFACES = (
    "agents",
    "python",
    "distribution",
    "frontend",
    "e2e",
    "package",
)


def _results(**overrides: str) -> dict[str, str]:
    """Build a job-result map where classification succeeded and nothing else ran."""
    results: dict[str, str] = {job: "success" for job in ci_changes.ALWAYS_REQUIRED_JOBS}
    for job in ci_changes.EVIDENCE_JOBS:
        results[job] = "skipped"
    results[ci_changes.PR_GUARD_JOB] = "skipped"
    results.update(overrides)
    return results


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_documentation_only_selects_only_documentation_validation() -> None:
    classification = ci_changes.classify_paths(
        ["docs/dev/workflow/quality.md", "README.md", "project/brief.md"]
    )

    assert classification.surfaces["docs"] is True
    for surface in NON_DOCUMENTATION_SURFACES:
        assert classification.surfaces[surface] is False, surface

    # A documentation-only pull request must not build, package, or drive a
    # browser: only the cheap static documentation job is required.
    assert classification.required_jobs == (ci_changes.DOCS_JOB,)


def test_agent_metadata_selects_the_static_agent_validation() -> None:
    classification = ci_changes.classify_paths([".agents/context-map.yaml", "AGENTS.md"])

    assert classification.surfaces["agents"] is True
    assert classification.required_jobs == (ci_changes.DOCS_JOB,)


def test_python_core_change_runs_python_validation_and_the_wheel_boundary() -> None:
    classification = ci_changes.classify_paths(["src/deepplant/model.py", "tests/test_model.py"])
    jobs = classification.required_jobs

    assert classification.surfaces["python"] is True
    assert classification.surfaces["distribution"] is True
    assert classification.surfaces["frontend"] is False
    assert classification.surfaces["e2e"] is False
    assert classification.surfaces["package"] is False
    assert ci_changes.PYTHON_JOB in jobs
    assert ci_changes.WHEEL_JOB in jobs
    assert ci_changes.WINDOWS_PACKAGE_JOB not in jobs
    assert ci_changes.LINUX_PACKAGE_JOB not in jobs


def test_frontend_change_runs_frontend_checks_e2e_and_native_packaging() -> None:
    classification = ci_changes.classify_paths(["apps/editor/src/process-pfd/transport/api.ts"])
    jobs = classification.required_jobs

    assert classification.surfaces["frontend"] is True
    assert classification.surfaces["e2e"] is True
    assert classification.surfaces["package"] is True
    assert classification.surfaces["python"] is False
    assert ci_changes.FRONTEND_JOB in jobs
    assert ci_changes.E2E_JOB in jobs
    assert ci_changes.WINDOWS_PACKAGE_JOB in jobs
    assert ci_changes.LINUX_PACKAGE_JOB in jobs
    assert ci_changes.WHEEL_JOB not in jobs


def test_editor_transport_change_requires_browser_evidence() -> None:
    classification = ci_changes.classify_paths(["src/deepplant/editor/api.py"])

    assert classification.surfaces["python"] is True
    assert classification.surfaces["e2e"] is True
    assert classification.surfaces["package"] is True
    # The frontend source is untouched, so the frontend-specific gate is not
    # required; browser evidence still covers the shared product path.
    assert classification.surfaces["frontend"] is False


def test_desktop_host_change_triggers_native_packaging() -> None:
    classification = ci_changes.classify_paths(["src/deepplant/editor/desktop_qt.py"])
    jobs = classification.required_jobs

    assert classification.surfaces["package"] is True
    assert classification.surfaces["python"] is True
    assert classification.surfaces["distribution"] is True
    assert ci_changes.WINDOWS_PACKAGE_JOB in jobs
    assert ci_changes.LINUX_PACKAGE_JOB in jobs


def test_packaging_configuration_triggers_native_packaging() -> None:
    classification = ci_changes.classify_paths(
        ["packaging/toolchain.toml", "packaging/licenses.toml"]
    )
    jobs = classification.required_jobs

    assert classification.surfaces["package"] is True
    assert classification.surfaces["python"] is True
    assert ci_changes.WINDOWS_PACKAGE_JOB in jobs
    assert ci_changes.LINUX_PACKAGE_JOB in jobs


def test_packaging_tooling_change_triggers_native_packaging() -> None:
    classification = ci_changes.classify_paths(["tools/package_editor.py"])

    assert classification.surfaces["package"] is True
    assert classification.surfaces["python"] is True


def test_dependency_metadata_is_treated_conservatively() -> None:
    classification = ci_changes.classify_paths(["pyproject.toml", "uv.lock"])
    jobs = classification.required_jobs

    assert classification.surfaces["python"] is True
    assert classification.surfaces["distribution"] is True
    assert classification.surfaces["package"] is True
    assert ci_changes.WHEEL_JOB in jobs
    assert ci_changes.WINDOWS_PACKAGE_JOB in jobs


def test_compliance_payload_document_is_a_packaging_input() -> None:
    classification = ci_changes.classify_paths(["THIRD_PARTY_NOTICES.md"])

    assert classification.surfaces["docs"] is True
    assert classification.surfaces["package"] is True


def test_wheel_licence_file_is_a_distribution_input() -> None:
    classification = ci_changes.classify_paths(["LICENSE"])

    assert classification.surfaces["docs"] is True
    assert classification.surfaces["distribution"] is True


@pytest.mark.parametrize(
    "path",
    [
        ".github/workflows/ci.yml",
        ".github/actions/local/action.yml",
        "Makefile",
        "tools/ci_changes.py",
        "new/unclassified-file.bin",
    ],
)
def test_build_tooling_and_unrecognized_paths_select_the_full_matrix(path: str) -> None:
    classification = ci_changes.classify_paths([path])

    assert classification.full is True, path
    assert set(ci_changes.EVIDENCE_JOBS) <= set(classification.required_jobs)


@pytest.mark.parametrize("event", ["push", "workflow_dispatch"])
def test_non_pull_request_events_select_the_full_matrix(event: str) -> None:
    classification = ci_changes.full_classification(f"{event} boundary")

    assert classification.full is True
    assert set(ci_changes.EVIDENCE_JOBS) <= set(classification.required_jobs)


def test_changed_paths_are_normalized() -> None:
    classification = ci_changes.classify_paths(["./docs/index.md", "/docs/index.md", "   "])

    assert classification.surfaces["docs"] is True
    assert classification.full is False


def test_every_surface_is_owned_by_a_job() -> None:
    jobs = ci_changes.jobs_for(dict.fromkeys(ci_changes.SURFACES, True))

    assert set(jobs) == set(ci_changes.EVIDENCE_JOBS)


def test_gate_passes_when_required_jobs_succeed_and_the_rest_are_skipped() -> None:
    results = _results(**{"python-checks": "success", "wheel-verification": "success"})

    problems = ci_changes.enforce_gate(
        [ci_changes.PYTHON_JOB, ci_changes.WHEEL_JOB],
        results,
        guard_required=False,
    )

    assert problems == ()


def test_gate_fails_when_a_required_job_failed() -> None:
    results = _results(**{"python-checks": "failure"})

    problems = ci_changes.enforce_gate([ci_changes.PYTHON_JOB], results, guard_required=False)

    assert problems


def test_gate_fails_when_a_required_job_was_cancelled() -> None:
    results = _results(**{"editor-package-windows": "cancelled"})

    problems = ci_changes.enforce_gate(
        [ci_changes.WINDOWS_PACKAGE_JOB], results, guard_required=False
    )

    assert problems


def test_gate_fails_when_a_required_job_was_skipped() -> None:
    # A skipped job must never mask a failure: if the classifier required the
    # job, "skipped" is not an acceptable result.
    results = _results()

    problems = ci_changes.enforce_gate([ci_changes.PYTHON_JOB], results, guard_required=False)

    assert problems


def test_gate_fails_when_an_irrelevant_job_failed() -> None:
    results = _results(**{"frontend-e2e": "failure"})

    problems = ci_changes.enforce_gate([], results, guard_required=False)

    assert problems


def test_gate_fails_when_classification_did_not_succeed() -> None:
    results = _results()
    results["classify-changes"] = "failure"

    problems = ci_changes.enforce_gate([], results, guard_required=False)

    assert problems


def test_gate_fails_when_the_pr_guard_is_required_and_did_not_run() -> None:
    results = _results()

    problems = ci_changes.enforce_gate([], results, guard_required=True)

    assert problems


def test_gate_passes_when_the_pr_guard_is_not_required() -> None:
    problems = ci_changes.enforce_gate([], _results(), guard_required=False)

    assert problems == ()


def test_gate_rejects_an_unknown_required_job() -> None:
    problems = ci_changes.enforce_gate(["not-a-job"], _results(), guard_required=False)

    assert problems


def test_workflow_selects_the_production_frontend_build_somewhere() -> None:
    # `make frontend-build` is deliberately outside the local `make check` gate,
    # so change-aware routing must not lose the shipped SPA bundle. This is the
    # structural half of that guarantee; the classifier half is
    # `test_frontend_change_runs_frontend_checks_e2e_and_native_packaging`.
    assert "make frontend-build" in _workflow_text()


def test_workflow_aggregate_gate_depends_on_every_evidence_job() -> None:
    text = _workflow_text()
    assert "\n  ci-gate:" in text
    gate = text.split("\n  ci-gate:", 1)[1]

    for job in ci_changes.EVIDENCE_JOBS:
        assert f"- {job}" in gate, job
    assert ci_changes.PR_GUARD_JOB in gate


def test_workflow_routes_conditional_jobs_on_classifier_outputs() -> None:
    text = _workflow_text()

    assert "needs.classify-changes.outputs.python == 'true'" in text
    assert "needs.classify-changes.outputs.frontend == 'true'" in text
    assert "needs.classify-changes.outputs.e2e == 'true'" in text
    assert "needs.classify-changes.outputs.package == 'true'" in text


def test_workflow_cancels_superseded_pull_request_runs() -> None:
    text = _workflow_text()

    assert "concurrency:" in text
    assert "cancel-in-progress" in text
    assert "github.event.pull_request.number" in text


def test_workflow_supports_manual_full_confidence_runs() -> None:
    text = _workflow_text()

    assert "workflow_dispatch:" in text
