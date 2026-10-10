"""Rendering and structural tests for the machine-rendered symbol library.

These tests pin the Issue #119 rendering contract: SVG is generated from a
definition deterministically, output is a restricted, themeable subset, anchors
are definition data rather than SVG inference, and the built-in representations
keep their structural shape, their neutral geometric anchors, and their asset
provenance. The catalogue spans two notation profiles (Issue #130), so lookups
resolve each representation by its explicit ``(notation_profile, symbol_id)``
identity.
"""

from __future__ import annotations

import dataclasses
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

import pytest

from deepplant.symbols import (
    SYMBOLS,
    AssetProvenance,
    Circle,
    Line,
    Polygon,
    StandardsReference,
    SymbolDefinition,
    render_symbol_svg,
)
from deepplant.symbols.profiles import (
    DEEPPLANT_DEFAULT_NOTATION_PROFILE,
    GENERIC_ISO_NOTATION_PROFILE,
)

CANONICAL_VIEW_BOX = "0 0 100 100"
ALLOWED_ELEMENT_NAMES = {"svg", "line", "circle", "polygon"}
ALLOWED_ROOT_ATTRIBUTES = {"viewBox", "fill", "stroke", "stroke-width"}
THEMEABLE_COLOR_VALUES = {"none", "currentColor"}
FORBIDDEN_ATTRIBUTES = {"href", "style", "class", "font-family", "onload"}

#: Every built-in graphical representation, as ``(notation_profile, symbol_id)``.
BUILTIN_REPRESENTATIONS = (
    (DEEPPLANT_DEFAULT_NOTATION_PROFILE, "fitting.restriction_orifice"),
    (DEEPPLANT_DEFAULT_NOTATION_PROFILE, "valve.ball"),
    (DEEPPLANT_DEFAULT_NOTATION_PROFILE, "valve.check"),
    (DEEPPLANT_DEFAULT_NOTATION_PROFILE, "valve.globe"),
    (GENERIC_ISO_NOTATION_PROFILE, "instrument.local"),
    (GENERIC_ISO_NOTATION_PROFILE, "pump.centrifugal"),
    (GENERIC_ISO_NOTATION_PROFILE, "valve.gate"),
)

#: The ``generic-iso`` subset, which the built-in convenience default also resolves.
GENERIC_ISO_IDS = ("instrument.local", "pump.centrifugal", "valve.gate")

ISO_10628_2 = "ISO 10628-2:2012"
ISO_15519_2 = "ISO 15519-2:2015"

#: The exact restriction-orifice document the re-authored project seed geometry
#: produces (seed D). Pinned so a contract change cannot silently alter geometry.
RESTRICTION_ORIFICE_DOCUMENT = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none" '
    'stroke="currentColor" stroke-width="2"><line x1="0" y1="50" x2="38" y2="50" />'
    '<line x1="38" y1="32" x2="38" y2="68" /><line x1="50" y1="20" x2="50" y2="43" />'
    '<line x1="50" y1="57" x2="50" y2="80" /><line x1="62" y1="32" x2="62" y2="68" />'
    '<line x1="62" y1="50" x2="100" y2="50" /></svg>\n'
)


def _builtin(notation_profile: str, symbol_id: str) -> SymbolDefinition:
    """Resolve one built-in representation explicitly by its full identity."""
    return SYMBOLS.get(symbol_id, notation_profile=notation_profile)


#: The exact gate-valve document the re-authored project seed geometry produces.
#: Pinned so a contract change cannot silently alter rendered geometry: the
#: geometry is DeepPlant-authored
#: (docs/dev/reference/symbol-seed-geometry.md, seed A), not restricted-derived.
GATE_VALVE_DOCUMENT = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none" '
    'stroke="currentColor" stroke-width="2"><line x1="0" y1="50" x2="28" y2="50" />'
    '<polygon points="28,34 28,66 50,50" /><polygon points="50,50 72,34 72,66" />'
    '<line x1="72" y1="50" x2="100" y2="50" /></svg>\n'
)

