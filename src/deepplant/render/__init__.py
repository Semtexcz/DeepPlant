# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Headless read-only process/PFD renderer.

This package renders a semantic `ProcessModel` into a complete standalone SVG
process/PFD diagram. It exposes the same public surface the former single
`deepplant.render` module provided; the implementation is organized by
capability:

- `symbols`: SVG symbol pack resolution and the function -> role policy;
- `layout`: deterministic graph layout and placement geometry;
- `routing`: orthogonal stream routing and arrowheads;
- `svg`: standalone SVG document generation.

Presentation geometry never touches the semantic models (ADR-0003): every
layout/routing value is transient, and rendering is deterministic.
"""

from __future__ import annotations

from deepplant.render.layout import (
    ProcessPfdAnchor,
    ProcessPfdLayout,
    ProcessPfdStepPlacement,
    ProcessPfdStreamPlacement,
    compute_process_pfd_layout,
)
from deepplant.render.svg import render_process_svg
from deepplant.render.symbols import ProcessRenderError, read_process_symbol_svg

__all__ = [
    "ProcessPfdAnchor",
    "ProcessPfdLayout",
    "ProcessPfdStepPlacement",
    "ProcessPfdStreamPlacement",
    "ProcessRenderError",
    "compute_process_pfd_layout",
    "read_process_symbol_svg",
    "render_process_svg",
]
