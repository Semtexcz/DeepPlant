"""Evidence for the pinned external packaging toolchain (Issue #85 review fix).

The native packaging jobs build user-facing artifacts with two non-Python tools
whose upstream inputs were previously fetched from a mutable locator. These
tests protect the reviewed contract instead of a doc sentence:

- ``packaging/toolchain.toml`` must pin an immutable release tag (never
  ``continuous``/``latest``/``master``/``main``) for every downloaded artifact;
- every downloaded artifact must declare a SHA-256;
- ``tools/packaging_toolchain.py`` (the reader CI uses) must surface exactly the
  values in that contract, and must fail closed on a mutable locator.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "packaging" / "toolchain.toml"
HELPER = ROOT / "tools" / "packaging_toolchain.py"

MUTABLE_LOCATORS = ("continuous", "latest", "master", "main")
RELEASE_URL = re.compile(
    r"^https://github\.com/[^/]+/[^/]+/releases/download/(?P<tag>[^/]+)/[^/]+$"
)
SHA256 = re.compile(r"^[0-9a-f]{64}$")

#: Sections that describe an artifact downloaded directly from upstream.
DOWNLOAD_SECTIONS = ("appimagetool", "appimage_runtime")


def _contract() -> dict[str, object]:
    return tomllib.loads(CONTRACT.read_text(encoding="utf-8"))


def _section(name: str) -> dict[str, object]:
    value = _contract().get(name)
    assert isinstance(value, dict), name
    return cast("dict[str, object]", value)


def _text(table: dict[str, object], key: str) -> str:
    value = table[key]
    assert isinstance(value, str), key
    return value


def _run_helper(
    *arguments: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HELPER), *arguments],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_contract_exists_and_is_versioned() -> None:
    assert CONTRACT.is_file()
    assert _contract()["schema_version"] == 1


def test_downloaded_artifacts_are_immutable_and_checksummed() -> None:
    for section in DOWNLOAD_SECTIONS:
        entry = _section(section)
        version = _text(entry, "version")
        url = _text(entry, "url")
        digest = _text(entry, "sha256")

        match = RELEASE_URL.match(url)
        assert match is not None, f"[{section}] is not an immutable release asset url: {url}"
        tag = match.group("tag")
        assert tag == version, f"[{section}] release tag {tag!r} must equal version {version!r}"
        assert tag not in MUTABLE_LOCATORS, f"[{section}] uses a mutable locator: {tag!r}"
        assert SHA256.match(digest), f"[{section}] sha256 is not 64 hex characters"
        assert _text(entry, "architecture") == "x86_64"


def test_inno_setup_is_pinned_to_an_exact_version() -> None:
    entry = _section("inno_setup")
    assert _text(entry, "chocolatey_package") == "innosetup"
    assert re.fullmatch(r"\d+\.\d+(\.\d+)?", _text(entry, "version"))


def test_helper_show_reports_the_pinned_inputs() -> None:
    result = _run_helper("show")
    assert result.returncode == 0, result.stderr
    for section in DOWNLOAD_SECTIONS:
        entry = _section(section)
        assert _text(entry, "version") in result.stdout
        assert _text(entry, "sha256") in result.stdout
    assert _text(_section("inno_setup"), "version") in result.stdout


def test_helper_export_writes_the_declared_values_to_github_env(tmp_path: Path) -> None:
    env_file = tmp_path / "github_env"
    env_file.write_text("", encoding="utf-8")
    result = _run_helper("export", env={**os.environ, "GITHUB_ENV": str(env_file)})
    assert result.returncode == 0, result.stderr

    exported: dict[str, str] = {}
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line:
            key, _, value = line.partition("=")
            exported[key] = value

    assert exported["APPIMAGETOOL_VERSION"] == _text(_section("appimagetool"), "version")
    assert exported["APPIMAGETOOL_URL"] == _text(_section("appimagetool"), "url")
    assert exported["APPIMAGETOOL_SHA256"] == _text(_section("appimagetool"), "sha256")
    assert exported["APPIMAGE_RUNTIME_SHA256"] == _text(_section("appimage_runtime"), "sha256")
    assert exported["INNO_SETUP_VERSION"] == _text(_section("inno_setup"), "version")


def test_helper_fails_closed_on_a_mutable_release_locator(tmp_path: Path) -> None:
    contract = tmp_path / "toolchain.toml"
    contract.write_text(
        "\n".join(
            [
                "schema_version = 1",
                "[appimagetool]",
                'version = "continuous"',
                'architecture = "x86_64"',
                'url = "https://github.com/AppImage/appimagetool/releases/download/continuous/tool"',
                f'sha256 = "{"0" * 64}"',
                'licence = "MIT"',
                "[appimage_runtime]",
                'version = "20251108"',
                'architecture = "x86_64"',
                'url = "https://github.com/AppImage/type2-runtime/releases/download/20251108/runtime-x86_64"',
                f'sha256 = "{"0" * 64}"',
                'licence = "MIT"',
                "[inno_setup]",
                'chocolatey_package = "innosetup"',
                'version = "6.7.1"',
                'licence = "Inno Setup License"',
            ]
        ),
        encoding="utf-8",
    )

    result = _run_helper("show", "--file", str(contract))
    assert result.returncode == 1
    assert "continuous" in result.stderr
