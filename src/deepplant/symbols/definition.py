# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Canonical machine-readable symbol definitions (Issue #119).

A :class:`SymbolDefinition` is the canonical source of one symbol's geometry:
semantics-free presentation data that the deterministic renderer
(:mod:`deepplant.symbols.svg`) turns into SVG on demand. A checked-in SVG file
is therefore never the canonical geometry, and a semantic model object is never
the symbol (ADR-0003, ADR-0017).

Coordinate system
-----------------

Every coordinate lives in the symbol's own normalized local view box,
``(min_x, min_y, width, height)``, which defaults to the canonical
``0 0 100 100`` (:data:`CANONICAL_VIEW_BOX`) the process symbol pack already
uses (ADR-0008). Coordinates are never screen pixels, and primitives and
anchors are validated to lie inside the declared box.

Vocabularies
------------

The drawing ``profile``, the ``diagram_types`` a symbol may be drawn in, the
anchor ``orientation`` and connection ``kind``, the standards ``verification``
state, and the asset ``origin`` are closed vocabularies. Each is defined once as
a frozenset here and validated when a definition is constructed, so an unknown
value fails loudly instead of silently rendering. ``category`` stays an open,
catalogue-defined subject area (like ``ProcessStep.function``, ADR-0009): the
catalogue grows with the reference material, not with a code change.

Two further invariants are enforced alongside those vocabularies, because the
current slice deliberately supports exactly one asset origin and one drawing
profile: ``deepplant-original`` geometry is accepted only under
``AGPL-3.0-only``, and :data:`GENERIC_ISO_PROFILE` requires at least one
standards relationship recording an *intended* correspondence.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import date
from typing import Literal

#: The canonical normalized symbol view box ``(min_x, min_y, width, height)``.
CANONICAL_VIEW_BOX: tuple[float, float, float, float] = (0.0, 0.0, 100.0, 100.0)

#: The profile whose meaning is "this DeepPlant-authored geometry is *intended*
#: to correspond to the named standards". It is the only profile that imposes a
#: standards requirement, because that requirement belongs to the meaning of the
#: profile and not to :class:`SymbolDefinition` in general. A company, project,
#: or custom profile would not have it.
GENERIC_ISO_PROFILE = "generic-iso"

#: Drawing profiles a symbol may belong to. ``generic-iso`` is the canonical MVP
#: profile; a company or project profile is not defined yet.
PROFILES: frozenset[str] = frozenset({GENERIC_ISO_PROFILE})

#: Standards-correspondence states that record an *intended* correspondence for a
#: concrete geometry. A bare ``reference`` is deliberately absent: it claims no
#: correspondence for any concrete geometry, so it can never make a symbol part of
#: the ``generic-iso`` profile.
INTENDED_CORRESPONDENCE_STATES: frozenset[str] = frozenset(
    {"candidate-alignment", "human-verified"}
)

#: Diagram types a symbol may be drawn in.
DIAGRAM_TYPES: frozenset[str] = frozenset({"pfd", "pid"})

#: Anchor orientations: the geometric direction a connection leaves the symbol
#: in, in the symbol's own coordinate system. This is routing/layout geometry
#: only: it never encodes process-flow direction, signal-flow direction, or
#: semantic inlet/outlet direction. A symbol-local connection role is expressed
#: by the anchor ``name``, not here.
ANCHOR_ORIENTATIONS: frozenset[str] = frozenset({"north", "east", "south", "west"})

#: Connection kinds an anchor may carry.
CONNECTION_KINDS: frozenset[str] = frozenset({"process", "signal"})

#: The only asset origin this slice supports: DeepPlant-authored geometry.
DEEPP_LANT_ORIGINAL_ORIGIN = "deepplant-original"

#: The licence DeepPlant-original symbol geometry is distributed under
#: (``docs/dev/workflow/standards.md``). Because this slice supports exactly one
#: origin, origin and licence are validated as an explicit pair rather than by
#: generic licence policy: ``deepplant-original`` geometry is accepted only under
#: this licence, and any other licence fails closed.
DEEPP_LANT_ORIGINAL_LICENSE = "AGPL-3.0-only"

