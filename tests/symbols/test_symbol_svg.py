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
    (DEEPPLANT_DEFAULT_NOTATION_PROFILE, "compressor.general"),
    (DEEPPLANT_DEFAULT_NOTATION_PROFILE, "fitting.reducer.concentric"),
    (DEEPPLANT_DEFAULT_NOTATION_PROFILE, "fitting.reducer.eccentric"),
    (DEEPPLANT_DEFAULT_NOTATION_PROFILE, "fitting.restriction_orifice"),
    (DEEPPLANT_DEFAULT_NOTATION_PROFILE, "mixer.inline"),
    (DEEPPLANT_DEFAULT_NOTATION_PROFILE, "reactor_burner.general"),
    (DEEPPLANT_DEFAULT_NOTATION_PROFILE, "valve.ball"),
    (DEEPPLANT_DEFAULT_NOTATION_PROFILE, "valve.check"),
    (DEEPPLANT_DEFAULT_NOTATION_PROFILE, "valve.globe"),
    (DEEPPLANT_DEFAULT_NOTATION_PROFILE, "valve.safety_relief.angle"),
    (DEEPPLANT_DEFAULT_NOTATION_PROFILE, "valve.safety_relief.straight"),
    (DEEPPLANT_DEFAULT_NOTATION_PROFILE, "valve.three_way"),
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
    'stroke="currentColor" stroke-width="2"><line x1="0" y1="50" x2="18" y2="50" />'
    '<line x1="18" y1="34" x2="18" y2="66" /><line x1="18" y1="34" x2="38" y2="41" />'
    '<line x1="18" y1="66" x2="38" y2="59" /><line x1="82" y1="34" x2="82" y2="66" />'
    '<line x1="62" y1="41" x2="82" y2="34" />'
    '<line x1="62" y1="59" x2="82" y2="66" />'
    '<line x1="82" y1="50" x2="100" y2="50" /><circle cx="50" cy="50" r="15" /></svg>\n'
)

#: The three #132 `deepplant-default` valve ids, with their pinned documents.
BASIC_VALVES = (
    ("valve.globe", GLOBE_VALVE_DOCUMENT),
    ("valve.check", CHECK_VALVE_DOCUMENT),
    ("valve.ball", BALL_VALVE_DOCUMENT),
)

#: Fragments that would prove a project/company tag or convention leaked into
#: The exact #135 documents the independently authored project seed geometry
#: produces (seeds H/I/J/K/L). Pinned so a contract change cannot silently alter
#: geometry, and so each representation's real structural distinction is visible in
#: the pinned bytes: the three-port convergence, the spring-loaded indication on both
#: safety/relief forms, and the two-sloping-side versus one-flat-side reducer body.
THREE_WAY_VALVE_DOCUMENT = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none" '
    'stroke="currentColor" stroke-width="2"><line x1="0" y1="40" x2="24" y2="40" />'
    '<polygon points="24,22 24,58 50,40" /><polygon points="76,22 76,58 50,40" />'
    '<polygon points="32,74 68,74 50,40" />'
    '<line x1="76" y1="40" x2="100" y2="40" />'
    '<line x1="50" y1="74" x2="50" y2="100" /></svg>\n'
)

SAFETY_RELIEF_VALVE_STRAIGHT_DOCUMENT = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none" '
    'stroke="currentColor" stroke-width="2"><line x1="0" y1="60" x2="28" y2="60" />'
    '<polygon points="28,44 28,76 50,60" /><polygon points="50,60 72,44 72,76" />'
    '<line x1="72" y1="60" x2="100" y2="60" /><line x1="50" y1="60" x2="50" y2="16" />'
    '<line x1="44" y1="40" x2="56" y2="32" /><line x1="44" y1="32" x2="56" y2="24" />'
    '<line x1="44" y1="24" x2="56" y2="16" /></svg>\n'
)

SAFETY_RELIEF_VALVE_ANGLE_DOCUMENT = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none" '
    'stroke="currentColor" stroke-width="2"><line x1="0" y1="48" x2="24" y2="48" />'
    '<polygon points="24,28 24,64 50,48" /><polygon points="32,80 68,80 50,48" />'
    '<line x1="50" y1="80" x2="50" y2="100" /><line x1="50" y1="48" x2="50" y2="18" />'
    '<line x1="44" y1="36" x2="56" y2="28" /><line x1="44" y1="28" x2="56" y2="20" />'
    '<line x1="44" y1="20" x2="56" y2="12" /></svg>\n'
)

