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

from deepplant.model import ProcessModel, ProcessStream
from deepplant.render import symbols
from deepplant.render.layout import (
    MARGIN,
    PlacedStep,
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
    element,
    fmt,
    points_attr,
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
    placed, placed_by_id, out_index, in_index, feedback_ids = _placement(
        process, symbol_pack, symbol_role_overrides
    )
    lane_by_id = _feedback_lane_offsets(placed, ordered_feedback(process, feedback_ids))
    routes = _route_streams(process, placed_by_id, out_index, in_index, feedback_ids, lane_by_id)
    stream_label_points = {
        stream.id: stream_label_point(routes[stream.id]) for stream in process.streams
    }

    view_min_x, view_min_y, view_width, view_height = _compute_view_extent(
        process, placed, routes, stream_label_points
    )

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
    svg.append(_streams_layer(process, routes))
    svg.append(_steps_layer(placed))
    svg.append(_labels_layer(process, placed, stream_label_points))

    document = ET.tostring(svg, encoding="unicode")
    return document + "\n"


def _placement(
    process: ProcessModel,
    symbol_pack: str,
    symbol_role_overrides: Mapping[str, str] | None,
) -> tuple[list[PlacedStep], dict[str, PlacedStep], dict[str, int], dict[str, int], set[str]]:
    """Resolve symbols and compute deterministic placement plus feedback edges."""
    role_by_step, variant_by_role = symbols.resolve_symbol_variants(
        process, symbol_pack, symbol_role_overrides
    )
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
    return placed, placed_by_id, out_index, in_index, feedback_ids


def _feedback_lane_offsets(
    placed: list[PlacedStep], feedback_streams: list[ProcessStream]
) -> dict[str, float]:
    """Assign each feedback stream its dedicated return-lane y offset."""
    lowest_symbol_y = max((position.y + SYMBOL_SIZE for position in placed), default=MARGIN)
    lane_base = lowest_symbol_y + LANE_CLEARANCE
    return {
        stream.id: lane_base + index * LANE_PITCH for index, stream in enumerate(feedback_streams)
    }


def _route_streams(
    process: ProcessModel,
    placed_by_id: dict[str, PlacedStep],
    out_index: dict[str, int],
    in_index: dict[str, int],
    feedback_ids: set[str],
    lane_by_id: dict[str, float],
) -> dict[str, list[Point]]:
    """Route every stream, forward or through its dedicated feedback lane."""
    routes: dict[str, list[Point]] = {}
    for stream in process.streams:
        source = placed_by_id[stream.source.step]
        target = placed_by_id[stream.target.step]
        source_point = source.out_anchor_points[out_index[stream.id]]
        target_point = target.in_anchor_points[in_index[stream.id]]
        if stream.id in feedback_ids:
            routes[stream.id] = route_feedback(
                source, source_point, target, target_point, lane_by_id[stream.id]
            )
        else:
            routes[stream.id] = route_forward(
                source,
                source_point,
                target,
                target_point,
                out_index[stream.id],
                len(source.symbol.out_anchors),
            )
    return routes


def _compute_view_extent(
    process: ProcessModel,
    placed: list[PlacedStep],
    routes: dict[str, list[Point]],
    stream_label_points: dict[str, Point],
) -> tuple[float, float, float, float]:
    """Return the deterministic ``(min_x, min_y, width, height)`` viewBox extent."""
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

    if not xs:
        extent = 2.0 * MARGIN
        return 0.0, 0.0, extent, extent
    view_min_x = min(xs) - MARGIN
    view_min_y = min(ys) - MARGIN
    return (
        view_min_x,
        view_min_y,
        (max(xs) + MARGIN) - view_min_x,
        (max(ys) + MARGIN) - view_min_y,
    )


def _streams_layer(process: ProcessModel, routes: dict[str, list[Point]]) -> Element:
    """Build the streams layer: one polyline plus arrowhead per stream."""
    layer = element(
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
        stream_group.append(element("polyline", {"points": points_attr(points)}))
        stream_group.append(
            element(
                "polygon",
                {
                    "points": points_attr(arrow_head(points)),
                    "fill": "currentColor",
                    "stroke": "none",
                },
            )
        )
        layer.append(stream_group)
    return layer


def _steps_layer(placed: list[PlacedStep]) -> Element:
    """Build the steps layer: one transformed group per placed step."""
    layer = element("g", {"data-deepplant-layer": "steps"})
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
        layer.append(step_group)
    return layer


def _labels_layer(
    process: ProcessModel,
    placed: list[PlacedStep],
    stream_label_points: dict[str, Point],
) -> Element:
    """Build the labels layer: step id/name labels plus stream id labels."""
    layer = element("g", {"data-deepplant-layer": "labels"})
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
        layer.append(label_group)
    for stream in process.streams:
        label = stream_label_points[stream.id]
        label_group = element("g", {"data-deepplant-stream-label": stream.id})
        label_group.append(_point_text(label.x, label.y, stream.id, STREAM_FONT_SIZE))
        layer.append(label_group)
    return layer
