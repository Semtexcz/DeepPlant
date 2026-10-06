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
from pathlib import Path
from typing import TYPE_CHECKING, cast

from PySide6.QtCore import QTimer

from deepplant.editor.desktop import WINDOW_TITLE
from deepplant.editor.desktop_qt.window import (
    CANVAS_PROBE_JS,
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
    results: dict[str, object] = {}
    report: dict[str, object] = {}
    finished = False

    def finish_once(code: int) -> None:
        """Finish exactly once, so a late timer cannot restart the loop exit."""
        nonlocal finished
        if finished:
            return
        finished = True
        stage_log(report_path, f"finish: exit code {code}")
        finish(code)

    def fail(message: str) -> None:
        stage_log(report_path, f"fail: {message}")
        write_json(report_path, {"verdict": "fail", "error": message})
        echo(f"self-check failed: {message}")
        finish_once(1)

    def failed_guard(step: str, work: Callable[[], None]) -> None:
        """Run one probe step, reporting an unexpected error instead of hanging.

        An exception raised inside a Qt callback would otherwise be printed to a
        stream a GUI build may not have and would leave the event loop running
        forever, which is exactly the failure mode automated callers cannot
        diagnose.
        """
        try:
            work()
        except Exception as exc:  # noqa: BLE001 - reported, never swallowed
            fail(f"{step} raised {type(exc).__name__}: {exc}")

    def finalize() -> None:
        stage_log(report_path, "finalize: begin")
        window = editor.window
        visible_before_close = window.isVisible()
        server_before_close = editor.server
        port_before_close = server_before_close.port if server_before_close is not None else None

        # The real close path: `closeEvent` -> stop the owned server -> Qt quits.
        window.close()
        window_closed = not window.isVisible()

        # Measured after close, from the server object itself - never inferred
        # from a cleared reference.
        shutdown = editor.server_shutdown
        server_after_close = editor.server
        thread_alive_after_close = bool(
            server_after_close is not None and server_after_close.running
        )
        server_stopped = bool(shutdown.requested and not thread_alive_after_close)
        port_released = port_before_close is None or not _port_accepts(port_before_close)

        content_extra: dict[str, object] = {}
        if has_project:
            content_checks, content_extra = _self_check_verdict(
                results.get("canvas"), results.get("inspector")
            )
        else:
            content_checks = True

        checks = _as_mapping(content_extra.get("checks"))
        checks["windowVisible"] = visible_before_close
        checks["windowClosed"] = window_closed
        checks["serverStopRequested"] = bool(shutdown.requested)
        checks["serverStopped"] = server_stopped
        checks["serverThreadTerminated"] = not thread_alive_after_close
        checks["portReleased"] = port_released
        lifecycle_passed = (
            visible_before_close
            and window_closed
            and bool(shutdown.requested)
            and server_stopped
            and not thread_alive_after_close
            and port_released
        )
        passed = bool(content_checks and lifecycle_passed)

        report.clear()
        report["checks"] = checks
        report["lifecycle"] = {
            "windowVisible": visible_before_close,
            "windowClosed": window_closed,
            "serverStopRequested": bool(shutdown.requested),
            "serverStopped": server_stopped,
            "serverThreadAliveAfterClose": thread_alive_after_close,
            "portReleased": port_released,
            # Only knowable after QApplication.exec() returns; completed there.
            "eventLoopReturned": False,
        }
        for key, value in content_extra.items():
            if key not in {"checks", "verdict"}:
                report[key] = value
        report["verdict"] = "pass" if passed else "fail"
        report["windowTitle"] = WINDOW_TITLE
        stage_log(
            report_path,
            f"finalize: serverStopped={server_stopped} "
            f"threadAlive={thread_alive_after_close} portReleased={port_released}",
        )
        write_json(report_path, report)
        echo(f"self-check verdict: {report['verdict']}")
        finish_once(0 if passed else 1)

    def probe_canvas() -> None:
        stage_log(report_path, "probe: canvas")
        view = editor.window.web_view
        if view is None:
            fail("the native window never created an embedded view")
            return
        view.page().runJavaScript(CANVAS_PROBE_JS, after_canvas)

    def after_canvas(raw: object) -> None:
        def handle() -> None:
            canvas = _parse_probe(raw)
            stage_log(report_path, f"probe: canvas result {bool(canvas)}")
            if not canvas:
                fail("the canvas probe returned no usable result")
                return
            results["canvas"] = canvas
            QTimer.singleShot(POST_SELECTION_SETTLE_MS, lambda: probe_inspector(canvas))

        failed_guard("the canvas probe", handle)

    def probe_inspector(canvas: dict[str, object]) -> None:
        view = editor.window.web_view
        if view is None:
            fail("the embedded view disappeared")
            return

        def handle_result(raw: object) -> None:
            after_inspector(canvas, raw)

        view.page().runJavaScript(INSPECTOR_PROBE_JS, handle_result)

    def after_inspector(canvas: dict[str, object], raw: object) -> None:
        del canvas

        def handle() -> None:
            results["inspector"] = _parse_probe(raw)
            stage_log(report_path, "probe: inspector done")
            finalize()

        failed_guard("the inspector probe", handle)

    def on_loaded(ok: bool) -> None:
        stage_log(report_path, f"page loaded: {ok}")
        if not ok:
            fail("the embedded page did not finish loading")
            return
        QTimer.singleShot(
            POST_LOAD_SETTLE_MS, lambda: failed_guard("the canvas probe", probe_canvas)
        )

    # The watchdog is armed before anything else, so no probe, dialog, or stalled
    # webview can keep the process alive past the caller's patience.
    stage_log(report_path, "self-check: watchdog armed")
    QTimer.singleShot(
        SELF_CHECK_TIMEOUT_MS,
        lambda: fail(f"the self-check did not finish within {SELF_CHECK_TIMEOUT_MS} ms"),
    )

    if not has_project:
        # No model was supplied: the bootstrap window is the thing under test.
        QTimer.singleShot(POST_LOAD_SETTLE_MS, lambda: failed_guard("the window check", finalize))
        return report

    editor.page_loaded_hook = on_loaded
    return report


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
