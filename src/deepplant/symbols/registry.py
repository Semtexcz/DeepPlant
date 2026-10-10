# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Symbol registry: the lookup boundary over the implemented symbol catalogue.

The registry is deliberately small (Issue #119, ADR-0017): it answers ``get``
and ``list`` for the definitions it was built from and holds no search,
filtering, variant, pack, plugin, or provider machinery. A definition is
presentation data that never enters the semantic model (ADR-0003).

Notation-profile aware identity (Issue #125)
--------------------------------------------

A graphical representation is identified by the pair
``(notation_profile, symbol_id)``, so one stable symbol id may legitimately hold
one representation per notation profile (Issue #124). A lookup that requests a
representation which is absent fails closed: a missing notation is never
permission to substitute another one. The registry only resolves a graphical
representation - selecting and persisting the notation profile of a project or
document is a separate concern that lives outside this package.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Final

from deepplant.symbols.catalogue import IMPLEMENTED_SYMBOLS
from deepplant.symbols.definition import SymbolDefinition, SymbolDefinitionError
from deepplant.symbols.profiles import (
    GENERIC_ISO_NOTATION_PROFILE,
    NOTATION_PROFILES,
    notation_profile_policy,
)


class SymbolRegistry:
    """An immutable lookup from ``(notation_profile, symbol_id)`` to a definition.

    A graphical representation is identified by the pair
    ``(notation_profile, symbol_id)``, so one symbol id may hold one definition per
    notation profile. ``default_notation_profile`` is construction-time
    configuration that applies to :meth:`get` when ``notation_profile`` is omitted;
    :meth:`list` returns every registered representation across all notation
    profiles unless a notation profile is passed explicitly to filter it. The
    registry holds no mutable runtime profile selection. Definitions are ordered by
    notation profile and then symbol id, so ``list`` is deterministic no matter what
    order the catalogue declared them in.
    """

    def __init__(
        self,
        definitions: Iterable[SymbolDefinition],
        *,
        default_notation_profile: str = GENERIC_ISO_NOTATION_PROFILE,
    ) -> None:
        self._default_notation_profile = _require_notation_profile(
            default_notation_profile, "registry default notation profile"
        )
        by_identity: dict[tuple[str, str], SymbolDefinition] = {}
        for definition in definitions:
            identity = (definition.notation_profile, definition.symbol_id)
            if identity in by_identity:
                raise SymbolDefinitionError(
                    "duplicate symbol representation "
                    f"(notation_profile={definition.notation_profile!r}, "
                    f"symbol_id={definition.symbol_id!r})"
                )
            by_identity[identity] = definition
        self._by_identity: dict[tuple[str, str], SymbolDefinition] = by_identity
        self._ordered: tuple[SymbolDefinition, ...] = tuple(
            sorted(
                by_identity.values(),
                key=lambda definition: (definition.notation_profile, definition.symbol_id),
            )
        )

    @property
    def default_notation_profile(self) -> str:
        """The construction-time notation profile the convenience lookups use."""
        return self._default_notation_profile

    def get(self, symbol_id: str, *, notation_profile: str | None = None) -> SymbolDefinition:
        """Return the representation of ``symbol_id`` in one notation profile.

        ``notation_profile`` defaults to this registry's
        :attr:`default_notation_profile`. A requested representation that is absent
        fails closed: the registry never substitutes another notation profile for
        the requested one.
        """
        profile = self._resolve_notation_profile(notation_profile)
        try:
            return self._by_identity[(profile, symbol_id)]
        except KeyError:
            raise SymbolDefinitionError(
                f"unknown symbol representation for symbol id {symbol_id!r} in "
                f"notation profile {profile!r}"
            ) from None

    def list(self, *, notation_profile: str | None = None) -> tuple[SymbolDefinition, ...]:
        """Return registered definitions in stable ``(notation_profile, symbol_id)`` order.

        With no argument every registered representation is returned. With a
        notation profile, only that profile's representations are returned: a
        recognised profile with no registered representation is a valid empty
        result, while an unknown profile fails closed.
        """
        if notation_profile is None:
            return self._ordered
        profile = _require_notation_profile(notation_profile, "requested notation profile")
        return tuple(
            definition for definition in self._ordered if definition.notation_profile == profile
        )

    def _resolve_notation_profile(self, notation_profile: str | None) -> str:
        """Return the requested notation profile, or this registry's default when omitted."""
        if notation_profile is None:
            return self._default_notation_profile
        return _require_notation_profile(notation_profile, "requested notation profile")


def _require_notation_profile(notation_profile: str, label: str) -> str:
    """Return ``notation_profile`` when it is recognised, failing closed otherwise."""
    if notation_profile_policy(notation_profile) is None:
        raise SymbolDefinitionError(
            f"unknown {label} {notation_profile!r}; expected one of {sorted(NOTATION_PROFILES)}"
        )
    return notation_profile


#: The built-in registry over the implemented symbol catalogue.
#:
#: Its convenience default is deliberately ``generic-iso``: the three legacy
#: representations are still authored in it, so ``SYMBOLS.get("valve.gate")`` keeps
#: resolving to the same definition. ``deepplant-default`` is the target product
#: default defined by Issue #124 and now holds its first built-in representation
#: (``fitting.restriction_orifice``, Issue #130), but this slice migrates no
#: definition and does not switch the convenience default: a ``deepplant-default``
#: lookup must request the profile explicitly, and an omitted-profile lookup of a
#: ``deepplant-default``-only symbol fails closed instead of falling back. This is
#: the migration state, not the target state (Issues #124, #125, #130).
SYMBOLS: Final[SymbolRegistry] = SymbolRegistry(
    IMPLEMENTED_SYMBOLS,
    default_notation_profile=GENERIC_ISO_NOTATION_PROFILE,
)
