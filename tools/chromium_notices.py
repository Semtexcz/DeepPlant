# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Version-matched Chromium third-party notices for the redistributed engine.

Qt WebEngine compiles the Chromium engine into ``Qt6WebEngineCore``, so a
distribution that ships Qt WebEngine must also honour the Chromium third-party
licences. Upstream does not publish that notice set as a single immutable release
file: Qt *generates* it at build time with Chromium's own
``tools/licenses/licenses.py`` (``credits`` mode), driven by
``qtwebengine/cmake/QtGnCredits.cmake`` for the GN target ``:QtWebEngineCore``,
and *publishes* the generated result as the ``qtwebengine-licensing``
documentation group for the exact Qt release.

This module turns that published, version-matched output into a deterministic
packaging input (Issue #93 review fix):

``generate``
    fetch the pinned upstream publication plus every component page it links to,
    and write one plain-text notice bundle (never a hand-written, necessarily
    partial component list);
``check``
    fetch the pinned upstream publication, verify its SHA-256, and prove that the
    bundled notice text covers **every** component upstream lists, so a stale or
    partial bundle fails closed.

The bundle is committed into the repository and shipped inside the application,
so the required notice material is real content in the artifact rather than a
pointer to where somebody else could regenerate it.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

#: Upstream publication of the generated third-party licence set: the versioned
#: Qt documentation tree for the Qt release the distributed wheels are built from.
DEFAULT_LIST_URL = "https://doc.qt.io/qt-6.11/qtwebengine-licensing.html"

#: Prefix of the per-component pages linked from that publication.
COMPONENT_URL_PREFIX = "https://doc.qt.io/qt-6.11/"

#: Provenance markers the bundle must carry; also asserted by the packaging tests.
REQUIRED_PROVENANCE_MARKERS = (
    "Chromium version        : ",
    "Qt WebEngine source tag : ",
    "Generator               : Chromium tools/licenses/licenses.py credits",
    "Publication SHA-256     : ",
)

_ROW = re.compile(
    r'<td class="tblName"[^>]*><p><a href="(?P<href>[^"]+\.html)">(?P<name>[^<]+)</a>'
    r'(?:</p></td><td class="tblDescr"><p>(?P<licence>[^<]*)</p>)?'
)
_HEADING = re.compile(r"^\[(?P<index>\d{3})\] (?P<name>.+)$", re.MULTILINE)
_SEPARATOR = "=" * 78
_TITLE = re.compile(r'<h1 class="title">(.*?)</h1>', re.S)
_HOMEPAGE = re.compile(r'<p><a href="([^"]*)">Project Homepage</a></p>')
_NOTICE_TEXT = re.compile(r'<pre class="cpp [a-z]+" translate="no">(.*?)</pre>', re.S)


class NoticeError(RuntimeError):
    """Raised when the notice bundle cannot be produced or verified."""


@dataclass(frozen=True)
class NoticeRow:
    """One row of the upstream third-party licence table."""

    slug: str
    name: str
    licences: str


@dataclass(frozen=True)
class NoticeComponent:
    """One component with the notice text upstream publishes for it."""

    name: str
    homepage: str
    text: str
    licences: str


def sha256_of_text(text: str) -> str:
    """Return the hex SHA-256 of ``text`` encoded as UTF-8."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def component_slug(href: str) -> str:
    """Return the component slug of a ``qtwebengine-3rdparty-<slug>.html`` link."""
    name = href.rsplit("/", 1)[-1]
    _prefix, separator, suffix = name.partition("qtwebengine-3rdparty-")
    if not separator or not suffix.endswith(".html"):
        raise NoticeError(f"unexpected component link: {href}")
    return suffix[: -len(".html")]


def parse_notice_rows(list_html: str) -> list[NoticeRow]:
    """Parse the upstream third-party licence table into ordered rows."""
    rows: list[NoticeRow] = []
    for match in _ROW.finditer(list_html):
        rows.append(
            NoticeRow(
                slug=component_slug(match.group("href")),
                name=html.unescape(match.group("name")).strip(),
                licences=html.unescape(match.group("licence") or "").strip(),
            )
        )
    if not rows:
        raise NoticeError("the upstream publication lists no third-party components")
    return rows


def upstream_component_names(list_html: str) -> list[str]:
    """Return the component names the upstream publication lists, in order."""
    return [row.name for row in parse_notice_rows(list_html)]


def bundle_component_names(bundle_text: str) -> list[str]:
    """Return the component names a generated bundle enumerates, in order."""
    return [match.group("name").strip() for match in _HEADING.finditer(bundle_text)]


def _extract_notice_text(document: str, slug: str) -> str:
    match = _NOTICE_TEXT.search(document)
    if match is None:
        raise NoticeError(f"component {slug!r} publishes no notice text")
    # The rendered pages escape twice (``&amp;quot;``), so unescape twice.
    return html.unescape(html.unescape(match.group(1))).strip("\n")


def _extract_homepage(document: str) -> str:
    match = _HOMEPAGE.search(document)
    return html.unescape(match.group(1)).strip() if match else ""


def _extract_title(document: str, slug: str) -> str:
    match = _TITLE.search(document)
    return html.unescape(match.group(1)).strip() if match else slug


def build_bundle(list_html: str, documents: dict[str, str]) -> str:
    """Return the deterministic notice bundle for one upstream publication.

    ``documents`` maps a component slug to its rendered component page. The
    output is byte-stable for fixed inputs: no timestamps or host details are
    embedded, so regenerating from the same upstream revision reproduces it.
    """
    rows = parse_notice_rows(list_html)
    components: list[NoticeComponent] = []
    seen: set[str] = set()
    for row in rows:
        if row.slug in seen:
            continue
        seen.add(row.slug)
        document = documents.get(row.slug)
        if document is None:
            raise NoticeError(f"no fetched page for component {row.slug!r}")
        licences = ", ".join(
            sorted({r.licences for r in rows if r.slug == row.slug and r.licences})
        )
        components.append(
            NoticeComponent(
                name=_extract_title(document, row.slug),
                homepage=_extract_homepage(document),
                text=_extract_notice_text(document, row.slug),
                licences=licences,
            )
        )

    lines: list[str] = [
        "Chromium third-party notices for the Qt WebEngine runtime",
        "==========================================================",
        "",
        "Generated by DeepPlant's packaging tooling from the notice set that upstream Qt",
        "generates for the Chromium code compiled into Qt WebEngine. It is not a",
        "hand-written list: the component set comes from the upstream publication",
        "recorded below, and every entry reproduces the notice text upstream publishes.",
        "",
        "Provenance",
        "----------",
        "Qt WebEngine version    : 6.11.2",
        "Qt WebEngine source tag : v6.11.2",
        "Chromium version        : 140.0.7339.264",
        "Generator               : Chromium tools/licenses/licenses.py credits",
        "                          driven by qtwebengine cmake/QtGnCredits.cmake",
        "                          (GN target :QtWebEngineCore)",
        f"Publication SHA-256     : {sha256_of_text(list_html)}",
        f"Components              : {len(components)} ({len(rows)} list entries)",
        "",
        "The SHA-256 above is the digest of the upstream publication this bundle was",
        "built from; the packaging job re-fetches that publication and fails if it no",
        "longer matches, so the shipped notices cannot silently drift from the engine.",
        "",
    ]
    for index, component in enumerate(components, start=1):
        lines.append(_SEPARATOR)
        lines.append(f"[{index:03d}] {component.name}")
        lines.append(
            "Licence identifier(s): " + (component.licences if component.licences else "(see text)")
        )
        if component.homepage:
            lines.append(f"Project homepage: {component.homepage}")
        lines.append("-" * 78)
        lines.append(component.text)
        lines.append("")
    return "\n".join(lines)


def _split_bundle_entries(bundle_text: str) -> list[NoticeComponent]:
    """Return the bundle's entries with their notice text, as shipped."""
    entries: list[NoticeComponent] = []
    for block in bundle_text.split(_SEPARATOR)[1:]:
        name, _, body = block.lstrip("\n").partition("\n")
        match = _HEADING.match(name.strip())
        if match is None:
            continue
        entries.append(
            NoticeComponent(
                name=match.group("name").strip(),
                homepage="",
                text=body.partition("-" * 78)[2],
                licences="",
            )
        )
    return entries


def bundle_components_without_text(bundle_text: str) -> list[str]:
    """Return the components whose shipped entry carries no notice text."""
    return [entry.name for entry in _split_bundle_entries(bundle_text) if not entry.text.strip()]


def check_bundle(bundle_text: str, list_html: str) -> list[str]:
    """Return the reasons ``bundle_text`` is not complete; empty when it is.

    ``bundle_text`` is checked against the *pinned* upstream publication, so this
    is the fail-closed proof that the shipped bundle covers every component
    upstream lists for the redistributed engine.
    """
    problems: list[str] = []
    for marker in REQUIRED_PROVENANCE_MARKERS:
        if marker not in bundle_text:
            problems.append(f"bundle is missing the provenance marker {marker!r}")
    if f"Publication SHA-256     : {sha256_of_text(list_html)}" not in bundle_text:
        problems.append("bundle was built from a different upstream publication")

    bundled = set(bundle_component_names(bundle_text))
    missing = sorted({name for name in upstream_component_names(list_html) if name not in bundled})
    if missing:
        problems.append(
            f"bundle omits {len(missing)} upstream component(s): " + ", ".join(missing[:10])
        )
    for entry in bundle_components_without_text(bundle_text):
        problems.append(f"component {entry!r} carries no notice text")
    return problems


def fetch_text(url: str, *, attempts: int = 4, timeout: float = 60.0) -> str:
    """Fetch ``url`` as UTF-8 text, retrying briefly on a transient failure."""
    last: Exception | None = None
    for _ in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310
                return response.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError, OSError) as error:  # pragma: no cover
            last = error
            time.sleep(2.0)
    raise NoticeError(f"could not fetch {url}: {last}")


