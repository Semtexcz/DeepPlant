# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""The packaged project-replacement (transition) self-check scenario.

Issue #97 review requires integrated evidence that the Editor session exists
independently of its active document: opening or replacing a project must not
recreate or leak the native window, the webview, the owned server, its socket, its
origin or its port. This module drives that scenario through the real application -
launch empty, open project A through the real Open handler, replace it with project
B, then attempt a failing open - and reads the *measured* identity of those
resources before and after every change. It decides no engineering semantics.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, cast

from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QMainWindow

from deepplant.editor.desktop import (
    EMPTY_WORKSPACE_STATUS_TEXT,
    TRANSITION_PROJECT_B_EXPECTED_STEPS,
    TRANSITION_PROJECT_B_EXPECTED_STREAMS,
    TRANSITION_PROJECT_B_PROBE_FUNCTION,
    TRANSITION_PROJECT_B_PROBE_STEP_ID,
)
from deepplant.editor.desktop_qt.probes import (
    EMPTY_WORKSPACE_PROBE_JS,
    EXPECTED_STEPS,
    EXPECTED_STREAMS,
    INSPECTOR_PROBE_JS,
    POST_LOAD_SETTLE_MS,
    POST_SELECTION_SETTLE_MS,
    PROBE_STEP_ID,
    canvas_probe_js,
)
from deepplant.editor.desktop_qt.session import (
    SelfCheckRun,
    as_mapping,
    fail,
    failed_guard,
    parse_probe,
    settle,
    stage_log,
)

__all__ = ["on_loaded", "verdict"]

if TYPE_CHECKING:
    from deepplant.editor.desktop_qt.runtime import DesktopEditor


def _linux_listening_ports(pid: int) -> set[int] | None:
    """Listening TCP ports owned by ``pid`` on Linux, or ``None`` when unreadable."""
    fd_dir = Path(f"/proc/{pid}/fd")
    inodes: set[str] = set()
    try:
        for entry in fd_dir.iterdir():
            try:
                target = os.readlink(entry)
            except OSError:
                continue
            if target.startswith("socket:[") and target.endswith("]"):
                inodes.add(target[len("socket:[") : -1])
    except OSError:
        return None
    ports: set[int] = set()
    for table in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            text = Path(table).read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines()[1:]:
            columns = line.split()
            # 0A is the TCP LISTEN state; column 9 is the socket inode.
            if len(columns) < 10 or columns[3] != "0A" or columns[9] not in inodes:
                continue
            try:
                ports.add(int(columns[1].rsplit(":", 1)[1], 16))
            except (IndexError, ValueError):
                continue
    return ports


