# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Notation-profile policy for the machine-rendered symbol library (Issue #125).

A **notation profile** selects *which* graphical notation represents a stable
symbol id. It is presentation-layer configuration and is distinct from visual
theme and from project/company annotation conventions. A project or document
presentation context may later select and persist a notation-profile id, but that
selection context is not itself another notation profile (Issue #124, ADR-0003).

This module is the single source of truth for the closed set of notation profiles
this slice recognises and for the one policy question the definition model has to
answer about a profile: whether it requires its geometry to record an *intended*
standards correspondence. It is deliberately a small immutable record plus a
fixed policy tuple - not a plugin system, a validator registry, a generic rule
engine, a configuration file, or a DSL (Issue #124).

Symbol id vs notation profile
-----------------------------

A symbol id is a stable, notation-independent representation concept
(``valve.gate``). The same symbol id may legitimately have one representation per
notation profile, so a registry identifies a graphical representation by the pair
``(notation_profile, symbol_id)`` (:mod:`deepplant.symbols.registry`). Missing a
requested representation is never permission to substitute another notation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

#: ``deepplant-default``: the DeepPlant-owned practical notation family, and the
#: target product default (Issue #124). Its standards relationship is *optional*:
#: the profile makes no ISO/ISA/PIP conformance claim, so a definition in it may
#: legitimately record no standards reference at all. Its built-in representations
#: are the restriction orifice (``fitting.restriction_orifice``, Issue #130) and the
#: three basic P&ID valves (Issue #132); the three legacy definitions stay in
#: ``generic-iso`` and were not migrated, redrawn, or reclassified.
DEEPPLANT_DEFAULT_NOTATION_PROFILE: Final[str] = "deepplant-default"

#: ``generic-iso``: the legacy/transitional profile the current built-in
#: catalogue was authored in, and this slice's temporary built-in convenience
#: default. It *means* DeepPlant-authored geometry intended to correspond to the
#: named standards, so a definition in this profile must record at least one
#: *intended* standards correspondence. It is retained until the catalogue
#: migration decided by Issue #124 happens (Issues #124, #125).
GENERIC_ISO_NOTATION_PROFILE: Final[str] = "generic-iso"


@dataclass(frozen=True)
class NotationProfilePolicy:
    """One recognised notation profile and the policy the model applies to it.

    ``profile_id``
        the profile identifier recorded on a
        :class:`~deepplant.symbols.definition.SymbolDefinition`;
    ``requires_intended_standards``
        whether a definition in this profile must record at least one standards
        relationship stating an *intended* correspondence
        (``candidate-alignment`` or ``human-verified``), with a bare
        ``reference`` never sufficient because it claims no correspondence for a
        concrete geometry.
    """

    profile_id: str
    requires_intended_standards: bool


#: The recognised production notation profiles, in stable order. A profile absent
#: from this tuple is unknown and fails closed rather than being accepted, and
#: Issue #125 deliberately adds no further profile: ``iso-10628``, PIP, ISA, and
#: company/project profiles belong to later evidence-based slices.
NOTATION_PROFILE_POLICIES: Final[tuple[NotationProfilePolicy, ...]] = (
    NotationProfilePolicy(
        profile_id=DEEPPLANT_DEFAULT_NOTATION_PROFILE,
        requires_intended_standards=False,
    ),
    NotationProfilePolicy(
        profile_id=GENERIC_ISO_NOTATION_PROFILE,
        requires_intended_standards=True,
    ),
)

#: The closed vocabulary of recognised notation profiles, derived from
#: :data:`NOTATION_PROFILE_POLICIES` so the policy set and the vocabulary cannot
#: drift apart.
NOTATION_PROFILES: Final[frozenset[str]] = frozenset(
    policy.profile_id for policy in NOTATION_PROFILE_POLICIES
)


def notation_profile_policy(profile_id: str) -> NotationProfilePolicy | None:
    """Return the policy for ``profile_id``, or ``None`` when it is unrecognised.

    Callers fail closed on ``None`` so that an unknown notation profile is a
    deterministic error rather than a silently accepted value.
    """
    for policy in NOTATION_PROFILE_POLICIES:
        if policy.profile_id == profile_id:
            return policy
    return None
