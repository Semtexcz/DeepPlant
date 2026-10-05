"""Evidence for the Linux runtime baseline and dependency audit (Issue #93 review).

The audit is the Linux artifact's fail-closed contract: it must inspect the
launcher itself as well as the Qt WebEngine binaries, and it must refuse an
artifact whose dependencies differ from the repository-owned baseline. These
tests exercise the parser, the classifier, the baseline comparison, and the whole
audit with synthetic ``ldd`` output, so they never depend on the developer
machine's real dynamic linking. The native Linux packaging job remains the system
evidence.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from collections.abc import Sequence
from pathlib import Path

import pytest

from tools import package_editor as pe

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "packaging" / "linux-runtime-baseline.toml"

SONAME = re.compile(r"^lib[a-zA-Z0-9_\-.+]*\.so(\.[0-9]+)*$")


def test_baseline_is_reviewable_and_reasoned() -> None:
    document = tomllib.loads(BASELINE.read_text(encoding="utf-8"))
    assert document["schema_version"] == 1
    assert document["baseline_image"] == "ubuntu-24.04"
    host = document["host"]
    assert len(host) >= 40, "the baseline must be the measured host set, not a stub"
    for name, reason in host.items():
        assert SONAME.match(name), f"baseline entry must be a SONAME: {name}"
        assert not name.startswith("/"), f"baseline must not pin absolute paths: {name}"
        assert isinstance(reason, str) and reason.strip()
    # The libraries a Qt/Chromium desktop application cannot run without.
    for required in ("libc.so.6", "libm.so.6", "libX11.so.6", "libnss3.so"):
        assert required in host


def test_baseline_loader_rejects_a_missing_or_malformed_baseline(tmp_path: Path) -> None:
    with pytest.raises(pe.PackagingError):
        pe.load_linux_runtime_baseline(tmp_path / "absent.toml")
    malformed = tmp_path / "baseline.toml"
    malformed.write_text('schema_version = 2\n[host]\n"libc.so.6" = "reason"\n', encoding="utf-8")
    with pytest.raises(pe.PackagingError):
        pe.load_linux_runtime_baseline(malformed)
    no_reason = tmp_path / "no-reason.toml"
    no_reason.write_text('schema_version = 1\n[host]\n"libc.so.6" = ""\n', encoding="utf-8")
    with pytest.raises(pe.PackagingError):
        pe.load_linux_runtime_baseline(no_reason)


def test_audited_targets_include_the_application_launcher() -> None:
    labels = [label for label, _form in pe.LINUX_AUDIT_TARGETS]
    assert labels == [
        "deepplant-editor",
        "QtWebEngineProcess",
        "libQt6WebEngineCore.so",
        "libqxcb.so",
    ]


def test_parse_ldd_output_handles_resolution_and_not_found() -> None:
    output = "\n".join(
        [
            "\tlinux-vdso.so.1 (0x00007ffd)",
            "\tlibc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f5a)",
            "\tlibmissing.so.9 => not found",
            "/lib64/ld-linux-x86-64.so.2 (0x00007f5b)",
        ]
    )
    assert pe.parse_ldd_output(output) == [
        ("libc.so.6", "/lib/x86_64-linux-gnu/libc.so.6"),
        ("libmissing.so.9", None),
    ]


def test_classify_linux_dependency_distinguishes_every_case(tmp_path: Path) -> None:
    app = tmp_path / "install" / "deepplant-editor"
    app.mkdir(parents=True)
    bundled = app / "_internal" / "libQt6Core.so.6"
    bundled.parent.mkdir(parents=True, exist_ok=True)
    bundled.write_text("x", encoding="utf-8")
    repo = tmp_path / "repo"
    repo.mkdir()
    checkout = repo / "src" / "libleaked.so.1"
    checkout.parent.mkdir(parents=True, exist_ok=True)
    checkout.write_text("x", encoding="utf-8")
    prefix = tmp_path / "uv-env"
    prefix.mkdir()
    venv = prefix / "lib" / "python3.12" / "site-packages" / "libpythonish.so.1"
    venv.parent.mkdir(parents=True, exist_ok=True)
    venv.write_text("x", encoding="utf-8")

    assert pe.classify_linux_dependency(bundled, app, repo_root=repo, python_prefix=prefix) == (
        "bundled"
    )
    assert pe.classify_linux_dependency(venv, app, repo_root=repo, python_prefix=prefix) == "uv-env"
    assert pe.classify_linux_dependency(checkout, app, repo_root=repo, python_prefix=prefix) == (
        "checkout"
    )
    assert pe.classify_linux_dependency(Path("/usr/lib/libX11.so.6"), app, repo_root=repo) == "host"


def test_check_host_baseline_reports_unexpected_and_stale() -> None:
    unexpected, stale = pe.check_host_baseline(
        {"libc.so.6", "libnew.so.1"}, {"libc.so.6", "libold"}
    )
    assert unexpected == ["libnew.so.1"]
    assert stale == ["libold"]


def _app_tree(tmp_path: Path, *, launcher: bool = True) -> Path:
    """Create the minimum packaged layout the Linux audit inspects."""
    app = tmp_path / "install" / "deepplant-editor"
    internal = app / "_internal"
    internal.mkdir(parents=True)
    if launcher:
        (app / "deepplant-editor").write_text("x", encoding="utf-8")
    (internal / "QtWebEngineProcess").write_text("x", encoding="utf-8")
    (internal / "libQt6WebEngineCore.so.6").write_text("x", encoding="utf-8")
    (internal / "libqxcb.so").write_text("x", encoding="utf-8")
    return app


def _ldd_lines(app: Path, host_libraries: list[str], *, extra: list[str] | None = None) -> str:
    """Return synthetic ``ldd`` output: one bundled Qt library plus host libraries."""
    lines = [f"\tlibQt6Core.so.6 => {app / '_internal' / 'libQt6Core.so.6'} (0x00007f)"]
    (app / "_internal" / "libQt6Core.so.6").write_text("x", encoding="utf-8")
    lines += [f"\t{name} => /usr/lib/x86_64-linux-gnu/{name} (0x00007f)" for name in host_libraries]
    lines += extra or []
    return "\n".join(lines)


def _audit(
    monkeypatch: pytest.MonkeyPatch,
    app: Path,
    ldd_text: str,
    baseline: dict[str, str] | None = None,
) -> dict[str, object]:
    """Run the audit with synthetic ldd output and a small deterministic baseline."""
    declared = baseline if baseline is not None else {"libc.so.6": "glibc", "libm.so.6": "libm"}

    def _which(_name: str) -> str:
        return "/usr/bin/ldd"

    def _run(command: Sequence[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, stdout=ldd_text, stderr="")

    def _baseline(_path: Path | None = None) -> dict[str, str]:
        return dict(declared)

    monkeypatch.setattr(pe.shutil, "which", _which)
    monkeypatch.setattr(pe.subprocess, "run", _run)
    monkeypatch.setattr(pe, "load_linux_runtime_baseline", _baseline)
    return pe.audit_linux_dependencies(app)


def test_audit_passes_with_declared_host_dependencies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _app_tree(tmp_path)
    inventory = _audit(monkeypatch, app, _ldd_lines(app, ["libc.so.6", "libm.so.6"]))
    assert inventory["audited_targets"] == [
        "QtWebEngineProcess",
        "deepplant-editor",
        "libQt6WebEngineCore.so",
        "libqxcb.so",
    ]
    targets = inventory["targets"]
    assert isinstance(targets, dict)
    assert targets["deepplant-editor"]["host"] == ["libc.so.6", "libm.so.6"]
    assert targets["deepplant-editor"]["bundled"] == ["libQt6Core.so.6"]
    baseline = inventory["host_baseline"]
    assert isinstance(baseline, dict)
    assert baseline["unexpected"] == []
    assert baseline["stale"] == []


def test_audit_fails_on_an_undeclared_host_dependency(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _app_tree(tmp_path)
    text = _ldd_lines(app, ["libc.so.6", "libbrandnew.so.7"])
    with pytest.raises(pe.PackagingError) as error:
        _audit(monkeypatch, app, text)
    assert "undeclared host dependency libbrandnew.so.7" in str(error.value)
    assert "linux-runtime-baseline.toml" in str(error.value)


def test_audit_fails_when_qt_resolves_from_the_host(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _app_tree(tmp_path)
    text = _ldd_lines(
        app, ["libc.so.6"], extra=["\tlibQt6Gui.so.6 => /usr/lib/libQt6Gui.so.6 (0x00007f)"]
    )
    with pytest.raises(pe.PackagingError) as error:
        _audit(monkeypatch, app, text)
    assert "Qt library libQt6Gui.so.6 resolves to the host" in str(error.value)


def test_audit_fails_when_a_dependency_resolves_into_the_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _app_tree(tmp_path)
    leaked = pe.REPO_ROOT / "src" / "deepplant" / "libleaked.so.1"
    text = _ldd_lines(app, ["libc.so.6"], extra=[f"\tlibleaked.so.1 => {leaked} (0x00007f)"])
    with pytest.raises(pe.PackagingError) as error:
        _audit(monkeypatch, app, text)
    assert "resolves into the checkout" in str(error.value)


def test_audit_fails_when_a_dependency_resolves_into_the_uv_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _app_tree(tmp_path)
    leaked = Path(sys.prefix) / "lib" / "libuvleak.so.1"
    text = _ldd_lines(app, ["libc.so.6"], extra=[f"\tlibuvleak.so.1 => {leaked} (0x00007f)"])
    with pytest.raises(pe.PackagingError) as error:
        _audit(monkeypatch, app, text)
    assert "resolves into the uv-env" in str(error.value)


def test_audit_fails_when_a_dependency_is_not_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _app_tree(tmp_path)
    text = _ldd_lines(app, ["libc.so.6"], extra=["\tlibmissing.so.9 => not found"])
    with pytest.raises(pe.PackagingError) as error:
        _audit(monkeypatch, app, text)
    assert "libmissing.so.9 is not found" in str(error.value)


def test_audit_fails_when_a_required_target_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _app_tree(tmp_path, launcher=False)
    with pytest.raises(pe.PackagingError) as error:
        _audit(monkeypatch, app, _ldd_lines(app, ["libc.so.6"]))
    assert "carries no deepplant-editor to audit" in str(error.value)


def test_select_audited_artifacts_requires_every_target(tmp_path: Path) -> None:
    app = _app_tree(tmp_path)
    found = pe.select_audited_artifacts(app)
    assert set(found) == {
        "deepplant-editor",
        "QtWebEngineProcess",
        "libQt6WebEngineCore.so",
        "libqxcb.so",
    }
    assert [path.name for path in found["deepplant-editor"]] == ["deepplant-editor"]
    assert [path.name for path in found["libqxcb.so"]] == ["libqxcb.so"]
