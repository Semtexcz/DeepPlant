# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Symbol registry: the lookup boundary over the implemented symbol catalogue.

The registry is deliberately small (Issue #119, ADR-0017): it answers ``get``
and ``list`` for the definitions it was built from and holds no search,
filtering, variant, pack, plugin, or provider machinery. A definition is
presentation data that never enters the semantic model (ADR-0003).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Final

from deepplant.symbols.catalogue import IMPLEMENTED_SYMBOLS
from deepplant.symbols.definition import SymbolDefinition, SymbolDefinitionError


class SymbolRegistry:
    """An immutable lookup from stable symbol id to symbol definition.

    Definitions are ordered by symbol id, so ``list`` is deterministic no matter
    what order the catalogue declared them in.
    """

    def __init__(self, definitions: Iterable[SymbolDefinition]) -> None:
        by_id: dict[str, SymbolDefinition] = {}
        for definition in definitions:
            if definition.symbol_id in by_id:
                raise SymbolDefinitionError(f"duplicate symbol id {definition.symbol_id!r}")
            by_id[definition.symbol_id] = definition
        self._by_id: dict[str, SymbolDefinition] = by_id
        self._ordered: tuple[SymbolDefinition, ...] = tuple(
            sorted(by_id.values(), key=lambda definition: definition.symbol_id)
        )

    def get(self, symbol_id: str) -> SymbolDefinition:
        """Return the definition registered for ``symbol_id``."""
        try:
            return self._by_id[symbol_id]
        except KeyError:
            raise SymbolDefinitionError(f"unknown symbol id {symbol_id!r}") from None

    def list(self) -> tuple[SymbolDefinition, ...]:
        """Return every registered definition, in stable symbol-id order."""
        return self._ordered


#: The built-in registry over the implemented symbol catalogue.
SYMBOLS: Final[SymbolRegistry] = SymbolRegistry(IMPLEMENTED_SYMBOLS)
