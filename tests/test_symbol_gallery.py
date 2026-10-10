"""Tests for the registry-driven symbol gallery generator (Issue #121).

The gallery is a derived developer artifact, so these tests pin the derivation
itself: completeness follows ``SYMBOLS.list()`` instead of a parallel list of
ids, every preview is the production renderer's own output, generation is
byte-stable, the metadata comes from the definition objects, and hostile
metadata cannot become active HTML. They also pin the output-directory contract:
the generator owns its directory through a marker, refuses to replace anything
else, and replaces an owned gallery without destroying it when a write fails. No
test writes into the repository: the filesystem tests generate into ``tmp_path``,
and the escaping test renders the page in memory.
"""

from __future__ import annotations

from datetime import date
from html import escape
from html.parser import HTMLParser
from pathlib import Path

import pytest

from deepplant.symbols import (
    SYMBOLS,
    AssetProvenance,
    Line,
    StandardsReference,
    SymbolAnchor,
    SymbolDefinition,
    SymbolRegistry,
    render_symbol_svg,
)
from tools import generate_symbol_gallery as gallery
from tools.generate_symbol_gallery import (
    DEFAULT_OUTPUT_DIR,
    INDEX_FILENAME,
    OWNERSHIP_MARKER,
    OWNERSHIP_MARKER_TEXT,
    SYMBOL_SUBDIR,
    GalleryResult,
    SymbolGalleryError,
    format_number,
    generate_symbol_gallery,
    render_gallery_page,
    require_safe_output_dir,
)

#: The repository root, used to check that the generator refuses to replace it.
ROOT = Path(__file__).resolve().parents[1]

#: The temporary output directory each filesystem test generates into.
TARGET = "gallery"

#: A ``generic-iso`` definition whose registry-derived metadata is hostile HTML,
#: used to prove the page escapes values instead of trusting them. Its standards
#: reference is a complete ``human-verified`` record, so the evidence fields are
#: exercised too.
HOSTILE_NAME = "<script>alert(1)</script>"
HOSTILE_CATEGORY = '<img src=x onerror="alert(2)">'
HOSTILE_LOCATOR = "<b>locator</b>"
HOSTILE_VERIFIER = 'A "verifier" <script>alert(3)</script>'
HOSTILE_VALUES = (HOSTILE_NAME, HOSTILE_CATEGORY, HOSTILE_LOCATOR, HOSTILE_VERIFIER)


def _hostile_definition() -> SymbolDefinition:
    """Build one valid definition carrying hostile-HTML metadata."""
    return SymbolDefinition(
        symbol_id="valve.hostile",
        name=HOSTILE_NAME,
        category=HOSTILE_CATEGORY,
        diagram_types=("pid",),
        notation_profile="generic-iso",
        primitives=(Line(x1=0.0, y1=50.0, x2=100.0, y2=50.0),),
        anchors=(SymbolAnchor(name="port_a", x=0.0, y=50.0, orientation="west", kind="process"),),
        provenance=AssetProvenance(origin="deepplant-original", license="AGPL-3.0-only"),
        standards=(
            StandardsReference(
                standard="ISO 10628-2:2012",
                verification="human-verified",
                locator=HOSTILE_LOCATOR,
                verified_by=HOSTILE_VERIFIER,
                verified_on=date(2026, 10, 8),
            ),
        ),
    )


def _generate(tmp_path: Path) -> GalleryResult:
    """Generate the built-in gallery into a temporary directory."""
    return generate_symbol_gallery(tmp_path / TARGET)


def _page(result: GalleryResult) -> str:
    return (result.output_dir / INDEX_FILENAME).read_text(encoding="utf-8")


def _preview(result: GalleryResult, symbol_id: str) -> Path:
    return result.output_dir / SYMBOL_SUBDIR / f"{symbol_id}.svg"


def _snapshot(target: Path) -> dict[str, bytes]:
    """Map every generated artifact to its exact bytes."""
    return {
        str(path.relative_to(target)): path.read_bytes()
        for path in sorted(target.rglob("*"))
        if path.is_file()
    }


def _marker(target: Path) -> Path:
    return target / OWNERSHIP_MARKER


