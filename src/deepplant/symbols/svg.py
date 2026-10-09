# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Deterministic SVG generation from a symbol definition (Issue #119).

The definition is the canonical geometry and this renderer is the only producer
of symbol SVG: generated output is never hand-edited and never checked in as the
source of truth (ADR-0017). Rendering is restricted by construction — one SVG
namespace, no text, scripts, external references, raster data, embedded fonts,
or fixed pixel dimensions, and a themeable ``currentColor``/``none`` style. Most
primitives stay hollow; a primitive with an explicit binary fill requirement may
opt into ``fill="currentColor"`` where the canonical geometry requires a solid
marker. That is one graphical fact, not a styling engine.
"""

from __future__ import annotations

import math
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element

from deepplant.symbols.definition import Circle, GraphicPrimitive, Line, SymbolDefinition

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NAMESPACE)

#: Engineering line width for generated symbol documents, in view-box units.
STROKE_WIDTH = 2.0


def _element(name: str, attributes: dict[str, str]) -> Element:
    """Create an SVG-namespaced element, keeping attribute insertion order."""
    return Element(f"{{{SVG_NAMESPACE}}}{name}", attributes)


def _number(value: float) -> str:
    """Format a coordinate deterministically and compactly.

    Whole numbers print without a decimal point; other values print with at most
    three decimals. The result depends only on the value, never on ambient state,
    so repeated rendering of one definition is byte-for-byte identical.
    """
    rounded = round(value, 3)
    if math.isclose(rounded, round(rounded), abs_tol=1e-9):
        return str(int(round(rounded)))
    return f"{rounded:.3f}".rstrip("0").rstrip(".")


def _point_pairs(points: tuple[tuple[float, float], ...]) -> str:
    """Format vertices as an SVG ``points`` value."""
    return " ".join(f"{_number(x)},{_number(y)}" for x, y in points)


def _primitive_element(primitive: GraphicPrimitive) -> Element:
    """Build the SVG element for one canonical primitive."""
    if isinstance(primitive, Line):
        return _element(
            "line",
            {
                "x1": _number(primitive.x1),
                "y1": _number(primitive.y1),
                "x2": _number(primitive.x2),
                "y2": _number(primitive.y2),
            },
        )
    if isinstance(primitive, Circle):
        attributes = {
            "cx": _number(primitive.cx),
            "cy": _number(primitive.cy),
            "r": _number(primitive.r),
        }
        if primitive.filled:
            # The one binary fill fact canonical geometry can require: a solid
            # marker painted with the themeable currentColor. A hollow circle
            # emits no fill attribute at all, so its SVG stays byte-identical.
            attributes["fill"] = "currentColor"
        return _element("circle", attributes)
    return _element("polygon", {"points": _point_pairs(primitive.points)})


def render_symbol_svg(definition: SymbolDefinition) -> str:
    """Render one symbol definition as a deterministic standalone SVG document.

    The document carries an explicit normalized ``viewBox`` and no fixed pixel
    ``width``/``height``, so it scales like every other DeepPlant symbol asset.
    Anchors are deliberately **not** written into the document: they are
    canonical definition data and are never inferred back out of generated
    geometry.
    """
    min_x, min_y, width, height = definition.view_box
    view_box = " ".join(_number(item) for item in (min_x, min_y, width, height))
    svg = _element(
        "svg",
        {
            "viewBox": view_box,
            "fill": "none",
            "stroke": "currentColor",
            "stroke-width": _number(STROKE_WIDTH),
        },
    )
    for primitive in definition.primitives:
        svg.append(_primitive_element(primitive))
    return ET.tostring(svg, encoding="unicode") + "\n"