#: Asset origins a distributed symbol's geometry may come from. Only
#: DeepPlant-original geometry exists in this slice: third-party import support is
#: deliberately deferred until the first concrete third-party asset, at which
#: point the complete ADR-0007 provenance requirements (upstream repository, ref,
#: author/copyright holder, licence, modification state) must be implemented - the
#: two-field record here is not sufficient for an imported asset.
ASSET_ORIGINS: frozenset[str] = frozenset({DEEPP_LANT_ORIGINAL_ORIGIN})

#: Standards-correspondence states: exactly the canonical governance vocabulary
#: in ``docs/dev/workflow/standards.md``. ``reference`` is the fail-safe default
#: (the standard guides direction, terminology, or structure, and no
#: correspondence is claimed for a concrete geometry). ``candidate-alignment``
#: records a concrete geometry that is *intended* to correspond to the named
#: standard but has not been human-verified against an authorized copy; it claims
#: no human check, and human verification is **not** a prerequisite for it.
#: ``human-verified`` may only be set with recorded evidence of a named human
#: check against an authorized copy (ADR-0007). This is independent of the asset
#: copyright/licence question answered by :class:`AssetProvenance`.
VERIFICATION_STATES: frozenset[str] = frozenset(
    {"reference", "candidate-alignment", "human-verified"}
)

_SYMBOL_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")
_ANCHOR_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class SymbolDefinitionError(ValueError):
    """Raised when a symbol definition violates the symbol-library contract."""


@dataclass(frozen=True)
class Line:
    """A straight stroked segment between two symbol-local points."""

    x1: float
    y1: float
    x2: float
    y2: float


@dataclass(frozen=True)
class Circle:
    """A stroked circle: a symbol-local centre and a positive radius."""

    cx: float
    cy: float
    r: float

    def __post_init__(self) -> None:
        if self.r <= 0:
            raise SymbolDefinitionError(f"circle radius must be positive, got {self.r!r}")


@dataclass(frozen=True)
class Polygon:
    """A closed stroked polygon with at least three symbol-local vertices."""

    points: tuple[tuple[float, float], ...]

    def __post_init__(self) -> None:
        if len(self.points) < 3:
            raise SymbolDefinitionError(
                f"a polygon needs at least three vertices, got {len(self.points)}"
            )


#: The graphical primitive vocabulary. Only the primitives an implemented
#: symbol actually needs are defined; a further primitive is added when a
#: verified symbol requires one, never in advance.
GraphicPrimitive = Line | Circle | Polygon


@dataclass(frozen=True)
class SymbolAnchor:
    """One explicit connection slot on a symbol, in symbol-local coordinates.

    An anchor is a machine-readable connection point that a consumer attaches a
    connection line to. It is never inferred from the generated SVG, and it is
    not a semantic connection object: ``symbol anchor != ProcessPort != Port``
    (ADR-0008). Declaration order in :attr:`SymbolDefinition.anchors` is the
    symbol's stable anchor order.

    Field roles:

    ``name``
        the symbol-local connection role: a stable local identifier such as
        ``port_a``, ``port_b``, ``suction``, ``discharge``, ``inlet``,
        ``outlet``, ``large_end``, ``small_end``, or ``tap``;
    ``x`` / ``y``
        the symbol-local connection coordinates;
    ``orientation``
        the geometric direction in which the connection leaves the symbol
        (``north``, ``east``, ``south``, or ``west``);
    ``kind``
        the connection class the slot accepts (``process`` or ``signal``).

    ``orientation`` carries no engineering meaning: it is purely geometric and
    never encodes process-flow direction, signal-flow direction, or semantic
    inlet/outlet direction. A symbol-local role may be expressed by ``name`` (for
    example ``inlet``, ``outlet``, ``suction``, or ``large_end``) and may later be
    mapped to engineering semantics by the consumer, but the anchor itself still
    does not become a :class:`ProcessPort`, a physical port or nozzle, or a
    general semantic connection object. There is no generic ``flow_direction``
    field on an anchor.
    """

    name: str
    x: float
    y: float
    orientation: Literal["north", "east", "south", "west"]
    kind: Literal["process", "signal"]

    def __post_init__(self) -> None:
        if not _ANCHOR_NAME_PATTERN.fullmatch(self.name):
            raise SymbolDefinitionError(
                f"anchor name {self.name!r} must match {_ANCHOR_NAME_PATTERN.pattern}"
            )
        if self.orientation not in ANCHOR_ORIENTATIONS:
            raise SymbolDefinitionError(
                f"anchor {self.name!r} has unknown orientation {self.orientation!r}; "
                f"expected one of {sorted(ANCHOR_ORIENTATIONS)}"
            )
        if self.kind not in CONNECTION_KINDS:
            raise SymbolDefinitionError(
                f"anchor {self.name!r} has unknown connection kind {self.kind!r}; "
                f"expected one of {sorted(CONNECTION_KINDS)}"
            )
        if not (_is_number(self.x) and _is_number(self.y)):
            raise SymbolDefinitionError(
                f"anchor {self.name!r} must have finite numeric coordinates, "
                f"got ({self.x!r}, {self.y!r})"
            )


