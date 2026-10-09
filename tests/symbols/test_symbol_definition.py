"""Validation tests for machine-readable symbol definitions (Issue #119).

A :class:`SymbolDefinition` is the canonical geometry source, so its invariants
are exercised directly: stable identity, closed vocabularies, the normalized
coordinate system, explicit anchors, asset provenance, and the standards
relationship its drawing profile requires. Nothing here depends on the renderer
or on YAML.
"""

from __future__ import annotations

import dataclasses
from datetime import date
from typing import Literal, cast

import pytest

from deepplant.symbols import (
    CANONICAL_VIEW_BOX,
    AssetProvenance,
    Circle,
    Line,
    Polygon,
    StandardsReference,
    SymbolAnchor,
    SymbolDefinition,
    SymbolDefinitionError,
)
from deepplant.symbols.definition import ANCHOR_ORIENTATIONS, ASSET_ORIGINS, VERIFICATION_STATES

#: An intended-correspondence reference, reused so each test varies exactly one
#: fact. It records the `candidate-alignment` state the current `generic-iso`
#: profile requires, and no restricted-derived locator, name, or verifier evidence.
CORRESPONDENCE = StandardsReference(standard="ISO 10628-2:2012", verification="candidate-alignment")

#: Valid asset provenance, reused so each test varies exactly one fact.
PROVENANCE = AssetProvenance(origin="deepplant-original", license="AGPL-3.0-only")

#: Complete human-verification evidence, reused by the `human-verified` tests.
VERIFIER = "Daniel Kopecký"
VERIFIED_ON = date(2026, 10, 8)

# The anchor vocabularies as this test states them, mirroring the closed sets the
# source module validates. A negative test needs a value the static type forbids,
# and ``cast`` is the minimal way to say so without weakening the source.
AnchorOrientation = Literal["north", "east", "south", "west"]
AnchorKind = Literal["process", "signal"]
BAD_ORIENTATION = cast(AnchorOrientation, "sideways")
BAD_KIND = cast(AnchorKind, "electrical")


def _symbol(
    *,
    symbol_id: str = "valve.gate",
    name: str = "Gate valve",
    category: str = "valve",
    diagram_types: tuple[str, ...] = ("pid",),
    profile: str = "generic-iso",
    primitives: tuple[Line | Circle | Polygon, ...] = (Line(x1=0.0, y1=50.0, x2=100.0, y2=50.0),),
    anchors: tuple[SymbolAnchor, ...] = (),
    provenance: AssetProvenance = PROVENANCE,
    standards: tuple[StandardsReference, ...] = (CORRESPONDENCE,),
    view_box: tuple[float, float, float, float] = CANONICAL_VIEW_BOX,
) -> SymbolDefinition:
    """Build one valid definition, so each test varies a single fact."""
    return SymbolDefinition(
        symbol_id=symbol_id,
        name=name,
        category=category,
        diagram_types=diagram_types,
        profile=profile,
        primitives=primitives,
        anchors=anchors,
        provenance=provenance,
        standards=standards,
        view_box=view_box,
    )


def test_a_valid_definition_keeps_its_declared_values() -> None:
    definition = _symbol(
        anchors=(SymbolAnchor(name="port_a", x=0.0, y=50.0, orientation="west", kind="process"),)
    )

    assert definition.symbol_id == "valve.gate"
    assert definition.profile == "generic-iso"
    assert definition.diagram_types == ("pid",)
    assert definition.view_box == CANONICAL_VIEW_BOX
    assert definition.provenance == PROVENANCE
    assert [anchor.name for anchor in definition.anchors] == ["port_a"]


@pytest.mark.parametrize(
    "symbol_id",
    ["valve", "Valve.Gate", "valve.gate.", ".valve", "valve..gate", "valve.-gate", ""],
)
def test_symbol_id_must_be_a_lowercase_dotted_name(symbol_id: str) -> None:
    with pytest.raises(SymbolDefinitionError, match="symbol id"):
        _symbol(symbol_id=symbol_id)


def test_blank_symbol_name_is_rejected() -> None:
    with pytest.raises(SymbolDefinitionError, match="symbol name"):
        _symbol(name="   ")


