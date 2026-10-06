# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Packaged-desktop self-check: the empty/loaded scenarios and the run harness.

The automated verification hook that drives the real native window and the real
embedded SPA through Qt's own JavaScript engine, records measured lifecycle facts
(window visibility, server-thread termination, loopback-port release), and writes a
machine-readable report plus a stage log. A stalled webview or platform dialog still
yields a bounded, failed run (Issue #93).

This module owns the run harness and the two scenarios Issue #93/#97/#98 require:
the shared SPA's ``empty`` workspace and the canonical fixture's ``loaded`` workflow.
The ``transition`` scenario - the long-lived session across project replacement
(Issue #97 review) - lives in :mod:`deepplant.editor.desktop_qt.transition`; the
shared run state and primitives live in
:mod:`deepplant.editor.desktop_qt.session`.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer

from deepplant.editor.desktop import (
    EMPTY_WORKSPACE_STATUS_TEXT,
    SELF_CHECK_SCENARIO_LOADED,
    SELF_CHECK_SCENARIO_TRANSITION,
    WINDOW_TITLE,
)
from deepplant.editor.desktop_qt.probes import (
    CANVAS_PROBE_JS,
    EMPTY_WORKSPACE_PROBE_JS,
    EXPECTED_STEPS,
    EXPECTED_STREAMS,
    INSPECTOR_PROBE_JS,
    POST_LOAD_SETTLE_MS,
    POST_SELECTION_SETTLE_MS,
    PROBE_STEP_ID,
    SELF_CHECK_TIMEOUT_MS,
)
from deepplant.editor.desktop_qt.session import (
    SelfCheckRun,
    as_mapping,
    fail,
    failed_guard,
    finish_once,
    parse_probe,
    port_accepts,
    stage_log,
    write_json,
)

if TYPE_CHECKING:
    from deepplant.editor.desktop_qt.runtime import DesktopEditor

__all__ = [
    "finalize_self_check_after_loop",
    "stage_log",
    "start_self_check",
    "write_json",
]


def _self_check_verdict(
    canvas: object,
    inspector: object,
) -> tuple[bool, dict[str, object]]:
    """Decide whether the real embedded application matched the expectations.

    The checks are read from the *rendered* page via the webview's JavaScript
    engine - the production host and the production SPA, not a mock.
    """
    canvas_fields = as_mapping(canvas)
    inspector_fields = as_mapping(inspector)
    fields = as_mapping(inspector_fields.get("fields"))
    checks: dict[str, object] = {
        "validationValid": canvas_fields.get("statusText") == "Valid",
        "processSteps": canvas_fields.get("processSteps") == EXPECTED_STEPS,
        "processStreams": canvas_fields.get("processStreams") == EXPECTED_STREAMS,
        "pumpSelected": inspector_fields.get("heading") == PROBE_STEP_ID,
        "inspectorFunction": fields.get("Function") == "pumping",
        "productionSpa": canvas_fields.get("devEntryPoint") is False,
    }
    passed = all(value is True for value in checks.values())
    return passed, {
        "verdict": "pass" if passed else "fail",
        "checks": checks,
        "canvas": canvas_fields,
        "inspector": inspector_fields,
    }


def _empty_workspace_verdict(probe: object) -> tuple[bool, dict[str, object]]:
    """Decide whether the real embedded application proved the empty workspace.

    Issue #97 requires the packaged no-project launch to prove the *shared Vue
    SPA*, not merely that a native bootstrap widget appeared. The checks below are
    read from the rendered page through the webview's JavaScript engine: the
    ordinary production SPA rendered with no active document, no engineering model
    was fabricated (zero projected steps), the status is the neutral "no project
    open" state rather than "Invalid", and no Process/PFD projection failure is
    reported.
    """
    fields = as_mapping(probe)
    checks: dict[str, object] = {
        "productionSpa": fields.get("devEntryPoint") is False,
        "workspaceEmpty": fields.get("processSteps") == 0,
        "statusNoProject": fields.get("statusText") == EMPTY_WORKSPACE_STATUS_TEXT,
        "emptyCanvasMessage": fields.get("emptyWorkspaceNotice") is True,
        "noProjectionError": fields.get("projectionError") is None,
    }
    passed = all(value is True for value in checks.values())
    return passed, {
        "verdict": "pass" if passed else "fail",
        "checks": checks,
        "workspace": fields,
    }


@dataclass(frozen=True)
class _CloseMeasurement:
    """Measured lifecycle facts taken before and after the real close path."""

    window_visible: bool
    window_closed: bool
    stop_requested: bool
    server_stopped: bool
    thread_alive_after_close: bool
    port_released: bool


def _measure_close(editor: DesktopEditor) -> _CloseMeasurement:
    """Close the real window and measure the owned-server lifecycle."""
    window = editor.window
    visible_before_close = window.isVisible()
    server_before_close = editor.server
    port_before_close = server_before_close.port if server_before_close is not None else None

    # The real close path: `closeEvent` -> stop the owned server -> Qt quits.
    window.close()
    window_closed = not window.isVisible()

    # Measured after close, from the server object itself - never inferred from a
    # cleared reference.
    shutdown = editor.server_shutdown
    server_after_close = editor.server
    thread_alive_after_close = bool(server_after_close is not None and server_after_close.running)
    return _CloseMeasurement(
        window_visible=visible_before_close,
        window_closed=window_closed,
        stop_requested=bool(shutdown.requested),
        server_stopped=bool(shutdown.requested and not thread_alive_after_close),
        thread_alive_after_close=thread_alive_after_close,
        port_released=port_before_close is None or not port_accepts(port_before_close),
    )


def _compose_report(
    run: SelfCheckRun, measurement: _CloseMeasurement
) -> tuple[dict[str, object], bool]:
    """Build the self-check report payload and the overall verdict."""
    content_extra: dict[str, object] = {}
    if run.scenario == SELF_CHECK_SCENARIO_TRANSITION:
        # Imported here: the replacement scenario is a peer module, and importing
        # it at module scope would couple the two scenarios' import graphs.
        from deepplant.editor.desktop_qt import transition

        content_checks, content_extra = transition.verdict(run)
    elif run.has_project:
        content_checks, content_extra = _self_check_verdict(
            run.results.get("canvas"), run.results.get("inspector")
        )
    else:
        content_checks, content_extra = _empty_workspace_verdict(run.results.get("workspace"))

    checks = as_mapping(content_extra.get("checks"))
    checks["windowVisible"] = measurement.window_visible
    checks["windowClosed"] = measurement.window_closed
    checks["serverStopRequested"] = measurement.stop_requested
    checks["serverStopped"] = measurement.server_stopped
    checks["serverThreadTerminated"] = not measurement.thread_alive_after_close
    checks["portReleased"] = measurement.port_released
    lifecycle_passed = (
        measurement.window_visible
        and measurement.window_closed
        and measurement.stop_requested
        and measurement.server_stopped
        and not measurement.thread_alive_after_close
        and measurement.port_released
    )
    passed = bool(content_checks and lifecycle_passed)

    report: dict[str, object] = {}
    report["checks"] = checks
    report["lifecycle"] = {
        "windowVisible": measurement.window_visible,
        "windowClosed": measurement.window_closed,
        "serverStopRequested": measurement.stop_requested,
        "serverStopped": measurement.server_stopped,
        "serverThreadAliveAfterClose": measurement.thread_alive_after_close,
        "portReleased": measurement.port_released,
        # Only knowable after QApplication.exec() returns; completed there.
        "eventLoopReturned": False,
    }
    for key, value in content_extra.items():
        if key not in {"checks", "verdict"}:
            report[key] = value
    report["verdict"] = "pass" if passed else "fail"
    report["scenario"] = run.scenario
    report["windowTitle"] = WINDOW_TITLE
    return report, passed


def _finalize(run: SelfCheckRun) -> None:
    """Complete the self-check: measure the close, write the report, finish."""
    stage_log(run.report_path, "finalize: begin")
    measurement = _measure_close(run.editor)
    report, passed = _compose_report(run, measurement)
    run.report.clear()
    run.report.update(report)
    stage_log(
        run.report_path,
        f"finalize: serverStopped={measurement.server_stopped} "
        f"threadAlive={measurement.thread_alive_after_close} "
        f"portReleased={measurement.port_released}",
    )
    write_json(run.report_path, run.report)
    run.echo(f"self-check verdict: {run.report['verdict']}")
    finish_once(run, 0 if passed else 1)


def _probe_canvas(run: SelfCheckRun) -> None:
    """Ask the embedded webview for the rendered process canvas facts."""
    stage_log(run.report_path, "probe: canvas")
    view = run.editor.window.web_view
    if view is None:
        fail(run, "the native window never created an embedded view")
        return

    def handle_result(raw: object) -> None:
        _after_canvas(run, raw)

    view.page().runJavaScript(CANVAS_PROBE_JS, handle_result)


def _after_canvas(run: SelfCheckRun, raw: object) -> None:
    """Consume the canvas probe result and schedule the inspector probe."""

    def handle() -> None:
        canvas = parse_probe(raw)
        stage_log(run.report_path, f"probe: canvas result {bool(canvas)}")
        if not canvas:
            fail(run, "the canvas probe returned no usable result")
            return
        run.results["canvas"] = canvas
        QTimer.singleShot(POST_SELECTION_SETTLE_MS, lambda: _probe_inspector(run))

    failed_guard(run, "the canvas probe", handle)


def _probe_inspector(run: SelfCheckRun) -> None:
    """Ask the embedded webview for the read-only Inspector facts."""
    view = run.editor.window.web_view
    if view is None:
        fail(run, "the embedded view disappeared")
        return

    def handle_result(raw: object) -> None:
        _after_inspector(run, raw)

    view.page().runJavaScript(INSPECTOR_PROBE_JS, handle_result)


def _after_inspector(run: SelfCheckRun, raw: object) -> None:
    """Consume the inspector probe result and finalize the run."""

    def handle() -> None:
        run.results["inspector"] = parse_probe(raw)
        stage_log(run.report_path, "probe: inspector done")
        _finalize(run)

    failed_guard(run, "the inspector probe", handle)


def _probe_empty(run: SelfCheckRun) -> None:
    """Ask the embedded webview for the rendered empty-workspace facts."""
    stage_log(run.report_path, "probe: empty workspace")
    view = run.editor.window.web_view
    if view is None:
        fail(run, "the native window never created an embedded view")
        return

    def handle_result(raw: object) -> None:
        _after_empty(run, raw)

    view.page().runJavaScript(EMPTY_WORKSPACE_PROBE_JS, handle_result)


def _after_empty(run: SelfCheckRun, raw: object) -> None:
    """Consume the empty-workspace probe result and finalize the run."""

    def handle() -> None:
        workspace = parse_probe(raw)
        stage_log(run.report_path, f"probe: empty workspace result {bool(workspace)}")
        if not workspace:
            fail(run, "the empty-workspace probe returned no usable result")
            return
        run.results["workspace"] = workspace
        _finalize(run)

    failed_guard(run, "the empty-workspace probe", handle)


def _on_loaded(run: SelfCheckRun, ok: bool) -> None:
    """React to the embedded page finishing (or failing) its load."""
    if run.finished:
        # A stray load (for example the ``about:blank`` teardown navigation) must
        # not restart the probe chain after the report has been written.
        return
    stage_log(run.report_path, f"page loaded: {ok}")
    if not ok:
        fail(run, "the embedded page did not finish loading")
        return
    run.loads += 1
    if run.scenario == SELF_CHECK_SCENARIO_TRANSITION:
        # The replacement lifecycle drives several loads; its own module owns that
        # sequence (empty launch -> project A -> project B).
        from deepplant.editor.desktop_qt import transition

        transition.on_loaded(run, ok)
        return
    if run.has_project:
        QTimer.singleShot(
            POST_LOAD_SETTLE_MS,
            lambda: failed_guard(run, "the canvas probe", lambda: _probe_canvas(run)),
        )
        return
    # No document was supplied: the shared SPA's empty-workspace state is the thing
    # under test, so the probe reads the real rendered page (Issue #97).
    QTimer.singleShot(
        POST_LOAD_SETTLE_MS,
        lambda: failed_guard(run, "the empty-workspace probe", lambda: _probe_empty(run)),
    )


def start_self_check(
    editor: DesktopEditor,
    report_path: Path,
    *,
    echo: Callable[[str], None],
    finish: Callable[[int], None],
    scenario: str = SELF_CHECK_SCENARIO_LOADED,
    projects: Sequence[Path] = (),
    invalid_project: Path | None = None,
) -> dict[str, object]:
    """Drive the packaged-desktop verification through the real application.

    Issue #93 requires the packaged Windows/Linux artifacts to prove the actual
    graphical product, not merely that an HTTP endpoint answered. This narrow,
    documented test hook launches the ordinary application, shows the real native
    window, drives the real embedded SPA through Qt's own JavaScript engine, then
    closes the window through the same ``closeEvent`` a user triggers and records
    whether the owned server thread and the loopback socket went away.

    ``scenario`` selects what is verified: the shared SPA with no document
    (``empty``), the canonical fixture opened through the ordinary path
    (``loaded``), or the project-replacement lifecycle (``transition``, Issue #97
    review), which opens ``projects`` in order and then attempts ``invalid_project``.

    The lifecycle facts are recorded as *measured* values, not bookkeeping flags:
    ``serverStopped`` is true only when the owned server thread has actually
    terminated, and the report is completed after the event loop returns (see
    :func:`finalize_self_check_after_loop`) so a forced exit can never make the
    report appear clean (Issue #93 review).

    Returns the mutable report so ``run_host`` can complete it after the loop.
    """
    run = SelfCheckRun(
        editor=editor,
        report_path=report_path,
        echo=echo,
        finish=finish,
        has_project=scenario == SELF_CHECK_SCENARIO_LOADED,
        scenario=scenario,
        transition_projects=tuple(projects),
        transition_invalid_project=invalid_project,
    )
    run.on_complete = lambda: _finalize(run)

    # The watchdog is armed before anything else, so no probe, dialog, or stalled
    # webview can keep the process alive past the caller's patience.
    stage_log(report_path, "self-check: watchdog armed")
    QTimer.singleShot(
        SELF_CHECK_TIMEOUT_MS,
        lambda: fail(run, f"the self-check did not finish within {SELF_CHECK_TIMEOUT_MS} ms"),
    )

    # The shared SPA loads in every scenario (Issue #97), so the page-loaded hook is
    # always installed; it decides which probe chain to run.
    editor.page_loaded_hook = lambda ok: _on_loaded(run, ok)
    return run.report


def finalize_self_check_after_loop(
    report_path: Path,
    report: dict[str, object],
    editor: DesktopEditor,
) -> None:
    """Complete the self-check report once the event loop has returned.

    ``eventLoopReturned`` and the final server-thread state are only knowable after
    ``QApplication.exec()`` returns, so they are recorded here rather than guessed
    inside the probe. This runs on the ordinary return path; the process is never
    force-exited to make the report look clean, so a stalled teardown shows up as a
    failed run instead of being hidden (Issue #93 review).
    """
    server = editor.server
    thread_alive = bool(server is not None and server.running)
    shutdown = editor.server_shutdown

    if not report:
        # The self-check failed before ``finalize()`` ran (a page-load or probe
        # failure, or the watchdog). Leave the failure report exactly as written.
        return

    checks = as_mapping(report.get("checks"))
    lifecycle = as_mapping(report.get("lifecycle"))
    checks["eventLoopReturned"] = True
    checks["serverThreadTerminated"] = not thread_alive
    lifecycle["eventLoopReturned"] = True
    lifecycle["serverThreadAliveAfterClose"] = thread_alive
    report["checks"] = checks
    report["lifecycle"] = lifecycle

    # A still-live owned server after the loop returned can only downgrade the
    # verdict; a failing verdict is never upgraded here.
    if report.get("verdict") == "pass" and (thread_alive or not shutdown.stopped):
        report["verdict"] = "fail"

    write_json(report_path, report)
    stage_log(
        report_path,
        f"host: report completed (eventLoopReturned=True, serverThreadAlive={thread_alive})",
    )
