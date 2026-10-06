# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Change-aware CI impact classification and the aggregate CI gate.

The GitHub Actions workflow in ``.github/workflows/ci.yml`` must run only the
validation that can provide relevant evidence for a pull request. Deciding that
inside YAML expressions is opaque and cannot be tested, so the decision lives
here as a small, dependency-free, deterministic module with two subcommands:

``classify``
    map the changed repository paths of a pull request to validation surfaces
    and the evidence jobs those surfaces require;
``changed-paths``
    discover the changed repository paths between two commits, keeping both the
    removed and added path of a rename/move;
``gate``
    decide whether the always-present aggregate required CI result may pass.

Design rules
------------

- A path is matched by explicit, reviewable rules. An **unrecognized** path is
  not ignored: it selects the conservative full matrix, so a file nobody has
  classified yet can never silently skip validation it might affect.
- A **rename or move preserves both sides**: changed-file discovery runs
  ``git diff --no-renames``, so the removed and added paths are each classified
  as a delete plus an add. A move across validation surfaces must not drop the
  surface the file left (Git's rename detection would report only the
  destination).
- ``.github/**`` (except the pull-request template), the ``Makefile`` and this
  module itself are build/CI tooling: they always select the full matrix.
- A non-``pull_request`` event (``push`` to ``main``, ``workflow_dispatch``) is
  never change-aware. ``main`` and release work keep full distribution
  confidence instead of being made cheaper.
- A surface is a *reason for evidence*, not an implementation detail. A file
  that is an input to a distributed artifact belongs to that artifact's surface
  (``LICENSE`` is a wheel *and* packaged-application input;
  ``THIRD_PARTY_NOTICES.md`` and ``assets/**`` are packaged-application inputs;
  the canonical ``src/deepplant/assets/**`` runtime symbols are python,
  distribution, E2E and packaged-application inputs).

Canonical documentation of the resulting PR matrix:
``docs/dev/workflow/quality.md``.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

#: Validation surfaces a change can require.
SURFACES: tuple[str, ...] = (
    "docs",
    "agents",
    "python",
    "distribution",
    "frontend",
    "e2e",
    "package",
)

#: Evidence jobs owned by the surfaces above. ``docs`` and ``agents`` share one
#: job; ``package`` owns the two native platform jobs.
DOCS_JOB = "docs-validation"
PYTHON_JOB = "python-checks"
WHEEL_JOB = "wheel-verification"
FRONTEND_JOB = "frontend-checks"
E2E_JOB = "frontend-e2e"
WINDOWS_PACKAGE_JOB = "editor-package-windows"
LINUX_PACKAGE_JOB = "editor-package-linux"

#: Every job whose result the aggregate gate evaluates.
EVIDENCE_JOBS: tuple[str, ...] = (
    DOCS_JOB,
    PYTHON_JOB,
    WHEEL_JOB,
    FRONTEND_JOB,
    E2E_JOB,
    WINDOWS_PACKAGE_JOB,
    LINUX_PACKAGE_JOB,
)

#: The stable aggregate result. This is the job a branch-protection rule should
#: require: it exists for every pull request and reports the whole matrix.
GATE_JOB = "ci-gate"

#: The guard that rejects direct pushes to ``main``. It only runs on
#: push-to-``main``, so it is required only on that lifecycle boundary.
PR_GUARD_JOB = "require-pr-for-main"

#: Jobs that must always succeed for the gate to pass: classification is the
#: input the whole routing decision depends on, so a failed classifier must never
#: degrade into "everything was irrelevant".
ALWAYS_REQUIRED_JOBS: tuple[str, ...] = ("classify-changes",)

CONSERVATIVE_REASON = "full matrix (conservative: build/CI tooling or unrecognized path)"

_PULL_REQUEST_TEMPLATE = ".github/pull_request_template.md"

#: Repository governance documents that are static metadata, not build inputs.
_ROOT_DOC_FILES: frozenset[str] = frozenset(
    {
        ".copier-answers.yml",
        ".gitignore",
        ".template-version",
        "CLA.md",
        "COMMERCIAL-LICENSING.md",
        "CONTRIBUTING.md",
        "README.md",
        "TRADEMARKS.md",
        "VISION.md",
    }
)

#: Root documents that are inputs to a distributed artifact rather than prose.
#: ``LICENSE`` is declared in ``license-files`` and therefore enters the wheel,
#: and ``tools/package_editor.py::stage_licenses`` also copies it into the
#: packaged application's compliance payload (``licenses/DEEPLANT-AGPL-3.0.txt``,
#: verified by ``REQUIRED_LICENSE_FILES``). ``THIRD_PARTY_NOTICES.md`` is the
#: other bundled compliance-payload document. ``LICENSE`` is thus both a wheel
#: and a packaged-product input, which the two sets below record.
_WHEEL_ROOT_FILES: frozenset[str] = frozenset({"LICENSE"})
_PACKAGE_ROOT_FILES: frozenset[str] = frozenset({"LICENSE", "THIRD_PARTY_NOTICES.md"})

_DOC_PREFIXES: tuple[str, ...] = ("docs/", "project/")

_AGENT_PREFIXES: tuple[str, ...] = (".agents/", ".codex/")
_AGENT_FILES: frozenset[str] = frozenset({"AGENTS.md", "tools/agent.py"})

_PYTHON_PREFIXES: tuple[str, ...] = ("src/", "tests/", "examples/", "tools/", "packaging/")
_PYTHON_FILES: frozenset[str] = frozenset(
    {
        "Makefile",
        "pyproject.toml",
        "pyrightconfig.desktop.json",
        "uv.lock",
    }
)

_DISTRIBUTION_PREFIXES: tuple[str, ...] = ("src/deepplant/",)
_DISTRIBUTION_FILES: frozenset[str] = frozenset(
    {
        "pyproject.toml",
        "uv.lock",
        "tools/verify_base_install.py",
        "tools/verify_wheel_contents.py",
    }
)

_FRONTEND_PREFIXES: tuple[str, ...] = ("apps/editor/",)

_E2E_PREFIXES: tuple[str, ...] = ("apps/editor/", "src/deepplant/editor/")
#: ``deepplant ui`` is the serving path the Playwright suite drives.
_E2E_FILES: frozenset[str] = frozenset({"src/deepplant/__main__.py"})

#: Runtime fixture loaded by the browser E2E suite
#: (``apps/editor/e2e/support/editor-server.ts``). Changing it must select the
#: browser E2E job, not only the generic ``examples/**`` Python surface. Other
#: ``examples/**`` subtrees stay Python-only.
_E2E_FIXTURE_PREFIXES: tuple[str, ...] = ("examples/realistic-process-fragment/",)

#: Runtime fixture loaded by the packaged-artifact smoke test
#: (``tools/package_editor.py`` ``SMOKE_MODEL``). It is a self-contained,
#: self-renderable model (Issue #98), so changing it must select both native
#: packaging jobs, not only the generic ``examples/**`` Python surface. The
#: realistic fragment above is never used by the packaged path: its ``PS-vessel``
#: step is honestly ``function: unspecified`` and needs an explicit presentation
#: choice an ordinary user cannot supply.
_PACKAGE_FIXTURE_PREFIXES: tuple[str, ...] = ("examples/process-graph/",)

#: The canonical DeepPlant symbol resources under ``src/deepplant/assets/**``.
#: They are runtime and packaged-product inputs, not merely Python source or
#: package metadata: the renderer reads them through ``importlib.resources``
#: (``src/deepplant/render/symbols.py::read_process_symbol_svg``), the Editor backend
#: serves them to the browser (``/api/symbols/<role>.svg``, ``editor/api.py``),
#: the Playwright suite drives that browser path, and ``tools/package_editor.py``
#: bundles and verifies a canonical symbol (``REQUIRED_SYMBOL``). A change here
#: therefore selects the conservative complete runtime ownership (``python`` and
#: ``distribution`` also come from the ``src/`` / ``src/deepplant/**`` rules):
#: ``python``, ``distribution``, ``e2e`` and ``package``. This is deliberately
#: scoped to the asset subtree - a generic ``src/deepplant/**`` Core change must
#: not pull in browser E2E or native packaging.
_RUNTIME_ASSET_PREFIXES: tuple[str, ...] = ("src/deepplant/assets/",)

_PACKAGE_PREFIXES: tuple[str, ...] = (
    "apps/editor/",
    "assets/",
    "packaging/",
    "src/deepplant/editor/",
)
_PACKAGE_FILES: frozenset[str] = frozenset(
    {
        "pyproject.toml",
        "pyrightconfig.desktop.json",
        "uv.lock",
        "tools/chromium_notices.py",
        "tools/editor_entry.py",
        "tools/package_editor.py",
        "tools/packaging_toolchain.py",
    }
)

#: Build/CI tooling: a change here can move any job, so it is never routed.
_CONSERVATIVE_FILES: frozenset[str] = frozenset({"Makefile", "tools/ci_changes.py"})
_CONSERVATIVE_PREFIXES: tuple[str, ...] = (".github/",)


@dataclass(frozen=True)
class Classification:
    """The surfaces and evidence jobs a set of changed paths requires."""

    surfaces: Mapping[str, bool]
    reason: str
    conservative_paths: tuple[str, ...] = ()
    unmatched_paths: tuple[str, ...] = ()

    @property
    def full(self) -> bool:
        """Whether the conservative full matrix was selected."""
        return all(self.surfaces.values())

    @property
    def required_jobs(self) -> tuple[str, ...]:
        """The evidence jobs this classification requires."""
        return jobs_for(self.surfaces)


def jobs_for(surfaces: Mapping[str, bool]) -> tuple[str, ...]:
    """Map validation surfaces to the evidence jobs that own them."""
    jobs: list[str] = []
    if surfaces["docs"] or surfaces["agents"]:
        jobs.append(DOCS_JOB)
    if surfaces["python"]:
        jobs.append(PYTHON_JOB)
    if surfaces["distribution"]:
        jobs.append(WHEEL_JOB)
    if surfaces["frontend"]:
        jobs.append(FRONTEND_JOB)
    if surfaces["e2e"]:
        jobs.append(E2E_JOB)
    if surfaces["package"]:
        jobs.append(WINDOWS_PACKAGE_JOB)
        jobs.append(LINUX_PACKAGE_JOB)
    return tuple(jobs)


def full_classification(reason: str) -> Classification:
    """Select the conservative full matrix for a lifecycle boundary."""
    return Classification(surfaces=dict.fromkeys(SURFACES, True), reason=reason)


def changed_paths(base: str, head: str, repo: str | os.PathLike[str] = ".") -> list[str]:
    """Return the changed repository-relative paths between two commits.

    Rename/move detection is deliberately disabled (``--no-renames``) so a move is
    reported as its removed **and** added path. Git's rename detection would
    otherwise report only the destination and silently drop the original path's
    validation surface: moving ``src/deepplant/editor/api.py`` to
    ``src/deepplant/api.py`` must still select the editor boundary it left.
    """
    command = ["git", "diff", "--no-renames", "--name-only", base, head]
    completed = subprocess.run(
        command,
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def classify_paths(paths: Iterable[str]) -> Classification:
    """Classify repository-relative changed paths into validation surfaces."""
    surfaces: dict[str, bool] = {surface: False for surface in SURFACES}
    conservative: list[str] = []
    unmatched: list[str] = []
    for raw in paths:
        path = _normalize(raw)
        if path is None:
            continue
        matched = _surfaces_for(path)
        if matched is None:
            conservative.append(path)
            continue
        if not matched:
            unmatched.append(path)
            continue
        for surface in matched:
            surfaces[surface] = True

    if conservative or unmatched:
        surfaces = dict.fromkeys(SURFACES, True)
        reason = CONSERVATIVE_REASON
    elif any(surfaces.values()):
        reason = "change-aware matrix"
    else:
        reason = "no tracked change"

    return Classification(
        surfaces=surfaces,
        reason=reason,
        conservative_paths=tuple(conservative),
        unmatched_paths=tuple(unmatched),
    )


def render_summary(classification: Classification) -> str:
    """Render a reviewer-readable routing decision for the CI log."""
    selected = classification.required_jobs
    lines = ["changed surfaces:"]
    for surface in SURFACES:
        value = "true" if classification.surfaces[surface] else "false"
        lines.append(f"  {surface}={value}")

    lines += ["", "selected jobs:"]
    lines += [f"  {job}" for job in selected]
    lines.append(f"  {GATE_JOB}")

    lines += ["", "skipped as irrelevant:"]
    skipped = [job for job in EVIDENCE_JOBS if job not in selected]
    lines += [f"  {job}" for job in skipped] if skipped else ["  (none)"]

    lines += ["", f"reason: {classification.reason}"]
    if classification.conservative_paths:
        lines += ["", "conservative triggers (build/CI tooling):"]
        lines += [f"  {path}" for path in classification.conservative_paths]
    if classification.unmatched_paths:
        lines += ["", "unrecognized paths (conservative by default):"]
        lines += [f"  {path}" for path in classification.unmatched_paths]
    return "\n".join(lines)


def enforce_gate(
    required_jobs: Sequence[str],
    results: Mapping[str, str],
    *,
    guard_required: bool,
) -> tuple[str, ...]:
    """Return the problems that must make the aggregate CI gate fail.

    An empty result means the gate may pass. The gate deliberately fails closed:
    a required job that failed, was cancelled, or never ran is a failure, and a
    job the classifier did not select may only be ``skipped`` (or ``success`` as
    a harmless bonus), never a failure.
    """
    required = set(required_jobs)
    problems: list[str] = []

    for job in sorted(required - set(EVIDENCE_JOBS)):
        problems.append(f"classifier requested an unknown job: {job}")

    for job in ALWAYS_REQUIRED_JOBS:
        result = results.get(job, "missing")
        if result != "success":
            problems.append(f"required job '{job}' did not pass (result: {result})")

    for job in EVIDENCE_JOBS:
        result = results.get(job, "missing")
        if job in required:
            if result != "success":
                problems.append(f"required job '{job}' did not pass (result: {result})")
        elif result not in ("skipped", "success"):
            problems.append(f"job '{job}' was not required for this change but reported '{result}'")

    if guard_required:
        result = results.get(PR_GUARD_JOB, "missing")
        if result != "success":
            problems.append(f"required job '{PR_GUARD_JOB}' did not pass (result: {result})")

    return tuple(problems)


def _normalize(raw: str) -> str | None:
    """Return a normalized repository-relative path, or ``None`` for a blank."""
    path = raw.strip().replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    path = path.lstrip("/")
    return path or None


def _surfaces_for(path: str) -> frozenset[str] | None:
    """Return the surfaces a path selects, or ``None`` for the full matrix."""
    if path == _PULL_REQUEST_TEMPLATE:
        return frozenset({"docs"})
    if path.startswith(_CONSERVATIVE_PREFIXES) or path in _CONSERVATIVE_FILES:
        return None

    surfaces: set[str] = set()
    if (
        path in _ROOT_DOC_FILES
        or path in _WHEEL_ROOT_FILES
        or path in _PACKAGE_ROOT_FILES
        or path.startswith(_DOC_PREFIXES)
    ):
        surfaces.add("docs")
    if path in _AGENT_FILES or path.startswith(_AGENT_PREFIXES):
        surfaces.add("agents")
    if path.startswith(_PYTHON_PREFIXES) or path in _PYTHON_FILES:
        surfaces.add("python")
    if (
        path.startswith(_DISTRIBUTION_PREFIXES)
        or path in _DISTRIBUTION_FILES
        or path in _WHEEL_ROOT_FILES
    ):
        surfaces.add("distribution")
    if path.startswith(_FRONTEND_PREFIXES):
        surfaces.add("frontend")
    if path.startswith(_E2E_PREFIXES) or path in _E2E_FILES:
        surfaces.add("e2e")
    if path.startswith(_PACKAGE_PREFIXES) or path in _PACKAGE_FILES or path in _PACKAGE_ROOT_FILES:
        surfaces.add("package")
    if path.startswith(_E2E_FIXTURE_PREFIXES):
        surfaces.add("e2e")
    if path.startswith(_PACKAGE_FIXTURE_PREFIXES):
        surfaces.add("package")
    if path.startswith(_RUNTIME_ASSET_PREFIXES):
        surfaces.add("e2e")
        surfaces.add("package")
    return frozenset(surfaces)


def _read_paths(positional: Sequence[str], paths_file: str | None) -> list[str]:
    if positional:
        return list(positional)
    if paths_file:
        return Path(paths_file).read_text(encoding="utf-8").splitlines()
    return sys.stdin.read().splitlines()


def _bool(value: bool) -> str:
    return "true" if value else "false"


def _split_list(raw: str) -> list[str]:
    return [item.strip() for item in raw.replace("\n", ",").split(",") if item.strip()]


def _parse_results(raw: str) -> dict[str, str]:
    results: dict[str, str] = {}
    for chunk in raw.replace(",", "\n").splitlines():
        item = chunk.strip()
        if not item or "=" not in item:
            continue
        name, _, value = item.partition("=")
        results[name.strip()] = value.strip()
    return results


def _env_true(raw: str) -> bool:
    return raw.strip().lower() in ("1", "true", "yes")


def _write_github_output(values: Mapping[str, str]) -> None:
    target = os.environ.get("GITHUB_OUTPUT")
    if not target:
        return
    with Path(target).open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def _write_step_summary(summary: str) -> None:
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if not target:
        return
    with Path(target).open("a", encoding="utf-8") as handle:
        handle.write(f"{summary}\n")


def build_parser() -> argparse.ArgumentParser:
    """Build the ``classify`` / ``changed-paths`` / ``gate`` command-line parser."""
    parser = argparse.ArgumentParser(
        prog="ci_changes",
        description="Change-aware CI impact classification and aggregate gate.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    classify = subparsers.add_parser(
        "classify",
        help="Classify changed paths into validation surfaces and evidence jobs.",
    )
    classify.add_argument(
        "--event",
        default="pull_request",
        choices=("pull_request", "push", "workflow_dispatch"),
    )
    classify.add_argument(
        "--paths-file",
        default=None,
        help="Read the changed paths from this file instead of standard input.",
    )
    classify.add_argument("paths", nargs="*")

    changed = subparsers.add_parser(
        "changed-paths",
        help="Print the changed paths between two commits (rename-safe).",
    )
    changed.add_argument("base")
    changed.add_argument("head")
    changed.add_argument("--repo", default=".")

    gate = subparsers.add_parser(
        "gate",
        help="Enforce the aggregate required CI result for this change.",
    )
    gate.add_argument("--required-jobs", default=None)
    gate.add_argument("--results", default=None)
    gate.add_argument("--enforce-pr-guard", action="store_true")

    return parser


def _run_classify(arguments: argparse.Namespace) -> int:
    event = cast(str, arguments.event)
    paths_file = cast("str | None", arguments.paths_file)
    positional = cast("list[str]", arguments.paths)

    if event == "pull_request":
        classification = classify_paths(_read_paths(positional, paths_file))
    else:
        classification = full_classification(
            f"full matrix ({event}: full-confidence lifecycle boundary)"
        )

    summary = render_summary(classification)
    print(summary, flush=True)
    _write_step_summary(summary)

    outputs = {surface: _bool(classification.surfaces[surface]) for surface in SURFACES}
    outputs["full"] = _bool(classification.full)
    outputs["reason"] = classification.reason
    outputs["required-jobs"] = ",".join(classification.required_jobs)
    _write_github_output(outputs)
    return 0


def _run_changed_paths(arguments: argparse.Namespace) -> int:
    base = cast(str, arguments.base)
    head = cast(str, arguments.head)
    repo = cast(str, arguments.repo)
    for path in changed_paths(base, head, repo=repo):
        print(path)
    return 0


def _run_gate(arguments: argparse.Namespace) -> int:
    required_argument = cast("str | None", arguments.required_jobs)
    results_argument = cast("str | None", arguments.results)
    guard_flag = cast(bool, arguments.enforce_pr_guard)

    required_raw = (
        required_argument if required_argument is not None else os.environ.get("REQUIRED_JOBS", "")
    )
    results_raw = (
        results_argument if results_argument is not None else os.environ.get("RESULTS", "")
    )
    guard_required = guard_flag or _env_true(os.environ.get("ENFORCE_PR_GUARD", ""))

    required = _split_list(required_raw)
    results = _parse_results(results_raw)
    problems = enforce_gate(required, results, guard_required=guard_required)

    lines = ["change-aware CI gate", "", "job results:"]
    for job in (*ALWAYS_REQUIRED_JOBS, PR_GUARD_JOB, *EVIDENCE_JOBS):
        result = results.get(job)
        if result is None:
            continue
        if job == PR_GUARD_JOB:
            mark = "required" if guard_required else "not required"
        elif job in ALWAYS_REQUIRED_JOBS:
            mark = "required"
        else:
            mark = "required" if job in required else "not required"
        lines.append(f"  {job}: {result} ({mark})")

    lines += ["", "required jobs: " + (", ".join(required) if required else "(none)")]
    if problems:
        lines += ["", "FAILED:"]
        lines += [f"  - {problem}" for problem in problems]
    else:
        lines += ["", "PASSED: every required job succeeded or was intentionally irrelevant."]

    summary = "\n".join(lines)
    print(summary, flush=True)
    _write_step_summary(summary)
    return 1 if problems else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the ``classify``, ``changed-paths``, or ``gate`` subcommand."""
    arguments = build_parser().parse_args(None if argv is None else list(argv))
    command = cast(str, arguments.command)
    if command == "classify":
        return _run_classify(arguments)
    if command == "changed-paths":
        return _run_changed_paths(arguments)
    return _run_gate(arguments)


if __name__ == "__main__":
    sys.exit(main())