def load_cached_page(cache: Path, slug: str) -> str:
    """Return a component page from ``cache``, fetching and caching it if needed."""
    path = cache / f"qtwebengine-3rdparty-{slug}.html"
    if path.is_file() and path.stat().st_size > 0:
        return path.read_text(encoding="utf-8")
    document = fetch_text(f"{COMPONENT_URL_PREFIX}qtwebengine-3rdparty-{slug}.html")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(document, encoding="utf-8")
    return document


def generate(list_url: str, output: Path, cache: Path) -> int:
    """Fetch the pinned publication and write the notice bundle to ``output``."""
    list_html = fetch_text(list_url)
    slugs: list[str] = []
    for row in parse_notice_rows(list_html):
        if row.slug not in slugs:
            slugs.append(row.slug)
    bundle = build_bundle(list_html, {slug: load_cached_page(cache, slug) for slug in slugs})
    problems = check_bundle(bundle, list_html)
    for problem in problems:
        print(f"error: {problem}", file=sys.stderr)
    if problems:
        return 1
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(bundle, encoding="utf-8")
    print(f"wrote {output} ({len(bundle.encode('utf-8'))} bytes, {len(slugs)} components)")
    return 0


def check(list_url: str, bundle: Path, expected_sha256: str | None) -> int:
    """Verify the committed bundle against the pinned upstream publication."""
    if not bundle.is_file():
        print(f"error: no Chromium notice bundle at {bundle}", file=sys.stderr)
        return 1
    try:
        list_html = fetch_text(list_url)
    except NoticeError as error:  # pragma: no cover - network failure path
        print(f"error: {error}", file=sys.stderr)
        return 1
    actual = sha256_of_text(list_html)
    if expected_sha256 is not None and actual != expected_sha256:
        print(
            "error: the upstream publication no longer matches the pinned SHA-256 "
            f"(expected {expected_sha256}, got {actual})",
            file=sys.stderr,
        )
        return 1
    bundle_text = bundle.read_text(encoding="utf-8")
    problems = check_bundle(bundle_text, list_html)
    for problem in problems:
        print(f"error: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(
        f"chromium notices verified: {len(bundle_component_names(bundle_text))} components "
        f"match {list_url}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Return the command-line parser for the notice tooling."""
    parser = argparse.ArgumentParser(description="Chromium third-party notice tooling")
    parser.add_argument(
        "command", choices=("generate", "check"), help="generate or verify the notice bundle"
    )
    parser.add_argument("--bundle", type=Path, required=True, help="notice bundle path")
    parser.add_argument("--list-url", default=DEFAULT_LIST_URL, help="upstream publication url")
    parser.add_argument(
        "--list-sha256", default=None, help="pinned SHA-256 of the upstream publication"
    )
    parser.add_argument(
        "--cache", type=Path, default=Path("build/chromium-notice-cache"), help="page cache"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the notice tooling command line."""
    args = build_parser().parse_args(argv)
    command: str = args.command
    bundle: Path = args.bundle
    if command == "generate":
        return generate(args.list_url, bundle, args.cache)
    return check(args.list_url, bundle, args.list_sha256)


if __name__ == "__main__":
    sys.exit(main())