@dataclass(frozen=True)
class AssetProvenance:
    """Where one symbol's geometry came from, and under what licence.

    Asset provenance and standards correspondence are independent concerns: a
    DeepPlant-original, company, project, or custom symbol has perfectly valid
    provenance without corresponding to any standard, and a
    :class:`StandardsReference` says nothing about copyright.

    ``origin`` is one of :data:`ASSET_ORIGINS`, and ``license`` is the licence
    identifier the geometry is distributed under. Both are required and validated
    on construction, so a distributed definition cannot carry an unknown origin
    or a blank licence.

    The pair also fails closed on an unsupported combination. Because this slice
    deliberately supports a single origin, ``deepplant-original`` geometry is
    accepted only under :data:`DEEPP_LANT_ORIGINAL_LICENSE` (``AGPL-3.0-only``,
    ``docs/dev/workflow/standards.md``); any other licence is rejected rather than
    silently recorded. That is one explicit origin/licence check, not a
    licence-policy mechanism: import support stays deferred until the first
    concrete imported asset (ADR-0007).

    This is the smallest provenance record the current implementation needs: a
    per-definition record, not a runtime provenance manifest, an asset-import
    pipeline, or an asset-management framework (ADR-0007, ADR-0017).
    """

    origin: str
    license: str

    def __post_init__(self) -> None:
        if self.origin not in ASSET_ORIGINS:
            raise SymbolDefinitionError(
                f"unknown asset origin {self.origin!r}; expected one of {sorted(ASSET_ORIGINS)}"
            )
        _require_non_blank(self.license, "asset provenance 'license'")
        _require_origin_license(self.origin, self.license)


@dataclass(frozen=True)
class StandardsReference:
    """The standards relationship one symbol's geometry is intended to express.

    ``standard`` is the document identifier and edition - repository-storable
    metadata under the standards policy: identifiers, editions, official sources,
    and DeepPlant-authored role notes. ``locator`` and ``name`` are optional and
    stay unrecorded until a permitted source or a recorded human verification
    supplies them; nothing restricted is copied into the repository (ADR-0007).

    ``verification`` is one of :data:`VERIFICATION_STATES`, defaults to the
    conservative ``reference``, and is independent of the asset copyright and
    licence provenance recorded in :class:`AssetProvenance`:

    ``reference``
        the standard guides direction, terminology, or structure, and no
        correspondence is claimed for this geometry. No evidence is required.
    ``candidate-alignment``
        this concrete geometry is *intended* to correspond to the named standard,
        but no human has compared it against an authorized copy. A human verifier
        is not required, and no verifier evidence may be recorded.
    ``human-verified``
        a named human checked the concrete geometry against an authorized copy.
        Construction fails closed unless the evidence is complete: a ``locator``,
        ``verified_by``, and ``verified_on``.

    ``verified_by`` and ``verified_on`` are the human-verification evidence, and
    may only appear together with ``verification="human-verified"``, so a
    ``reference`` or ``candidate-alignment`` record can never misleadingly imply a
    human check (ADR-0007).
    """

    standard: str
    locator: str | None = None
    name: str | None = None
    verification: str = "reference"
    verified_by: str | None = None
    verified_on: date | None = None

    def __post_init__(self) -> None:
        _require_non_blank(self.standard, "standards reference 'standard'")
        _require_optional_non_blank(self.locator, "standards reference 'locator'")
        _require_optional_non_blank(self.name, "standards reference 'name'")
        _require_optional_non_blank(self.verified_by, "standards reference 'verified_by'")
        if self.verification not in VERIFICATION_STATES:
            raise SymbolDefinitionError(
                f"unknown verification state {self.verification!r}; "
                f"expected one of {sorted(VERIFICATION_STATES)}"
            )
        _require_optional_date(self.verified_on, "standards reference 'verified_on'")
        if self.verification == "human-verified":
            _require_human_verification(self)
        else:
            _require_no_human_verification(self)


