"""Registry tests for the machine-rendered symbol library (Issues #119, #125).

The registry is the lookup boundary between the catalogue and a renderer or
editor consumer: it must resolve a graphical representation by
``(notation_profile, symbol_id)``, expose the registered set deterministically
and completely, and refuse a representation it does not know. A lookup never
substitutes one notation profile for another.
"""

from __future__ import annotations

import pytest

from deepplant.symbols import (
    SYMBOLS,
    AssetProvenance,
    Line,
    StandardsReference,
    SymbolDefinition,
    SymbolDefinitionError,
    SymbolRegistry,
)
from deepplant.symbols.profiles import (
    DEEPPLANT_DEFAULT_NOTATION_PROFILE,
    GENERIC_ISO_NOTATION_PROFILE,
    NOTATION_PROFILES,
)

#: The three representations the reviewed first Issue #119 slice implements.
IMPLEMENTED_IDS = ("instrument.local", "pump.centrifugal", "valve.gate")

#: An intended-correspondence relationship, which the ``generic-iso`` profile
#: requires. It records no restricted-derived locator, name, or verifier evidence.
CORRESPONDENCE = StandardsReference(standard="ISO 10628-2:2012", verification="candidate-alignment")


def _definition(
    symbol_id: str = "valve.example",
    *,
    notation_profile: str = GENERIC_ISO_NOTATION_PROFILE,
    standards: tuple[StandardsReference, ...] = (CORRESPONDENCE,),
) -> SymbolDefinition:
    """Build one valid synthetic definition, so each test varies one fact."""
    return SymbolDefinition(
        symbol_id=symbol_id,
        name=f"Test {symbol_id}",
        category="test",
        diagram_types=("pid",),
        notation_profile=notation_profile,
        primitives=(Line(x1=0.0, y1=50.0, x2=100.0, y2=50.0),),
        anchors=(),
        provenance=AssetProvenance(origin="deepplant-original", license="AGPL-3.0-only"),
        standards=standards,
    )


# ---------------------------------------------------------------------------
# The built-in registry
# ---------------------------------------------------------------------------


def test_the_builtin_registry_exposes_exactly_the_implemented_symbols() -> None:
    assert tuple(definition.symbol_id for definition in SYMBOLS.list()) == IMPLEMENTED_IDS


def test_the_builtin_convenience_default_is_still_generic_iso() -> None:
    # Issue #125 neither migrates the existing catalogue nor switches the built-in
    # runtime default: `deepplant-default` is the future product default (#124), but
    # the current catalogue contains no `deepplant-default` representation yet.
    assert SYMBOLS.default_notation_profile == GENERIC_ISO_NOTATION_PROFILE


def test_get_resolves_a_stable_symbol_id() -> None:
    definition = SYMBOLS.get("valve.gate")

    assert definition.name == "Gate valve"
    assert definition.notation_profile == GENERIC_ISO_NOTATION_PROFILE
    assert SYMBOLS.get("valve.gate") is definition


def test_get_resolves_explicitly_through_the_builtin_default_profile() -> None:
    assert SYMBOLS.get("valve.gate", notation_profile=GENERIC_ISO_NOTATION_PROFILE) is SYMBOLS.get(
        "valve.gate"
    )


def test_every_builtin_symbol_keeps_its_generic_iso_representation() -> None:
    for definition in SYMBOLS.list():
        assert definition.notation_profile == GENERIC_ISO_NOTATION_PROFILE


def test_the_builtin_registry_registers_no_deepplant_default_representation() -> None:
    # Issue #125 recognises the profile without migrating any geometry into it, so a
    # known profile with zero definitions must be a valid empty result (#124, #125).
    assert SYMBOLS.list(notation_profile=DEEPPLANT_DEFAULT_NOTATION_PROFILE) == ()


def test_get_fails_closed_on_an_unknown_symbol_id() -> None:
    with pytest.raises(SymbolDefinitionError, match="unknown symbol representation"):
        SYMBOLS.get("valve.globe")


# ---------------------------------------------------------------------------
# Notation-profile aware identity
# ---------------------------------------------------------------------------


def test_the_same_symbol_id_may_coexist_in_two_notation_profiles() -> None:
    default = _definition(
        "valve.example", notation_profile=DEEPPLANT_DEFAULT_NOTATION_PROFILE, standards=()
    )
    generic = _definition("valve.example")

    registry = SymbolRegistry([default, generic])

    found_default = registry.get(
        "valve.example", notation_profile=DEEPPLANT_DEFAULT_NOTATION_PROFILE
    )
    found_generic = registry.get("valve.example", notation_profile=GENERIC_ISO_NOTATION_PROFILE)

    assert found_default is default
    assert found_generic is generic
    assert len(registry.list()) == 2


