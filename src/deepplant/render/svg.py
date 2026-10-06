# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Standalone SVG document generation for a rendered process/PFD.

Turns the transient layout and routing geometry into a complete, deterministic
standalone SVG document (ADR-0008, ADR-0009). Output is byte-for-byte stable
for the same `ProcessModel`: no randomness, timestamps, or external resources.
This is the public `render_process_svg` entry point.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element

from deepplant.model import ProcessModel
from deepplant.render import symbols
from deepplant.render.layout import (
    MARGIN,
    assign_layers,
    detect_feedback,
    ordered_feedback,
    ordered_incoming,
    ordered_outgoing,
    place_steps_and_assign,
)
from deepplant.render.routing import (
    LANE_CLEARANCE,
    LANE_PITCH,
    STREAM_FONT_SIZE,
    arrow_head,
    route_feedback,
    route_forward,
    stream_label_point,
)
from deepplant.render.symbols import (
    SYMBOL_SIZE,
    Point,
    ProcessRenderError,
    available_pack_roles,
    element,
    fmt,
    parse_symbol_variant,
    points_attr,
    resolve_symbol_role_by_step,
)

# Engineering line style and text metrics for the generated document.
STROKE_WIDTH = 2.0
STEP_LABEL_1_OFFSET = 16.0
STEP_LABEL_2_OFFSET = 34.0

ID_FONT_SIZE = 13.0
NAME_FONT_SIZE = 11.0
FONT_FAMILY = "sans-serif"


def _point_text(x: float, y: float, text: str, size: float) -> Element:
    """Create a single-line centered ``<text>`` element."""
    node = element(
        "text",
        {
            "x": fmt(x),
            "y": fmt(y),
            "text-anchor": "middle",
            "font-family": FONT_FAMILY,
            "font-size": fmt(size),
            "fill": "currentColor",
        },
    )
    node.text = text
    return node


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
    pack_dir = symbols.pack_directory(symbol_pack)
    available_roles = available_pack_roles(pack_dir)
    role_by_step = resolve_symbol_role_by_step(process, symbol_pack, symbol_role_overrides)
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
    variant_by_role = {role: parse_symbol_variant(pack_dir, role) for role in roles}

    outgoing = {step.id: ordered_outgoing(process.streams, step) for step in process.steps}
    incoming = {step.id: ordered_incoming(process.streams, step) for step in process.steps}
    feedback_ids = set(detect_feedback(process.steps, outgoing, incoming))
    layers = assign_layers(process.steps, process.streams, outgoing, feedback_ids)
    placed, placed_by_id, out_index, in_index = place_steps_and_assign(
        process,
        symbol_pack,
        variant_by_role,
        role_by_step,
        outgoing,
        incoming,
        layers,
    )

    feedback_streams = ordered_feedback(process, feedback_ids)
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
            routes[stream.id] = route_feedback(
                source,
                source_point,
                target,
                target_point,
                lane_by_id[stream.id],
            )
        else:
            out_anchor_count = len(source.symbol.out_anchors)
            routes[stream.id] = route_forward(
                source,
                source_point,
                target,
                target_point,
                out_index[stream.id],
                out_anchor_count,
            )

    stream_label_points = {
        stream.id: stream_label_point(routes[stream.id]) for stream in process.streams
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

    svg = element(
        "svg",
        {
            "width": fmt(view_width),
            "height": fmt(view_height),
            "viewBox": (
                f"{fmt(view_min_x)} {fmt(view_min_y)} {fmt(view_width)} {fmt(view_height)}"
            ),
        },
    )

    # --- streams, then steps, then labels ----------------------------------
    streams_layer = element(
        "g",
        {
            "data-deepplant-layer": "streams",
            "stroke": "currentColor",
            "stroke-width": fmt(STROKE_WIDTH),
            "fill": "none",
        },
    )
    for stream in process.streams:
        points = routes[stream.id]
        stream_group = element("g", {"data-deepplant-stream": stream.id})
        polyline = element("polyline", {"points": points_attr(points)})
        stream_group.append(polyline)
        arrow = element(
            "polygon",
            {
                "points": points_attr(arrow_head(points)),
                "fill": "currentColor",
                "stroke": "none",
            },
        )
        stream_group.append(arrow)
        streams_layer.append(stream_group)

    steps_layer = element("g", {"data-deepplant-layer": "steps"})
    for position in placed:
        step_group = element(
            "g",
            {
                "data-deepplant-step": position.step.id,
                "transform": f"translate({fmt(position.x)} {fmt(position.y)})",
            },
        )
        for child in position.symbol.geometry:
            step_group.append(deepcopy(child))
        steps_layer.append(step_group)

    labels_layer = element("g", {"data-deepplant-layer": "labels"})
    for position in placed:
        label_group = element("g", {"data-deepplant-step-label": position.step.id})
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
        label_group = element("g", {"data-deepplant-stream-label": stream.id})
        label_group.append(_point_text(label.x, label.y, stream.id, STREAM_FONT_SIZE))
        labels_layer.append(label_group)

    svg.append(streams_layer)
    svg.append(steps_layer)
    svg.append(labels_layer)

    document = ET.tostring(svg, encoding="unicode")
    return document + "\n"