def test_blank_symbol_category_is_rejected() -> None:
    with pytest.raises(SymbolDefinitionError, match="symbol category"):
        _symbol(category="")


def test_unknown_drawing_profile_is_rejected() -> None:
    with pytest.raises(SymbolDefinitionError, match="drawing profile"):
        _symbol(profile="yara-chpn")


# ---------------------------------------------------------------------------
# The `generic-iso` profile invariant
# ---------------------------------------------------------------------------


def test_generic_iso_rejects_a_definition_without_a_standards_reference() -> None:
    # `generic-iso` *means* intended standards correspondence, so it cannot be
    # claimed by a definition that records no standards relationship at all.
    with pytest.raises(SymbolDefinitionError, match="records no standards reference"):
        _symbol(standards=())


def test_generic_iso_rejects_reference_only_standards() -> None:
    # `reference` claims no correspondence for a concrete geometry, so it can never
    # make a symbol part of the intended-correspondence `generic-iso` profile.
    with pytest.raises(SymbolDefinitionError, match="no intended correspondence"):
        _symbol(standards=(StandardsReference(standard="ISO 10628-2:2012"),))


def test_generic_iso_rejects_a_reference_mixed_into_an_intended_correspondence() -> None:
    with pytest.raises(SymbolDefinitionError, match="no intended correspondence"):
        _symbol(
            standards=(
                CORRESPONDENCE,
                StandardsReference(standard="ISO 15519-2:2015"),
            )
        )


@pytest.mark.parametrize("verification", ["candidate-alignment", "human-verified"])
def test_generic_iso_accepts_an_intended_correspondence(verification: str) -> None:
    if verification == "human-verified":
        reference = StandardsReference(
            standard="ISO 10628-2:2012",
            verification="human-verified",
            locator="recorded locator",
            verified_by=VERIFIER,
            verified_on=VERIFIED_ON,
        )
    else:
        reference = StandardsReference(standard="ISO 10628-2:2012", verification=verification)

    definition = _symbol(standards=(reference,))

    assert definition.profile == "generic-iso"
    assert definition.standards == (reference,)


def test_the_standards_field_stays_optional_at_the_definition_level() -> None:
    # The requirement is profile-specific, not blanket: `standards` has no imposed
    # default, and a future company, project, or custom profile may legitimately
    # record none. The current `generic-iso` profile is what requires an intended
    # correspondence.
    fields = {field.name: field for field in dataclasses.fields(SymbolDefinition)}

    assert fields["standards"].default == ()


@pytest.mark.parametrize("diagram_types", [(), ("pfd", "pfd"), ("pfd", "p&id")])
def test_diagram_types_must_be_a_non_empty_known_set(diagram_types: tuple[str, ...]) -> None:
    with pytest.raises(SymbolDefinitionError):
        _symbol(diagram_types=diagram_types)


def test_a_definition_without_geometry_is_rejected() -> None:
    with pytest.raises(SymbolDefinitionError, match="at least one primitive"):
        _symbol(primitives=())


def test_a_premature_third_party_origin_is_rejected() -> None:
    # Third-party import provenance is deferred until the first concrete
    # third-party asset: the two-field record is not sufficient for an imported
    # asset, so the vocabulary accepts DeepPlant-original geometry only (ADR-0007).
    with pytest.raises(SymbolDefinitionError, match="unknown asset origin 'third-party'"):
        AssetProvenance(origin="third-party", license="CC0-1.0")


def test_the_same_standard_may_not_be_recorded_twice() -> None:
    with pytest.raises(
        SymbolDefinitionError, match="records the standard 'ISO 10628-2:2012' twice"
    ):
        _symbol(standards=(CORRESPONDENCE, StandardsReference(standard="ISO 10628-2:2012")))


@pytest.mark.parametrize(
    "view_box",
    [(0.0, 0.0, 0.0, 100.0), (0.0, 0.0, 100.0, -1.0), (0.0, 0.0, 100.0)],
)
def test_view_box_must_be_a_sized_box(view_box: tuple[float, float, float, float]) -> None:
    with pytest.raises(SymbolDefinitionError, match="view box"):
        _symbol(view_box=view_box, primitives=())


