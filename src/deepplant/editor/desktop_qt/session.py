# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Shared runtime state and low-level primitives for the packaged self-check.

The packaged-desktop self-check is a callback-driven, asynchronous run: Qt timers
and the webview's JavaScript engine drive a probe chain. This module owns the
mutable run state and the small primitives every scenario shares (report and
stage-log writing, probe-result parsing, bounded failure handling, and Qt timer
scheduling), so the scenario modules build on one common base instead of
duplicating it. It decides no engineering semantics.
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

from deepplant.editor.desktop import SELF_CHECK_SCENARIO_LOADED

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


def port_accepts(port: int) -> bool:
    """Whether the loopback port still accepts connections."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1.0):
            return True
    except OSError:
        return False


def parse_probe(raw: object) -> dict[str, object]:
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


def as_mapping(value: object) -> dict[str, object]:
    """Return ``value`` as a plain ``dict[str, object]`` (empty when it is not one)."""
    if isinstance(value, dict):
        return dict(cast("dict[str, object]", value))
    return {}


@dataclass
class SelfCheckRun:
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
    scenario: str = SELF_CHECK_SCENARIO_LOADED
    transition_projects: tuple[Path, ...] = ()
    transition_invalid_project: Path | None = None
    loads: int = 0
    results: dict[str, object] = field(default_factory=dict[str, object])
    report: dict[str, object] = field(default_factory=dict[str, object])
    finished: bool = False
    #: Installed by the self-check so a scenario can complete the run without
    #: importing the module that owns the report composition.
    on_complete: Callable[[], None] | None = None


def finish_once(run: SelfCheckRun, code: int) -> None:
    """Finish exactly once, so a late timer cannot restart the loop exit."""
    if run.finished:
        return
    run.finished = True
    stage_log(run.report_path, f"finish: exit code {code}")
    run.finish(code)


def fail(run: SelfCheckRun, message: str) -> None:
    """Record and report a self-check failure, then finish the run.

    Idempotent: once the run has finished, a late callback (a stray
    ``loadFinished`` during teardown, or the watchdog) must not overwrite an
    already-written report.
    """
    if run.finished:
        return
    stage_log(run.report_path, f"fail: {message}")
    write_json(run.report_path, {"verdict": "fail", "error": message})
    run.echo(f"self-check failed: {message}")
    finish_once(run, 1)


def failed_guard(run: SelfCheckRun, step: str, work: Callable[[], None]) -> None:
    """Run one probe step, reporting an unexpected error instead of hanging.

    An exception raised inside a Qt callback would otherwise be printed to a
    stream a GUI build may not have and would leave the event loop running
    forever, which is exactly the failure mode automated callers cannot diagnose.
    """
    try:
        work()
    except Exception as exc:  # noqa: BLE001 - reported, never swallowed
        fail(run, f"{step} raised {type(exc).__name__}: {exc}")


def settle(ms: int, then: Callable[[], None]) -> None:
    """Continue after a bounded settle delay, so the SPA can finish rendering."""
    QTimer.singleShot(ms, then)