CONCENTRIC_REDUCER_DOCUMENT = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none" '
    'stroke="currentColor" stroke-width="2"><line x1="0" y1="50" x2="25" y2="50" />'
    '<polygon points="25,14 75,32 75,68 25,86" />'
    '<line x1="75" y1="50" x2="100" y2="50" /></svg>\n'
)

ECCENTRIC_REDUCER_DOCUMENT = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none" '
    'stroke="currentColor" stroke-width="2"><line x1="0" y1="32" x2="25" y2="32" />'
    '<polygon points="25,14 75,14 75,50 25,86" />'
    '<line x1="75" y1="32" x2="100" y2="32" /></svg>\n'
)

#: The reusable spring-loaded indication every safety/relief form carries, drawn on
#: the body axis above the junction: the stem plus its three load marks. Shared
#: verbatim by both forms, so the mark - not the body orientation - identifies the
#: device family.
SAFETY_RELIEF_SPRING_MARKS = (
    Line(x1=44.0, y1=40.0, x2=56.0, y2=32.0),
    Line(x1=44.0, y1=32.0, x2=56.0, y2=24.0),
    Line(x1=44.0, y1=24.0, x2=56.0, y2=16.0),
)

#: The five #135 `deepplant-default` base representations, as
#: ``(symbol_id, name, category, document)``.
REMAINING_MVP_SYMBOLS = (
    ("valve.three_way", "Three-way valve", "valve", THREE_WAY_VALVE_DOCUMENT),
    (
        "valve.safety_relief.straight",
        "Safety/relief valve, straight",
        "valve",
        SAFETY_RELIEF_VALVE_STRAIGHT_DOCUMENT,
    ),
    (
        "valve.safety_relief.angle",
        "Safety/relief valve, angle",
        "valve",
        SAFETY_RELIEF_VALVE_ANGLE_DOCUMENT,
    ),
    ("fitting.reducer.concentric", "Concentric reducer", "fitting", CONCENTRIC_REDUCER_DOCUMENT),
    ("fitting.reducer.eccentric", "Eccentric reducer", "fitting", ECCENTRIC_REDUCER_DOCUMENT),
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
        Line(x1=0.0, y1=50.0, x2=18.0, y2=50.0),
        Line(x1=18.0, y1=34.0, x2=18.0, y2=66.0),
        Line(x1=18.0, y1=34.0, x2=38.0, y2=41.0),
        Line(x1=18.0, y1=66.0, x2=38.0, y2=59.0),
        Line(x1=82.0, y1=34.0, x2=82.0, y2=66.0),
        Line(x1=62.0, y1=41.0, x2=82.0, y2=34.0),
        Line(x1=62.0, y1=59.0, x2=82.0, y2=66.0),
        Line(x1=82.0, y1=50.0, x2=100.0, y2=50.0),
        Circle(cx=50.0, cy=50.0, r=15.0),
    )
    assert [item for item in definition.primitives if isinstance(item, Circle)] == [
        Circle(cx=50.0, cy=50.0, r=15.0)
    ]
    # Every side-body diagonal ends on the central circle, never inside it.
    body_diagonals = tuple(
        primitive
        for primitive in definition.primitives[2:7]
        if isinstance(primitive, Line) and primitive.x1 != primitive.x2
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
# The #135 remaining MVP base P&ID representations (deepplant-default)
# ---------------------------------------------------------------------------


def _remaining(symbol_id: str) -> SymbolDefinition:
    """Resolve one #135 representation by its explicit identity."""
    return SYMBOLS.get(symbol_id, notation_profile=DEEPPLANT_DEFAULT_NOTATION_PROFILE)


@pytest.mark.parametrize(("symbol_id", "_name", "_category", "document"), REMAINING_MVP_SYMBOLS)
def test_the_rendered_remaining_mvp_symbol_document_is_unchanged(
    symbol_id: str, _name: str, _category: str, document: str
) -> None:
    assert render_symbol_svg(_remaining(symbol_id)) == document


@pytest.mark.parametrize(("symbol_id", "name", "category", "_document"), REMAINING_MVP_SYMBOLS)
def test_remaining_mvp_symbol_identity_contract(
    symbol_id: str, name: str, category: str, _document: str
) -> None:
    definition = _remaining(symbol_id)

    assert definition.name == name
    assert definition.category == category
    assert definition.diagram_types == ("pid",)
    assert definition.notation_profile == DEEPPLANT_DEFAULT_NOTATION_PROFILE
    # `deepplant-default` makes no conformance claim, so no standards relationship is
    # recorded and none is invented to populate the field (ADR-0007). A14 and A16
    # record none even though the coverage matrix names a concept-level ISO reference
    # direction for them: that direction is not a correspondence for this geometry,
    # and a relief set pressure is authored document data (D04), never base geometry.
    assert definition.standards == ()
    assert definition.provenance == AssetProvenance(
        origin="deepplant-original", license="AGPL-3.0-only"
    )


@pytest.mark.parametrize(("symbol_id", "_name", "_category", "_document"), REMAINING_MVP_SYMBOLS)
def test_remaining_mvp_symbols_use_neutral_process_anchors(
    symbol_id: str, _name: str, _category: str, _document: str
) -> None:
    definition = _remaining(symbol_id)

    # Every port is a neutral graphical connection point, so neither a bent body, a
    # third port, nor an asymmetric reducer offset silently becomes process-flow
    # semantics: no `inlet`/`outlet`/`common`/`upstream`/`downstream` name is encoded
    # and no flow-direction field exists on the anchor.
    assert {anchor.name for anchor in definition.anchors}.isdisjoint(
        {"inlet", "outlet", "common", "upstream", "downstream"}
    )
    assert all(anchor.kind == "process" for anchor in definition.anchors)
    assert all(anchor.orientation for anchor in definition.anchors)
    assert "flow_direction" not in {
        field.name for field in dataclasses.fields(definition.anchors[0])
    }


def test_no_variant_selector_was_added_to_the_definition_model() -> None:
    # A14 and A16 are each one Core requirement whose reviewed notation has two forms.
    # #135 models each form as its own definition, so the definition model gains no
    # `variant`, `selector`, `style`, or `option` field and no variant framework: the
    # forms are distinguished by their real geometry.
    assert {field.name for field in dataclasses.fields(SymbolDefinition)} == {
        "symbol_id",
        "name",
        "category",
        "diagram_types",
        "notation_profile",
        "primitives",
        "anchors",
        "provenance",
        "standards",
        "view_box",
    }


def test_the_remaining_mvp_symbols_add_no_new_primitive_capability() -> None:
    # #135 needed no renderer, primitive, or styling expansion: every new body, taper,
    # and spring mark is an existing `Line` or `Polygon`.
    for symbol_id, _name, _category, _document in REMAINING_MVP_SYMBOLS:
        definition = _remaining(symbol_id)

        assert all(isinstance(item, Line | Polygon) for item in definition.primitives), symbol_id


def test_three_way_valve_contract() -> None:
    definition = _remaining("valve.three_way")

    assert definition.name == "Three-way valve"
    # Three triangular body halves meeting at one junction point, so the third
    # connection is real body geometry and not a mark painted on a two-port bowtie
    # (seed H). The three stubs are DeepPlant's connection representation of the
    # adjacent pipeline.
    assert definition.primitives == (
        Line(x1=0.0, y1=40.0, x2=24.0, y2=40.0),
        Polygon(points=((24.0, 22.0), (24.0, 58.0), (50.0, 40.0))),
        Polygon(points=((76.0, 22.0), (76.0, 58.0), (50.0, 40.0))),
        Polygon(points=((32.0, 74.0), (68.0, 74.0), (50.0, 40.0))),
        Line(x1=76.0, y1=40.0, x2=100.0, y2=40.0),
        Line(x1=50.0, y1=74.0, x2=50.0, y2=100.0),
    )


def test_the_three_way_valve_bodies_meet_at_one_junction() -> None:
    definition = _remaining("valve.three_way")
    bodies = [item for item in definition.primitives if isinstance(item, Polygon)]

    # Exactly three bodies sharing exactly one point is what makes this a three-port
    # body; no body overlaps another and none is a mark on a completed glyph.
    assert len(bodies) == 3
    for body in bodies:
        assert (50.0, 40.0) in body.points


def test_the_three_way_valve_exposes_three_neutral_process_ports() -> None:
    definition = _remaining("valve.three_way")

    # One port per body, named neutrally: which path is open is a document or
    # operating state, not a graphical property of the reusable base representation.
    assert [
        (anchor.name, anchor.orientation, anchor.kind, anchor.x, anchor.y)
        for anchor in definition.anchors
    ] == [
        ("port_a", "west", "process", 0.0, 40.0),
        ("port_b", "east", "process", 100.0, 40.0),
        ("port_c", "south", "process", 50.0, 100.0),
    ]


def test_straight_safety_relief_valve_contract() -> None:
    definition = _remaining("valve.safety_relief.straight")

    # Straight form: both process connections stay on one axis, and the spring-loaded
    # indication sits on the body's perpendicular stem (seed I).
    assert definition.primitives == (
        Line(x1=0.0, y1=60.0, x2=28.0, y2=60.0),
        Polygon(points=((28.0, 44.0), (28.0, 76.0), (50.0, 60.0))),
        Polygon(points=((50.0, 60.0), (72.0, 44.0), (72.0, 76.0))),
        Line(x1=72.0, y1=60.0, x2=100.0, y2=60.0),
        Line(x1=50.0, y1=60.0, x2=50.0, y2=16.0),
        Line(x1=44.0, y1=40.0, x2=56.0, y2=32.0),
        Line(x1=44.0, y1=32.0, x2=56.0, y2=24.0),
        Line(x1=44.0, y1=24.0, x2=56.0, y2=16.0),
    )
    assert [(anchor.orientation, anchor.x, anchor.y) for anchor in definition.anchors] == [
        ("west", 0.0, 60.0),
        ("east", 100.0, 60.0),
    ]


def test_angle_safety_relief_valve_contract() -> None:
    definition = _remaining("valve.safety_relief.angle")

    # Angle form: the second process connection leaves the body orthogonally instead
    # of continuing the axis, and the spring indication is drawn on the junction so it
    # reads as the valve's stem and load (seed J). This is a real connection-topology
    # difference, not a rotated straight form.
    assert definition.primitives == (
        Line(x1=0.0, y1=48.0, x2=24.0, y2=48.0),
        Polygon(points=((24.0, 28.0), (24.0, 64.0), (50.0, 48.0))),
        Polygon(points=((32.0, 80.0), (68.0, 80.0), (50.0, 48.0))),
        Line(x1=50.0, y1=80.0, x2=50.0, y2=100.0),
        Line(x1=50.0, y1=48.0, x2=50.0, y2=18.0),
        Line(x1=44.0, y1=36.0, x2=56.0, y2=28.0),
        Line(x1=44.0, y1=28.0, x2=56.0, y2=20.0),
        Line(x1=44.0, y1=20.0, x2=56.0, y2=12.0),
    )
    assert [(anchor.orientation, anchor.x, anchor.y) for anchor in definition.anchors] == [
        ("west", 0.0, 48.0),
        ("south", 50.0, 100.0),
    ]


def test_the_safety_relief_forms_share_the_spring_indication_but_not_the_topology() -> None:
    straight = _remaining("valve.safety_relief.straight")
    angle = _remaining("valve.safety_relief.angle")

    # A14 is one Core requirement with two reviewed forms, so the pair is two
    # independent definitions: different ids, different names, and a genuinely
    # different second connection (collinear east versus orthogonal south). The angle
    # form therefore cannot be a rotation of the straight form.
    assert straight.symbol_id != angle.symbol_id
    assert straight.name != angle.name
    assert {(anchor.x, anchor.y) for anchor in straight.anchors} == {(0.0, 60.0), (100.0, 60.0)}
    assert {(anchor.x, anchor.y) for anchor in angle.anchors} == {(0.0, 48.0), (50.0, 100.0)}

    # The reusable device mark is the same on both forms: a stem on the body junction
    # plus three parallel load marks crossing it. The mark is what identifies a
    # safety/relief valve, so no set pressure, tag, or annotation carries it.
    for definition in (straight, angle):
        lines = [item for item in definition.primitives if isinstance(item, Line)]
        marks = [line for line in lines if line.x1 != line.x2 and line.y1 != line.y2]

        assert len(marks) == 3
        assert all(line.x2 - line.x1 == 12.0 for line in marks)
        assert all(line.y1 - line.y2 == 8.0 for line in marks)
        # Evenly spaced load marks, crossing a stem that starts at the body junction.
        assert [line.y1 for line in marks] == [
            marks[0].y1 - 8.0 * index for index in range(len(marks))
        ]
        assert any(line.x1 == line.x2 == 50.0 and line.y1 in {60.0, 48.0} for line in lines)


def _reducer_body(symbol_id: str) -> tuple[tuple[float, float], ...]:
    """Resolve one reducer form's single body outline, read from the definition."""
    polygons = [item for item in _remaining(symbol_id).primitives if isinstance(item, Polygon)]

    assert len(polygons) == 1, symbol_id
    return polygons[0].points


def _body_sides(points: tuple[tuple[float, float], ...]) -> list[tuple[float, float]]:
    """Each body side as ``(run, rise)``, pairing consecutive vertices and closing."""
    return [
        (
            points[(index + 1) % len(points)][0] - points[index][0],
            points[(index + 1) % len(points)][1] - points[index][1],
        )
        for index in range(len(points))
    ]


def _body_face(points: tuple[tuple[float, float], ...], x: float) -> tuple[float, float]:
    """The end face at ``x`` as ``(lower, higher)`` y."""
    face = sorted(y for point_x, y in points if point_x == x)

    assert len(face) == 2, x
    return (face[0], face[1])


def test_concentric_reducer_contract() -> None:
    definition = _remaining("fitting.reducer.concentric")

    assert definition.name == "Concentric reducer"
    assert definition.category == "fitting"
    # One polygon tapering symmetrically about the process axis, so both connection
    # faces stay centred on the same axis (seed K).
    assert definition.primitives == (
        Line(x1=0.0, y1=50.0, x2=25.0, y2=50.0),
        Polygon(points=((25.0, 14.0), (75.0, 32.0), (75.0, 68.0), (25.0, 86.0))),
        Line(x1=75.0, y1=50.0, x2=100.0, y2=50.0),
    )


def test_eccentric_reducer_contract() -> None:
    definition = _remaining("fitting.reducer.eccentric")

    assert definition.name == "Eccentric reducer"
    assert definition.category == "fitting"
    # One polygon whose flat side runs parallel to the process axis while the opposite
    # side carries the whole reduction, so the one-sided offset is visible (seed L).
    assert definition.primitives == (
        Line(x1=0.0, y1=32.0, x2=25.0, y2=32.0),
        Polygon(points=((25.0, 14.0), (75.0, 14.0), (75.0, 50.0), (25.0, 86.0))),
        Line(x1=75.0, y1=32.0, x2=100.0, y2=32.0),
    )
    # Both stubs leave on the same level connection axis, the centre line of the smaller
    # east face, so the anchors are collinear and a line runs straight through; the
    # eccentricity is the larger end's offset about that axis, not an anchor offset.
    assert [(anchor.orientation, anchor.x, anchor.y) for anchor in definition.anchors] == [
        ("west", 0.0, 32.0),
        ("east", 100.0, 32.0),
    ]


def test_the_two_sloping_side_reducer_is_two_end_faces_between_two_slopes() -> None:
    sides = _body_sides(_reducer_body("fitting.reducer.concentric"))

    # The two-sloping-side form is a four-sided outline: a larger vertical end face, a
    # smaller vertical end face, and two sloping sides that carry the whole reduction
    # between them, so no long body side is horizontal (seed K).
    assert len(sides) == 4
    assert len([side for side in sides if side[0] == 0.0]) == 2
    assert len([side for side in sides if side[0] != 0.0 and side[1] != 0.0]) == 2
    assert all(side[1] != 0.0 for side in sides)


def test_the_one_flat_side_reducer_is_two_end_faces_a_flat_edge_and_a_slope() -> None:
    points = _reducer_body("fitting.reducer.eccentric")
    sides = _body_sides(points)

    # The one-flat-side form is a four-sided outline: a larger vertical end face, a
    # smaller vertical end face, one long horizontal side, and one long sloping side
    # (seed L).
    assert len(sides) == 4
    assert len([side for side in sides if side[0] == 0.0]) == 2
    flat = [side for side in sides if side[0] != 0.0 and side[1] == 0.0]
    sloping = [side for side in sides if side[0] != 0.0 and side[1] != 0.0]
    assert len(flat) == 1
    assert len(sloping) == 1

    # The flat side spans both end faces at the larger end's size and stays parallel to
    # the process axis, while the single sloping side carries the whole reduction in
    # one steep diagonal.
    body_length = 75.0 - 25.0
    west_lower, west_higher = _body_face(points, 25.0)
    east_lower, east_higher = _body_face(points, 75.0)
    assert abs(flat[0][0]) == body_length
    assert abs(sloping[0][0]) == body_length
    assert abs(sloping[0][1]) == (west_higher - west_lower) - (east_higher - east_lower)
    assert abs(sloping[0][1]) > abs(flat[0][1])


def test_the_reducer_bodies_read_as_a_tall_compact_taper() -> None:
    # Both reducer forms were re-authored after an operator visual review found the
    # first authored pass too long and too shallow. The larger end is the visually
    # dominant face, the smaller end is about half its height and still reads as a face
    # rather than as a line, and the outline is taller than it is long, so the reduction
    # is steep instead of a shallow horizontal transition. These are DeepPlant-authored
    # project proportions, not measurements taken from any reference artwork.
    for symbol_id in ("fitting.reducer.concentric", "fitting.reducer.eccentric"):
        points = _reducer_body(symbol_id)
        west_lower, west_higher = _body_face(points, 25.0)
        east_lower, east_higher = _body_face(points, 75.0)
        large_height = west_higher - west_lower
        small_height = east_higher - east_lower
        body_length = 75.0 - 25.0

        assert (west_lower, west_higher) == (14.0, 86.0)
        assert small_height == large_height / 2.0
        # Taller than long: the body is a compact taper, not a stretched duct length.
        assert large_height > body_length
        # Both faces stay inside the canonical view box, so the taller body is drawn at
        # the same display scale as every other normalized symbol.
        assert 0.0 <= west_lower < west_higher <= 100.0
        assert 0.0 <= east_lower < east_higher <= 100.0


def test_each_reducer_connects_on_one_level_axis_through_its_smaller_end() -> None:
    for symbol_id in ("fitting.reducer.concentric", "fitting.reducer.eccentric"):
        definition = _remaining(symbol_id)
        points = _reducer_body(symbol_id)
        stubs = [item for item in definition.primitives if isinstance(item, Line)]
        west_lower, west_higher = _body_face(points, 25.0)
        east_lower, east_higher = _body_face(points, 75.0)

        # One stub per end face, and each stub stops at the face plane it belongs to, so
        # no stub passes through the reducer body.
        assert len(stubs) == 2
        west_stub, east_stub = stubs
        assert (west_stub.x1, west_stub.x2) == (0.0, 25.0)
        assert (east_stub.x1, east_stub.x2) == (75.0, 100.0)
        # Both stubs are horizontal and level with each other, on the centre line of the
        # smaller end face, so a process line runs straight through the fitting. On the
        # two-sloping-side form both faces are centred on that axis; on the one-flat-side
        # form the larger face is offset about it by the eccentricity.
        assert west_stub.y1 == west_stub.y2 == east_stub.y1 == east_stub.y2
        assert east_stub.y1 == (east_lower + east_higher) / 2.0
        # The connection axis stays inside both end faces, so no stub meets an end corner
        # or leaves the body outline.
        assert west_lower < west_stub.y1 < west_higher
        assert east_lower < east_stub.y1 < east_higher
        # Each external anchor coincides with the far end of its own stub, and the pair
        # is exactly two neutral process anchors.
        assert [(anchor.x, anchor.y) for anchor in definition.anchors] == [
            (west_stub.x1, west_stub.y1),
            (east_stub.x2, east_stub.y2),
        ]
        assert len(definition.anchors) == 2
        assert {anchor.kind for anchor in definition.anchors} == {"process"}


def test_the_two_reducer_forms_are_distinguished_by_symmetry_not_by_rotation() -> None:
    concentric = _remaining("fitting.reducer.concentric")
    eccentric = _remaining("fitting.reducer.eccentric")
    axis_y = 50.0

    bodies: dict[str, Polygon] = {}
    for definition in (concentric, eccentric):
        polygons = [item for item in definition.primitives if isinstance(item, Polygon)]

        assert len(polygons) == 1, definition.symbol_id
        bodies[definition.symbol_id] = polygons[0]

    # The two-sloping-side form: every end offset is mirrored about the process axis.
    for x, y in bodies[concentric.symbol_id].points:
        assert (x, 2.0 * axis_y - y) in bodies[concentric.symbol_id].points

    # The one-flat-side form: the flat side is a straight edge parallel to the process
    # axis at one end size, and the whole reduction is one-sided, so the form is not
    # symmetric about that axis. A rotated two-sloping-side body would still be
    # symmetric, so this cannot be a rotation.
    eccentric_points = bodies[eccentric.symbol_id].points
    flat_side = [(x, y) for x, y in eccentric_points if x in {25.0, 75.0} and y == 14.0]
    assert sorted(flat_side) == [(25.0, 14.0), (75.0, 14.0)]
    assert any((x, 2.0 * axis_y - y) not in eccentric_points for x, y in eccentric_points)


def test_the_two_reducer_forms_share_their_connection_and_end_geometry() -> None:
    concentric = _remaining("fitting.reducer.concentric")
    eccentric = _remaining("fitting.reducer.eccentric")

    # The forms differ only in the taper's symmetry: the same neutral anchor names, the
    # same end-face planes, the same body extent, and the same end sizes (72 units west,
    # 36 units east). No nominal size, bore, or `DN` value is embedded in either.
    for definition in (concentric, eccentric):
        points = _reducer_body(definition.symbol_id)
        west_lower, west_higher = _body_face(points, 25.0)
        east_lower, east_higher = _body_face(points, 75.0)

        assert (west_lower, west_higher) == (14.0, 86.0)
        assert east_higher - east_lower == 36.0

    # Two-sloping-side form: the axis runs through the centre of both end faces, so
    # `port_a` and `port_b` are collinear and each one is a face centre.
    assert [
        (anchor.name, anchor.orientation, anchor.x, anchor.y) for anchor in concentric.anchors
    ] == [
        ("port_a", "west", 0.0, 50.0),
        ("port_b", "east", 100.0, 50.0),
    ]
    assert [item for item in concentric.primitives if isinstance(item, Line)] == [
        Line(x1=0.0, y1=50.0, x2=25.0, y2=50.0),
        Line(x1=75.0, y1=50.0, x2=100.0, y2=50.0),
    ]

    # One-flat-side form: both stubs leave on the same level connection axis, which is
    # the centre line of the smaller east face at y = 32, so a line runs straight
    # through the fitting instead of jogging at it.
    assert [
        (anchor.name, anchor.orientation, anchor.x, anchor.y) for anchor in eccentric.anchors
    ] == [
        ("port_a", "west", 0.0, 32.0),
        ("port_b", "east", 100.0, 32.0),
    ]
    assert [item for item in eccentric.primitives if isinstance(item, Line)] == [
        Line(x1=0.0, y1=32.0, x2=25.0, y2=32.0),
        Line(x1=75.0, y1=32.0, x2=100.0, y2=32.0),
    ]
    # The eccentricity is the body's offset about that level axis: measured downwards
    # (SVG `y` grows downward), the larger west face centre sits exactly half the
    # end-size difference below the connection axis, so the larger end drops away from
    # the straight run while the flat side stays flush with it.
    west_height, east_height = 72.0, 36.0
    west_centre = sum(_body_face(_reducer_body(eccentric.symbol_id), 25.0)) / 2.0
    assert west_centre - eccentric.anchors[0].y == (west_height - east_height) / 2.0 == 18.0


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