def test_polygon_needs_at_least_three_vertices() -> None:
    with pytest.raises(SymbolDefinitionError, match="three vertices"):
        Polygon(points=((0.0, 0.0), (10.0, 0.0)))


@pytest.mark.parametrize("radius", [0.0, -5.0])
def test_circle_radius_must_be_positive(radius: float) -> None:
    with pytest.raises(SymbolDefinitionError, match="radius"):
        Circle(cx=50.0, cy=50.0, r=radius)


def test_circle_fill_defaults_to_hollow() -> None:
    # The one binary fill fact defaults to hollow, so adding it leaves every
    # existing definition and its rendered SVG unchanged.
    assert Circle(cx=50.0, cy=50.0, r=8.0).filled is False
    assert Circle(cx=50.0, cy=50.0, r=8.0, filled=True).filled is True


@pytest.mark.parametrize("filled", ["yes", 1, 0, None])
def test_circle_fill_must_be_a_boolean(filled: object) -> None:
    with pytest.raises(SymbolDefinitionError, match="boolean"):
        Circle(cx=50.0, cy=50.0, r=8.0, filled=cast(bool, filled))


def test_geometry_outside_the_view_box_is_rejected() -> None:
    with pytest.raises(SymbolDefinitionError, match="outside the view box"):
        _symbol(primitives=(Line(x1=0.0, y1=50.0, x2=101.0, y2=50.0),))


def test_circle_extremes_are_checked_against_the_view_box() -> None:
    with pytest.raises(SymbolDefinitionError, match="outside the view box"):
        _symbol(primitives=(Circle(cx=90.0, cy=50.0, r=20.0),))


# ---------------------------------------------------------------------------
# Anchors
# ---------------------------------------------------------------------------


def test_anchor_name_must_be_a_lowercase_identifier() -> None:
    with pytest.raises(SymbolDefinitionError, match="anchor name"):
        SymbolAnchor(name="Port A", x=0.0, y=50.0, orientation="west", kind="process")


@pytest.mark.parametrize("orientation", ["north", "east", "south", "west"])
def test_every_geometric_anchor_orientation_is_accepted(orientation: AnchorOrientation) -> None:
    anchor = SymbolAnchor(name="port_a", x=0.0, y=50.0, orientation=orientation, kind="process")

    assert anchor.orientation == orientation


def test_the_accepted_orientations_are_the_geometric_vocabulary() -> None:
    # Orientation is routing geometry, so the vocabulary is the four cardinal
    # directions and never a flow/semantic value such as `in` or `out`.
    assert ANCHOR_ORIENTATIONS == {"north", "east", "south", "west"}


def test_unknown_anchor_orientation_is_rejected() -> None:
    with pytest.raises(SymbolDefinitionError, match="unknown orientation 'sideways'"):
        SymbolAnchor(name="port_a", x=0.0, y=50.0, orientation=BAD_ORIENTATION, kind="process")


def test_a_semantic_flow_direction_is_not_a_valid_orientation() -> None:
    with pytest.raises(SymbolDefinitionError, match="unknown orientation"):
        SymbolAnchor(
            name="port_a",
            x=0.0,
            y=50.0,
            orientation=cast(AnchorOrientation, "in"),
            kind="process",
        )


def test_unknown_anchor_connection_kind_is_rejected() -> None:
    with pytest.raises(SymbolDefinitionError, match="connection kind"):
        SymbolAnchor(name="port_a", x=0.0, y=50.0, orientation="west", kind=BAD_KIND)


@pytest.mark.parametrize("x", [float("nan"), float("inf"), -float("inf")])
def test_anchor_coordinates_must_be_finite(x: float) -> None:
    with pytest.raises(SymbolDefinitionError, match="finite numeric"):
        SymbolAnchor(name="port_a", x=x, y=50.0, orientation="west", kind="process")


def test_duplicate_anchor_names_are_rejected() -> None:
    first = SymbolAnchor(name="port_a", x=0.0, y=50.0, orientation="west", kind="process")
    second = SymbolAnchor(name="port_a", x=100.0, y=50.0, orientation="east", kind="process")

    with pytest.raises(SymbolDefinitionError, match="duplicate anchor name 'port_a'"):
        _symbol(anchors=(first, second))