class _PageParser(HTMLParser):
    """Record every element (with its attributes) and every text node."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[tuple[str, dict[str, str | None]]] = []
        self.text: list[str] = []

    @property
    def element_names(self) -> set[str]:
        return {name for name, _ in self.elements}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.elements.append((tag, dict(attrs)))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.elements.append((tag, dict(attrs)))

    def handle_data(self, data: str) -> None:
        self.text.append(data)


def _parsed_page(page: str) -> _PageParser:
    """Parse a generated page with the standard-library parser."""
    parser = _PageParser()
    parser.feed(page)
    parser.close()
    return parser


def _registry_ids() -> tuple[str, ...]:
    """The expected symbol ids, always derived from the registry itself."""
    return tuple(definition.symbol_id for definition in SYMBOLS.list())


def test_the_default_output_directory_is_the_documented_ignored_location() -> None:
    assert DEFAULT_OUTPUT_DIR == Path("build") / "symbol-gallery"


def test_every_registered_symbol_appears_in_the_gallery(tmp_path: Path) -> None:
    result = _generate(tmp_path)
    page = _page(result)

    assert result.symbol_ids == _registry_ids()
    assert result.index_path == result.output_dir / INDEX_FILENAME
    for definition in SYMBOLS.list():
        assert definition.symbol_id in page
        assert _preview(result, definition.symbol_id).is_file()


def test_each_preview_is_the_production_renderer_output(tmp_path: Path) -> None:
    result = _generate(tmp_path)

    for definition in SYMBOLS.list():
        assert _preview(result, definition.symbol_id).read_text(
            encoding="utf-8"
        ) == render_symbol_svg(definition)


def test_generation_is_byte_stable(tmp_path: Path) -> None:
    first = generate_symbol_gallery(tmp_path / "first")
    second = generate_symbol_gallery(tmp_path / "second")

    artifacts = _snapshot(first.output_dir)
    assert artifacts[OWNERSHIP_MARKER] == OWNERSHIP_MARKER_TEXT.encode("utf-8")
    assert _snapshot(second.output_dir) == artifacts
    assert _page(first) == _page(second)


def test_regeneration_removes_stale_previews(tmp_path: Path) -> None:
    target = tmp_path / TARGET
    generate_symbol_gallery(target)
    stale = target / SYMBOL_SUBDIR / "removed.symbol.svg"
    stale.write_text('<svg xmlns="http://www.w3.org/2000/svg" />\n', encoding="utf-8")

    result = generate_symbol_gallery(target)

    assert not stale.exists()
    assert result.symbol_ids == _registry_ids()
    for definition in SYMBOLS.list():
        assert _preview(result, definition.symbol_id).is_file()


def test_a_new_gallery_is_created_and_marked_as_owned(tmp_path: Path) -> None:
    result = _generate(tmp_path)

    assert _marker(result.output_dir).read_text(encoding="utf-8") == OWNERSHIP_MARKER_TEXT
    for definition in SYMBOLS.list():
        assert _preview(result, definition.symbol_id).is_file()
    # Exactly the current artifacts: no temporary directory, backup, or extra file
    # survives a successful generation.
    assert sorted(_snapshot(result.output_dir)) == sorted(
        [OWNERSHIP_MARKER, INDEX_FILENAME]
        + [f"{SYMBOL_SUBDIR}/{definition.symbol_id}.svg" for definition in SYMBOLS.list()]
    )


def test_generation_creates_missing_parent_directories(tmp_path: Path) -> None:
    result = generate_symbol_gallery(tmp_path / "missing" / TARGET)

    assert result.index_path.is_file()


def test_an_owned_gallery_can_be_refreshed(tmp_path: Path) -> None:
    target = tmp_path / TARGET
    generate_symbol_gallery(target)
    before = _snapshot(target)
    stale = target / SYMBOL_SUBDIR / "removed.symbol.svg"
    stale.write_text('<svg xmlns="http://www.w3.org/2000/svg" />\n', encoding="utf-8")

    result = generate_symbol_gallery(target)
    fresh = generate_symbol_gallery(tmp_path / "fresh")

    assert result.symbol_ids == _registry_ids()
    assert not stale.exists()
    assert _marker(target).read_text(encoding="utf-8") == OWNERSHIP_MARKER_TEXT
    assert OWNERSHIP_MARKER in before
    assert _snapshot(target) == before
    assert _snapshot(target) == _snapshot(fresh.output_dir)


def test_the_marker_alone_establishes_ownership(tmp_path: Path) -> None:
    target = tmp_path / TARGET
    target.mkdir()
    _marker(target).write_text(OWNERSHIP_MARKER_TEXT, encoding="utf-8")

    result = generate_symbol_gallery(target)

    assert result.symbol_ids == _registry_ids()
    assert (target / INDEX_FILENAME).is_file()
    for definition in SYMBOLS.list():
        assert _preview(result, definition.symbol_id).is_file()


def test_an_existing_unowned_directory_is_refused_untouched(tmp_path: Path) -> None:
    target = tmp_path / TARGET
    target.mkdir()
    sentinel = target / "sentinel.txt"
    sentinel.write_text("not a gallery\n", encoding="utf-8")

    with pytest.raises(SymbolGalleryError):
        generate_symbol_gallery(target)

    assert target.is_dir()
    assert sentinel.read_text(encoding="utf-8") == "not a gallery\n"
    assert sorted(path.name for path in target.iterdir()) == ["sentinel.txt"]


def test_a_failed_write_leaves_the_previous_gallery_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / TARGET
    generate_symbol_gallery(target)
    before = _snapshot(target)

    def failing_write(directory: Path, documents: tuple[tuple[str, str], ...], page: str) -> None:
        """Start writing the replacement, then fail the way a full disk would."""
        (directory / SYMBOL_SUBDIR).mkdir(parents=True)
        (directory / SYMBOL_SUBDIR / "partial.svg").write_text("<svg />\n", encoding="utf-8")
        raise OSError("simulated write failure")

    monkeypatch.setattr(gallery, "_write_gallery_files", failing_write)

    with pytest.raises(OSError, match="simulated write failure"):
        generate_symbol_gallery(target)

    # The previous gallery is byte-for-byte intact, and no temporary sibling of it
    # survives the failure.
    assert _snapshot(target) == before
    assert sorted(path.name for path in tmp_path.iterdir()) == [TARGET]


def test_the_page_carries_the_registry_metadata(tmp_path: Path) -> None:
    result = _generate(tmp_path)
    page = _page(result)

    for definition in SYMBOLS.list():
        provenance = definition.provenance
        assert f"<dt>Symbol id</dt><dd>{escape(definition.symbol_id)}</dd>" in page
        assert f"<dt>Name</dt><dd>{escape(definition.name)}</dd>" in page
        assert f"<dt>Category</dt><dd>{escape(definition.category)}</dd>" in page
        assert f"<dt>Notation profile</dt><dd>{escape(definition.notation_profile)}</dd>" in page
        assert f"<dt>Origin</dt><dd>{escape(provenance.origin)}</dd>" in page
        assert f"<dt>Licence</dt><dd>{escape(provenance.license)}</dd>" in page
        diagram_types = escape(", ".join(definition.diagram_types))
        assert f"<dt>Diagram types</dt><dd>{diagram_types}</dd>" in page
        for anchor in definition.anchors:
            assert anchor.name in page
            assert anchor.orientation in page
            assert anchor.kind in page
            coordinates = f"({format_number(anchor.x)}, {format_number(anchor.y)})"
            assert coordinates in page
        for reference in definition.standards:
            assert reference.standard in page
            assert reference.verification in page


def test_the_page_exposes_the_deepplant_default_representation(tmp_path: Path) -> None:
    result = _generate(tmp_path)
    page = _page(result)

    # Issue #130 adds the first `deepplant-default` representation. The card and its
    # notation profile are derived from `SYMBOLS.list()`, not from a parallel list.
    assert "fitting.restriction_orifice" in page
    assert "<dt>Notation profile</dt><dd>deepplant-default</dd>" in page
    assert _preview(result, "fitting.restriction_orifice").is_file()
    assert _preview(result, "fitting.restriction_orifice").read_text(
        encoding="utf-8"
    ) == render_symbol_svg(
        SYMBOLS.get("fitting.restriction_orifice", notation_profile="deepplant-default")
    )


def test_the_page_positions_each_anchor_marker_from_the_view_box(tmp_path: Path) -> None:
    result = _generate(tmp_path)
    page = _page(result)

    for definition in SYMBOLS.list():
        min_x, min_y, width, height = definition.view_box
        for anchor in definition.anchors:
            left = format_number((anchor.x - min_x) / width * 100.0)
            top = format_number((anchor.y - min_y) / height * 100.0)
            # The marker is gallery-only CSS positioned over the generated SVG;
            # the production document itself stays anchor-free.
            assert f'style="left: {left}%; top: {top}%"' in page
            assert "anchor" not in _preview(result, definition.symbol_id).read_text("utf-8")


@pytest.mark.parametrize("hostile", HOSTILE_VALUES)
def test_registry_metadata_cannot_become_active_html(hostile: str) -> None:
    page = render_gallery_page(SymbolRegistry([_hostile_definition()]))

    # The value is escaped in the source and, once parsed, survives only as
    # decoded text: it never becomes an element or an attribute.
    parsed = _parsed_page(page)
    assert hostile in "".join(parsed.text)
    assert hostile not in page
    assert escape(hostile, quote=True) in page
    assert "script" not in parsed.element_names
    assert "b" not in parsed.element_names
    assert all(name != "onerror" for _, attributes in parsed.elements for name in attributes)


def test_the_page_is_static_and_self_contained(tmp_path: Path) -> None:
    result = _generate(tmp_path)
    page = _page(result)

    assert "<script" not in page
    assert "://" not in page
    for definition in SYMBOLS.list():
        assert f'src="{SYMBOL_SUBDIR}/{definition.symbol_id}.svg"' in page


@pytest.mark.parametrize("broad", [Path("/"), Path.home(), ROOT])
def test_a_too_broad_output_directory_is_refused(broad: Path) -> None:
    with pytest.raises(SymbolGalleryError):
        require_safe_output_dir(broad)