@dataclass(frozen=True)
class SymbolDefinition:
    """One symbol's canonical, machine-readable graphical definition.

    Field roles:

    ``symbol_id``
        stable identity, a lowercase dotted name (``valve.gate``);
    ``name`` / ``category``
        human-readable name and open catalogue subject area;
    ``diagram_types``
        the diagram types the representation may be drawn in;
    ``profile``
        the drawing profile the geometry belongs to;
    ``primitives``
        the geometry, in symbol-local coordinates;
    ``anchors``
        the explicit connection slots, in stable declaration order;
    ``provenance``
        where the geometry came from and under which licence;
    ``standards``
        the standards relationship and its verification state; optional at this
        level, but required by the ``generic-iso`` profile;
    ``view_box``
        the normalized local coordinate box, canonical ``0 0 100 100``.

    Asset provenance is always required, and standards correspondence is optional
    *at this level*: a future company, project, or custom symbol is a valid
    definition without a standards reference, and nothing here invents one for it.
    A profile may require one, and :data:`GENERIC_ISO_PROFILE` does, because that
    profile *means* intended standards correspondence: it demands at least one
    :class:`StandardsReference` recording an intended correspondence, so a bare
    ``reference`` cannot make a symbol part of it.

    The definition carries no tags, line numbers, or project annotations: a
    project-specific label is never part of base symbol geometry.
    """

    symbol_id: str
    name: str
    category: str
    diagram_types: tuple[str, ...]
    profile: str
    primitives: tuple[GraphicPrimitive, ...]
    anchors: tuple[SymbolAnchor, ...]
    provenance: AssetProvenance
    standards: tuple[StandardsReference, ...] = ()
    view_box: tuple[float, float, float, float] = CANONICAL_VIEW_BOX

    def __post_init__(self) -> None:
        if not _SYMBOL_ID_PATTERN.fullmatch(self.symbol_id):
            raise SymbolDefinitionError(
                f"symbol id {self.symbol_id!r} must match {_SYMBOL_ID_PATTERN.pattern}"
            )
        _require_non_blank(self.name, "symbol name")
        _require_non_blank(self.category, "symbol category")
        _require_diagram_types(self.diagram_types)
        if self.profile not in PROFILES:
            raise SymbolDefinitionError(
                f"symbol '{self.symbol_id}' has unknown drawing profile {self.profile!r}; "
                f"expected one of {sorted(PROFILES)}"
            )
        bounds = _view_box_bounds(self.symbol_id, self.view_box)
        _require_primitives(self.symbol_id, self.primitives, bounds)
        _require_anchors(self.symbol_id, self.anchors, bounds)
        _require_unique_standards(self.symbol_id, self.standards)
        _require_profile_standards(self.symbol_id, self.profile, self.standards)


def _is_number(value: object) -> bool:
    """Whether ``value`` is a finite real number (never a bool)."""
    if isinstance(value, bool):
        return False
    return isinstance(value, int | float) and math.isfinite(value)


def _require_non_blank(value: str, label: str) -> None:
    """Fail closed when a required textual field is blank."""
    if not value.strip():
        raise SymbolDefinitionError(f"{label} must be a non-blank string")


def _require_optional_non_blank(value: str | None, label: str) -> None:
    """Fail closed when an optional textual field is recorded but blank."""
    if value is not None and not value.strip():
        raise SymbolDefinitionError(f"{label} must be a non-blank string when recorded")


def _require_optional_date(value: object, label: str) -> None:
    """Fail closed when an optional date field is recorded as a non-date."""
    if value is not None and not isinstance(value, date):
        raise SymbolDefinitionError(f"{label} must be a date when recorded, got {value!r}")