def test_anchor_outside_the_view_box_is_rejected() -> None:
    outside = SymbolAnchor(name="port_a", x=-1.0, y=50.0, orientation="west", kind="process")

    with pytest.raises(SymbolDefinitionError, match="outside the view box"):
        _symbol(anchors=(outside,))


def test_anchors_may_sit_on_the_view_box_boundary() -> None:
    definition = _symbol(
        anchors=(
            SymbolAnchor(name="port_a", x=0.0, y=50.0, orientation="west", kind="process"),
            SymbolAnchor(name="port_b", x=100.0, y=50.0, orientation="east", kind="process"),
        )
    )

    assert [(anchor.name, anchor.x) for anchor in definition.anchors] == [
        ("port_a", 0.0),
        ("port_b", 100.0),
    ]


# ---------------------------------------------------------------------------
# Asset provenance
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("origin", ["deepplant-original"])
def test_every_asset_origin_in_the_vocabulary_is_accepted(origin: str) -> None:
    provenance = AssetProvenance(origin=origin, license="AGPL-3.0-only")

    assert provenance.origin == origin


def test_the_asset_origin_vocabulary_is_closed() -> None:
    # Only DeepPlant-original geometry exists in this slice; third-party import
    # support is deferred until the first concrete third-party asset (ADR-0007).
    assert ASSET_ORIGINS == {"deepplant-original"}


def test_asset_provenance_is_a_required_definition_field() -> None:
    # Provenance is not optional and has no silent default, so a distributed
    # definition cannot omit it and thereby claim nothing about its origin.
    fields = {field.name: field for field in dataclasses.fields(SymbolDefinition)}

    assert "provenance" in fields
    assert fields["provenance"].default is dataclasses.MISSING
    assert fields["standards"].default == ()


def test_unknown_asset_origin_is_rejected() -> None:
    with pytest.raises(SymbolDefinitionError, match="unknown asset origin 'somewhere-else'"):
        AssetProvenance(origin="somewhere-else", license="AGPL-3.0-only")


def test_asset_license_must_not_be_blank() -> None:
    with pytest.raises(SymbolDefinitionError, match="asset provenance 'license'"):
        AssetProvenance(origin="deepplant-original", license="  ")


@pytest.mark.parametrize("license_id", ["MIT", "CC0-1.0", "AGPL-3.0-or-later", "unknown"])
def test_deepplant_original_geometry_rejects_another_licence(license_id: str) -> None:
    # DeepPlant-original geometry is distributed under AGPL-3.0-only, so the pair
    # fails closed rather than silently accepting a different licence.
    with pytest.raises(SymbolDefinitionError, match="deepplant-original.*AGPL-3.0-only"):
        AssetProvenance(origin="deepplant-original", license=license_id)


def test_deepplant_original_geometry_accepts_its_declared_licence() -> None:
    provenance = AssetProvenance(origin="deepplant-original", license="AGPL-3.0-only")

    assert provenance.origin == "deepplant-original"
    assert provenance.license == "AGPL-3.0-only"


# ---------------------------------------------------------------------------
# Standards correspondence
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("blank_field", ["standard", "locator", "name"])
def test_recorded_standards_reference_fields_must_not_be_blank(blank_field: str) -> None:
    fields = {
        "standard": "ISO 10628-2:2012",
        "locator": "recorded locator",
        "name": "recorded name",
    }
    fields[blank_field] = "  "

    with pytest.raises(SymbolDefinitionError, match=blank_field):
        StandardsReference(
            standard=fields["standard"],
            locator=fields["locator"],
            name=fields["name"],
        )


def test_the_optional_standards_metadata_defaults_to_unrecorded() -> None:
    # Locator, standard-authored name, and verifier evidence stay unrecorded until
    # a permitted source or a human verification supplies them, so nothing
    # restricted-derived is implied here.
    reference = StandardsReference(standard="ISO 10628-2:2012")

    assert reference.locator is None
    assert reference.name is None
    assert reference.verified_by is None
    assert reference.verified_on is None