def _windows_listening_ports(pid: int) -> set[int] | None:
    """Listening TCP ports owned by ``pid`` on Windows, or ``None`` if unavailable."""
    try:
        completed = subprocess.run(
            ["netstat", "-ano", "-p", "TCP"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    ports: set[int] = set()
    for line in completed.stdout.splitlines():
        columns = line.split()
        # Proto, Local Address, Foreign Address, State, PID.
        if len(columns) != 5 or columns[3].upper() != "LISTENING":
            continue
        try:
            if int(columns[4]) != pid:
                continue
            ports.add(int(columns[1].rsplit(":", 1)[1]))
        except ValueError:
            continue
    return ports


def _listening_tcp_ports(pid: int) -> set[int] | None:
    """Return the TCP ports ``pid`` is listening on, or ``None`` when unknown.

    This is the measured half of "opening a project must not leave an extra
    serving socket behind": the owned ``EditorServer`` binds exactly one loopback
    listener, so the process's set of listening ports must not change while the
    workspace moves between documents. Linux reads ``/proc``; Windows parses
    ``netstat -ano``; another platform reports ``None`` (unknown) rather than
    guessing.
    """
    if os.name == "nt":
        return _windows_listening_ports(pid)
    if sys.platform.startswith("linux"):
        return _linux_listening_ports(pid)
    return None


def _session_identity(editor: DesktopEditor) -> dict[str, object]:
    """Capture the measured identity of the long-lived session resources.

    These are *measured* objects and OS facts, not bookkeeping flags: the Python
    identity of the native window, the embedded webview and the owned server, the
    server's origin and bound port, the count of Qt main windows and web views, and
    the process's listening TCP ports. Comparing snapshots taken before and after a
    document change is what proves the session is reused rather than recreated.
    """
    window = editor.window
    view = window.web_view
    server = editor.server
    widgets = QApplication.allWidgets()
    listeners = _listening_tcp_ports(os.getpid())
    return {
        "windowId": id(window),
        "viewId": None if view is None else id(view),
        "serverId": None if server is None else id(server),
        "origin": editor.current_origin(),
        "port": None if server is None else server.port,
        "baseUrl": None if server is None else server.base_url,
        "mainWindowCount": sum(1 for widget in widgets if isinstance(widget, QMainWindow)),
        "webViewCount": sum(1 for widget in widgets if isinstance(widget, QWebEngineView)),
        "listeningPorts": None if listeners is None else sorted(listeners),
    }


def _probe_script(
    run: SelfCheckRun,
    script: str,
    key: str,
    then: Callable[[], None],
) -> None:
    """Run one JavaScript probe, store its parsed result, then continue."""
    stage_log(run.report_path, f"probe: {key}")
    view = run.editor.window.web_view
    if view is None:
        fail(run, f"the {key} probe found no embedded view")
        return

    def handle_result(raw: object) -> None:
        def handle() -> None:
            parsed = parse_probe(raw)
            stage_log(run.report_path, f"probe: {key} result {bool(parsed)}")
            if not parsed:
                fail(run, f"the {key} probe returned no usable result")
                return
            run.results[key] = parsed
            then()

        failed_guard(run, f"the {key} probe", handle)

    view.page().runJavaScript(script, handle_result)


def _open_transition_project(run: SelfCheckRun, index: int) -> None:
    """Open one transition project through the real Open handler.

    The native file chooser is bypassed by pointing the window's documented
    automation seam at a controlled path; everything after that - the loader
    boundary, the workspace activation and the reload of the *existing* webview -
    is the production ``File -> Open…`` implementation.
    """
    if index >= len(run.transition_projects):
        fail(run, f"the transition scenario has no project at index {index}")
        return
    project = run.transition_projects[index]
    stage_log(run.report_path, f"transition: open project {index} ({project.name})")
    run.editor.window.open_path_provider = lambda _directory, _path=project: str(_path)
    run.editor.open_from_dialog()


def _transition_after_launch(run: SelfCheckRun) -> None:
    """Capture the empty launch, then open project A."""
    run.results["identity_launch"] = _session_identity(run.editor)
    _probe_script(
        run, EMPTY_WORKSPACE_PROBE_JS, "workspace", lambda: _open_transition_project(run, 0)
    )


def _transition_after_project_a(run: SelfCheckRun) -> None:
    """Probe project A's rendered canvas (which activates its probe step)."""
    run.results["identity_after_a"] = _session_identity(run.editor)
    _probe_script(
        run,
        canvas_probe_js(PROBE_STEP_ID),
        "canvas_a",
        lambda: settle(POST_SELECTION_SETTLE_MS, lambda: _transition_after_a_inspector(run)),
    )


def _transition_after_a_inspector(run: SelfCheckRun) -> None:
    """Read project A's Inspector, then replace it with project B."""
    _probe_script(run, INSPECTOR_PROBE_JS, "inspector_a", lambda: _open_transition_project(run, 1))


def _transition_after_project_b(run: SelfCheckRun) -> None:
    """Read project B's Inspector *before* selecting anything.

    It must show no selection, which is how the selection made in project A is
    proven not to survive the replacement.
    """
    _probe_script(
        run,
        INSPECTOR_PROBE_JS,
        "inspector_b_unselected",
        lambda: _probe_script(
            run,
            canvas_probe_js(TRANSITION_PROJECT_B_PROBE_STEP_ID),
            "canvas_b",
            lambda: settle(POST_SELECTION_SETTLE_MS, lambda: _transition_after_b_inspector(run)),
        ),
    )


def _transition_after_b_inspector(run: SelfCheckRun) -> None:
    """Read project B's Inspector, then attempt a failing open."""
    _probe_script(run, INSPECTOR_PROBE_JS, "inspector_b", lambda: _transition_fail_open(run))


def _transition_fail_open(run: SelfCheckRun) -> None:
    """Attempt an invalid open and prove project B stays active.

    The failing load is reported through the window's one user-facing error
    mechanism (the modal message box, replaced here by a recorder). Because the
    load fails *before* the workspace is touched, the same session - displaying
    project B - must remain rendered.
    """
    run.results["identity_after_b"] = _session_identity(run.editor)
    invalid = run.transition_invalid_project
    if invalid is None:
        fail(run, "the transition scenario has no invalid project")
        return
    window = run.editor.window
    recorded: list[str] = []
    window.error_reporter = recorded.append
    window.open_path_provider = lambda _directory: str(invalid)
    stage_log(run.report_path, "transition: open an invalid project")
    run.editor.open_from_dialog()
    run.results["error_message"] = recorded[-1] if recorded else None
    run.results["error_reported"] = bool(recorded)
    run.results["identity_after_failed"] = _session_identity(run.editor)
    _probe_script(
        run,
        canvas_probe_js(TRANSITION_PROJECT_B_PROBE_STEP_ID),
        "canvas_b_after_failed",
        lambda: settle(POST_SELECTION_SETTLE_MS, lambda: _transition_after_failed_inspector(run)),
    )


def _transition_after_failed_inspector(run: SelfCheckRun) -> None:
    """Read the still-active project B Inspector, then complete the run."""
    _probe_script(run, INSPECTOR_PROBE_JS, "inspector_b_after_failed", lambda: _complete(run))


def _complete(run: SelfCheckRun) -> None:
    """Complete the run through the finalizer the self-check installed."""
    on_complete = run.on_complete
    if on_complete is None:
        fail(run, "the self-check installed no completion step")
        return
    on_complete()


def on_loaded(run: SelfCheckRun, ok: bool) -> None:
    """React to one page load of the replacement lifecycle.

    Load 1 is the initial empty launch, load 2 follows opening project A and load 3
    follows replacing it with project B. The failing open never reaches the page,
    so there is no fourth load - an extra load is itself a failure.
    """
    if not ok:
        fail(run, "the embedded page did not finish loading")
        return
    load = run.loads
    if load == 1:
        settle(POST_LOAD_SETTLE_MS, lambda: _transition_after_launch(run))
    elif load == 2:
        settle(POST_LOAD_SETTLE_MS, lambda: _transition_after_project_a(run))
    elif load == 3:
        settle(POST_LOAD_SETTLE_MS, lambda: _transition_after_project_b(run))
    else:
        fail(run, f"the transition scenario saw an unexpected extra page load ({load})")


def _no_additional_serving_socket(identities: dict[str, dict[str, object]]) -> bool:
    """Whether the process's listening sockets stayed exactly as they started.

    Reads the *measured* listening-port sets from every identity snapshot: they
    must be known, identical, and contain the owned server's port, so opening or
    replacing a project cannot have left an extra serving socket behind. Requiring
    the *same* set (rather than an absolute count) stays honest on a host that
    already has an unrelated listener while still failing on any port the session's
    document changes added.
    """
    snapshots = list(identities.values())
    listener_sets = [snapshot.get("listeningPorts") for snapshot in snapshots]
    if not listener_sets or any(value is None for value in listener_sets):
        return False
    normalized: list[tuple[int, ...]] = []
    for value in listener_sets:
        if not isinstance(value, list):
            return False
        normalized.append(tuple(cast("list[int]", value)))
    if len(set(normalized)) != 1:
        return False
    ports = set(normalized[0])
    server_ports = {snapshot.get("port") for snapshot in snapshots}
    if not ports or None in server_ports:
        return False
    return all(port in ports for port in server_ports)


def _content_checks(run: SelfCheckRun) -> dict[str, object]:
    """The rendered-content checks for the replacement lifecycle."""
    workspace = as_mapping(run.results.get("workspace"))
    canvas_a = as_mapping(run.results.get("canvas_a"))
    inspector_a = as_mapping(run.results.get("inspector_a"))
    inspector_b_unselected = as_mapping(run.results.get("inspector_b_unselected"))
    canvas_b = as_mapping(run.results.get("canvas_b"))
    inspector_b = as_mapping(run.results.get("inspector_b"))
    canvas_b_after = as_mapping(run.results.get("canvas_b_after_failed"))
    inspector_b_after = as_mapping(run.results.get("inspector_b_after_failed"))
    error_message = run.results.get("error_message")
    fields_a = as_mapping(inspector_a.get("fields"))
    fields_b = as_mapping(inspector_b.get("fields"))
    fields_b_after = as_mapping(inspector_b_after.get("fields"))
    return {
        "emptyAtLaunch": (
            workspace.get("processSteps") == 0
            and workspace.get("statusText") == EMPTY_WORKSPACE_STATUS_TEXT
            and workspace.get("emptyWorkspaceNotice") is True
            and workspace.get("projectionError") is None
            and workspace.get("devEntryPoint") is False
        ),
        "projectARendered": (
            canvas_a.get("processSteps") == EXPECTED_STEPS
            and canvas_a.get("processStreams") == EXPECTED_STREAMS
            and canvas_a.get("probeNodeFound") is True
        ),
        "projectASelected": inspector_a.get("heading") == PROBE_STEP_ID
        and fields_a.get("Function") == "pumping",
        "projectBReplacedA": (
            canvas_b.get("processSteps") == TRANSITION_PROJECT_B_EXPECTED_STEPS
            and canvas_b.get("processStreams") == TRANSITION_PROJECT_B_EXPECTED_STREAMS
            and canvas_b.get("probeNodeFound") is True
        ),
        "projectBSelected": inspector_b.get("heading") == TRANSITION_PROJECT_B_PROBE_STEP_ID
        and fields_b.get("Function") == TRANSITION_PROJECT_B_PROBE_FUNCTION,
        "selectionResetOnReplacement": inspector_b_unselected.get("heading") == "Inspector",
        "failedLoadKeptProjectB": (
            canvas_b_after.get("processSteps") == TRANSITION_PROJECT_B_EXPECTED_STEPS
            and inspector_b_after.get("heading") == TRANSITION_PROJECT_B_PROBE_STEP_ID
            and fields_b_after.get("Function") == TRANSITION_PROJECT_B_PROBE_FUNCTION
        ),
        "errorReported": isinstance(error_message, str) and bool(error_message),
        "productionSpa": canvas_a.get("devEntryPoint") is False
        and canvas_b.get("devEntryPoint") is False,
    }


def _session_checks(identities: dict[str, dict[str, object]]) -> dict[str, object]:
    """The measured session-identity checks for the replacement lifecycle."""

    def stable(field: str) -> bool:
        values = [snapshot.get(field) for snapshot in identities.values()]
        return None not in values and len(set(values)) == 1

    return {
        "windowUnchanged": stable("windowId"),
        "viewUnchanged": stable("viewId"),
        "serverUnchanged": stable("serverId"),
        "originUnchanged": stable("origin"),
        "portUnchanged": stable("port"),
        "singleWindow": all(
            snapshot.get("mainWindowCount") == 1 for snapshot in identities.values()
        ),
        "singleView": all(snapshot.get("webViewCount") == 1 for snapshot in identities.values()),
        "noAdditionalServingSocket": _no_additional_serving_socket(identities),
    }


def verdict(run: SelfCheckRun) -> tuple[bool, dict[str, object]]:
    """Decide whether the real replacement lifecycle matched the expectations.

    Every value is read from the real rendered page (canvas/Inspector probes) or
    measured from the live session objects, so a pass is evidence of the actual
    long-lived desktop session rather than of isolated unit behaviour.
    """
    identities: dict[str, dict[str, object]] = {
        name: as_mapping(run.results.get(f"identity_{name}"))
        for name in ("launch", "after_a", "after_b", "after_failed")
    }
    checks = _content_checks(run)
    checks.update(_session_checks(identities))
    passed = all(value is True for value in checks.values())
    extra: dict[str, object] = {
        "verdict": "pass" if passed else "fail",
        "checks": checks,
        "transition": {
            "launch": as_mapping(run.results.get("workspace")),
            "projectA": {
                "canvas": as_mapping(run.results.get("canvas_a")),
                "inspector": as_mapping(run.results.get("inspector_a")),
            },
            "projectB": {
                "canvas": as_mapping(run.results.get("canvas_b")),
                "inspectorUnselected": as_mapping(run.results.get("inspector_b_unselected")),
                "inspector": as_mapping(run.results.get("inspector_b")),
            },
            "failedOpen": {
                "error": run.results.get("error_message"),
                "canvas": as_mapping(run.results.get("canvas_b_after_failed")),
                "inspector": as_mapping(run.results.get("inspector_b_after_failed")),
            },
        },
        "session": identities,
    }
    return passed, extra
