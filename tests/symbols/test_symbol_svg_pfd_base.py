"""Structural contracts for the #137 remaining MVP PFD base representations.

Issue #137 adds the two remaining resolved MVP PFD base representations that
establish one reusable built-in identity, in the ``deepplant-default`` profile: the
compressor (``compressor.general``) and the in-line mixer (``mixer.inline``). They
are the first *equipment* symbols authored in that profile, so this module pins
their exact rendered bytes, their identity, their neutral process anchors, their
structural decomposition, and the standards state each representation's own review
supports.

Issue #137 deliberately adds no reactor/burner built-in symbol: the selected PFD
requires the reaction/burning *process step* to be representable, which does not
establish one reusable built-in equipment identity (``ProcessStep != Equipment``), so
that requirement is covered by a project-selected standard equipment representation
or a project/company-specific graphic instead.

It is a separate module from ``test_symbol_svg.py`` on purpose: that module already
carries the #119/#125/#130/#132/#135 contracts and sits close to the test-module
logical-LOC hard limit enforced by ``make architecture-check``. Splitting the new
slice keeps both modules inside the guardrail instead of weakening it.
"""

from __future__ import annotations

import dataclasses
import math
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

import pytest

from deepplant.symbols import (
    SYMBOLS,
    AssetProvenance,
    Circle,
    Line,
    Polygon,
    SymbolDefinition,
    render_symbol_svg,
)
from deepplant.symbols.profiles import DEEPPLANT_DEFAULT_NOTATION_PROFILE

ISO_10628_2 = "ISO 10628-2:2012"

#: The exact #137 documents the independently authored project seed geometry
#: produces (seeds M/N). Pinned so a contract change cannot silently alter geometry,
#: and so each representation's real structural distinction stays visible in the
#: pinned bytes: the circular casing with its narrowing compression band, and the
#: mixing body with its single bent element and its third (north) connection.
COMPRESSOR_DOCUMENT = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none" '
    'stroke="currentColor" stroke-width="2"><line x1="0" y1="50" x2="24" y2="50" />'
    '<circle cx="50" cy="50" r="26" /><line x1="32" y1="34" x2="72" y2="44" />'
    '<line x1="32" y1="66" x2="72" y2="56" /><line x1="76" y1="50" x2="100" y2="50" />'
    "</svg>\n"
)

MIXER_DOCUMENT = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none" '
    'stroke="currentColor" stroke-width="2"><line x1="0" y1="50" x2="24" y2="50" />'
    '<polygon points="24,26 76,26 76,74 24,74" /><line x1="36" y1="36" x2="36" y2="52" />'
    '<line x1="36" y1="36" x2="64" y2="64" /><line x1="64" y1="64" x2="64" y2="48" />'
    '<line x1="76" y1="50" x2="100" y2="50" /><line x1="50" y1="26" x2="50" y2="0" />'
    "</svg>\n"
)

#: The two #137 `deepplant-default` PFD base representations, as
#: ``(symbol_id, name, document)``.
PFD_BASE_SYMBOLS = (
    ("compressor.general", "Compressor", COMPRESSOR_DOCUMENT),
    ("mixer.inline", "Inline mixer", MIXER_DOCUMENT),
)

#: The standards state each representation's own review supports: both adopt the
#: distinctive mark of a reviewed ISO 10628-2:2012 equipment form, so both record an
#: intended correspondence at `candidate-alignment`, which claims no human check for
#: a concrete geometry.
PFD_BASE_STANDARDS = (
    ("compressor.general", "candidate-alignment"),
    ("mixer.inline", "candidate-alignment"),
)

#: Fragments that would prove a project/company tag, code, or convention leaked into
#: reusable base symbol geometry.
PROJECT_TEXT_FRAGMENTS = ("PIT", "TIT", "FIC", "FV-", "P-101", "DN", "SIS", "DCS", "YARA")


def _pfd_base(symbol_id: str) -> SymbolDefinition:
    """Resolve one #137 representation by its explicit identity."""
    return SYMBOLS.get(symbol_id, notation_profile=DEEPPLANT_DEFAULT_NOTATION_PROFILE)


def _root(document: str) -> Element:
    return ElementTree.fromstring(document)


def _lines(definition: SymbolDefinition) -> list[Line]:
    return [item for item in definition.primitives if isinstance(item, Line)]


def _bodies(definition: SymbolDefinition) -> list[Polygon]:
    return [item for item in definition.primitives if isinstance(item, Polygon)]


# ---------------------------------------------------------------------------
# Contract of the #137 PFD base representations (deepplant-default)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("symbol_id", "_name", "document"), PFD_BASE_SYMBOLS)
def test_the_rendered_pfd_base_document_is_unchanged(
    symbol_id: str, _name: str, document: str
) -> None:
    assert render_symbol_svg(_pfd_base(symbol_id)) == document


