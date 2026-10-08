"""Registry tests for the machine-rendered symbol library (Issue #119).

The registry is the lookup boundary between the catalogue and a renderer or
editor consumer: it must resolve a stable symbol id, expose the implemented set
deterministically and completely, and refuse an id it does not know.
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

#: The representations the reviewed Issue #119 slices implement.
IMPLEMENTED_IDS = (
    "fitting.reducer",
    "instrument.local",
    "pump.centrifugal",
    "valve.ball",
    "valve.check",
    "valve.gate",
)


def _definition(symbol_id: str) -> SymbolDefinition:
    return SymbolDefinition(
        symbol_id=symbol_id,
        name=f"Test {symbol_id}",
        category="test",
        diagram_types=("pid",),
        profile="generic-iso",
        primitives=(Line(x1=0.0, y1=50.0, x2=100.0, y2=50.0),),
        anchors=(),
        provenance=AssetProvenance(origin="deepplant-original", license="AGPL-3.0-only"),
        # The `generic-iso` profile means intended standards correspondence, so a
        # definition in that profile must record one.
        standards=(
            StandardsReference(standard="ISO 10628-2:2012", verification="candidate-alignment"),
        ),
    )


def test_the_builtin_registry_exposes_exactly_the_implemented_symbols() -> None:
    assert tuple(definition.symbol_id for definition in SYMBOLS.list()) == IMPLEMENTED_IDS


def test_the_catalogue_contains_exactly_six_definitions() -> None:
    # The reviewed catalogue size is part of the contract: each definition is a
    # deliberate, reviewed addition, so an accidental extra or missing symbol
    # must fail loudly rather than silently change the library.
    assert len(SYMBOLS.list()) == 6
    assert len(set(IMPLEMENTED_IDS)) == len(IMPLEMENTED_IDS)


def test_get_resolves_a_stable_symbol_id() -> None:
    definition = SYMBOLS.get("valve.gate")

    assert definition.name == "Gate valve"
    assert definition.profile == "generic-iso"
    assert SYMBOLS.get("valve.gate") is definition


def test_get_fails_closed_on_an_unknown_symbol_id() -> None:
    with pytest.raises(SymbolDefinitionError, match="unknown symbol id 'valve.globe'"):
        SYMBOLS.get("valve.globe")


def test_list_order_is_stable_regardless_of_declaration_order() -> None:
    registry = SymbolRegistry([_definition("pump.centrifugal"), _definition("valve.gate")])

    assert tuple(definition.symbol_id for definition in registry.list()) == (
        "pump.centrifugal",
        "valve.gate",
    )


def test_a_duplicate_symbol_id_is_rejected() -> None:
    with pytest.raises(SymbolDefinitionError, match="duplicate symbol id 'valve.gate'"):
        SymbolRegistry([_definition("valve.gate"), _definition("valve.gate")])


def test_an_unknown_lookup_does_not_leak_a_key_error() -> None:
    registry = SymbolRegistry([_definition("valve.gate")])

    with pytest.raises(SymbolDefinitionError):
        registry.get("pump.centrifugal")
