# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Headless read-only process/PFD SVG renderer.

This module renders a semantic :class:`~deepplant.model.ProcessModel` into a
complete standalone SVG document. It is the first runtime consumer of the
pack-aware SVG symbol + anchor contract (ADR-0008, ``docs/svg-symbols.md``).

Architecture (ADR-0009):

* Input domain: ``ProcessModel`` -> ``ProcessStep[]`` (each owning
  ``ProcessPort[]``) and ``ProcessStream[]``. The physical layer
  (``Equipment``, ``Port``, ``Connection``) is intentionally not rendered.
* ``ProcessStep.function`` is canonical engineering semantics. A
  presentation-layer policy maps each function onto a *symbol role*; an
  explicit per-step ``symbol_role_overrides`` mapping may replace that policy
  for a single render call. The chosen *symbol pack* maps a role to a
  pack-local SVG asset with ordered ``anchor-in-N`` / ``anchor-out-N`` slots.
  Presentation geometry never touches the semantic models (ADR-0003); every
  layout/routing value in this module is transient.
* Output is deterministic: the same ``ProcessModel`` always produces
  byte-for-byte identical SVG. No randomness, timestamps, hash iteration, or
  external resources are used.

Resolution precedence for a step's symbol role is deliberate and simple:

1. an explicit per-step ``symbol_role_overrides`` entry for that step id;
2. the default ``ProcessStep.function`` -> symbol-role presentation policy;
3. otherwise :class:`ProcessRenderError` (no silent fallback to arbitrary
   symbols).

