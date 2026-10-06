# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Deterministic orthogonal stream routing geometry.

Transient route polylines from a source output anchor to a target input
anchor, including the dedicated feedback (recycle) return lanes and the
self-contained arrowheads. Routing is presentation geometry only; feedback is
distinguished geometrically, never by a semantic kind (ADR-0003).
"""

from __future__ import annotations

import math

from deepplant.render.layout import MARGIN, ROW_PITCH, PlacedStep
from deepplant.render.symbols import SYMBOL_SIZE, Point

# Routing heuristics: gutters/streets between symbol columns, deterministic
# parallel-bus staggering, and dedicated feedback lanes below the diagram.
ROW_STREET_OFFSET = 30.0  # y offset below a row band's symbols for a "street"
BUS_STAGGER = 20.0  # deterministic separation of parallel vertical bus lines
STUB = 15.0  # short run between a column edge and a gutter/bus
FEEDBACK_APPROACH = 60.0  # recycle rises this far left of its target step
FEEDBACK_DROP = 50.0  # recycle drops this far right of its source step
LANE_CLEARANCE = 70.0  # first feedback lane offset below the lowest step
LANE_PITCH = 44.0  # vertical distance between feedback lanes
ARROW_LENGTH = 10.0
ARROW_HALF_WIDTH = 4.0

STREAM_LABEL_OFFSET = 8.0
STREAM_FONT_SIZE = 11.0

# ---------------------------------------------------------------------------
# Stream routing (deterministic, simple, no collision search)
# ---------------------------------------------------------------------------


def route_forward(
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


def route_feedback(
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


def arrow_head(points: list[Point]) -> list[Point]:
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


def stream_label_point(points: list[Point]) -> Point:
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