def _require_human_verification(reference: StandardsReference) -> None:
    """Fail closed when a ``human-verified`` record is missing its evidence.

    The canonical policy (``docs/dev/workflow/standards.md``) defines
    ``human-verified`` as a *named human* check against an authorized copy, and
    requires the recorded result to identify the standard, the specific
    symbol/rule, the date, and the verifier (ADR-0007). ``reference`` and
    ``candidate-alignment`` carry no such requirement.
    """
    missing = [
        field
        for field, value in (
            ("locator", reference.locator),
            ("verified_by", reference.verified_by),
            ("verified_on", reference.verified_on),
        )
        if value is None
    ]
    if missing:
        raise SymbolDefinitionError(
            f"standards reference {reference.standard!r} is 'human-verified' but "
            f"records no {' and '.join(missing)}; a human verification needs the "
            "standard, a locator, the verifier, and the date"
        )


def _require_no_human_verification(reference: StandardsReference) -> None:
    """Fail closed when verifier evidence appears without a human verification.

    ``reference`` and ``candidate-alignment`` claim no human check, so storing a
    verifier or date on them would misleadingly imply one.
    """
    recorded = [
        field
        for field, value in (
            ("verified_by", reference.verified_by),
            ("verified_on", reference.verified_on),
        )
        if value is not None
    ]
    if recorded:
        raise SymbolDefinitionError(
            f"standards reference {reference.standard!r} records "
            f"{' and '.join(recorded)} without verification 'human-verified'; "
            "verifier evidence belongs only to a human-verified correspondence"
        )


def _require_diagram_types(diagram_types: tuple[str, ...]) -> None:
    """Fail closed on an empty, unknown, or duplicated diagram-type list."""
    if not diagram_types:
        raise SymbolDefinitionError("a symbol must declare at least one diagram type")
    unknown = [item for item in diagram_types if item not in DIAGRAM_TYPES]
    if unknown:
        raise SymbolDefinitionError(
            f"unknown diagram type(s) {sorted(unknown)}; expected {sorted(DIAGRAM_TYPES)}"
        )
    if len(set(diagram_types)) != len(diagram_types):
        raise SymbolDefinitionError(f"duplicate diagram type(s) in {list(diagram_types)}")


def _view_box_bounds(
    symbol_id: str, view_box: tuple[float, float, float, float]
) -> tuple[float, float, float, float]:
    """Validate a normalized view box and return ``(min_x, min_y, max_x, max_y)``."""
    if len(view_box) != 4 or not all(_is_number(item) for item in view_box):
        raise SymbolDefinitionError(
            f"symbol '{symbol_id}' view box must be four finite numbers, got {view_box!r}"
        )
    min_x, min_y, width, height = view_box
    if width <= 0 or height <= 0:
        raise SymbolDefinitionError(
            f"symbol '{symbol_id}' view box must have a positive size, got {view_box!r}"
        )
    return (min_x, min_y, min_x + width, min_y + height)


def _primitive_points(primitive: GraphicPrimitive) -> tuple[tuple[float, float], ...]:
    """Return the coordinates a primitive is drawn at, for bounds checking."""
    if isinstance(primitive, Line):
        return ((primitive.x1, primitive.y1), (primitive.x2, primitive.y2))
    if isinstance(primitive, Circle):
        return (
            (primitive.cx - primitive.r, primitive.cy),
            (primitive.cx + primitive.r, primitive.cy),
            (primitive.cx, primitive.cy - primitive.r),
            (primitive.cx, primitive.cy + primitive.r),
        )
    return primitive.points


def _require_primitives(
    symbol_id: str,
    primitives: tuple[GraphicPrimitive, ...],
    bounds: tuple[float, float, float, float],
) -> None:
    """Fail closed when geometry is absent or leaves the normalized view box."""
    if not primitives:
        raise SymbolDefinitionError(f"symbol '{symbol_id}' must define at least one primitive")
    min_x, min_y, max_x, max_y = bounds
    for primitive in primitives:
        for x, y in _primitive_points(primitive):
            if not (_is_number(x) and _is_number(y)):
                raise SymbolDefinitionError(
                    f"symbol '{symbol_id}' has a non-finite coordinate in {primitive!r}"
                )
            if not (min_x <= x <= max_x and min_y <= y <= max_y):
                raise SymbolDefinitionError(
                    f"symbol '{symbol_id}' has a coordinate ({x}, {y}) outside the "
                    f"view box {bounds!r}"
                )