Only the built-in ``basic`` symbol pack is supported by this first
implementation. An unknown pack, a role missing from the chosen pack, a
function without any resolvable symbol role, or a role whose anchor capacity
cannot represent a step's stream incidence raises
:class:`ProcessRenderError` instead of silently degrading. ``unspecified`` is
a legal engineering function but has no default symbol role: rendering it
without an explicit presentation override is a presentation error, not a
semantic-model error.
"""

from __future__ import annotations

import heapq
import math
from collections.abc import Iterator, Mapping
from copy import deepcopy
from dataclasses import dataclass
from importlib import resources
from importlib.resources.abc import Traversable
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element, ParseError

from deepplant.model import ProcessModel, ProcessStep, ProcessStream

__all__ = ["ProcessRenderError", "render_process_svg"]

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
_ANCHOR_GROUP_ID = "deepplant-anchors"
_BUILTIN_PACKS = ("basic",)
_CANONICAL_VIEWBOX = "0 0 100 100"
_TOP_LEVEL_GEOMETRY_NAMES = frozenset(
    {"g", "path", "line", "polyline", "polygon", "rect", "circle", "ellipse"}
)

# --- Renderer-internal presentation geometry ---------------------------------
# The built-in pack draws every symbol on a canonical 100x100 local viewBox
# (docs/svg-symbols.md). The renderer places those canvases on a deterministic
# grid; the constants below are implementation heuristics, not engineering
# semantics.
SYMBOL_SIZE = 100.0
COLUMN_PITCH = 250.0
ROW_PITCH = 180.0
MARGIN = 40.0
ROW_STREET_OFFSET = 30.0  # y offset below a row band's symbols for a "street"
BUS_STAGGER = 20.0  # deterministic separation of parallel vertical bus lines
STUB = 15.0  # short run between a column edge and a gutter/bus
FEEDBACK_APPROACH = 60.0  # recycle rises this far left of its target step
FEEDBACK_DROP = 50.0  # recycle drops this far right of its source step
LANE_CLEARANCE = 70.0  # first feedback lane offset below the lowest step
LANE_PITCH = 44.0  # vertical distance between feedback lanes
ARROW_LENGTH = 10.0
ARROW_HALF_WIDTH = 4.0
STROKE_WIDTH = 2.0
STEP_LABEL_1_OFFSET = 16.0
STEP_LABEL_2_OFFSET = 34.0
STREAM_LABEL_OFFSET = 8.0
ID_FONT_SIZE = 13.0
NAME_FONT_SIZE = 11.0
STREAM_FONT_SIZE = 11.0
FONT_FAMILY = "sans-serif"


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


@dataclass(frozen=True)
class PlacedStep:
    """Transient presentation placement of one process step."""

    step: ProcessStep
    layer: int
    row: int
    x: float
    y: float
    symbol: SymbolVariant
    in_anchor_points: tuple[Point, ...]
    out_anchor_points: tuple[Point, ...]


# ---------------------------------------------------------------------------
# Small SVG helpers (ElementTree, standard library only)
# ---------------------------------------------------------------------------


def _tag(name: str) -> str:
    """Return an ElementTree tag name in the SVG namespace."""
    return f"{{{SVG_NS}}}{name}"


def _element(name: str, attrib: dict[str, str] | None = None) -> Element:
    """Create an SVG-namespace Element with ordered attributes."""
    return Element(_tag(name), attrib or {})


def _fmt(value: float) -> str:
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


def _points_attr(points: list[Point]) -> str:
    return " ".join(f"{_fmt(point.x)},{_fmt(point.y)}" for point in points)


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


def _point_text(x: float, y: float, text: str, size: float) -> Element:
    """Create a single-line centered ``<text>`` element."""
    node = _element(
        "text",
        {
            "x": _fmt(x),
            "y": _fmt(y),
            "text-anchor": "middle",
            "font-family": FONT_FAMILY,
            "font-size": _fmt(size),
            "fill": "currentColor",
        },
    )
    node.text = text
    return node


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


def _pack_directory(pack: str) -> Traversable:
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


def _available_pack_roles(directory: Traversable) -> frozenset[str]:
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


def _resolve_symbol_role_by_step(
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


def _parse_symbol_variant(directory: Traversable, role: str) -> SymbolVariant:
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


# ---------------------------------------------------------------------------
# Topology analysis: incidence, anchors, feedback edges, layers
# ---------------------------------------------------------------------------


def _port_index(step: ProcessStep, port_id: str) -> int:
    """Declaration order of ``port_id`` within a step (a stable ordering key).

    ``ProcessModel`` guarantees the port exists (structural rule S3), so the
    fallback position is unreachable for valid models.
    """
    for index, port in enumerate(step.ports):
        if port.id == port_id:
            return index
    return len(step.ports)


def _ordered_outgoing(streams: list[ProcessStream], step: ProcessStep) -> list[ProcessStream]:
    """Outgoing streams in stable (port order, stream id) order."""
    return sorted(
        (stream for stream in streams if stream.source.step == step.id),
        key=lambda stream: (_port_index(step, stream.source.port), stream.id),
    )


def _ordered_incoming(streams: list[ProcessStream], step: ProcessStep) -> list[ProcessStream]:
    """Incoming streams in stable (port order, stream id) order."""
    return sorted(
        (stream for stream in streams if stream.target.step == step.id),
        key=lambda stream: (_port_index(step, stream.target.port), stream.id),
    )


def _detect_feedback(
    steps: list[ProcessStep],
    outgoing: dict[str, list[ProcessStream]],
    incoming: dict[str, list[ProcessStream]],
) -> list[str]:
    """Classify feedback (back) edges with a deterministic iterative DFS.

    Traversal starts from all steps with zero total incoming ``ProcessStream``
    incidence in declaration order, then visits any remaining unvisited steps in
    declaration order. Incoming incidence is computed before feedback
    classification, so a back edge never makes a downstream node look like a
    root. Within one step, outgoing streams are visited in stable (port order,
    stream id) order. A stream whose target is still on the DFS stack is a
    feedback edge and is returned in discovery order; the remaining forward
    graph is acyclic. This is a deliberately simple deterministic heuristic, not
    a general optimal cycle-cutting algorithm.
    """
    step_ids = [step.id for step in steps]
    starts = [step.id for step in steps if not incoming[step.id]]
    starts.extend(step_id for step_id in step_ids if step_id not in starts)
    white, gray, black = 0, 1, 2
    state = {step_id: white for step_id in step_ids}
    feedback: list[str] = []

    for start in starts:
        if state[start] != white:
            continue
        state[start] = gray
        stack: list[tuple[str, Iterator[ProcessStream]]] = [(start, iter(outgoing.get(start, [])))]
        while stack:
            node, iterator = stack[-1]
            advanced = False
            for stream in iterator:
                target = stream.target.step
                if state[target] == white:
                    state[target] = gray
                    stack.append((target, iter(outgoing.get(target, []))))
                    advanced = True
                    break
                if state[target] == gray:
                    feedback.append(stream.id)
            if not advanced:
                state[node] = black
                stack.pop()
    return feedback


def _assign_layers(
    steps: list[ProcessStep],
    streams: list[ProcessStream],
    outgoing: dict[str, list[ProcessStream]],
    feedback_ids: set[str],
) -> dict[str, int]:
    """Assign each step to a column (layer) by longest forward path.

    The heap processes the forward graph deterministically: roots first, then
    always the node with the smallest ``(layer, declaration index)``. Every
    forward edge therefore points from a strictly earlier column to a strictly
    later one, which keeps the main process direction left-to-right.
    """
    layer_by_id = {step.id: 0 for step in steps}
    index_by_id = {step.id: index for index, step in enumerate(steps)}
    indegree = {step.id: 0 for step in steps}
    adjacency: dict[str, list[ProcessStream]] = {}
    for step in steps:
        adjacency[step.id] = []
    for stream in streams:
        if stream.id in feedback_ids:
            continue
        adjacency[stream.source.step].append(stream)
        indegree[stream.target.step] += 1

    heap: list[tuple[int, int, str]] = []
    for step in steps:
        if indegree[step.id] == 0:
            heap.append((0, index_by_id[step.id], step.id))
    heapq.heapify(heap)

    while heap:
        _, _, step_id = heapq.heappop(heap)
        for stream in adjacency[step_id]:
            candidate = layer_by_id[step_id] + 1
            if candidate > layer_by_id[stream.target.step]:
                layer_by_id[stream.target.step] = candidate
            indegree[stream.target.step] -= 1
            if indegree[stream.target.step] == 0:
                target = stream.target.step
                heapq.heappush(
                    heap,
                    (layer_by_id[target], index_by_id[target], target),
                )
    return layer_by_id


def _place_steps_and_assign(
    process: ProcessModel,
    pack: str,
    variant_by_role: dict[str, SymbolVariant],
    role_by_step: Mapping[str, str],
    outgoing: dict[str, list[ProcessStream]],
    incoming: dict[str, list[ProcessStream]],
    layers: dict[str, int],
) -> tuple[list[PlacedStep], dict[str, PlacedStep], dict[str, int], dict[str, int]]:
    """Compute deterministic node placement and stream-to-anchor assignment.

    Rows derive from each step's incoming forward topology (upstream row,
    upstream output-port order, then stream id), with target declaration order
    and step id as deterministic fallbacks; columns come from the layered
    layout. Input/output roles derive purely from
    ``ProcessStream`` incidence (``target`` -> input, ``source`` -> output).
    Streams map onto ``anchor-in-N`` / ``anchor-out-N`` in stable order
    (semantic port declaration order first, then stream id), matching the
    pack-local anchor contract. ``role_by_step`` carries the already-resolved
    presentation symbol role for each step (ADR-0009): the chosen variant is
    ``variant_by_role[role_by_step[step.id]]``, never ``step.function``.
    Anchor-capacity errors are presentation compatibility errors and are
    raised here as :class:`ProcessRenderError`.
    """
    step_by_id = {step.id: step for step in process.steps}
    declaration_index = {step.id: index for index, step in enumerate(process.steps)}
    row_members: dict[int, list[str]] = {}
    for step in process.steps:
        row_members.setdefault(layers[step.id], []).append(step.id)
    row_by_id: dict[str, int] = {}
    for layer in sorted(row_members):

        def row_key(step_id: str, current_layer: int = layer) -> tuple[int, int, str, int, str]:
            forward = [
                stream for stream in incoming[step_id] if layers[stream.source.step] < current_layer
            ]
            if forward:
                stream = min(
                    forward,
                    key=lambda item: (
                        row_by_id[item.source.step],
                        _port_index(step_by_id[item.source.step], item.source.port),
                        item.id,
                    ),
                )
                return (
                    row_by_id[stream.source.step],
                    _port_index(step_by_id[stream.source.step], stream.source.port),
                    stream.id,
                    declaration_index[step_id],
                    step_id,
                )
            return (len(process.steps), len(process.steps), "", declaration_index[step_id], step_id)

        for index, step_id in enumerate(sorted(row_members[layer], key=row_key)):
            row_by_id[step_id] = index

    out_index: dict[str, int] = {stream.id: 0 for stream in process.streams}
    in_index: dict[str, int] = {stream.id: 0 for stream in process.streams}
    for step in process.steps:
        role = role_by_step[step.id]
        variant = variant_by_role[role]
        outs = outgoing[step.id]
        ins = incoming[step.id]
        if len(outs) > len(variant.out_anchors):
            raise _anchor_capacity_error(
                pack, step, role, "outgoing", len(outs), len(variant.out_anchors)
            )
        if len(ins) > len(variant.in_anchors):
            raise _anchor_capacity_error(
                pack, step, role, "incoming", len(ins), len(variant.in_anchors)
            )
        for index, stream in enumerate(outs):
            out_index[stream.id] = index
        for index, stream in enumerate(ins):
            in_index[stream.id] = index

    placed: list[PlacedStep] = []
    placed_by_id: dict[str, PlacedStep] = {}
    for step in process.steps:
        layer = layers[step.id]
        row = row_by_id[step.id]
        x = MARGIN + layer * COLUMN_PITCH
        y = MARGIN + row * ROW_PITCH
        role = role_by_step[step.id]
        variant = variant_by_role[role]
        placed_step = PlacedStep(
            step=step,
            layer=layer,
            row=row,
            x=x,
            y=y,
            symbol=variant,
            in_anchor_points=tuple(
                Point(x + anchor.x, y + anchor.y) for anchor in variant.in_anchors
            ),
            out_anchor_points=tuple(
                Point(x + anchor.x, y + anchor.y) for anchor in variant.out_anchors
            ),
        )
        placed.append(placed_step)
        placed_by_id[step.id] = placed_step
    return placed, placed_by_id, out_index, in_index


def _anchor_capacity_error(
    pack: str,
    step: ProcessStep,
    symbol_role: str,
    direction: str,
    required: int,
    available: int,
) -> ProcessRenderError:
    noun = "input" if direction == "incoming" else "output"
    return ProcessRenderError(
        f"cannot render step '{step.id}' (engineering function '{step.function}', "
        f"resolved symbol role '{symbol_role}') with symbol pack "
        f"{pack!r}: {required} {direction} stream(s) exceed the {available} available "
        f"{noun} anchor(s) in the selected symbol variant"
    )


def _ordered_feedback(
    process: ProcessModel,
    feedback_ids: set[str],
) -> list[ProcessStream]:
    """Feedback streams in the stable order used for dedicated return lanes.

    Lanes are allocated in (source step declaration order, source port order,
    stream id) order so every graph yields the same lane assignment. The
    semantic model stores no recycle flag; a feedback stream is an ordinary
    ``ProcessStream`` that participates in a graph cycle.
    """
    step_by_id = {step.id: step for step in process.steps}
    index_by_id = {step.id: index for index, step in enumerate(process.steps)}

    def sort_key(stream: ProcessStream) -> tuple[int, int, str]:
        source = step_by_id[stream.source.step]
        return (
            index_by_id[stream.source.step],
            _port_index(source, stream.source.port),
            stream.id,
        )

    feedback = [stream for stream in process.streams if stream.id in feedback_ids]
    return sorted(feedback, key=sort_key)


# ---------------------------------------------------------------------------
# Stream routing (deterministic, simple, no collision search)
# ---------------------------------------------------------------------------


def _route_forward(
    source: PlacedStep,
    source_anchor: Point,
    target: PlacedStep,
    target_anchor: Point,
    out_index: int,
    out_count: int,
) -> list[Point]:
    """Route one ordinary (non-feedback) forward stream orthogonally.

    Adjacent columns sharing a row use a straight horizontal line. Adjacent
    columns on different rows use a single vertical bus inside the empty
    gutter between the two symbols; parallel buses are staggered determinis-
    tically by the source output-anchor index. Streams whose endpoints are
    further apart bend down into the empty horizontal street below the lower
    endpoint row, so they never pass through an intermediate symbol canvas.
    """
    sx = source_anchor.x
    sy = source_anchor.y
    tx = target_anchor.x
    ty = target_anchor.y
    column_span = target.layer - source.layer

    if column_span == 1 and sy == ty:
        return [Point(sx, sy), Point(tx, ty)]

    if column_span == 1:
        bus = (sx + tx) / 2.0 + (out_index - (out_count - 1) / 2.0) * BUS_STAGGER
        return [
            Point(sx, sy),
            Point(bus, sy),
            Point(bus, ty),
            Point(tx, ty),
        ]

    street = MARGIN + max(source.row, target.row) * ROW_PITCH + SYMBOL_SIZE + ROW_STREET_OFFSET
    leave_x = sx + STUB
    enter_x = tx - STUB
    return [
        Point(sx, sy),
        Point(leave_x, sy),
        Point(leave_x, street),
        Point(enter_x, street),
        Point(enter_x, ty),
        Point(tx, ty),
    ]


def _route_feedback(
    source: PlacedStep,
    source_anchor: Point,
    target: PlacedStep,
    target_anchor: Point,
    lane_y: float,
) -> list[Point]:
    """Route one feedback stream on a dedicated return lane below the process.

    The stream leaves the source output anchor to the right, drops to its
    allocated lane, runs left along the lane, rises in the gutter to the left
    of the target, and finally enters the target's input anchor horizontally.
    Feedback streams stay ordinary ``ProcessStream`` objects; they are only
    distinguished geometrically here.
    """
    sx = source_anchor.x
    sy = source_anchor.y
    tx = target_anchor.x
    ty = target_anchor.y
    drop_x = sx + FEEDBACK_DROP
    rise_x = tx - FEEDBACK_APPROACH
    return [
        Point(sx, sy),
        Point(drop_x, sy),
        Point(drop_x, lane_y),
        Point(rise_x, lane_y),
        Point(rise_x, ty),
        Point(tx, ty),
    ]


def _arrow_head(points: list[Point]) -> list[Point]:
    """Small self-contained arrowhead triangle at the end of a route.

    Deterministic and self-contained: no ``<marker>``, no external CSS.
    """
    tip = points[-1]
    previous = points[-2]
    dx = tip.x - previous.x
    dy = tip.y - previous.y
    length = math.hypot(dx, dy)
    if length == 0.0:
        return [tip, tip, tip]
    ux = dx / length
    uy = dy / length
    px = -uy
    py = ux
    base_x = tip.x - ux * ARROW_LENGTH
    base_y = tip.y - uy * ARROW_LENGTH
    return [
        tip,
        Point(base_x + px * ARROW_HALF_WIDTH, base_y + py * ARROW_HALF_WIDTH),
        Point(base_x - px * ARROW_HALF_WIDTH, base_y - py * ARROW_HALF_WIDTH),
    ]


def _stream_label_point(points: list[Point]) -> Point:
    """Baseline position for a stream label near its longest horizontal run.

    The label sits beside (above, or below when the run is in the upper half
    of the route) the longest horizontal segment, far from the endpoint
    glyphs, so step and stream labels remain distinguishable.
    """
    xs = [point.x for point in points]
    ys = [point.y for point in points]
    mid_y = (min(ys) + max(ys)) / 2.0

    best: tuple[float, float, float, float] | None = None
    for left, right in zip(points, points[1:], strict=False):
        if left.y == right.y:
            length = abs(right.x - left.x)
            if best is None or length > best[3]:
                best = (left.y, min(left.x, right.x), max(left.x, right.x), length)
    if best is not None and best[3] >= 40.0:
        x = (best[1] + best[2]) / 2.0
        if best[0] >= mid_y:
            return Point(x, best[0] - STREAM_LABEL_OFFSET)
        return Point(x, best[0] + STREAM_LABEL_OFFSET + STREAM_FONT_SIZE)
    return Point((min(xs) + max(xs)) / 2.0, min(ys) - STREAM_LABEL_OFFSET)


def render_process_svg(
    process: ProcessModel,
    *,
    symbol_pack: str = "basic",
    symbol_role_overrides: Mapping[str, str] | None = None,
) -> str:
    """Render a :class:`~deepplant.model.ProcessModel` as a standalone SVG.

    The returned document is complete (valid XML/SVG with a deterministic
    viewBox, ``currentColor`` engineering line style, UTF-8-safe labels, and a
    trailing newline) and contains no external resources. Repeated calls with
    the same ``process`` return byte-for-byte identical output.

    Symbol roles are resolved at this presentation boundary (ADR-0009), never
    read from the semantic model: for each step, an explicit
    ``symbol_role_overrides`` entry wins over the default engineering
    ``function`` -> symbol-role presentation policy; an engineering function
    with neither fails with :class:`ProcessRenderError`.

    Args:
        process: The semantic process model to render. Physical-layer objects
            are never rendered by this function.
        symbol_pack: The explicitly chosen symbol pack. Only ``basic`` is
            supported by this first implementation.
        symbol_role_overrides: Optional transient presentation overrides keyed
            by ``ProcessStep.id``, each value being the presentation symbol
            role to draw for that step in this render call. The mapping is
            read-only and is never stored on the semantic model, in YAML, or
            in any view file. An override key must reference an existing step
            id, and an override role must be non-blank, filename-safe, and
            present in the selected symbol pack.

    Raises:
        ProcessRenderError: If the pack is unknown, a step's engineering
            function has no resolvable presentation symbol role (and no
            override supplies one), an override is invalid, a resolved role is
            missing from the pack, the pack SVG/anchor contract is broken, or
            a step needs more input/output anchors than its chosen symbol
            provides.
    """
    pack_dir = _pack_directory(symbol_pack)
    available_roles = _available_pack_roles(pack_dir)
    role_by_step = _resolve_symbol_role_by_step(process, symbol_pack, symbol_role_overrides)
    for step in process.steps:
        role = role_by_step[step.id]
        if role not in available_roles:
            raise ProcessRenderError(
                f"cannot render step '{step.id}' (engineering function "
                f"'{step.function}', resolved symbol role '{role}') with symbol pack "
                f"{symbol_pack!r}: the selected pack has no SVG asset for that "
                "presentation symbol role"
            )
    roles = list(dict.fromkeys(role_by_step[step.id] for step in process.steps))
    variant_by_role = {role: _parse_symbol_variant(pack_dir, role) for role in roles}

    outgoing = {step.id: _ordered_outgoing(process.streams, step) for step in process.steps}
    incoming = {step.id: _ordered_incoming(process.streams, step) for step in process.steps}
    feedback_ids = set(_detect_feedback(process.steps, outgoing, incoming))
    layers = _assign_layers(process.steps, process.streams, outgoing, feedback_ids)
    placed, placed_by_id, out_index, in_index = _place_steps_and_assign(
        process,
        symbol_pack,
        variant_by_role,
        role_by_step,
        outgoing,
        incoming,
        layers,
    )

    feedback_streams = _ordered_feedback(process, feedback_ids)
    lowest_symbol_y = max((position.y + SYMBOL_SIZE for position in placed), default=MARGIN)
    lane_base = lowest_symbol_y + LANE_CLEARANCE
    lane_by_id = {
        stream.id: lane_base + index * LANE_PITCH for index, stream in enumerate(feedback_streams)
    }

    routes: dict[str, list[Point]] = {}
    for stream in process.streams:
        source = placed_by_id[stream.source.step]
        target = placed_by_id[stream.target.step]
        source_point = source.out_anchor_points[out_index[stream.id]]
        target_point = target.in_anchor_points[in_index[stream.id]]
        if stream.id in feedback_ids:
            routes[stream.id] = _route_feedback(
                source,
                source_point,
                target,
                target_point,
                lane_by_id[stream.id],
            )
        else:
            out_anchor_count = len(source.symbol.out_anchors)
            routes[stream.id] = _route_forward(
                source,
                source_point,
                target,
                target_point,
                out_index[stream.id],
                out_anchor_count,
            )

    stream_label_points = {
        stream.id: _stream_label_point(routes[stream.id]) for stream in process.streams
    }

    # --- bounds -----------------------------------------------------------
    xs: list[float] = []
    ys: list[float] = []

    def add_box(left: float, top: float, right: float, bottom: float) -> None:
        xs.extend((left, right))
        ys.extend((top, bottom))

    def add_text(x: float, baseline: float, text: str, size: float) -> None:
        half_width = len(text) * size * 0.60 / 2.0
        xs.append(x - half_width)
        xs.append(x + half_width)
        ys.append(baseline - size)
        ys.append(baseline + size * 0.35)

    for position in placed:
        add_box(position.x, position.y, position.x + SYMBOL_SIZE, position.y + SYMBOL_SIZE)
        center_x = position.x + SYMBOL_SIZE / 2.0
        bottom = position.y + SYMBOL_SIZE
        add_text(center_x, bottom + STEP_LABEL_1_OFFSET, position.step.id, ID_FONT_SIZE)
        if position.step.name:
            add_text(center_x, bottom + STEP_LABEL_2_OFFSET, position.step.name, NAME_FONT_SIZE)
    for stream in process.streams:
        for point in routes[stream.id]:
            xs.append(point.x)
            ys.append(point.y)
        label = stream_label_points[stream.id]
        add_text(label.x, label.y, stream.id, STREAM_FONT_SIZE)

    # --- viewBox -----------------------------------------------------------
    default_extent = 2.0 * MARGIN
    if xs:
        view_min_x = min(xs) - MARGIN
        view_min_y = min(ys) - MARGIN
        view_width = (max(xs) + MARGIN) - view_min_x
        view_height = (max(ys) + MARGIN) - view_min_y
    else:
        view_min_x = 0.0
        view_min_y = 0.0
        view_width = default_extent
        view_height = default_extent

    svg = _element(
        "svg",
        {
            "width": _fmt(view_width),
            "height": _fmt(view_height),
            "viewBox": (
                f"{_fmt(view_min_x)} {_fmt(view_min_y)} {_fmt(view_width)} {_fmt(view_height)}"
            ),
        },
    )

    # --- streams, then steps, then labels ----------------------------------
    streams_layer = _element(
        "g",
        {
            "data-deepplant-layer": "streams",
            "stroke": "currentColor",
            "stroke-width": _fmt(STROKE_WIDTH),
            "fill": "none",
        },
    )
    for stream in process.streams:
        points = routes[stream.id]
        stream_group = _element("g", {"data-deepplant-stream": stream.id})
        polyline = _element("polyline", {"points": _points_attr(points)})
        stream_group.append(polyline)
        arrow = _element(
            "polygon",
            {
                "points": _points_attr(_arrow_head(points)),
                "fill": "currentColor",
                "stroke": "none",
            },
        )
        stream_group.append(arrow)
        streams_layer.append(stream_group)

    steps_layer = _element("g", {"data-deepplant-layer": "steps"})
    for position in placed:
        step_group = _element(
            "g",
            {
                "data-deepplant-step": position.step.id,
                "transform": f"translate({_fmt(position.x)} {_fmt(position.y)})",
            },
        )
        for child in position.symbol.geometry:
            step_group.append(deepcopy(child))
        steps_layer.append(step_group)

    labels_layer = _element("g", {"data-deepplant-layer": "labels"})
    for position in placed:
        label_group = _element("g", {"data-deepplant-step-label": position.step.id})
        center_x = position.x + SYMBOL_SIZE / 2.0
        bottom = position.y + SYMBOL_SIZE
        step_id_node = _point_text(
            center_x, bottom + STEP_LABEL_1_OFFSET, position.step.id, ID_FONT_SIZE
        )
        step_id_node.set("font-weight", "bold")
        label_group.append(step_id_node)
        if position.step.name:
            label_group.append(
                _point_text(
                    center_x,
                    bottom + STEP_LABEL_2_OFFSET,
                    position.step.name,
                    NAME_FONT_SIZE,
                )
            )
        labels_layer.append(label_group)
    for stream in process.streams:
        label = stream_label_points[stream.id]
        label_group = _element("g", {"data-deepplant-stream-label": stream.id})
        label_group.append(_point_text(label.x, label.y, stream.id, STREAM_FONT_SIZE))
        labels_layer.append(label_group)

    svg.append(streams_layer)
    svg.append(steps_layer)
    svg.append(labels_layer)

    document = ET.tostring(svg, encoding="unicode")
    return document + "\n"
