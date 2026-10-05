"""Evidence for the Chromium third-party notice mechanism (Issue #93 review fix).

The previous review round shipped only a pointer document that admitted the
Chromium notice set was not reproduced. These tests protect the replacement
mechanism instead of a documentation sentence:

- the parser/build logic turns the *upstream* generated component table into a
  deterministic notice bundle, so no component list is written by hand;
- completeness is proven against the pinned upstream publication, and a missing
  component, an entry without notice text, or a bundle built from a different
  publication all fail;
- the bundle shipped in the repository really enumerates the upstream component
  set with notice text, rather than being a placeholder listing URLs.

The fixtures are local strings; the real native job is the system evidence.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from tools.chromium_notices import (
    DEFAULT_LIST_URL,
    REQUIRED_PROVENANCE_MARKERS,
    NoticeError,
    build_bundle,
    bundle_component_names,
    bundle_components_without_text,
    check_bundle,
    component_slug,
    parse_notice_rows,
    sha256_of_text,
    upstream_component_names,
)

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "packaging" / "licenses" / "Qt-WebEngine" / "Chromium-THIRD-PARTY-NOTICES.txt"
MANIFEST = ROOT / "packaging" / "licenses.toml"

ROW_ZLIB = (
    '<tr class="odd topAlign"><td class="tblName" translate="no">'
    '<p><a href="qtwebengine-3rdparty-zlib.html">zlib</a></p></td>'
    '<td class="tblDescr"><p>Zlib</p></td></tr>'
)
ROW_BORINGSSL = (
    '<tr class="even topAlign"><td class="tblName" translate="no">'
    '<p><a href="qtwebengine-3rdparty-boringssl.html">BoringSSL</a></p></td>'
    '<td class="tblDescr"><p>MIT &amp; BSD-3-Clause</p></td></tr>'
)
ROW_CHROMIUM = (
    '<tr class="odd topAlign"><td class="tblName" translate="no">'
    '<p><a href="qtwebengine-3rdparty-chromium-global.html">Chromium License</a></p></td>'
    '<td class="tblDescr"><p>BSD</p></td></tr>'
)
LIST_HTML = "<table>" + ROW_ZLIB + ROW_BORINGSSL + ROW_CHROMIUM + "</table>"


def _page(title: str, homepage: str, text: str, *, css: str = "cpp plain") -> str:
    return (
        '<div class="context">\n'
        f'<h1 class="title">{title}</h1>\n'
        '<div class="descr" id="details">\n'
        f'<p><a href="{homepage}">Project Homepage</a></p>\n'
        f'<div class="pre"><pre class="{css}" translate="no">{text}</pre></div>\n'
        "</div>\n</div>"
    )


def _documents() -> dict[str, str]:
    return {
        "zlib": _page(
            "zlib",
            "http://zlib.net/",
            "version 1.2.12\n Copyright (C) 1995-2022 Jean-loup Gailly &amp;amp; Mark Adler",
        ),
        "boringssl": _page(
            "BoringSSL", "https://boringssl.googlesource.com/boringssl/", "ISC-style licence text"
        ),
        "chromium-global": _page(
            "Chromium License",
            "https://www.chromium.org/",
            'Copyright 2015 The Chromium Authors\n "AS IS"',
            css="cpp prettyprint",
        ),
    }


def test_parse_notice_rows_reads_slug_name_and_licences() -> None:
    rows = parse_notice_rows(LIST_HTML)
    assert [row.slug for row in rows] == ["zlib", "boringssl", "chromium-global"]
    assert [row.name for row in rows] == ["zlib", "BoringSSL", "Chromium License"]
    # HTML entities in the licence column are decoded.
    assert rows[1].licences == "MIT & BSD-3-Clause"


def test_parse_notice_rows_rejects_a_publication_without_components() -> None:
    with pytest.raises(NoticeError):
        parse_notice_rows("<html><body>no table here</body></html>")


@pytest.mark.parametrize(
    "href",
    ["qtwebengine-3rdparty-zlib.html", "https://doc.qt.io/qt-6.11/qtwebengine-3rdparty-zlib.html"],
)
def test_component_slug_accepts_upstream_links(href: str) -> None:
    assert component_slug(href) == "zlib"


def test_component_slug_rejects_an_unexpected_link() -> None:
    with pytest.raises(NoticeError):
        component_slug("qtwebengine-not-a-component.html")


def test_build_bundle_is_deterministic_and_carries_notice_text() -> None:
    first = build_bundle(LIST_HTML, _documents())
    second = build_bundle(LIST_HTML, _documents())
    assert first == second, "regenerating from the same input must be byte-stable"
    for marker in REQUIRED_PROVENANCE_MARKERS:
        assert marker in first
    assert f"Publication SHA-256     : {sha256_of_text(LIST_HTML)}" in first
    assert bundle_component_names(first) == ["zlib", "BoringSSL", "Chromium License"]
    # The double-escaped entity is decoded in the shipped text.
    assert "Jean-loup Gailly & Mark Adler" in first
    assert bundle_components_without_text(first) == []
    assert check_bundle(first, LIST_HTML) == []


def test_build_bundle_requires_every_component_page() -> None:
    documents = _documents()
    del documents["boringssl"]
    with pytest.raises(NoticeError):
        build_bundle(LIST_HTML, documents)


def test_check_bundle_fails_when_an_upstream_component_is_missing() -> None:
    bundle = build_bundle(LIST_HTML, _documents())
    truncated = "\n".join(line for line in bundle.splitlines() if "BoringSSL" not in line)
    problems = check_bundle(truncated, LIST_HTML)
    assert any("omits" in problem and "BoringSSL" in problem for problem in problems)


def test_check_bundle_fails_when_an_entry_has_no_notice_text() -> None:
    documents = _documents()
    documents["boringssl"] = _page("BoringSSL", "https://example.invalid/", "   ")
    bundle = build_bundle(LIST_HTML, documents)
    problems = check_bundle(bundle, LIST_HTML)
    assert any("carries no notice text" in problem for problem in problems)


def test_check_bundle_fails_when_built_from_another_publication() -> None:
    bundle = build_bundle(LIST_HTML, _documents())
    problems = check_bundle(bundle, LIST_HTML.replace("Zlib", "Zlib-1.3"))
    assert any("different upstream publication" in problem for problem in problems)


def test_check_bundle_fails_without_the_provenance_markers() -> None:
    problems = check_bundle("[001] zlib\n" + "-" * 78 + "\nsome text\n", LIST_HTML)
    assert any("provenance marker" in problem for problem in problems)


def test_shipped_bundle_is_real_evidence_not_a_placeholder() -> None:
    assert BUNDLE.is_file(), BUNDLE
    text = BUNDLE.read_text(encoding="utf-8")
    assert len(text) > 100_000, "the shipped notice bundle must carry real notice text"
    for marker in REQUIRED_PROVENANCE_MARKERS:
        assert marker in text
    manifest = tomllib.loads(MANIFEST.read_text(encoding="utf-8"))
    chromium = manifest["chromium"]
    names = set(bundle_component_names(text))
    assert len(names) == chromium["components"]
    assert chromium["version"] in text
    assert f"Publication SHA-256     : {chromium['publication_sha256']}" in text
    # Components that are certainly part of the shipped Chromium engine.
    assert {"zlib", "BoringSSL", "libvpx", "sqlite"} <= names
    assert bundle_components_without_text(text) == []
    # The pinned publication is the versioned Qt documentation, not a mutable branch.
    assert chromium["publication"] == DEFAULT_LIST_URL
    assert chromium["publication"].endswith("qtwebengine-licensing.html")
    assert len(chromium["publication_sha256"]) == 64
    assert upstream_component_names(LIST_HTML) == ["zlib", "BoringSSL", "Chromium License"]
