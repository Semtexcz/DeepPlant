# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""SVG symbol pack resolution and symbol-role presentation policy.

The base module of the headless renderer: the SVG namespace and the
symbol/anchor contract constants, the renderer-internal presentation
primitives (`Point`, `Anchor`, `SymbolVariant`), the pack-aware symbol-pack
resolution through `importlib.resources` (ADR-0008), and the default
engineering-function -> presentation-symbol-role policy (ADR-0009). It also
owns the canonical SVG text accessor `read_process_symbol_svg`.

``ProcessStep.function`` is canonical engineering semantics; a symbol role is
a presentation value resolved here and never stored on the semantic model
(ADR-0003, ADR-0009).
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from importlib import resources
from importlib.resources.abc import Traversable
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element, ParseError

from deepplant.model import ProcessModel

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
_ANCHOR_GROUP_ID = "deepplant-anchors"
_BUILTIN_PACKS = ("basic",)
_CANONICAL_VIEWBOX = "0 0 100 100"
_TOP_LEVEL_GEOMETRY_NAMES = frozenset(
    {"g", "path", "line", "polyline", "polygon", "rect", "circle", "ellipse"}
)

# The built-in pack draws every symbol on this canonical square local viewBox
# (docs/dev/reference/svg-symbols.md); the renderer places those canvases on a
# deterministic grid (see layout/routing constants).
SYMBOL_SIZE = 100.0


class ProcessRenderError(ValueError):
    """Raised when a :class:`ProcessModel` cannot be rendered as an SVG."""


@dataclass(frozen=True)
class Point:
    """An immutable two-dimensional point in output-SVG coordinates."""

    x: float
    y: float


@dataclass(frozen=True)
class Anchor:
    """One pack-local ordered anchor slot, in local symbol coordinates."""

    x: float
    y: float


@dataclass(frozen=True)
class SymbolVariant:
    """Parsed pack-local realization of one symbol role.

    ``geometry`` holds the visible children of the pack SVG with the hidden
    anchor group removed and every (already unsafe) duplicate-prone ``id``
    stripped; ``in_anchors`` / ``out_anchors`` hold the ordered anchor slots
    read from the ``deepplant-anchors`` group.
    """

    role: str
    geometry: tuple[Element, ...]
    in_anchors: tuple[Anchor, ...]
    out_anchors: tuple[Anchor, ...]


def _tag(name: str) -> str:
    """Return an ElementTree tag name in the SVG namespace."""
    return f"{{{SVG_NS}}}{name}"


def element(name: str, attrib: dict[str, str] | None = None) -> Element:
    """Create an SVG-namespace Element with ordered attributes."""
    return Element(_tag(name), attrib or {})


def fmt(value: float) -> str:
    """Format a coordinate deterministically and compactly.

    Whole numbers print without a decimal point; other values print with at
    most three decimals. The representation depends only on the value, never
    on ambient state, so output stays byte-for-byte deterministic.
    """
    rounded = round(value, 3)
    if math.isclose(rounded, round(rounded), abs_tol=1e-9):
        return str(int(round(rounded)))
    text = f"{rounded:.3f}".rstrip("0").rstrip(".")
    return text or "0"


def points_attr(points: list[Point]) -> str:
    return " ".join(f"{fmt(point.x)},{fmt(point.y)}" for point in points)


