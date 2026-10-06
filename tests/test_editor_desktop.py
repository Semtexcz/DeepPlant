"""Focused tests for the standalone desktop host boundary (Issue #93).

These exercise the Qt-free part of the host: the embedded-navigation policy, the
command-line wiring, the initial-project load, and the ``--self-check`` hand-off.
The Qt window itself is not constructed here; it is exercised for real by the
native packaging jobs, which are the only environments that install the
``desktop`` extra (see docs/dev/workflow/packaging.md).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from deepplant.editor.application import EditorApplication
from deepplant.editor.desktop import (
    DesktopHostError,
    editor_origin,
    initial_open_directory,
    is_allowed_navigation,
    run_desktop_editor,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REALISTIC_EXAMPLE = REPO_ROOT / "examples" / "realistic-process-fragment" / "plant.yaml"
#: The canonical packaged smoke fixture (Issue #98): self-contained, so the
#: ordinary path renders it with no presentation override.
SMOKE_EXAMPLE = REPO_ROOT / "examples" / "process-graph" / "plant.yaml"


@pytest.fixture()
def assets_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "dist"
    directory.mkdir()
    (directory / "index.html").write_text("<!doctype html><p>DeepPlant</p>", encoding="utf-8")
    return directory


class _RecordingHost:
    """Stand-in for the Qt host: records exactly what the CLI handed it."""

    def __init__(self, exit_code: int = 0) -> None:
        self.calls: list[dict[str, object]] = []
        self._exit_code = exit_code

    def __call__(self, **kwargs: object) -> int:
        self.calls.append(kwargs)
        return self._exit_code


ORIGIN = editor_origin("127.0.0.1", 51843)


def test_navigation_policy_is_the_exact_editor_origin() -> None:
    """Only the active EditorServer origin, plus internal schemes, is allowed."""
    assert is_allowed_navigation(f"{ORIGIN}/", allowed_origin=ORIGIN) is True
    assert is_allowed_navigation(f"{ORIGIN}/assets/index-abc.js", allowed_origin=ORIGIN) is True

    assert is_allowed_navigation("about:blank", allowed_origin=ORIGIN) is True
    assert is_allowed_navigation("data:text/plain,hello", allowed_origin=ORIGIN) is True
    assert is_allowed_navigation(f"blob:{ORIGIN}/abc", allowed_origin=ORIGIN) is True


def test_navigation_policy_rejects_any_other_loopback_origin() -> None:
    """A different port or a different loopback host name is a different origin."""
    assert is_allowed_navigation("http://127.0.0.1:8080/", allowed_origin=ORIGIN) is False
    assert is_allowed_navigation("http://localhost:51843/", allowed_origin=ORIGIN) is False
    assert is_allowed_navigation("http://[::1]:51843/", allowed_origin=ORIGIN) is False


def test_navigation_policy_rejects_external_and_file_urls() -> None:
    assert is_allowed_navigation("https://example.com/", allowed_origin=ORIGIN) is False
    assert is_allowed_navigation("http://192.168.0.10:51843/", allowed_origin=ORIGIN) is False
    assert is_allowed_navigation("file:///etc/passwd", allowed_origin=ORIGIN) is False


def test_navigation_policy_allows_only_internal_schemes_without_a_server() -> None:
    """With no active server even the loopback origin is not the current one."""
    assert is_allowed_navigation("about:blank", allowed_origin=None) is True
    assert is_allowed_navigation(f"{ORIGIN}/", allowed_origin=None) is False


def test_navigation_policy_follows_a_replaced_server_origin() -> None:
    """Opening another model moves the permitted origin to the new port."""
    first = editor_origin("127.0.0.1", 51843)
    second = editor_origin("127.0.0.1", 51999)
    assert is_allowed_navigation(f"{first}/", allowed_origin=first) is True
    assert is_allowed_navigation(f"{first}/", allowed_origin=second) is False
    assert is_allowed_navigation(f"{second}/", allowed_origin=second) is True


def test_open_directory_falls_back_when_the_platform_reports_no_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A missing home directory must not stop the application from starting.

    The packaged Windows desktop smoke found this: in a session where the
    platform cannot report a home directory, ``Path.home()`` raises
    ``RuntimeError`` and the Editor failed at startup. The Open dialog now starts
    from the working directory instead.
    """

    def no_home() -> Path:
        raise RuntimeError("Could not determine home directory.")

    monkeypatch.setattr(Path, "home", staticmethod(no_home))
    monkeypatch.chdir(tmp_path)

    assert initial_open_directory() == str(tmp_path)


