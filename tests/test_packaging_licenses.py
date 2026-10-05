"""Evidence for the redistribution compliance payload (Issue #93 review fix).

DeepPlant's artifacts redistribute PySide6, the Qt libraries, Qt WebEngine, the
`QtWebEngineProcess` helper and Chromium runtime data. Repository documentation is
not artifact evidence, so the applicable notice texts are staged into the installed
application. These tests protect that contract:

- `packaging/licenses.toml` must be version-matched to the PySide6 version resolved
  in `uv.lock`;
- every pinned entry must use an immutable upstream URL at the exact Qt tag and
  declare a SHA-256 (never a mutable `latest`/`continuous` locator);
- the pinned destinations plus the project-owned documents must cover the required
  payload the artifact verification demands.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import cast

import pytest

from tools.package_editor import REQUIRED_LICENSE_FILES, load_licenses_manifest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packaging" / "licenses.toml"
STATIC_DIR = ROOT / "packaging" / "licenses"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
MUTABLE_LOCATORS = ("latest", "continuous", "master", "main")


def _pyside6_version() -> str:
    """Return the PySide6 version resolved in ``uv.lock``."""
    document: dict[str, object] = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    packages = document["package"]
    assert isinstance(packages, list)
    for package in cast("list[object]", packages):
        if not isinstance(package, dict):
            continue
        table = cast("dict[str, object]", package)
        if table.get("name") == "pyside6":
            version = table.get("version")
            assert isinstance(version, str)
            return version
    raise AssertionError("uv.lock does not pin pyside6")


def _entries() -> list[dict[str, object]]:
    manifest = load_licenses_manifest()
    files = manifest["file"]
    assert isinstance(files, list)
    return [cast("dict[str, object]", entry) for entry in cast("list[object]", files)]


def test_manifest_is_version_matched_to_uv_lock() -> None:
    manifest = load_licenses_manifest()
    version = _pyside6_version()
    assert manifest["pyside6_version"] == version
    assert manifest["qt_version"] == version
    assert manifest["qt_tag"] == f"v{version}"


def test_every_pinned_file_is_immutable_and_checksummed() -> None:
    manifest = load_licenses_manifest()
    tag = manifest["qt_tag"]
    assert isinstance(tag, str)
    entries = _entries()
    assert entries, "packaging/licenses.toml declares no files"
    for table in entries:
        url = table["url"]
        digest = table["sha256"]
        assert isinstance(url, str)
        assert tag in url, f"url is not at the Qt tag {tag}: {url}"
        assert not any(part in url for part in MUTABLE_LOCATORS), f"mutable locator: {url}"
        assert isinstance(digest, str) and SHA256.match(digest), f"bad digest: {digest}"


def test_pinned_destinations_cover_the_required_payload() -> None:
    required = set(REQUIRED_LICENSE_FILES)
    destinations = {cast("str", table["destination"]) for table in _entries()}
    assert destinations <= required, sorted(destinations - required)
    # The verification must also demand the project-owned compliance documents.
    assert {
        "README.md",
        "CORRESPONDING-SOURCE.md",
        "DEEPLANT-AGPL-3.0.txt",
        "THIRD_PARTY_NOTICES.md",
    } <= required
    # ...and the real Chromium notice evidence, not just an explanatory pointer.
    assert {
        "Qt-WebEngine/Chromium-NOTICES.md",
        "Qt-WebEngine/Chromium-THIRD-PARTY-NOTICES.txt",
        "Qt-WebEngine/Chromium-VERSION.txt",
        "Qt-WebEngine/Chromium-LICENSE-BSD.txt",
    } <= required


def test_chromium_notice_mechanism_is_declared_and_version_matched() -> None:
    manifest = load_licenses_manifest()
    chromium = cast("dict[str, object]", manifest["chromium"])
    assert chromium["version"] == "140.0.7339.264"
    assert chromium["source_tag"] == manifest["qt_tag"]
    assert "licenses.py" in cast("str", chromium["generator"])
    assert ":QtWebEngineCore" in cast("str", chromium["generator"])
    assert cast("str", chromium["publication"]).startswith("https://")
    assert SHA256.match(cast("str", chromium["publication_sha256"]))
    assert cast("int", chromium["components"]) > 0
    # The bundle is shipped from the project-owned payload, not fetched at build.
    destinations = {cast("str", table["destination"]) for table in _entries()}
    assert cast("str", chromium["bundle"]) not in destinations


def test_manifest_requires_the_chromium_notice_mechanism(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = tmp_path / "licenses.toml"
    manifest.write_text(
        "\n".join(
            [
                "schema_version = 1",
                'pyside6_version = "6.11.2"',
                'qt_version = "6.11.2"',
                'qt_tag = "v6.11.2"',
                "[[file]]",
                'destination = "Qt/x.txt"',
                'url = "https://example.com/v6.11.2/x.txt"',
                f'sha256 = "{"0" * 64}"',
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("tools.package_editor.LICENSES_MANIFEST", manifest)
    try:
        load_licenses_manifest()
    except Exception as exc:  # noqa: BLE001 - the message is the assertion
        assert "[chromium]" in str(exc)
    else:  # pragma: no cover - the guard must fail closed
        raise AssertionError("a manifest without the Chromium notice mechanism was accepted")


def test_project_compliance_documents_exist_and_name_the_versions() -> None:
    for relative in (
        "README.md",
        "CORRESPONDING-SOURCE.md",
        "Qt-WebEngine/Chromium-NOTICES.md",
    ):
        assert (STATIC_DIR / relative).is_file(), relative
    readme = (STATIC_DIR / "README.md").read_text(encoding="utf-8")
    assert _pyside6_version() in readme


def test_corresponding_source_document_records_the_mechanism_and_revisions() -> None:
    text = (STATIC_DIR / "CORRESPONDING-SOURCE.md").read_text(encoding="utf-8")
    # The operative licence option and the exact upstream revisions it refers to.
    assert "4(d)(1)" in text
    assert "shared library mechanism" in text
    for revision in (
        "a33fa2a897e5ee58e385b3f88dc247d99fca56db",
        "5170777d28bee1ce92cc693a0dbf2ad01492e5cf",
    ):
        assert revision in text
    assert "three years" in text


def test_chromium_notice_document_states_what_is_actually_shipped() -> None:
    text = (STATIC_DIR / "Qt-WebEngine" / "Chromium-NOTICES.md").read_text(encoding="utf-8")
    assert "Chromium-THIRD-PARTY-NOTICES.txt" in text
    assert "140.0.7339.264" in text
    assert "licenses.py" in text
    # The previous round's incorrect claim about about:credits must be gone.
    assert "can display the aggregated" not in text


def test_manifest_rejects_a_mutable_locator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = tmp_path / "licenses.toml"
    manifest.write_text(
        "\n".join(
            [
                "schema_version = 1",
                'pyside6_version = "6.11.2"',
                'qt_version = "6.11.2"',
                'qt_tag = "v6.11.2"',
                "[[file]]",
                'destination = "Qt/x.txt"',
                'url = "https://example.com/latest/x.txt"',
                f'sha256 = "{"0" * 64}"',
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("tools.package_editor.LICENSES_MANIFEST", manifest)
    try:
        load_licenses_manifest()
    except Exception as exc:  # noqa: BLE001 - the message is the assertion
        assert "mutable locator" in str(exc)
    else:  # pragma: no cover - the guard must fail closed
        raise AssertionError("a mutable locator was accepted")