def _local_name(element: Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _strip_duplicate_ids(element: Element) -> None:
    """Remove ``id`` attributes recursively from a copied geometry subtree.

    The composed diagram may contain the same pack symbol many times. Pack
    SVGs may carry harmless local ids (e.g. ``pump-body``, the anchor group,
    ``anchor-out-0``); duplicating them in one document would be invalid SVG.
    The safe symbol contract forbids functional internal/external references,
    so ids can simply be dropped from every copied visible geometry subtree.
    """
    for node in element.iter():
        if "id" in node.attrib:
            del node.attrib["id"]


# ---------------------------------------------------------------------------
# Pack resolution and symbol parsing
# ---------------------------------------------------------------------------

# --- Presentation policy: engineering function -> symbol role -----------------
# ADR-0009: ``ProcessStep.function`` is canonical engineering semantics and is
# never a symbol role. The renderer owns a small default presentation policy
# that maps the DeepPlant engineering functions known to have a sensible
# ``basic``-pack realisation onto their presentation symbol roles. This is
# presentation-layer policy, not engineering semantics; a future presentation
# or view policy may resolve functions to roles differently, while a different
# symbol pack may realise the same resolved role differently. Keep it private
# unless a concrete public need exists.
_DEFAULT_SYMBOL_ROLE_BY_FUNCTION: dict[str, str] = {
    "source": "source",
    "sink": "sink",
    "mixing": "mixing",
    "splitting_material": "splitting",
    "pumping": "pump",
    "heat_exchange": "heat_exchanger",
}


def pack_directory(pack: str) -> Traversable:
    """Resolve a built-in symbol pack through Python package resources.

    The canonical asset tree lives inside the installed package
    (``src/deepplant/assets/symbols/process/``) so the renderer works from a
    source checkout and from an installed wheel alike. ``pack`` is validated
    before any path traversal so a caller-supplied name can never escape the
    built-in resource tree.
    """
    if pack not in _BUILTIN_PACKS:
        available = ", ".join(repr(name) for name in _BUILTIN_PACKS)
        raise ProcessRenderError(
            f"unknown process symbol pack {pack!r}; supported built-in pack(s): {available}"
        )
    directory = resources.files("deepplant").joinpath("assets", "symbols", "process", pack)
    if not directory.is_dir():
        raise ProcessRenderError(f"process symbol pack {pack!r} has no packaged asset directory")
    return directory


def available_pack_roles(directory: Traversable) -> frozenset[str]:
    """Return the symbol roles (SVG filename stems) present in one pack.

    Roles are pack-local: this is the set the current pack can actually draw,
    not an engineering classification and not a claim about other packs.
    """
    try:
        children = directory.iterdir()
    except OSError as exc:
        raise ProcessRenderError(f"cannot enumerate symbol pack {directory.name!r}: {exc}") from exc
    return frozenset(
        child.name[: -len(".svg")] for child in children if child.name.endswith(".svg")
    )


def resolve_symbol_role_by_step(
    process: ProcessModel,
    symbol_pack: str,
    overrides: Mapping[str, str] | None,
) -> dict[str, str]:
    """Resolve every step to a presentation symbol role for one render call.

    Deterministic precedence (ADR-0009):

    1. an explicit per-step ``overrides[step.id]`` entry, when present;
    2. the default ``ProcessStep.function`` -> symbol-role presentation policy;
    3. otherwise :class:`ProcessRenderError`.

    Overrides are validated before use: an override key must reference an
    existing step id, and an override value must be a non-blank, plain,
    filename-safe symbol role. Overrides live only at this presentation
    boundary; nothing here mutates the semantic model.
    """
    explicit = dict(overrides or {})
    step_ids = {step.id for step in process.steps}
    for step_id in explicit:
        if step_id not in step_ids:
            raise ProcessRenderError(
                f"presentation symbol-role override for unknown step id {step_id!r}: "
                "override keys must reference ProcessSteps in the rendered model"
            )
        role = explicit[step_id]
        if not role.strip():
            raise ProcessRenderError(
                f"presentation symbol-role override for step '{step_id}' has a blank symbol role"
            )
        if not _is_plain_role(role):
            raise ProcessRenderError(
                f"presentation symbol-role override for step '{step_id}' is not a "
                f"plain, filename-safe symbol role: {role!r}"
            )

    resolved: dict[str, str] = {}
    for step in process.steps:
        if step.id in explicit:
            resolved[step.id] = explicit[step.id]
            continue
        default_role = _DEFAULT_SYMBOL_ROLE_BY_FUNCTION.get(step.function)
        if default_role is None:
            raise ProcessRenderError(
                f"cannot render step '{step.id}' (engineering function "
                f"'{step.function}') with symbol pack {symbol_pack!r}: no "
                "presentation symbol role could be resolved for this step (no "
                "per-step symbol-role override and no default "
                "function -> symbol-role mapping for this engineering function)"
            )
        resolved[step.id] = default_role
    return resolved


def _is_plain_role(role: str) -> bool:
    """A role must be a plain filename stem usable inside the pack directory.

    A symbol role is a presentation value chosen by the presentation policy or
    an explicit override; treating it blindly as a filename would let a role
    name files outside the pack. The renderer therefore accepts only plain
    roles resolving to a pack-local ``<role>.svg`` asset.
    """
    return bool(role) and "/" not in role and "\\" not in role and role not in {".", ".."}


def parse_symbol_variant(directory: Traversable, role: str) -> SymbolVariant:
    """Parse one ``<role>.svg`` into visible geometry plus ordered anchors.

    The renderer validates the SVG contract invariants it relies on for
    placement/routing while accepting every contract-permitted top-level
    geometry element, not only ``<g>``.
    """
    if not _is_plain_role(role):
        raise ProcessRenderError(f"cannot select a pack asset for non-filename-safe role {role!r}")
    asset = directory.joinpath(f"{role}.svg")
    try:
        source = asset.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ProcessRenderError(
            f"symbol pack {directory.name!r} has no SVG asset for role {role!r}"
        ) from exc
    except OSError as exc:
        raise ProcessRenderError(
            f"cannot read role {role!r} asset in symbol pack {directory.name!r}: {exc}"
        ) from exc

    try:
        root = ET.fromstring(source)
    except ParseError as exc:
        raise ProcessRenderError(
            f"role {role!r} asset in symbol pack {directory.name!r} is not valid XML: {exc}"
        ) from exc

    if root.tag != _tag("svg"):
        raise ProcessRenderError(
            f"role {role!r} asset in symbol pack {directory.name!r} must have an SVG root"
        )
    if root.get("viewBox") != _CANONICAL_VIEWBOX:
        raise ProcessRenderError(
            f"role {role!r} asset in symbol pack {directory.name!r} must use canonical "
            f"viewBox={_CANONICAL_VIEWBOX!r}"
        )
    if "width" in root.attrib or "height" in root.attrib:
        raise ProcessRenderError(
            f"role {role!r} asset in symbol pack {directory.name!r} must not set fixed width/height"
        )

    anchor_groups = [
        element
        for element in root.iter()
        if _local_name(element) == "g" and element.get("id") == _ANCHOR_GROUP_ID
    ]
    if len(anchor_groups) != 1:
        raise ProcessRenderError(
            f"role {role!r} asset in symbol pack {directory.name!r} must contain exactly "
            f"one <g id={_ANCHOR_GROUP_ID!r}> group"
        )
    anchor_group = anchor_groups[0]

    geometry: list[Element] = []
    for child in root:
        if _local_name(child) not in _TOP_LEVEL_GEOMETRY_NAMES:
            raise ProcessRenderError(
                f"role {role!r} asset in symbol pack {directory.name!r} has an "
                f"unexpected top-level <{_local_name(child)}> element"
            )
        if child is not anchor_group:
            copied = deepcopy(child)
            _remove_anchor_group(copied)
            geometry.append(copied)

    in_slots: list[tuple[int, Anchor]] = []
    out_slots: list[tuple[int, Anchor]] = []
    anchor_ids: set[str] = set()
    for circle in anchor_group:
        if _local_name(circle) != "circle":
            raise ProcessRenderError(
                f"role {role!r} asset in symbol pack {directory.name!r} has a non-circle "
                "element inside the anchors group"
            )
        anchor_id = circle.get("id") or ""
        if anchor_id in anchor_ids:
            raise ProcessRenderError(
                f"role {role!r} asset in symbol pack {directory.name!r} has duplicate "
                f"anchor id {anchor_id!r}"
            )
        anchor_ids.add(anchor_id)
        cx = circle.get("cx")
        cy = circle.get("cy")
        if cx is None or cy is None:
            raise ProcessRenderError(
                f"role {role!r} asset in symbol pack {directory.name!r} has anchor "
                f"{anchor_id!r} without numeric cx/cy"
            )
        parsed = _parse_anchor_slot(anchor_id, cx, cy)
        if parsed is None:
            raise ProcessRenderError(
                f"role {role!r} asset in symbol pack {directory.name!r} has an anchor id "
                f"that is not anchor-in-N/anchor-out-N: {anchor_id!r}"
            )
        index, direction, anchor = parsed
        if direction == "in":
            in_slots.append((index, anchor))
        else:
            out_slots.append((index, anchor))

    def _ordered(slots: list[tuple[int, Anchor]]) -> tuple[Anchor, ...]:
        ordered = sorted(slots, key=lambda slot: slot[0])
        indices = [index for index, _ in ordered]
        if len(indices) != len(set(indices)):
            raise ProcessRenderError(
                f"role {role!r} asset in symbol pack {directory.name!r} has duplicate "
                "anchor indices"
            )
        if indices != list(range(len(indices))):
            raise ProcessRenderError(
                f"role {role!r} asset in symbol pack {directory.name!r} has "
                "non-contiguous anchor indices"
            )
        return tuple(anchor for _, anchor in ordered)

    in_anchors = _ordered(in_slots)
    out_anchors = _ordered(out_slots)
    for child in geometry:
        _strip_duplicate_ids(child)
    return SymbolVariant(
        role=role,
        geometry=tuple(geometry),
        in_anchors=in_anchors,
        out_anchors=out_anchors,
    )


def _remove_anchor_group(element: Element) -> None:
    """Remove the unique anchors group from copied geometry, wherever nested."""
    for child in list(element):
        if _local_name(child) == "g" and child.get("id") == _ANCHOR_GROUP_ID:
            element.remove(child)
        else:
            _remove_anchor_group(child)


def _parse_anchor_slot(anchor_id: str, cx: str, cy: str) -> tuple[int, str, Anchor] | None:
    """Parse one ``anchor-in-N`` / ``anchor-out-N`` circle into a slot."""
    prefix_in = "anchor-in-"
    prefix_out = "anchor-out-"
    if anchor_id.startswith(prefix_in):
        suffix = anchor_id[len(prefix_in) :]
        direction = "in"
    elif anchor_id.startswith(prefix_out):
        suffix = anchor_id[len(prefix_out) :]
        direction = "out"
    else:
        return None
    if not suffix.isdigit():
        raise ProcessRenderError(f"anchor id {anchor_id!r} has a non-numeric index")
    try:
        x_value = float(cx)
        y_value = float(cy)
    except ValueError as exc:
        raise ProcessRenderError(
            f"anchor id {anchor_id!r} has non-numeric cx/cy coordinates"
        ) from exc
    if not math.isfinite(x_value) or not math.isfinite(y_value):
        raise ProcessRenderError(f"anchor id {anchor_id!r} has non-finite cx/cy coordinates")
    if not 0.0 <= x_value <= SYMBOL_SIZE or not 0.0 <= y_value <= SYMBOL_SIZE:
        raise ProcessRenderError(
            f"anchor id {anchor_id!r} has coordinates outside the canonical 100x100 viewBox"
        )
    return int(suffix), direction, Anchor(x=x_value, y=y_value)


def read_process_symbol_svg(symbol_pack: str, symbol_role: str) -> str:
    """Return the canonical SVG text for one presentation symbol role.

    A presentation-facing accessor for the packaged symbol pack: it resolves the
    built-in pack through ``importlib.resources`` (ADR-0008), so a non-SVG
    consumer such as a local viewer reads the single canonical asset copy
    instead of shipping a second one. ``symbol_role`` must be a plain,
    filename-safe role present in the selected pack.

    Raises:
        ProcessRenderError: If the pack is unknown, the role is not a plain
            filename-safe stem, or the pack has no asset for that role.
    """
    directory = pack_directory(symbol_pack)
    if not _is_plain_role(symbol_role):
        raise ProcessRenderError(
            f"cannot select a pack asset for non-filename-safe role {symbol_role!r}"
        )
    asset = directory.joinpath(f"{symbol_role}.svg")
    try:
        return asset.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ProcessRenderError(
            f"symbol pack {symbol_pack!r} has no SVG asset for role {symbol_role!r}"
        ) from exc
    except OSError as exc:
        raise ProcessRenderError(
            f"cannot read role {symbol_role!r} asset in symbol pack {symbol_pack!r}: {exc}"
        ) from exc