def _require_anchors(
    symbol_id: str,
    anchors: tuple[SymbolAnchor, ...],
    bounds: tuple[float, float, float, float],
) -> None:
    """Fail closed on duplicate names or anchors outside the normalized view box."""
    seen: set[str] = set()
    for anchor in anchors:
        if anchor.name in seen:
            raise SymbolDefinitionError(
                f"symbol '{symbol_id}' has duplicate anchor name {anchor.name!r}"
            )
        seen.add(anchor.name)
    min_x, min_y, max_x, max_y = bounds
    for anchor in anchors:
        if not (min_x <= anchor.x <= max_x and min_y <= anchor.y <= max_y):
            raise SymbolDefinitionError(
                f"symbol '{symbol_id}' anchor {anchor.name!r} at "
                f"({anchor.x}, {anchor.y}) is outside the view box {bounds!r}"
            )


def _require_unique_standards(symbol_id: str, standards: tuple[StandardsReference, ...]) -> None:
    """Fail closed when one symbol records the same standard twice.

    A standards relationship is optional at this level: a future company,
    project, or custom symbol may legitimately record none, and each supplied
    :class:`StandardsReference` validates itself on construction. Whether a symbol
    must record one is a profile question, decided by
    :func:`_require_profile_standards` (ADR-0007).
    """
    seen: set[str] = set()
    for reference in standards:
        if reference.standard in seen:
            raise SymbolDefinitionError(
                f"symbol '{symbol_id}' records the standard {reference.standard!r} twice"
            )
        seen.add(reference.standard)


def _require_origin_license(origin: str, license_id: str) -> None:
    """Fail closed when a known origin carries a licence it is not distributed under.

    This slice supports a single origin, so the rule is one explicit pair rather
    than a licence-policy mechanism: ``deepplant-original`` geometry is distributed
    under :data:`DEEPP_LANT_ORIGINAL_LICENSE`, and recording any other licence
    would contradict the repository contract (``docs/dev/workflow/standards.md``,
    ADR-0007).
    """
    if origin == DEEPP_LANT_ORIGINAL_ORIGIN and license_id != DEEPP_LANT_ORIGINAL_LICENSE:
        raise SymbolDefinitionError(
            f"asset origin {DEEPP_LANT_ORIGINAL_ORIGIN!r} is distributed under "
            f"{DEEPP_LANT_ORIGINAL_LICENSE!r}, not {license_id!r}"
        )


def _require_profile_standards(
    symbol_id: str, profile: str, standards: tuple[StandardsReference, ...]
) -> None:
    """Fail closed when a drawing profile requires a correspondence it lacks.

    Standards correspondence stays optional at the :class:`SymbolDefinition`
    level, because a future company, project, or custom profile may legitimately
    record none. :data:`GENERIC_ISO_PROFILE` is different: it *means*
    DeepPlant-authored geometry intended to correspond to the named references, so
    it requires at least one :class:`StandardsReference`, every recorded
    relationship must record that intended correspondence, and a bare
    ``reference`` is not sufficient - it claims no correspondence for a concrete
    geometry (ADR-0007).
    """
    if profile != GENERIC_ISO_PROFILE:
        return
    if not standards:
        raise SymbolDefinitionError(
            f"symbol '{symbol_id}' is profile {GENERIC_ISO_PROFILE!r} but records no "
            "standards reference; that profile means intended standards correspondence"
        )
    without_correspondence = [
        reference.standard
        for reference in standards
        if reference.verification not in INTENDED_CORRESPONDENCE_STATES
    ]
    if without_correspondence:
        raise SymbolDefinitionError(
            f"symbol '{symbol_id}' is profile {GENERIC_ISO_PROFILE!r} but the "
            f"standard(s) {sorted(without_correspondence)} record no intended "
            "correspondence; a bare 'reference' claims no correspondence for a "
            "concrete geometry"
        )
