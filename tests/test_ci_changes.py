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

import subprocess
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


def _git(repo: Path, *args: str) -> str:
    """Run git in a throwaway repository with a deterministic identity."""
    completed = subprocess.run(
        [
            "git",
            "-c",
            "user.email=ci@example.invalid",
            "-c",
            "user.name=CI",
            *args,
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def _repo_with_rename(tmp_path: Path) -> tuple[Path, str, str]:
    """Create a repository whose only change is moving an editor module.

    Returns the repository, the base commit and the head commit. Moving
    ``src/deepplant/editor/api.py`` to ``src/deepplant/api.py`` crosses from the
    editor/packaging surface into the distribution surface, so a lossy discovery
    would drop the editor boundary the file left.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    original = repo / "src" / "deepplant" / "editor" / "api.py"
    original.parent.mkdir(parents=True)
    original.write_text("value = 1\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "add editor api")
    base = _git(repo, "rev-parse", "HEAD").strip()

    _git(repo, "mv", "src/deepplant/editor/api.py", "src/deepplant/api.py")
    _git(repo, "commit", "-q", "-m", "move editor api")
    head = _git(repo, "rev-parse", "HEAD").strip()
    return repo, base, head


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
    classification = ci_changes.classify_paths(
        ["src/deepplant/model/plant.py", "tests/model/test_model.py"]
    )
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


def test_architecture_guardrail_files_select_the_python_job() -> None:
    # The guardrail is owned by the Python surface: its checker, its regression
    # tests, and the Python source it protects must all route to `python-checks`.
    # A `tools/**` checker is deliberately not a conservative full-matrix trigger
    # (unlike the `Makefile`/`.github/**` tooling that invokes it).
    classification = ci_changes.classify_paths(
        ["tools/architecture_check.py", "tests/test_architecture_check.py"]
    )
    jobs = classification.required_jobs

    assert classification.surfaces["python"] is True
    assert classification.full is False
    assert ci_changes.PYTHON_JOB in jobs
    assert classification.surfaces["package"] is False


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
    classification = ci_changes.classify_paths(["src/deepplant/editor/desktop_qt/runtime.py"])
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


def test_realistic_fragment_fixture_runs_e2e_but_not_native_packaging() -> None:
    # The browser E2E suite (`editor-server.ts` REALISTIC_PROJECT) loads
    # `examples/realistic-process-fragment/plant.yaml` at runtime, so a change to
    # the fixture must select E2E - not only the generic `examples/**` Python
    # surface. Since Issue #98 the packaged smoke test no longer loads it: its
    # `PS-vessel` step is honestly `function: unspecified` and the ordinary user
    # path cannot supply the presentation override, so native packaging is not
    # selected by this fixture.
    classification = ci_changes.classify_paths(["examples/realistic-process-fragment/plant.yaml"])
    jobs = classification.required_jobs

    assert classification.surfaces["python"] is True
    assert classification.surfaces["e2e"] is True
    assert classification.surfaces["package"] is False
    assert classification.surfaces["frontend"] is False
    assert ci_changes.PYTHON_JOB in jobs
    assert ci_changes.E2E_JOB in jobs
    assert ci_changes.WINDOWS_PACKAGE_JOB not in jobs
    assert ci_changes.LINUX_PACKAGE_JOB not in jobs


def test_packaged_smoke_fixture_runs_both_native_packaging_jobs() -> None:
    # The packaged-artifact smoke test (`tools/package_editor.py` `SMOKE_MODEL`)
    # loads `examples/process-graph/plant.yaml` at runtime, so a change to that
    # self-contained fixture must select both native packaging jobs. The browser
    # E2E suite does not load it, so E2E is not selected.
    classification = ci_changes.classify_paths(["examples/process-graph/plant.yaml"])
    jobs = classification.required_jobs

    assert classification.surfaces["python"] is True
    assert classification.surfaces["package"] is True
    assert classification.surfaces["e2e"] is False
    assert classification.surfaces["frontend"] is False
    assert ci_changes.PYTHON_JOB in jobs
    assert ci_changes.WINDOWS_PACKAGE_JOB in jobs
    assert ci_changes.LINUX_PACKAGE_JOB in jobs
    assert ci_changes.E2E_JOB not in jobs


def test_other_examples_remain_python_only() -> None:
    # Only the fixtures the runtime actually loads own the E2E/package surface;
    # the broader rule is not silently widened to every example.
    classification = ci_changes.classify_paths(["examples/minimal-process/plant.yaml"])
    jobs = classification.required_jobs

    assert classification.surfaces["python"] is True
    assert classification.surfaces["e2e"] is False
    assert classification.surfaces["package"] is False
    assert ci_changes.E2E_JOB not in jobs
    assert ci_changes.WINDOWS_PACKAGE_JOB not in jobs


def test_canonical_runtime_asset_selects_python_wheel_e2e_and_native_packaging() -> None:
    # `src/deepplant/assets/**` (here the real `pump.svg`) is a runtime input, not
    # Python package metadata: the renderer reads it through `importlib.resources`,
    # the Editor backend serves it to the browser at `/api/symbols/<role>.svg`, the
    # Playwright suite drives that path, and `tools/package_editor.py` bundles and
    # verifies a canonical symbol (`REQUIRED_SYMBOL`). A change here must therefore
    # select python, wheel, browser E2E, and both native packaging jobs.
    classification = ci_changes.classify_paths(
        ["src/deepplant/assets/symbols/process/basic/pump.svg"]
    )
    jobs = classification.required_jobs

    assert classification.surfaces["python"] is True
    assert classification.surfaces["distribution"] is True
    assert classification.surfaces["e2e"] is True
    assert classification.surfaces["package"] is True
    assert classification.surfaces["frontend"] is False
    assert ci_changes.PYTHON_JOB in jobs
    assert ci_changes.WHEEL_JOB in jobs
    assert ci_changes.E2E_JOB in jobs
    assert ci_changes.WINDOWS_PACKAGE_JOB in jobs
    assert ci_changes.LINUX_PACKAGE_JOB in jobs


def test_desktop_typecheck_config_is_a_packaging_input() -> None:
    # Both native jobs run the strict desktop type check with
    # `pyright --project pyrightconfig.desktop.json`, so changing that project
    # file must run the jobs that consume it.
    classification = ci_changes.classify_paths(["pyrightconfig.desktop.json"])
    jobs = classification.required_jobs

    assert classification.surfaces["python"] is True
    assert classification.surfaces["package"] is True
    assert ci_changes.WINDOWS_PACKAGE_JOB in jobs
    assert ci_changes.LINUX_PACKAGE_JOB in jobs


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


def test_licence_file_is_also_a_packaged_product_input() -> None:
    # `tools/package_editor.py::stage_licenses` copies the root `LICENSE` into the
    # distributed compliance payload (`licenses/DEEPLANT-AGPL-3.0.txt`, verified by
    # `REQUIRED_LICENSE_FILES`), exactly like `THIRD_PARTY_NOTICES.md`. Routing the
    # licence through the wheel surface alone would let a licence change skip the
    # native packaging jobs that actually ship it.
    classification = ci_changes.classify_paths(["LICENSE"])
    jobs = classification.required_jobs

    assert classification.surfaces["docs"] is True
    assert classification.surfaces["distribution"] is True
    assert classification.surfaces["package"] is True
    assert ci_changes.WHEEL_JOB in jobs
    assert ci_changes.WINDOWS_PACKAGE_JOB in jobs
    assert ci_changes.LINUX_PACKAGE_JOB in jobs


@pytest.mark.parametrize(
    "path",
    [
        ".github/workflows/ci.yml",
        ".github/actions/local/action.yml",
        ".gitattributes",
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


def test_changed_paths_reports_both_sides_of_a_rename(tmp_path: Path) -> None:
    # This tests the changed-file discovery contract itself, not classify_paths()
    # with a hand-written list: the bug is in how Git produces the path list. Git
    # rename detection reports only the destination, so discovery must disable it
    # and keep the removed path too.
    repo, base, head = _repo_with_rename(tmp_path)

    paths = ci_changes.changed_paths(base, head, repo=repo)

    assert "src/deepplant/editor/api.py" in paths
    assert "src/deepplant/api.py" in paths


def test_rename_across_validation_surfaces_keeps_the_removed_surface(tmp_path: Path) -> None:
    # End to end: discovery feeds classification, and the surface the file left
    # (the editor boundary: browser E2E + native packaging) must survive the move.
    repo, base, head = _repo_with_rename(tmp_path)

    classification = ci_changes.classify_paths(ci_changes.changed_paths(base, head, repo=repo))

    assert classification.surfaces["e2e"] is True
    assert classification.surfaces["package"] is True
    assert classification.surfaces["distribution"] is True


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


def test_workflow_discovers_changed_paths_through_the_classifier() -> None:
    # The tested classifier owns rename-safe discovery; the workflow must not
    # re-add a raw `git diff --name-only` that can lose a moved file's original
    # path (and therefore the validation surface it left).
    text = _workflow_text()

    assert "ci_changes.py changed-paths" in text
    assert "git diff --name-only" not in text


def test_workflow_cancels_superseded_pull_request_runs() -> None:
    text = _workflow_text()

    assert "concurrency:" in text
    assert "cancel-in-progress" in text
    assert "github.event.pull_request.number" in text


def test_workflow_supports_manual_full_confidence_runs() -> None:
    text = _workflow_text()

    assert "workflow_dispatch:" in text
