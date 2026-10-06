"""Lifecycle tests for the owned local editor server (Issues #79, #93).

The native desktop host starts the loopback server, shows the window, and must
stop the server deterministically when the window closes. These tests exercise
that owned lifecycle directly, without a browser and without a GUI toolkit:
the server answers real HTTP on loopback, and after ``stop()`` the socket is
closed and the serving thread is gone.
"""

from __future__ import annotations

import json
import socket
import threading
from collections.abc import Sequence
from pathlib import Path
from typing import cast
from urllib.request import urlopen

import pytest

from deepplant.editor.api import EditorServer
from deepplant.editor.application import (
    EditorWorkspace,
    create_empty_workspace,
    load_editor_application,
)
from deepplant.editor.desktop import (
    SMOKE_EXPECTED_STEPS,
    SMOKE_EXPECTED_STREAMS,
    TRANSITION_PROJECT_B_EXPECTED_STEPS,
    TRANSITION_PROJECT_B_EXPECTED_STREAMS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REALISTIC_EXAMPLE = REPO_ROOT / "examples" / "realistic-process-fragment" / "plant.yaml"
VESSEL_OVERRIDES = {"PS-vessel": "vessel"}
#: The canonical self-contained fixture and a distinguishable second model. Since
#: Issue #97 a document change is a *workspace state change*, so the two are used
#: below to prove one long-lived server serves both (no second server is created).
SMOKE_EXAMPLE = REPO_ROOT / "examples" / "process-graph" / "plant.yaml"
REPLACEMENT_EXAMPLE = REPO_ROOT / "examples" / "process-graph" / "replacement.yaml"


@pytest.fixture()
def workspace(tmp_path: Path) -> EditorWorkspace:
    assets = tmp_path / "dist"
    assets.mkdir()
    (assets / "index.html").write_text("<!doctype html><p>DeepPlant</p>", encoding="utf-8")
    application = load_editor_application(
        REALISTIC_EXAMPLE,
        symbol_role_overrides=VESSEL_OVERRIDES,
        assets_dir=assets,
    )
    editor_workspace = EditorWorkspace(assets_dir=assets)
    editor_workspace.activate(application)
    return editor_workspace


def _get_json(url: str) -> tuple[int, dict[str, object]]:
    with urlopen(url, timeout=15) as response:  # noqa: S310 - loopback only
        return response.status, json.loads(response.read().decode("utf-8"))


def _projection_of(payload: dict[str, object]) -> dict[str, object]:
    projection = payload["projection"]
    assert isinstance(projection, dict)
    return cast("dict[str, object]", projection)


def _sequence(value: object) -> Sequence[object]:
    assert isinstance(value, list)
    return cast("Sequence[object]", value)


def _document_name(payload: dict[str, object]) -> str:
    """Return ``workspace.document.name`` from a projection envelope."""
    document = _mapping(_mapping(payload["workspace"])["document"])
    name = document["name"]
    assert isinstance(name, str)
    return name


def _mapping(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast("dict[str, object]", value)


def _port_accepts(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except OSError:
        return False


def test_server_binds_loopback_and_serves_the_editor(workspace: EditorWorkspace) -> None:
    server = EditorServer(workspace, port=0)
    try:
        assert server.host == "127.0.0.1"
        assert server.port > 0
        assert server.running is False

        server.start()

        assert server.running is True
        status, payload = _get_json(f"{server.base_url}api/projection")
        assert status == 200
        assert payload["workspace"] == {
            "state": "loaded",
            "document": {
                "name": REALISTIC_EXAMPLE.name,
                "plant_id": "demo",
                "plant_name": "Realistic Process Fragment",
            },
        }
        assert payload["validation"] == {"valid": True, "message": "Valid"}
        steps = _sequence(_projection_of(payload)["steps"])
        assert len(steps) == 7
    finally:
        assert server.stop() is True


def test_server_serves_an_empty_workspace(tmp_path: Path) -> None:
    """An editor session with no project open is a first-class servable state."""
    assets = tmp_path / "dist"
    assets.mkdir()
    (assets / "index.html").write_text("<!doctype html><p>DeepPlant</p>", encoding="utf-8")
    server = EditorServer(create_empty_workspace(assets), port=0)
    try:
        server.start()
        assert server.running is True

        status, payload = _get_json(f"{server.base_url}api/projection")
        assert status == 200
        assert payload["workspace"] == {"state": "empty", "document": None}
        assert payload["validation"] is None
        assert payload["projection"] is None
        assert "error" not in payload
    finally:
        assert server.stop() is True


def test_stop_releases_the_listening_socket(workspace: EditorWorkspace) -> None:
    server = EditorServer(workspace, port=0)
    server.start()
    port = server.port
    assert _port_accepts("127.0.0.1", port) is True

    assert server.stop() is True

    assert server.running is False
    assert _port_accepts("127.0.0.1", port) is False


def test_stop_is_idempotent_and_safe_before_start(workspace: EditorWorkspace) -> None:
    never_started = EditorServer(workspace, port=0)
    assert never_started.stop() is True
    assert never_started.stop() is True

    started = EditorServer(workspace, port=0)
    started.start()
    assert started.stop() is True
    assert started.stop() is True


def test_start_refuses_a_second_time(workspace: EditorWorkspace) -> None:
    server = EditorServer(workspace, port=0)
    server.start()
    try:
        with pytest.raises(RuntimeError):
            server.start()
    finally:
        server.stop()


def test_stopping_a_server_releases_its_port(workspace: EditorWorkspace) -> None:
    """Generic ``EditorServer`` lifecycle: a stopped server frees its port.

    This is deliberately *not* a statement about opening another project. Since
    Issue #97 a document change reuses the one long-lived server (see
    ``test_changing_the_active_document_reuses_the_same_server``); this test only
    pins the owned-server primitive: after ``stop()`` the bound port no longer
    accepts connections, while an unrelated running server still does.
    """
    first = EditorServer(workspace, port=0)
    first.start()
    first_port = first.port
    second = EditorServer(workspace, port=0)
    second.start()
    try:
        assert second.port != first_port
        assert first.stop() is True
        assert _port_accepts("127.0.0.1", first_port) is False
        assert _port_accepts("127.0.0.1", second.port) is True
    finally:
        second.stop()


def test_changing_the_active_document_reuses_the_same_server(tmp_path: Path) -> None:
    """Issue #97: opening another project must not create a second server.

    The session owns one ``EditorServer`` bound to the *workspace*, so activating a
    different document is a state change: the same object, bound port and origin
    keep serving, and ``/api/projection`` reports the new document. This is the
    behaviour the previous ``test_replacing_a_server_releases_the_previous_port``
    misdescribed as creating a second server.
    """
    assets = tmp_path / "dist"
    assets.mkdir()
    (assets / "index.html").write_text("<!doctype html><p>DeepPlant</p>", encoding="utf-8")
    workspace = EditorWorkspace(assets_dir=assets)
    workspace.activate(load_editor_application(SMOKE_EXAMPLE, assets_dir=assets))

    server = EditorServer(workspace, port=0)
    server.start()
    try:
        port = server.port
        base_url = server.base_url

        status, payload = _get_json(f"{base_url}api/projection")
        assert status == 200
        assert _document_name(payload) == SMOKE_EXAMPLE.name
        assert len(_sequence(_projection_of(payload)["steps"])) == SMOKE_EXPECTED_STEPS
        assert len(_sequence(_projection_of(payload)["streams"])) == SMOKE_EXPECTED_STREAMS

        # Replace the active document: the server, its port and its origin are the
        # same owned session, and the projection now describes the new document.
        workspace.activate(load_editor_application(REPLACEMENT_EXAMPLE, assets_dir=assets))

        assert server.port == port
        assert server.base_url == base_url
        status, payload = _get_json(f"{base_url}api/projection")
        assert status == 200
        assert _document_name(payload) == REPLACEMENT_EXAMPLE.name
        assert (
            len(_sequence(_projection_of(payload)["steps"])) == TRANSITION_PROJECT_B_EXPECTED_STEPS
        )
        assert (
            len(_sequence(_projection_of(payload)["streams"]))
            == TRANSITION_PROJECT_B_EXPECTED_STREAMS
        )
        assert _port_accepts("127.0.0.1", port) is True
    finally:
        assert server.stop() is True
    assert _port_accepts("127.0.0.1", port) is False


class _NeverEndingThread(threading.Thread):
    """A serving-thread stand-in that terminates only when released (Issue #93).

    The real serving thread runs Uvicorn and cannot be made to hang on demand, so
    the timeout/retained-state contract is exercised with a controlled thread
    instead of a real multi-second sleep.
    """

    def __init__(self) -> None:
        super().__init__(name="test-editor-server", daemon=True)
        self._released = threading.Event()
        self.joins = 0

    def release(self) -> None:
        """Allow the stand-in to terminate, as a real server eventually would."""
        self._released.set()

    def run(self) -> None:
        # Never started in these tests; present so this really is a Thread.
        self._released.wait()

    def join(self, timeout: float | None = None) -> None:
        self.joins += 1
        self._released.wait(timeout)

    def is_alive(self) -> bool:
        return not self._released.is_set()


class _ControllableServer(EditorServer):
    """An EditorServer whose serving thread is a controlled stand-in (Issue #93)."""

    def __init__(self, workspace: EditorWorkspace) -> None:
        super().__init__(workspace, port=0)
        self.serving = _NeverEndingThread()
        self._thread = self.serving


def test_stop_is_truthful_while_the_owned_thread_is_still_alive(
    workspace: EditorWorkspace,
) -> None:
    """A timed-out stop must not erase a still-live owned server (Issue #93).

    The previous implementation cleared the thread reference even when the thread
    was still alive, so a caller could infer "stopped" from a cleared reference
    instead of from the actual thread state. The reference is now retained, so
    ``running`` stays truthful and a later ``stop()`` can still join it.
    """
    server = _ControllableServer(workspace)
    try:
        assert server.running is True
        assert server.stop(timeout=0.0) is False
        assert server.running is True
        assert server.stop_requested is True
        # A second bounded stop re-joins the same owned thread, not a forgotten one.
        assert server.stop(timeout=0.0) is False
        assert server.serving.joins == 2
    finally:
        server.serving.release()
        assert server.stop(timeout=1.0) is True
    assert server.running is False


def test_a_timed_out_stop_completes_once_the_owned_thread_ends(
    workspace: EditorWorkspace,
) -> None:
    """An earlier timeout must not prevent the server from eventually stopping."""
    server = _ControllableServer(workspace)
    assert server.stop(timeout=0.0) is False
    assert server.running is True

    server.serving.release()

    assert server.stop(timeout=1.0) is True
    assert server.running is False
    assert _port_accepts("127.0.0.1", server.port) is False