#: The exact #132 basic valve documents the independently authored project seed
#: geometry produces (seeds E/F/G). Pinned so a contract change cannot silently
#: alter geometry, and so the one filled mark each of globe/check carries - and the
#: ball's hollow circle - are visible in the pinned bytes.
GLOBE_VALVE_DOCUMENT = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none" '
    'stroke="currentColor" stroke-width="2"><line x1="0" y1="50" x2="28" y2="50" />'
    '<polygon points="28,34 28,66 50,50" /><polygon points="50,50 72,34 72,66" />'
    '<line x1="72" y1="50" x2="100" y2="50" />'
    '<circle cx="50" cy="50" r="8" fill="currentColor" /></svg>\n'
)

CHECK_VALVE_DOCUMENT = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none" '
    'stroke="currentColor" stroke-width="2"><line x1="0" y1="50" x2="28" y2="50" />'
    '<line x1="28" y1="34" x2="72" y2="34" /><line x1="72" y1="34" x2="72" y2="66" />'
    '<line x1="72" y1="66" x2="28" y2="66" /><line x1="28" y1="66" x2="28" y2="34" />'
    '<line x1="28" y1="34" x2="72" y2="66" /><line x1="72" y1="50" x2="100" y2="50" />'
    '<circle cx="28" cy="34" r="5" fill="currentColor" /></svg>\n'
)

BALL_VALVE_DOCUMENT = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none" '
    'stroke="currentColor" stroke-width="2"><line x1="0" y1="50" x2="28" y2="50" />'
    '<line x1="28" y1="34" x2="28" y2="66" /><line x1="28" y1="34" x2="38" y2="41" />'
    '<line x1="28" y1="66" x2="38" y2="59" /><line x1="62" y1="41" x2="72" y2="34" />'
    '<line x1="62" y1="59" x2="72" y2="66" />'
    '<line x1="72" y1="50" x2="100" y2="50" /><circle cx="50" cy="50" r="15" /></svg>\n'
)

#: The three #132 `deepplant-default` valve ids, with their pinned documents.
BASIC_VALVES = (
    ("valve.globe", GLOBE_VALVE_DOCUMENT),
    ("valve.check", CHECK_VALVE_DOCUMENT),
    ("valve.ball", BALL_VALVE_DOCUMENT),
)

#: Fragments that would prove a project/company tag or convention leaked into
#: base symbol geometry.
PROJECT_TEXT_FRAGMENTS = ("PIT", "TIT", "FIC", "FV-", "P-101", "DN", "SIS", "DCS", "YARA")


def _root(document: str) -> Element:
    return ElementTree.fromstring(document)


