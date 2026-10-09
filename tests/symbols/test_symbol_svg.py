"""Rendering and structural tests for the machine-rendered symbol library.

These tests pin the Issue #119 rendering contract: SVG is generated from a
definition deterministically, output is a restricted, themeable subset, anchors
are definition data rather than SVG inference, and the three implemented
representations keep their structural shape, their neutral geometric anchors, and
their asset provenance.
"""

from __future__ import annotations

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

CANONICAL_VIEW_BOX = "0 0 100 100"
ALLOWED_ELEMENT_NAMES = {"svg", "line", "circle", "polygon"}
ALLOWED_ROOT_ATTRIBUTES = {"viewBox", "fill", "stroke", "stroke-width"}
THEMEABLE_COLOR_VALUES = {"none", "currentColor"}
FORBIDDEN_ATTRIBUTES = {"href", "style", "class", "font-family", "onload"}

#: The three representations the first Issue #119 slice implements.
IMPLEMENTED_IDS = ("instrument.local", "pump.centrifugal", "valve.gate")

ISO_10628_2 = "ISO 10628-2:2012"
ISO_15519_2 = "ISO 15519-2:2015"

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


@pytest.mark.parametrize("symbol_id", IMPLEMENTED_IDS)
def test_rendering_is_deterministic(symbol_id: str) -> None:
    definition = SYMBOLS.get(symbol_id)

    assert render_symbol_svg(definition) == render_symbol_svg(definition)


@pytest.mark.parametrize("symbol_id", IMPLEMENTED_IDS)
def test_a_rebuilt_definition_renders_identically(symbol_id: str) -> None:
    definition = SYMBOLS.get(symbol_id)
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
# Structural contracts of the three implemented representations
# ---------------------------------------------------------------------------


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


@pytest.mark.parametrize("symbol_id", IMPLEMENTED_IDS)
def test_no_symbol_claims_human_verification(symbol_id: str) -> None:
    for reference in SYMBOLS.get(symbol_id).standards:
        assert reference.verification != "human-verified"


@pytest.mark.parametrize("symbol_id", IMPLEMENTED_IDS)
def test_no_restricted_derived_standards_detail_is_recorded(symbol_id: str) -> None:
    # A locator, the standard's own name for a representation, or a verifier may
    # only be recorded from a permitted source or by a human verifier; neither
    # exists yet, so all stay unrecorded rather than carrying restricted-derived
    # detail or falsely implying a human check.
    for reference in SYMBOLS.get(symbol_id).standards:
        assert reference.locator is None
        assert reference.name is None
        assert reference.verified_by is None
        assert reference.verified_on is None


def test_every_implemented_symbol_declares_the_generic_iso_notation_profile() -> None:
    # Issue #125 renames the field and makes the registry profile-aware but migrates
    # no geometry: the three built-in representations all stay `generic-iso`.
    for definition in SYMBOLS.list():
        assert definition.notation_profile == "generic-iso"
