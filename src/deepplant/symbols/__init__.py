# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Machine-rendered standard symbol library (Issue #119).

A symbol's canonical geometry is a typed, machine-readable
:class:`~deepplant.symbols.definition.SymbolDefinition`, not an SVG file:
:func:`~deepplant.symbols.svg.render_symbol_svg` generates SVG from the
definition deterministically, and :data:`~deepplant.symbols.registry.SYMBOLS`
looks a graphical representation up by notation profile and stable symbol id
(Issue #125).

The package holds presentation data only: it carries no project tags, line
numbers, or company conventions, nothing it defines enters the semantic model,
and it imports nothing outside the standard library, so symbols can be rendered
from Python and the CLI without the editor, a browser, or a network
(ADR-0003, ADR-0007, ADR-0017).
"""

from deepplant.symbols.definition import (
    CANONICAL_VIEW_BOX,
    AssetProvenance,
    Circle,
    Line,
    Polygon,
    StandardsReference,
    SymbolAnchor,
    SymbolDefinition,
    SymbolDefinitionError,
)
from deepplant.symbols.registry import SYMBOLS, SymbolRegistry
from deepplant.symbols.svg import render_symbol_svg

__all__ = [
    "CANONICAL_VIEW_BOX",
    "SYMBOLS",
    "AssetProvenance",
    "Circle",
    "Line",
    "Polygon",
    "StandardsReference",
    "SymbolAnchor",
    "SymbolDefinition",
    "SymbolDefinitionError",
    "SymbolRegistry",
    "render_symbol_svg",
]