def test_a_reference_is_valid_without_human_verification_evidence() -> None:
    # `reference` claims no correspondence for a concrete geometry, so it requires
    # no locator, verifier, or date.
    reference = StandardsReference(standard="ISO 10628-2:2012", verification="reference")

    assert reference.verification == "reference"
    assert reference.locator is None
    assert reference.verified_by is None
    assert reference.verified_on is None


def test_candidate_alignment_is_valid_without_human_verification_evidence() -> None:
    # Human verification is NOT a prerequisite for `candidate-alignment`: the
    # geometry is intended to correspond, with no human check claimed.
    reference = StandardsReference(standard="ISO 10628-2:2012", verification="candidate-alignment")

    assert reference.verification == "candidate-alignment"
    assert reference.locator is None
    assert reference.verified_by is None
    assert reference.verified_on is None


def test_human_verified_fails_closed_without_a_locator() -> None:
    with pytest.raises(SymbolDefinitionError, match="locator"):
        StandardsReference(
            standard="ISO 10628-2:2012",
            verification="human-verified",
            verified_by=VERIFIER,
            verified_on=VERIFIED_ON,
        )


def test_human_verified_fails_closed_without_a_verifier() -> None:
    with pytest.raises(SymbolDefinitionError, match="verified_by"):
        StandardsReference(
            standard="ISO 10628-2:2012",
            verification="human-verified",
            locator="recorded locator",
            verified_on=VERIFIED_ON,
        )


def test_human_verified_fails_closed_without_a_date() -> None:
    with pytest.raises(SymbolDefinitionError, match="verified_on"):
        StandardsReference(
            standard="ISO 10628-2:2012",
            verification="human-verified",
            locator="recorded locator",
            verified_by=VERIFIER,
        )


def test_a_complete_human_verified_record_is_accepted() -> None:
    reference = StandardsReference(
        standard="ISO 10628-2:2012",
        verification="human-verified",
        locator="recorded locator",
        verified_by=VERIFIER,
        verified_on=VERIFIED_ON,
    )

    assert reference.verification == "human-verified"
    assert reference.verified_by == VERIFIER
    assert reference.verified_on == VERIFIED_ON


@pytest.mark.parametrize("verification", ["reference", "candidate-alignment"])
def test_verifier_evidence_without_human_verification_is_rejected(verification: str) -> None:
    # A weaker state must never misleadingly imply a human check.
    with pytest.raises(SymbolDefinitionError, match="human-verified"):
        StandardsReference(
            standard="ISO 10628-2:2012",
            verification=verification,
            verified_by=VERIFIER,
            verified_on=VERIFIED_ON,
        )


def test_a_recorded_verifier_must_not_be_blank() -> None:
    with pytest.raises(SymbolDefinitionError, match="verified_by"):
        StandardsReference(
            standard="ISO 10628-2:2012",
            verification="human-verified",
            locator="recorded locator",
            verified_by="  ",
            verified_on=VERIFIED_ON,
        )


def test_verified_on_must_be_a_date_when_recorded() -> None:
    with pytest.raises(SymbolDefinitionError, match="verified_on"):
        StandardsReference(
            standard="ISO 10628-2:2012",
            verification="human-verified",
            locator="recorded locator",
            verified_by=VERIFIER,
            verified_on=cast(date, "2026-10-08"),
        )


def test_standards_reference_rejects_an_unknown_verification_state() -> None:
    with pytest.raises(SymbolDefinitionError, match="verification state"):
        StandardsReference(
            standard="ISO 10628-2:2012",
            verification="looks-similar",
        )


def test_verification_state_defaults_to_the_conservative_reference() -> None:
    reference = StandardsReference(standard="ISO 10628-2:2012")

    assert reference.verification == "reference"


def test_verification_states_follow_the_canonical_governance_vocabulary() -> None:
    # docs/dev/workflow/standards.md defines exactly these three states; the
    # library must not add a conflicting fourth public alignment state.
    assert VERIFICATION_STATES == {"reference", "candidate-alignment", "human-verified"}