def test_open_directory_never_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """With neither a home nor a working directory, Qt's own default is used."""

    def no_home() -> Path:
        raise RuntimeError("Could not determine home directory.")

    def no_cwd() -> Path:
        raise OSError("no working directory")

    monkeypatch.setattr(Path, "home", staticmethod(no_home))
    monkeypatch.setattr(Path, "cwd", staticmethod(no_cwd))

    assert initial_open_directory() == ""


def test_no_path_starts_the_window_without_a_project(assets_dir: Path) -> None:
    """Launching without an argument is the primary workflow, never an error."""
    host = _RecordingHost()

    code = run_desktop_editor(None, assets_dir=assets_dir, host_runner=host)

    assert code == 0
    assert len(host.calls) == 1
    assert host.calls[0]["initial_application"] is None
    assert callable(host.calls[0]["loader"])


def test_optional_path_loads_the_model_into_the_window(assets_dir: Path) -> None:
    host = _RecordingHost()

    code = run_desktop_editor(
        REALISTIC_EXAMPLE,
        symbol_role_entries=["PS-vessel=vessel"],
        assets_dir=assets_dir,
        host_runner=host,
    )

    assert code == 0
    application = host.calls[0]["initial_application"]
    assert isinstance(application, EditorApplication)
    assert application.project_path == REALISTIC_EXAMPLE
    assert application.symbol_role_overrides == {"PS-vessel": "vessel"}


def test_optional_path_loads_the_self_contained_smoke_fixture(assets_dir: Path) -> None:
    """Issue #98: the canonical smoke fixture opens through the ordinary path.

    A path argument is loaded through the same boundary a `File -> Open…`
    selection uses, and the self-contained fixture needs no presentation override.
    """
    host = _RecordingHost()

    code = run_desktop_editor(SMOKE_EXAMPLE, assets_dir=assets_dir, host_runner=host)

    assert code == 0
    application = host.calls[0]["initial_application"]
    assert isinstance(application, EditorApplication)
    assert application.project_path == SMOKE_EXAMPLE
    assert not application.symbol_role_overrides
    assert application.projection_view().projectable is True


def test_an_unloadable_initial_model_is_a_message_not_a_window(assets_dir: Path) -> None:
    host = _RecordingHost()

    with pytest.raises(DesktopHostError):
        run_desktop_editor(
            REPO_ROOT / "examples" / "does-not-exist.yaml",
            assets_dir=assets_dir,
            host_runner=host,
        )

    assert host.calls == []


def test_an_invalid_symbol_role_is_reported_before_the_window(assets_dir: Path) -> None:
    host = _RecordingHost()

    with pytest.raises(DesktopHostError):
        run_desktop_editor(
            None,
            symbol_role_entries=["not-a-pair"],
            assets_dir=assets_dir,
            host_runner=host,
        )

    assert host.calls == []


def test_self_check_requires_a_report_path(assets_dir: Path) -> None:
    with pytest.raises(DesktopHostError):
        run_desktop_editor(
            None,
            self_check=True,
            assets_dir=assets_dir,
            host_runner=_RecordingHost(),
        )


def test_self_check_is_forwarded_to_the_native_host(assets_dir: Path, tmp_path: Path) -> None:
    host = _RecordingHost(exit_code=1)
    report = tmp_path / "desktop-report.json"

    code = run_desktop_editor(
        REALISTIC_EXAMPLE,
        symbol_role_entries=["PS-vessel=vessel"],
        assets_dir=assets_dir,
        self_check=True,
        report_path=report,
        host_runner=host,
    )

    assert code == 1
    assert host.calls[0]["self_check"] is True
    assert host.calls[0]["report_path"] == report


def test_the_loader_is_bound_to_the_configured_assets(assets_dir: Path, tmp_path: Path) -> None:
    """The Open dialog's loader uses the same boundary as the initial load."""
    host = _RecordingHost()
    run_desktop_editor(None, assets_dir=assets_dir, host_runner=host)
    loader = host.calls[0]["loader"]
    assert callable(loader)

    other = tmp_path / "copy.yaml"
    other.write_text(REALISTIC_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")

    application = loader(other)

    assert isinstance(application, EditorApplication)
    assert application.assets_dir == assets_dir