@pytest.mark.parametrize(("symbol_id", "name", "_document"), PFD_BASE_SYMBOLS)
def test_pfd_base_identity_contract(symbol_id: str, name: str, _document: str) -> None:
    definition = _pfd_base(symbol_id)

    # These are PFD equipment outlines in the DeepPlant-owned practical profile, and
    # each one is DeepPlant-authored geometry under the repository licence.
    assert definition.name == name
    assert definition.category == "equipment"
    assert definition.diagram_types == ("pfd",)
    assert definition.notation_profile == DEEPPLANT_DEFAULT_NOTATION_PROFILE
    assert definition.view_box == (0.0, 0.0, 100.0, 100.0)
    assert definition.provenance == AssetProvenance(
        origin="deepplant-original", license="AGPL-3.0-only"
    )


@pytest.mark.parametrize(("symbol_id", "_name", "_document"), PFD_BASE_SYMBOLS)
def test_pfd_base_symbols_use_neutral_process_anchors(
    symbol_id: str, _name: str, _document: str
) -> None:
    definition = _pfd_base(symbol_id)

    # Every port is a neutral graphical connection point: no `inlet`/`outlet` and no
    # `suction`/`discharge` name is adopted even though the equipment families are
    # asymmetric in reality, and no flow-direction field exists on the anchor.
    assert all(anchor.kind == "process" for anchor in definition.anchors)
    assert all(anchor.name.startswith("port_") for anchor in definition.anchors)
    assert {anchor.name for anchor in definition.anchors}.isdisjoint(
        {"inlet", "outlet", "common", "suction", "discharge", "upstream", "downstream"}
    )
    assert "flow_direction" not in {
        field.name for field in dataclasses.fields(definition.anchors[0])
    }


@pytest.mark.parametrize(("symbol_id", "verification"), PFD_BASE_STANDARDS)
def test_each_pfd_base_symbol_records_the_standards_state_its_review_supports(
    symbol_id: str, verification: str
) -> None:
    definition = _pfd_base(symbol_id)

    assert len(definition.standards) == 1
    reference = definition.standards[0]
    assert reference.standard == ISO_10628_2
    assert reference.verification == verification
    # Neither a locator, the standard's own name for a representation, a verifier,
    # nor a date may be recorded from restricted material or falsely imply a human
    # check (ADR-0007).
    assert reference.locator is None
    assert reference.name is None
    assert reference.verified_by is None
    assert reference.verified_on is None


@pytest.mark.parametrize(("symbol_id", "_name", "_document"), PFD_BASE_SYMBOLS)
def test_no_pfd_base_symbol_claims_human_verification(
    symbol_id: str, _name: str, _document: str
) -> None:
    for reference in _pfd_base(symbol_id).standards:
        assert reference.verification != "human-verified"


@pytest.mark.parametrize(("symbol_id", "_name", "_document"), PFD_BASE_SYMBOLS)
def test_pfd_base_documents_carry_no_project_or_company_text(
    symbol_id: str, _name: str, _document: str
) -> None:
    document = render_symbol_svg(_pfd_base(symbol_id))

    for fragment in PROJECT_TEXT_FRAGMENTS:
        assert fragment not in document, f"{fragment!r} leaked into {symbol_id}"


@pytest.mark.parametrize(("symbol_id", "_name", "_document"), PFD_BASE_SYMBOLS)
def test_the_pfd_base_symbols_add_no_new_primitive_capability(
    symbol_id: str, _name: str, _document: str
) -> None:
    # #137 needed no renderer, primitive, or styling expansion: every casing, body,
    # mark, and stub is an existing `Line`, `Circle`, or `Polygon`, and no new mark
    # is filled.
    definition = _pfd_base(symbol_id)
    primitive_types = {type(item) for item in definition.primitives}

    assert primitive_types <= {Line, Circle, Polygon}
    assert all(not item.filled for item in definition.primitives if isinstance(item, Circle)), (
        symbol_id
    )
    assert _root(render_symbol_svg(definition)).get("viewBox") == "0 0 100 100"


def test_compressor_contract() -> None:
    definition = _pfd_base("compressor.general")

    # A circular casing interrupted by its two connection stubs, plus the two
    # compression chords that narrow towards the east (seed M). This is a different
    # mark from the pump's: the pump's internal lines meet at one point on the
    # circumference and it carries a full through-line, while these two chords stay
    # apart and no process line crosses the casing.
    assert [item for item in definition.primitives if isinstance(item, Circle)] == [
        Circle(cx=50.0, cy=50.0, r=26.0)
    ]
    assert definition.primitives == (
        Line(x1=0.0, y1=50.0, x2=24.0, y2=50.0),
        Circle(cx=50.0, cy=50.0, r=26.0),
        Line(x1=32.0, y1=34.0, x2=72.0, y2=44.0),
        Line(x1=32.0, y1=66.0, x2=72.0, y2=56.0),
        Line(x1=76.0, y1=50.0, x2=100.0, y2=50.0),
    )
    assert [
        (anchor.name, anchor.orientation, anchor.kind, anchor.x, anchor.y)
        for anchor in definition.anchors
    ] == [
        ("port_a", "west", "process", 0.0, 50.0),
        ("port_b", "east", "process", 100.0, 50.0),
    ]