def test_a_duplicate_representation_identifies_both_parts() -> None:
    # The error must name the full representation identity, not merely a duplicate
    # symbol id, because the same symbol id is legitimate in another profile.
    with pytest.raises(SymbolDefinitionError) as error:
        SymbolRegistry([_definition("valve.example"), _definition("valve.example")])

    message = str(error.value)
    assert "duplicate symbol representation" in message
    assert f"notation_profile={GENERIC_ISO_NOTATION_PROFILE!r}" in message
    assert "symbol_id='valve.example'" in message


def test_listing_is_ordered_by_notation_profile_then_symbol_id() -> None:
    registry = SymbolRegistry(
        [
            _definition("valve.b"),
            _definition(
                "valve.a", notation_profile=DEEPPLANT_DEFAULT_NOTATION_PROFILE, standards=()
            ),
            _definition(
                "valve.b", notation_profile=DEEPPLANT_DEFAULT_NOTATION_PROFILE, standards=()
            ),
        ]
    )

    assert [
        (definition.notation_profile, definition.symbol_id) for definition in registry.list()
    ] == [
        (DEEPPLANT_DEFAULT_NOTATION_PROFILE, "valve.a"),
        (DEEPPLANT_DEFAULT_NOTATION_PROFILE, "valve.b"),
        (GENERIC_ISO_NOTATION_PROFILE, "valve.b"),
    ]


# ---------------------------------------------------------------------------
# Default, fail-closed lookup, and listing
# ---------------------------------------------------------------------------


def test_list_order_is_stable_regardless_of_declaration_order() -> None:
    registry = SymbolRegistry([_definition("pump.centrifugal"), _definition("valve.gate")])

    assert tuple(definition.symbol_id for definition in registry.list()) == (
        "pump.centrifugal",
        "valve.gate",
    )


def test_the_default_notation_profile_is_registry_configuration() -> None:
    registry = SymbolRegistry(
        [_definition("valve.example")],
        default_notation_profile=GENERIC_ISO_NOTATION_PROFILE,
    )

    assert registry.default_notation_profile == GENERIC_ISO_NOTATION_PROFILE
    assert registry.get("valve.example") is registry.get(
        "valve.example", notation_profile=GENERIC_ISO_NOTATION_PROFILE
    )


def test_a_missing_representation_fails_closed_instead_of_substituting_notation() -> None:
    # A requested notation that is absent is an error, never permission to return the
    # representation another profile happens to hold.
    generic = _definition("valve.example", notation_profile=GENERIC_ISO_NOTATION_PROFILE)
    registry = SymbolRegistry([generic])

    with pytest.raises(SymbolDefinitionError) as error:
        registry.get("valve.example", notation_profile=DEEPPLANT_DEFAULT_NOTATION_PROFILE)

    message = str(error.value)
    assert "'valve.example'" in message
    assert DEEPPLANT_DEFAULT_NOTATION_PROFILE in message


def test_an_unknown_requested_notation_profile_fails_closed() -> None:
    registry = SymbolRegistry([_definition("valve.example")])

    with pytest.raises(SymbolDefinitionError, match="unknown requested notation profile"):
        registry.get("valve.example", notation_profile="iso-10628")

    with pytest.raises(SymbolDefinitionError, match="unknown requested notation profile"):
        registry.list(notation_profile="iso-10628")


def test_an_unknown_default_notation_profile_fails_closed() -> None:
    with pytest.raises(SymbolDefinitionError, match="unknown registry default notation profile"):
        SymbolRegistry([_definition("valve.example")], default_notation_profile="iso-10628")


def test_listing_filters_by_notation_profile_and_keeps_known_profiles_empty() -> None:
    registry = SymbolRegistry(
        [
            _definition("valve.example", notation_profile=GENERIC_ISO_NOTATION_PROFILE),
            _definition(
                "pump.example", notation_profile=DEEPPLANT_DEFAULT_NOTATION_PROFILE, standards=()
            ),
        ]
    )

    assert [definition.symbol_id for definition in registry.list()] == [
        "pump.example",
        "valve.example",
    ]
    assert [
        definition.symbol_id
        for definition in registry.list(notation_profile=DEEPPLANT_DEFAULT_NOTATION_PROFILE)
    ] == ["pump.example"]
    # A recognised profile with no registered representation is a valid empty result.
    assert (
        SymbolRegistry([_definition("valve.example")]).list(
            notation_profile=DEEPPLANT_DEFAULT_NOTATION_PROFILE
        )
        == ()
    )


def test_the_notation_profile_vocabulary_is_closed() -> None:
    # Issue #125 recognises exactly two production profiles; every other candidate
    # (`iso-10628`, PIP, ISA, company/project) belongs to a later evidence-based slice.
    assert NOTATION_PROFILES == {
        DEEPPLANT_DEFAULT_NOTATION_PROFILE,
        GENERIC_ISO_NOTATION_PROFILE,
    }


def test_an_unknown_lookup_does_not_leak_a_key_error() -> None:
    registry = SymbolRegistry([_definition("valve.example")])

    with pytest.raises(SymbolDefinitionError):
        registry.get("pump.example")