def _local_name(element: Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _elements(definition: SymbolDefinition, name: str) -> list[Element]:
    return [
        element
        for element in _root(render_symbol_svg(definition)).iter()
        if _local_name(element) == name
    ]


@pytest.mark.parametrize(("notation_profile", "symbol_id"), BUILTIN_REPRESENTATIONS)
def test_rendering_is_deterministic(notation_profile: str, symbol_id: str) -> None:
    definition = _builtin(notation_profile, symbol_id)

    assert render_symbol_svg(definition) == render_symbol_svg(definition)


@pytest.mark.parametrize(("notation_profile", "symbol_id"), BUILTIN_REPRESENTATIONS)
def test_a_rebuilt_definition_renders_identically(notation_profile: str, symbol_id: str) -> None:
    definition = _builtin(notation_profile, symbol_id)
    rebuilt = SymbolDefinition(
        symbol_id=definition.symbol_id,
        name=definition.name,
        category=definition.category,
        diagram_types=definition.diagram_types,
        notation_profile=definition.notation_profile,
        primitives=definition.primitives,
        anchors=definition.anchors,
        provenance=definition.provenance,
        standards=definition.standards,
        view_box=definition.view_box,
    )

    assert render_symbol_svg(rebuilt) == render_symbol_svg(definition)


def test_the_rendered_gate_valve_document_is_unchanged() -> None:
    assert render_symbol_svg(SYMBOLS.get("valve.gate")) == GATE_VALVE_DOCUMENT


def test_the_renderer_stays_notation_profile_agnostic() -> None:
    # Issue #125 keeps the renderer profile-agnostic: it renders the definition it is
    # given and never branches on `notation_profile`, so two definitions that differ
    # only in profile render identical geometry. Profile-specific geometry belongs in
    # distinct definitions, not in renderer conditionals.
    default = SymbolDefinition(
        symbol_id="valve.example",
        name="Example valve",
        category="valve",
        diagram_types=("pid",),
        notation_profile="deepplant-default",
        primitives=(Line(x1=0.0, y1=50.0, x2=100.0, y2=50.0),),
        anchors=(),
        provenance=AssetProvenance(origin="deepplant-original", license="AGPL-3.0-only"),
        standards=(),
    )
    generic = SymbolDefinition(
        symbol_id="valve.example",
        name="Example valve",
        category="valve",
        diagram_types=("pid",),
        notation_profile="generic-iso",
        primitives=(Line(x1=0.0, y1=50.0, x2=100.0, y2=50.0),),
        anchors=(),
        provenance=AssetProvenance(origin="deepplant-original", license="AGPL-3.0-only"),
        standards=(
            StandardsReference(standard="ISO 10628-2:2012", verification="candidate-alignment"),
        ),
    )

    assert render_symbol_svg(default) == render_symbol_svg(generic)


def test_every_registered_symbol_renders_a_well_formed_document() -> None:
    for definition in SYMBOLS.list():
        document = render_symbol_svg(definition)

        assert document.startswith("<svg ")
        assert document.endswith("\n")
        assert _local_name(_root(document)) == "svg"


def test_generated_documents_use_a_normalized_scalable_view_box() -> None:
    for definition in SYMBOLS.list():
        root = _root(render_symbol_svg(definition))

        assert root.get("viewBox") == CANONICAL_VIEW_BOX
        assert root.get("width") is None
        assert root.get("height") is None
        assert set(root.attrib) == ALLOWED_ROOT_ATTRIBUTES


def test_generated_documents_use_a_themeable_restricted_style() -> None:
    for definition in SYMBOLS.list():
        root = _root(render_symbol_svg(definition))

        assert root.get("fill") == "none"
        assert root.get("stroke") == "currentColor"


def test_generated_documents_contain_only_the_restricted_element_subset() -> None:
    for definition in SYMBOLS.list():
        for element in _root(render_symbol_svg(definition)).iter():
            name = _local_name(element)

            assert name in ALLOWED_ELEMENT_NAMES, f"unexpected element <{name}>"
            assert element.text is None or not element.text.strip()
            assert element.tail is None or not element.tail.strip()


def test_generated_documents_carry_no_external_or_active_content() -> None:
    for definition in SYMBOLS.list():
        for element in _root(render_symbol_svg(definition)).iter():
            for attribute_name, value in element.attrib.items():
                assert attribute_name not in FORBIDDEN_ATTRIBUTES, attribute_name
                assert "url(" not in value
                assert "javascript:" not in value
                assert not value.startswith("data:")
                assert not value.startswith("http")
                if attribute_name in {"fill", "stroke"}:
                    assert value in THEMEABLE_COLOR_VALUES, value


def test_generated_documents_carry_no_project_or_company_text() -> None:
    for definition in SYMBOLS.list():
        document = render_symbol_svg(definition)

        for fragment in PROJECT_TEXT_FRAGMENTS:
            assert fragment not in document, f"{fragment!r} leaked into {definition.symbol_id}"


# ---------------------------------------------------------------------------
# Structural contracts of the built-in representations
# ---------------------------------------------------------------------------


def test_restriction_orifice_contract() -> None:
    definition = SYMBOLS.get(
        "fitting.restriction_orifice",
        notation_profile=DEEPPLANT_DEFAULT_NOTATION_PROFILE,
    )

    assert definition.name == "Restriction orifice"
    assert definition.category == "fitting"
    assert definition.diagram_types == ("pid",)
    assert definition.notation_profile == DEEPPLANT_DEFAULT_NOTATION_PROFILE

    # Two neutral process anchors on the piping axis, with geometric orientations
    # only. No inlet/outlet or flow direction may be encoded (seed D).
    assert [
        (anchor.name, anchor.orientation, anchor.kind, anchor.x, anchor.y)
        for anchor in definition.anchors
    ] == [
        ("port_a", "west", "process", 0.0, 50.0),
        ("port_b", "east", "process", 100.0, 50.0),
    ]
    assert {anchor.name for anchor in definition.anchors}.isdisjoint({"inlet", "outlet"})

    # The exact DeepPlant-authored primitive tuple: continuous outer transverse
    # strokes frame a centered split restriction stroke; connection stubs stop at
    # the outer strokes. No circle or annotation primitive is part of this
    # representation (seed D).
    assert definition.primitives == (
        Line(x1=0.0, y1=50.0, x2=38.0, y2=50.0),
        Line(x1=38.0, y1=32.0, x2=38.0, y2=68.0),
        Line(x1=50.0, y1=20.0, x2=50.0, y2=43.0),
        Line(x1=50.0, y1=57.0, x2=50.0, y2=80.0),
        Line(x1=62.0, y1=32.0, x2=62.0, y2=68.0),
        Line(x1=62.0, y1=50.0, x2=100.0, y2=50.0),
    )
    assert [item for item in definition.primitives if isinstance(item, Circle)] == []


def test_the_rendered_restriction_orifice_document_is_unchanged() -> None:
    definition = SYMBOLS.get(
        "fitting.restriction_orifice",
        notation_profile=DEEPPLANT_DEFAULT_NOTATION_PROFILE,
    )

    assert render_symbol_svg(definition) == RESTRICTION_ORIFICE_DOCUMENT


def test_the_restriction_orifice_records_no_standards_relationship() -> None:
    # `deepplant-default` makes no ISO/ISA/PIP conformance claim, so the correct
    # state is that no StandardsReference is recorded at all — not a `reference`
    # relationship. `—` is the absence of a recorded relationship, not a
    # verification state, and no standards family is invented to populate it
    # (ADR-0007).
    definition = SYMBOLS.get(
        "fitting.restriction_orifice",
        notation_profile=DEEPPLANT_DEFAULT_NOTATION_PROFILE,
    )

    assert definition.standards == ()


def test_gate_valve_contract() -> None:
    definition = SYMBOLS.get("valve.gate")

    assert definition.name == "Gate valve"
    assert definition.category == "valve"
    assert definition.notation_profile == "generic-iso"
    assert definition.diagram_types == ("pid",)

    # Neutral graphical connection ports with geometric orientations. A generic
    # gate valve is not inherently an inlet/outlet device, so neither the names
    # nor a flow direction may be encoded here.
    assert [
        (anchor.name, anchor.orientation, anchor.kind, anchor.x, anchor.y)
        for anchor in definition.anchors
    ] == [
        ("port_a", "west", "process", 0.0, 50.0),
        ("port_b", "east", "process", 100.0, 50.0),
    ]
    assert {anchor.name for anchor in definition.anchors}.isdisjoint({"inlet", "outlet"})

    # The connectable body is two triangles meeting apex to apex on the axis,
    # authored from the DeepPlant project seed geometry (seed A).
    assert [item for item in definition.primitives if isinstance(item, Polygon)] == [
        Polygon(points=((28.0, 34.0), (28.0, 66.0), (50.0, 50.0))),
        Polygon(points=((50.0, 50.0), (72.0, 34.0), (72.0, 66.0))),
    ]


def test_centrifugal_pump_contract() -> None:
    definition = SYMBOLS.get("pump.centrifugal")

    assert definition.name == "Centrifugal pump"
    assert definition.category == "equipment"
    assert definition.diagram_types == ("pfd", "pid")

    # Semantically named pump nozzles whose geometry stays purely graphical: the
    # name carries the engineering meaning, the orientation only says where the
    # line leaves the symbol.
    assert [
        (anchor.name, anchor.orientation, anchor.kind, anchor.x, anchor.y)
        for anchor in definition.anchors
    ] == [
        ("suction", "west", "process", 0.0, 50.0),
        ("discharge", "east", "process", 100.0, 50.0),
    ]

    # One circular casing of radius 24, drawn on the canonical normalized view box
    # (seed B).
    assert [item for item in definition.primitives if isinstance(item, Circle)] == [
        Circle(cx=50.0, cy=50.0, r=24.0)
    ]


def test_local_field_instrument_contract() -> None:
    definition = SYMBOLS.get("instrument.local")

    assert definition.category == "instrument"
    assert definition.diagram_types == ("pid",)

    # Exactly one base anchor: the process tap that attaches the reusable graphic
    # to the process. The base graphic must not assume a signal connection,
    # because only some instrument functions have one.
    assert [(anchor.name, anchor.orientation, anchor.kind) for anchor in definition.anchors] == [
        ("tap", "south", "process")
    ]


def test_the_local_field_instrument_has_no_unconditional_signal_anchor() -> None:
    definition = SYMBOLS.get("instrument.local")

    assert len(definition.anchors) == 1
    assert [anchor for anchor in definition.anchors if anchor.kind == "signal"] == []
    assert {anchor.name for anchor in definition.anchors}.isdisjoint({"signal"})


def test_the_local_field_instrument_stays_a_reusable_base_graphic() -> None:
    definition = SYMBOLS.get("instrument.local")

    # A field-mounted instrument is a plain circle (seed C): no additional graphics
    # inside it, so the representation stays reusable for any instrument function.
    assert [item for item in definition.primitives if isinstance(item, Circle)] == [
        Circle(cx=50.0, cy=40.0, r=20.0)
    ]
    assert len(_elements(definition, "circle")) == 1
    assert _elements(definition, "text") == []


# ---------------------------------------------------------------------------
# The #132 basic P&ID valves (deepplant-default)
# ---------------------------------------------------------------------------


def _basic_valve(symbol_id: str) -> SymbolDefinition:
    """Resolve one #132 valve representation by its explicit identity."""
    return SYMBOLS.get(symbol_id, notation_profile=DEEPPLANT_DEFAULT_NOTATION_PROFILE)


@pytest.mark.parametrize(("symbol_id", "document"), BASIC_VALVES)
def test_the_rendered_basic_valve_document_is_unchanged(symbol_id: str, document: str) -> None:
    assert render_symbol_svg(_basic_valve(symbol_id)) == document


@pytest.mark.parametrize(("symbol_id", "_document"), BASIC_VALVES)
def test_basic_valve_identity_contract(symbol_id: str, _document: str) -> None:
    definition = _basic_valve(symbol_id)

    assert definition.name in {"Globe valve", "Check valve", "Ball valve"}
    assert definition.category == "valve"
    assert definition.diagram_types == ("pid",)
    assert definition.notation_profile == DEEPPLANT_DEFAULT_NOTATION_PROFILE
    # `deepplant-default` makes no conformance claim, so no standards relationship is
    # recorded and none is invented; the coverage matrix's concept-level ISO
    # reference direction is not a correspondence for this geometry (ADR-0007).
    assert definition.standards == ()
    assert definition.provenance == AssetProvenance(
        origin="deepplant-original", license="AGPL-3.0-only"
    )


@pytest.mark.parametrize(("symbol_id", "_document"), BASIC_VALVES)
def test_basic_valve_uses_neutral_process_anchors(symbol_id: str, _document: str) -> None:
    definition = _basic_valve(symbol_id)

    # Neutral two-port graphical connection points with geometric orientations only.
    # A check valve's glyph is asymmetric, but that is a recognizability mark, not a
    # flow-direction contract: no `inlet`/`outlet`/`upstream`/`downstream` name and
    # no flow-direction field is encoded.
    assert [
        (anchor.name, anchor.orientation, anchor.kind, anchor.x, anchor.y)
        for anchor in definition.anchors
    ] == [
        ("port_a", "west", "process", 0.0, 50.0),
        ("port_b", "east", "process", 100.0, 50.0),
    ]
    assert {anchor.name for anchor in definition.anchors}.isdisjoint(
        {"inlet", "outlet", "upstream", "downstream"}
    )
    assert "flow_direction" not in {
        field.name for field in dataclasses.fields(definition.anchors[0])
    }


def test_valve_globe_contract() -> None:
    definition = _basic_valve("valve.globe")

    assert definition.name == "Globe valve"
    # Two-triangle body on the axis with a small solid central disc as the variant
    # mark, and the disc drawn last so it reads over the apex (seed E).
    assert definition.primitives == (
        Line(x1=0.0, y1=50.0, x2=28.0, y2=50.0),
        Polygon(points=((28.0, 34.0), (28.0, 66.0), (50.0, 50.0))),
        Polygon(points=((50.0, 50.0), (72.0, 34.0), (72.0, 66.0))),
        Line(x1=72.0, y1=50.0, x2=100.0, y2=50.0),
        Circle(cx=50.0, cy=50.0, r=8.0, filled=True),
    )


def test_valve_check_contract() -> None:
    definition = _basic_valve("valve.check")

    assert definition.name == "Check valve"
    # Rectangular body with a corner-to-corner closing stroke and a small solid
    # hinge peg at one corner (seed F). The asymmetry is the valve's recognizability,
    # never its anchor semantics.
    assert definition.primitives == (
        Line(x1=0.0, y1=50.0, x2=28.0, y2=50.0),
        Line(x1=28.0, y1=34.0, x2=72.0, y2=34.0),
        Line(x1=72.0, y1=34.0, x2=72.0, y2=66.0),
        Line(x1=72.0, y1=66.0, x2=28.0, y2=66.0),
        Line(x1=28.0, y1=66.0, x2=28.0, y2=34.0),
        Line(x1=28.0, y1=34.0, x2=72.0, y2=66.0),
        Line(x1=72.0, y1=50.0, x2=100.0, y2=50.0),
        Circle(cx=28.0, cy=34.0, r=5.0, filled=True),
    )


def test_valve_ball_contract() -> None:
    definition = _basic_valve("valve.ball")

    assert definition.name == "Ball valve"
    # The hollow central circle is a structural body element. Four side-body
    # diagonals terminate at its circumference, preserving its clean interior
    # (seed G); the hollow outline distinguishes it from the globe's solid disc.
    assert definition.primitives == (
        Line(x1=0.0, y1=50.0, x2=28.0, y2=50.0),
        Line(x1=28.0, y1=34.0, x2=28.0, y2=66.0),
        Line(x1=28.0, y1=34.0, x2=38.0, y2=41.0),
        Line(x1=28.0, y1=66.0, x2=38.0, y2=59.0),
        Line(x1=62.0, y1=41.0, x2=72.0, y2=34.0),
        Line(x1=62.0, y1=59.0, x2=72.0, y2=66.0),
        Line(x1=72.0, y1=50.0, x2=100.0, y2=50.0),
        Circle(cx=50.0, cy=50.0, r=15.0),
    )
    assert [item for item in definition.primitives if isinstance(item, Circle)] == [
        Circle(cx=50.0, cy=50.0, r=15.0)
    ]
    # Every side-body diagonal ends on the central circle, never inside it.
    body_diagonals = tuple(
        primitive for primitive in definition.primitives[2:6] if isinstance(primitive, Line)
    )
    assert len(body_diagonals) == 4
    assert [
        (line.x2, line.y2) if line.x1 < 50.0 else (line.x1, line.y1) for line in body_diagonals
    ] == [(38.0, 41.0), (38.0, 59.0), (62.0, 41.0), (62.0, 59.0)]


def test_only_the_globe_and_check_valves_use_a_filled_circle() -> None:
    # The `filled` capability exists for a concrete requirement (the globe disc and
    # the check hinge), so YAGNI is pinned: no other representation fills a circle.
    for definition in SYMBOLS.list():
        filled = [
            item for item in definition.primitives if isinstance(item, Circle) and item.filled
        ]
        if definition.symbol_id == "valve.globe":
            assert filled == [Circle(cx=50.0, cy=50.0, r=8.0, filled=True)]
        elif definition.symbol_id == "valve.check":
            assert filled == [Circle(cx=28.0, cy=34.0, r=5.0, filled=True)]
        else:
            assert filled == [], definition.symbol_id


def test_a_hollow_circle_renders_no_child_level_fill() -> None:
    circles = _elements(_basic_valve("valve.ball"), "circle")

    assert len(circles) == 1
    assert circles[0].get("fill") is None
    assert set(circles[0].attrib) == {"cx", "cy", "r"}


def test_a_filled_circle_renders_only_the_themeable_current_colour_fill() -> None:
    circles = _elements(_basic_valve("valve.globe"), "circle")

    assert len(circles) == 1
    assert circles[0].get("fill") == "currentColor"
    # Exactly one extra attribute, and only the themeable `currentColor`: no literal
    # colour, CSS, `style`, or `class` is introduced by the capability.
    assert set(circles[0].attrib) == {"cx", "cy", "r", "fill"}


# ---------------------------------------------------------------------------
# Asset provenance
# ---------------------------------------------------------------------------


def test_every_built_in_symbol_records_deepplant_original_provenance() -> None:
    for definition in SYMBOLS.list():
        assert definition.provenance.origin == "deepplant-original"
        assert definition.provenance.license == "AGPL-3.0-only"


def test_provenance_and_standards_correspondence_are_independent() -> None:
    for definition in SYMBOLS.list():
        # A definition must carry valid asset provenance regardless of whether it
        # records a standards relationship at all.
        assert definition.provenance.origin
        assert definition.provenance.license
        assert all(reference.standard for reference in definition.standards)


# ---------------------------------------------------------------------------
# Standards relationship
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("symbol_id", "standard"),
    [
        ("valve.gate", ISO_10628_2),
        ("pump.centrifugal", ISO_10628_2),
        ("instrument.local", ISO_15519_2),
    ],
)
def test_each_symbol_records_the_standard_it_is_intended_to_align_with(
    symbol_id: str, standard: str
) -> None:
    definition = SYMBOLS.get(symbol_id)

    assert len(definition.standards) == 1
    # Canonical and conservative: the geometry is DeepPlant-authored project seed
    # geometry that is *intended* to correspond to the named standard, but no human
    # has compared it against an authorized copy. `candidate-alignment` claims no
    # human verification, and it is neither `reference` nor `human-verified`
    # (ADR-0007).
    assert definition.standards[0].standard == standard
    assert definition.standards[0].verification == "candidate-alignment"