def test_the_compressor_compression_band_is_mirrored_and_narrows_inside_the_casing() -> None:
    definition = _pfd_base("compressor.general")
    chords = [line for line in _lines(definition) if line.y1 != line.y2]

    assert len(chords) == 2
    upper = next(line for line in chords if line.y1 < 50.0)
    lower = next(line for line in chords if line.y1 > 50.0)
    # Mirror symmetry about the process axis, and a band that genuinely narrows
    # towards the east rather than a symmetric pair of parallel strokes.
    assert upper.x1 == lower.x1
    assert upper.x2 == lower.x2
    assert upper.y1 + lower.y1 == 100.0
    assert upper.y2 + lower.y2 == 100.0
    gap_west = lower.y1 - upper.y1
    gap_east = lower.y2 - upper.y2
    assert 0.0 < gap_east < gap_west
    # Both chords stay inside the casing, so neither crosses the circumference.
    for chord in chords:
        for x, y in ((chord.x1, chord.y1), (chord.x2, chord.y2)):
            assert math.hypot(x - 50.0, y - 50.0) <= 26.0


def test_mixer_contract() -> None:
    definition = _pfd_base("mixer.inline")

    # One closed in-line body, one bent mixing element inside it, and three
    # connection stubs (seed N). The element is a real mixing mark, so it is not a
    # body edge and not an annotation.
    assert definition.primitives == (
        Line(x1=0.0, y1=50.0, x2=24.0, y2=50.0),
        Polygon(points=((24.0, 26.0), (76.0, 26.0), (76.0, 74.0), (24.0, 74.0))),
        Line(x1=36.0, y1=36.0, x2=36.0, y2=52.0),
        Line(x1=36.0, y1=36.0, x2=64.0, y2=64.0),
        Line(x1=64.0, y1=64.0, x2=64.0, y2=48.0),
        Line(x1=76.0, y1=50.0, x2=100.0, y2=50.0),
        Line(x1=50.0, y1=26.0, x2=50.0, y2=0.0),
    )


def test_the_mixer_carries_two_process_inlets_and_one_outlet() -> None:
    definition = _pfd_base("mixer.inline")

    # The A04 requirement is a mixer with two or more process inlets, so the fixed
    # representation exposes three process ports rather than the two an in-line
    # element alone would have. Which port is an inlet is document data, so the ports
    # stay neutral and each one has a real stub reaching the view-box edge.
    assert [(anchor.name, anchor.orientation, anchor.kind) for anchor in definition.anchors] == [
        ("port_a", "west", "process"),
        ("port_b", "east", "process"),
        ("port_c", "north", "process"),
    ]
    for anchor in definition.anchors:
        assert anchor.x in (0.0, 100.0) or anchor.y in (0.0, 100.0)
        assert any(
            (line.x1, line.y1) == (anchor.x, anchor.y) or (line.x2, line.y2) == (anchor.x, anchor.y)
            for line in _lines(definition)
        ), anchor.name


def test_the_mixer_element_stays_inside_its_body() -> None:
    definition = _pfd_base("mixer.inline")
    element = [
        line
        for line in _lines(definition)
        if all(
            24.0 < x < 76.0 and 26.0 < y < 74.0 for x, y in ((line.x1, line.y1), (line.x2, line.y2))
        )
    ]

    # Exactly the three segments of the bent element, and every endpoint strictly
    # inside the body, so the body edge remains the glyph/piping boundary.
    assert len(element) == 3
    assert {point for line in element for point in ((line.x1, line.y1), (line.x2, line.y2))} == {
        (36.0, 36.0),
        (36.0, 52.0),
        (64.0, 48.0),
        (64.0, 64.0),
    }
    assert len(_bodies(definition)) == 1


def test_the_two_pfd_base_representations_are_distinct() -> None:
    # No shared equipment glyph: each family is its own geometry and its own
    # document, so a consumer can never substitute one for another.
    definitions = [_pfd_base(symbol_id) for symbol_id, _name, _document in PFD_BASE_SYMBOLS]

    assert len({definition.primitives for definition in definitions}) == 2
    assert len({render_symbol_svg(definition) for definition in definitions}) == 2
    assert len({definition.symbol_id for definition in definitions}) == 2
