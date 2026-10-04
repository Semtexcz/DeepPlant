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
from collections.abc import Sequence
from pathlib import Path
from typing import cast
from urllib.request import urlopen

import pytest

from deepplant.editor.api import EditorServer
from deepplant.editor.application import EditorApplication, load_editor_application

REPO_ROOT = Path(__file__).resolve().parents[1]
REALISTIC_EXAMPLE = REPO_ROOT / "examples" / "realistic-process-fragment" / "plant.yaml"
VESSEL_OVERRIDES = {"PS-vessel": "vessel"}


@pytest.fixture()
def application(tmp_path: Path) -> EditorApplication:
    assets = tmp_path / "dist"
    assets.mkdir()
    (assets / "index.html").write_text("<!doctype html><p>DeepPlant</p>", encoding="utf-8")
    return load_editor_application(
        REALISTIC_EXAMPLE,
        symbol_role_overrides=VESSEL_OVERRIDES,
        assets_dir=assets,
    )


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


def _port_accepts(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except OSError:
        return False


def test_server_binds_loopback_and_serves_the_editor(application: EditorApplication) -> None:
    server = EditorServer(application, port=0)
    try:
        assert server.host == "127.0.0.1"
        assert server.port > 0
        assert server.running is False

        server.start()

        assert server.running is True
        status, payload = _get_json(f"{server.base_url}api/projection")
        assert status == 200
        assert payload["validation"] == {"valid": True, "message": "Valid"}
        steps = _sequence(_projection_of(payload)["steps"])
        assert len(steps) == 7
    finally:
        assert server.stop() is True


def test_stop_releases_the_listening_socket(application: EditorApplication) -> None:
    server = EditorServer(application, port=0)
    server.start()
    port = server.port
    assert _port_accepts("127.0.0.1", port) is True

    assert server.stop() is True

    assert server.running is False
    assert _port_accepts("127.0.0.1", port) is False


def test_stop_is_idempotent_and_safe_before_start(application: EditorApplication) -> None:
    never_started = EditorServer(application, port=0)
    assert never_started.stop() is True
    assert never_started.stop() is True

    started = EditorServer(application, port=0)
    started.start()
    assert started.stop() is True
    assert started.stop() is True


def test_start_refuses_a_second_time(application: EditorApplication) -> None:
    server = EditorServer(application, port=0)
    server.start()
    try:
        with pytest.raises(RuntimeError):
            server.start()
    finally:
        server.stop()


def test_replacing_a_server_releases_the_previous_port(application: EditorApplication) -> None:
    """Opening another model in the same window must not leak a socket."""
    first = EditorServer(application, port=0)
    first.start()
    first_port = first.port
    second = EditorServer(application, port=0)
    second.start()
    try:
        assert second.port != first_port
        assert first.stop() is True
        assert _port_accepts("127.0.0.1", first_port) is False
        assert _port_accepts("127.0.0.1", second.port) is True
    finally:
        second.stop()
