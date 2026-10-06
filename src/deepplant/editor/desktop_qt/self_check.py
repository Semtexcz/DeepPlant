# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Packaged-desktop self-check, probing, and diagnostics.

The automated verification hook that drives the real native window and the
real embedded SPA through Qt's own JavaScript engine, records measured
lifecycle facts (window visibility, server-thread termination, loopback-port
release), and writes a machine-readable report plus a stage log. A stalled
webview or platform dialog still yields a bounded, failed run (Issue #93).
"""

from __future__ import annotations

import json
import socket
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, cast

from PySide6.QtCore import QTimer

from deepplant.editor.desktop import EMPTY_WORKSPACE_STATUS_TEXT, WINDOW_TITLE
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

if TYPE_CHECKING:
    from deepplant.editor.desktop_qt.runtime import DesktopEditor


def write_json(path: Path, payload: dict[str, object]) -> None:
    """Write one JSON report, creating the parent directory if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stage_log(report_path: Path, message: str) -> None:
    """Append one diagnostic line next to the self-check report.

    A packaged Windows Editor is a GUI (``--windowed``) executable with no
    console, so stdout/stderr carry nothing. This is the deliberate diagnostics
    path for that case: a small stage log beside the machine-readable report, so
    a stalled or failing run is diagnosable instead of silent.
    """
    log_path = report_path.with_name(report_path.name + ".log")
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{time.monotonic():.3f} {message}\n")
    except OSError:
        # Diagnostics must never break the application under test.
        return


def _port_accepts(port: int) -> bool:
    """Whether the loopback port still accepts connections."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1.0):
            return True
    except OSError:
        return False


def _parse_probe(raw: object) -> dict[str, object]:
    """Narrow a JavaScript probe result into a plain mapping (never raise)."""
    if not isinstance(raw, str):
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    return dict(cast("dict[str, object]", parsed))


def _self_check_verdict(
    canvas: object,
    inspector: object,
) -> tuple[bool, dict[str, object]]:
    """Decide whether the real embedded application matched the expectations.

    The checks are read from the *rendered* page via the webview's JavaScript
    engine - the production host and the production SPA, not a mock.
    """
    canvas_fields = _as_mapping(canvas)
    inspector_fields = _as_mapping(inspector)
    fields = _as_mapping(inspector_fields.get("fields"))
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
    fields = _as_mapping(probe)
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


@dataclass
class _SelfCheckRun:
    """Mutable state carried across one packaged-desktop self-check run.

    The probe chain is callback-driven and asynchronous (Qt timers and the
    webview's JavaScript engine), so the run's accumulated probe results, the
    report being built, and the one-shot finish guard must be shared by several
    helpers. This is genuine run state, not a service object.
    """

    editor: DesktopEditor
    report_path: Path
    echo: Callable[[str], None]
    finish: Callable[[int], None]
    has_project: bool
    results: dict[str, object] = field(default_factory=dict[str, object])
    report: dict[str, object] = field(default_factory=dict[str, object])
    finished: bool = False


def _finish_once(run: _SelfCheckRun, code: int) -> None:
    """Finish exactly once, so a late timer cannot restart the loop exit."""
    if run.finished:
        return
    run.finished = True
    stage_log(run.report_path, f"finish: exit code {code}")
    run.finish(code)


def _fail(run: _SelfCheckRun, message: str) -> None:
    """Record and report a self-check failure, then finish the run."""
    stage_log(run.report_path, f"fail: {message}")
    write_json(run.report_path, {"verdict": "fail", "error": message})
    run.echo(f"self-check failed: {message}")
    _finish_once(run, 1)


def _failed_guard(run: _SelfCheckRun, step: str, work: Callable[[], None]) -> None:
    """Run one probe step, reporting an unexpected error instead of hanging.

    An exception raised inside a Qt callback would otherwise be printed to a
    stream a GUI build may not have and would leave the event loop running
    forever, which is exactly the failure mode automated callers cannot
    diagnose.
    """
    try:
        work()
    except Exception as exc:  # noqa: BLE001 - reported, never swallowed
        _fail(run, f"{step} raised {type(exc).__name__}: {exc}")


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
        port_released=port_before_close is None or not _port_accepts(port_before_close),
    )


def _compose_report(
    run: _SelfCheckRun, measurement: _CloseMeasurement
) -> tuple[dict[str, object], bool]:
    """Build the self-check report payload and the overall verdict."""
    content_extra: dict[str, object] = {}
    if run.has_project:
        content_checks, content_extra = _self_check_verdict(
            run.results.get("canvas"), run.results.get("inspector")
        )
    else:
        content_checks, content_extra = _empty_workspace_verdict(run.results.get("workspace"))

    checks = _as_mapping(content_extra.get("checks"))
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
    report["windowTitle"] = WINDOW_TITLE
    return report, passed


def _finalize(run: _SelfCheckRun) -> None:
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
    _finish_once(run, 0 if passed else 1)


def _probe_canvas(run: _SelfCheckRun) -> None:
    """Ask the embedded webview for the rendered process canvas facts."""
    stage_log(run.report_path, "probe: canvas")
    view = run.editor.window.web_view
    if view is None:
        _fail(run, "the native window never created an embedded view")
        return

    def handle_result(raw: object) -> None:
        _after_canvas(run, raw)

    view.page().runJavaScript(CANVAS_PROBE_JS, handle_result)


def _after_canvas(run: _SelfCheckRun, raw: object) -> None:
    """Consume the canvas probe result and schedule the inspector probe."""

    def handle() -> None:
        canvas = _parse_probe(raw)
        stage_log(run.report_path, f"probe: canvas result {bool(canvas)}")
        if not canvas:
            _fail(run, "the canvas probe returned no usable result")
            return
        run.results["canvas"] = canvas
        QTimer.singleShot(POST_SELECTION_SETTLE_MS, lambda: _probe_inspector(run))

    _failed_guard(run, "the canvas probe", handle)


def _probe_inspector(run: _SelfCheckRun) -> None:
    """Ask the embedded webview for the read-only Inspector facts."""
    view = run.editor.window.web_view
    if view is None:
        _fail(run, "the embedded view disappeared")
        return

    def handle_result(raw: object) -> None:
        _after_inspector(run, raw)

    view.page().runJavaScript(INSPECTOR_PROBE_JS, handle_result)


def _after_inspector(run: _SelfCheckRun, raw: object) -> None:
    """Consume the inspector probe result and finalize the run."""

    def handle() -> None:
        run.results["inspector"] = _parse_probe(raw)
        stage_log(run.report_path, "probe: inspector done")
        _finalize(run)

    _failed_guard(run, "the inspector probe", handle)


def _probe_empty(run: _SelfCheckRun) -> None:
    """Ask the embedded webview for the rendered empty-workspace facts."""
    stage_log(run.report_path, "probe: empty workspace")
    view = run.editor.window.web_view
    if view is None:
        _fail(run, "the native window never created an embedded view")
        return

    def handle_result(raw: object) -> None:
        _after_empty(run, raw)

    view.page().runJavaScript(EMPTY_WORKSPACE_PROBE_JS, handle_result)


def _after_empty(run: _SelfCheckRun, raw: object) -> None:
    """Consume the empty-workspace probe result and finalize the run."""

    def handle() -> None:
        workspace = _parse_probe(raw)
        stage_log(run.report_path, f"probe: empty workspace result {bool(workspace)}")
        if not workspace:
            _fail(run, "the empty-workspace probe returned no usable result")
            return
        run.results["workspace"] = workspace
        _finalize(run)

    _failed_guard(run, "the empty-workspace probe", handle)


def _on_loaded(run: _SelfCheckRun, ok: bool) -> None:
    """React to the embedded page finishing (or failing) its load."""
    stage_log(run.report_path, f"page loaded: {ok}")
    if not ok:
        _fail(run, "the embedded page did not finish loading")
        return
    if run.has_project:
        QTimer.singleShot(
            POST_LOAD_SETTLE_MS,
            lambda: _failed_guard(run, "the canvas probe", lambda: _probe_canvas(run)),
        )
        return
    # No document was supplied: the shared SPA's empty-workspace state is the thing
    # under test, so the probe reads the real rendered page (Issue #97).
    QTimer.singleShot(
        POST_LOAD_SETTLE_MS,
        lambda: _failed_guard(run, "the empty-workspace probe", lambda: _probe_empty(run)),
    )


def start_self_check(
    editor: DesktopEditor,
    report_path: Path,
    *,
    echo: Callable[[str], None],
    finish: Callable[[int], None],
    has_project: bool,
) -> dict[str, object]:
    """Drive the packaged-desktop verification through the real application.

    Issue #93 requires the packaged Windows/Linux artifacts to prove the actual
    graphical product, not merely that an HTTP endpoint answered. This narrow,
    documented test hook launches the ordinary application, shows the real native
    window, drives the real embedded SPA through Qt's own JavaScript engine, then
    closes the window through the same ``closeEvent`` a user triggers and records
    whether the owned server thread and the loopback socket went away.

    The lifecycle facts are recorded as *measured* values, not bookkeeping flags:
    ``serverStopped`` is true only when the owned server thread has actually
    terminated, and the report is completed after the event loop returns (see
    :func:`finalize_self_check_after_loop`) so a forced exit can never make the
    report appear clean (Issue #93 review).

    Returns the mutable report so ``run_host`` can complete it after the loop.
    """
    run = _SelfCheckRun(
        editor=editor,
        report_path=report_path,
        echo=echo,
        finish=finish,
        has_project=has_project,
    )

    # The watchdog is armed before anything else, so no probe, dialog, or stalled
    # webview can keep the process alive past the caller's patience.
    stage_log(report_path, "self-check: watchdog armed")
    QTimer.singleShot(
        SELF_CHECK_TIMEOUT_MS,
        lambda: _fail(run, f"the self-check did not finish within {SELF_CHECK_TIMEOUT_MS} ms"),
    )

    # The shared SPA loads in both cases (Issue #97), so the page-loaded hook is
    # always installed; it decides which probe to run from ``has_project``.
    editor.page_loaded_hook = lambda ok: _on_loaded(run, ok)
    return run.report


def _as_mapping(value: object) -> dict[str, object]:
    """Return ``value`` as a plain ``dict[str, object]`` (empty when it is not one)."""
    if isinstance(value, dict):
        return dict(cast("dict[str, object]", value))
    return {}


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

    checks = _as_mapping(report.get("checks"))
    lifecycle = _as_mapping(report.get("lifecycle"))
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