@pytest.mark.parametrize(("notation_profile", "symbol_id"), BUILTIN_REPRESENTATIONS)
def test_no_symbol_claims_human_verification(notation_profile: str, symbol_id: str) -> None:
    for reference in _builtin(notation_profile, symbol_id).standards:
        assert reference.verification != "human-verified"


@pytest.mark.parametrize(("notation_profile", "symbol_id"), BUILTIN_REPRESENTATIONS)
def test_no_restricted_derived_standards_detail_is_recorded(
    notation_profile: str, symbol_id: str
) -> None:
    # A locator, the standard's own name for a representation, or a verifier may
    # only be recorded from a permitted source or by a human verifier; neither
    # exists yet, so all stay unrecorded rather than carrying restricted-derived
    # detail or falsely implying a human check.
    for reference in _builtin(notation_profile, symbol_id).standards:
        assert reference.locator is None
        assert reference.name is None
        assert reference.verified_by is None
        assert reference.verified_on is None


@pytest.mark.parametrize("symbol_id", GENERIC_ISO_IDS)
def test_every_generic_iso_symbol_declares_the_generic_iso_notation_profile(
    symbol_id: str,
) -> None:
    # Issue #130 adds the first `deepplant-default` representation but migrates no
    # existing geometry: the three legacy built-in representations all stay
    # `generic-iso`, and only the restriction orifice is `deepplant-default`.
    assert SYMBOLS.get(symbol_id).notation_profile == "generic-iso"


def test_the_builtin_catalogue_spans_two_notation_profiles() -> None:
    profiles = {definition.notation_profile for definition in SYMBOLS.list()}

    assert profiles == {DEEPPLANT_DEFAULT_NOTATION_PROFILE, GENERIC_ISO_NOTATION_PROFILE}
