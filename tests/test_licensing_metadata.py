import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_project_license_metadata_and_governance_files() -> None:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert metadata["project"]["license"] == "AGPL-3.0-only"
    assert metadata["project"]["license-files"] == ["LICENSE"]

    for relative in (
        "LICENSE",
        "CONTRIBUTING.md",
        "CLA.md",
        "COMMERCIAL-LICENSING.md",
        "TRADEMARKS.md",
        "THIRD_PARTY_NOTICES.md",
        ".github/pull_request_template.md",
    ):
        assert (ROOT / relative).is_file(), relative


def test_readme_uses_unambiguous_license_language_and_links_governance() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "AGPL-3.0-only" in readme
    assert "AGPL-3.0-or-later" not in readme
    for link in (
        "CONTRIBUTING.md",
        "CLA.md",
        "COMMERCIAL-LICENSING.md",
        "THIRD_PARTY_NOTICES.md",
        "TRADEMARKS.md",
    ):
        assert f"]({link})" in readme
