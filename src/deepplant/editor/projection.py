# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""DeepPlant-owned Process/PFD projection for consumer applications.

This module turns a semantic :class:`~deepplant.model.ProcessModel` into an
explicit, read-only presentation projection for consumer applications; the local
Engineering Editor is the first consumer. It is an application/consumer concern
and obeys the one-way dependency direction (ADR-0002, ADR-0003):

    semantic model
            ↑
    projection / application layer
            ↑
    transport / UI

The projection is deliberately DeepPlant-owned: it expresses exactly what a
process/PFD view needs, and it carries no framework concept (no Vue Flow node or
edge types, handles, dimensions, selection, or generated ids). Framework
identity and canvas wiring belong to the frontend adapter, which maps these
projection objects onto its own view objects while keeping the DeepPlant
semantic identity (``kind`` + ``id``) explicit.

Presentation values in this module are the resolved symbol role and the
deterministic placement/anchor geometry delegated to
:func:`~deepplant.render.compute_process_pfd_layout`. They are transient view
data (ADR-0003, ADR-0008, ADR-0009): they are never written back to the semantic
model, to YAML, or to any view file.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from deepplant.model import PlantModel, ProcessStep, ProcessStream
from deepplant.render import ProcessPfdLayout, compute_process_pfd_layout

__all__ = [
    "KIND_PROCESS_STEP",
    "KIND_PROCESS_STREAM",
    "ProcessAnchorProjection",
    "ProcessPfdProjection",
    "ProcessPfdProjectionError",
    "ProcessStepProjection",
    "ProcessStreamEndpointProjection",
    "ProcessStreamProjection",
    "ValidationStatus",
    "project_process_pfd",
    "projection_to_dict",
]

DEFAULT_SYMBOL_PACK: str = "basic"

# DeepPlant semantic identity carried by every projected engineering object.
# Framework ids (Vue Flow node/edge ids) are the adapter's concern and never
# replace this identity.
KIND_PROCESS_STEP: Literal["process-step"] = "process-step"
KIND_PROCESS_STREAM: Literal["process-stream"] = "process-stream"


class ProcessPfdProjectionError(ValueError):
    """Raised when a loaded plant model cannot be projected to a Process/PFD view."""


@dataclass(frozen=True)
class ProcessAnchorProjection:
    """One presentation anchor slot in symbol-local pack coordinates.

    An anchor is an SVG presentation slot (``anchor-in-N`` / ``anchor-out-N``,
    ADR-0008), not a ``ProcessPort``.
    """

    index: int
    x: float
    y: float


@dataclass(frozen=True)
class ProcessStepProjection:
    """Read-only projection of one semantic ``ProcessStep`` for a PFD view."""

    kind: Literal["process-step"]
    id: str
    name: str | None
    function: str
    symbol_role: str
    ports: tuple[str, ...]
    x: float
    y: float
    in_anchors: tuple[ProcessAnchorProjection, ...]
    out_anchors: tuple[ProcessAnchorProjection, ...]


@dataclass(frozen=True)
class ProcessStreamEndpointProjection:
    """Read-only projection of one ``ProcessStream`` endpoint."""

    step: str
    port: str
    anchor: int


@dataclass(frozen=True)
class ProcessStreamProjection:
    """Read-only projection of one semantic ``ProcessStream`` for a PFD view."""

    kind: Literal["process-stream"]
    id: str
    name: str | None
    source: ProcessStreamEndpointProjection
    target: ProcessStreamEndpointProjection
    is_feedback: bool


@dataclass(frozen=True)
class ValidationStatus:
    """Current validation state, owned by the Python DeepPlant boundary."""

    valid: bool
    message: str


@dataclass(frozen=True)
class ProcessPfdProjection:
    """Read-only Process/PFD projection of one ``PlantModel``.

    Carries only what a process/PFD view of this slice needs: explicit semantic
    identity, the semantic properties shown to the user, and DeepPlant-owned
    presentation geometry. It never carries physical-layer objects and never
    carries framework state.
    """

    plant_id: str
    plant_name: str | None
    symbol_pack: str
    symbol_size: float
    steps: tuple[ProcessStepProjection, ...]
    streams: tuple[ProcessStreamProjection, ...]
    validation: ValidationStatus


def project_process_pfd(
    model: PlantModel,
    *,
    symbol_pack: str = DEFAULT_SYMBOL_PACK,
    symbol_role_overrides: Mapping[str, str] | None = None,
) -> ProcessPfdProjection:
    """Project a loaded plant model into a read-only Process/PFD view.

    The semantic ``ProcessModel`` is the only source of engineering meaning. The
    physical layer (``Equipment`` / ``Port`` / ``Connection`` / ``PipingModel``)
    is deliberately excluded: this slice is Process/PFD only, and no
    process ↔ physical mapping exists (ADR-0016).

    ``symbol_role_overrides`` reuses the renderer's presentation-boundary concept
    (ADR-0009): a transient ``ProcessStep.id`` -> symbol-role mapping supplied by
    the caller for this projection only. It is never stored on the semantic
    model, in YAML, or in any view file, so the realistic fragment's vessel can
    be drawn as a vessel while its canonical ``function`` stays ``unspecified``.

    Raises:
        ProcessPfdProjectionError: If the plant has no ``process`` section to
            project.
        ProcessRenderError: If the process cannot be presented (unknown or
            unresolvable symbol role, invalid override, broken pack asset
            contract, or anchor-capacity overflow).
    """
    process = model.process
    if process is None:
        raise ProcessPfdProjectionError(
            f"plant '{model.plant.id}' has no process model to project: "
            "no 'process' section is authored in this plant"
        )

    layout = compute_process_pfd_layout(
        process,
        symbol_pack=symbol_pack,
        symbol_role_overrides=symbol_role_overrides,
    )

    step_by_id = {step.id: step for step in process.steps}
    streams_by_id = {stream.id: stream for stream in process.streams}

    return ProcessPfdProjection(
        plant_id=model.plant.id,
        plant_name=model.plant.name,
        symbol_pack=layout.symbol_pack,
        symbol_size=layout.symbol_size,
        steps=_projected_steps(layout, step_by_id),
        streams=_projected_streams(layout, streams_by_id),
        validation=ValidationStatus(valid=True, message="Valid"),
    )


def _projected_steps(
    layout: ProcessPfdLayout, step_by_id: Mapping[str, ProcessStep]
) -> tuple[ProcessStepProjection, ...]:
    """Project each placed step with its semantic properties and geometry."""
    return tuple(
        ProcessStepProjection(
            kind=KIND_PROCESS_STEP,
            id=placement.step_id,
            name=step_by_id[placement.step_id].name,
            function=step_by_id[placement.step_id].function,
            symbol_role=placement.symbol_role,
            ports=tuple(port.id for port in step_by_id[placement.step_id].ports),
            x=placement.x,
            y=placement.y,
            in_anchors=tuple(
                ProcessAnchorProjection(index=anchor.index, x=anchor.x, y=anchor.y)
                for anchor in placement.in_anchors
            ),
            out_anchors=tuple(
                ProcessAnchorProjection(index=anchor.index, x=anchor.x, y=anchor.y)
                for anchor in placement.out_anchors
            ),
        )
        for placement in layout.steps
    )


def _projected_streams(
    layout: ProcessPfdLayout, streams_by_id: Mapping[str, ProcessStream]
) -> tuple[ProcessStreamProjection, ...]:
    """Project each placed stream endpoint pair with its semantic name."""
    return tuple(
        ProcessStreamProjection(
            kind=KIND_PROCESS_STREAM,
            id=placement.stream_id,
            name=streams_by_id[placement.stream_id].name,
            source=ProcessStreamEndpointProjection(
                step=placement.source_step,
                port=placement.source_port,
                anchor=placement.source_anchor,
            ),
            target=ProcessStreamEndpointProjection(
                step=placement.target_step,
                port=placement.target_port,
                anchor=placement.target_anchor,
            ),
            is_feedback=placement.is_feedback,
        )
        for placement in layout.streams
    )


def projection_to_dict(projection: ProcessPfdProjection) -> dict[str, object]:
    """Serialize a projection into the JSON-ready transport shape.

    The transport shape stays DeepPlant-owned. It carries explicit semantic
    identity (``kind`` + ``id``), the semantic properties the Inspector shows,
    and DeepPlant presentation geometry only. It deliberately contains no
    framework-specific concept (no Vue Flow node/edge type, handle, dimension,
    selection, or generated id); the frontend adapter produces those.
    """
    payload: dict[str, object] = {
        "plant": {"id": projection.plant_id, "name": projection.plant_name},
        "symbol_pack": projection.symbol_pack,
        "symbol_size": projection.symbol_size,
        "validation": {
            "valid": projection.validation.valid,
            "message": projection.validation.message,
        },
        "steps": [
            {
                "kind": step.kind,
                "id": step.id,
                "name": step.name,
                "function": step.function,
                "symbol_role": step.symbol_role,
                "ports": list(step.ports),
                "x": step.x,
                "y": step.y,
                "in_anchors": [
                    {"index": anchor.index, "x": anchor.x, "y": anchor.y}
                    for anchor in step.in_anchors
                ],
                "out_anchors": [
                    {"index": anchor.index, "x": anchor.x, "y": anchor.y}
                    for anchor in step.out_anchors
                ],
            }
            for step in projection.steps
        ],
        "streams": [
            {
                "kind": stream.kind,
                "id": stream.id,
                "name": stream.name,
                "source": {
                    "step": stream.source.step,
                    "port": stream.source.port,
                    "anchor": stream.source.anchor,
                },
                "target": {
                    "step": stream.target.step,
                    "port": stream.target.port,
                    "anchor": stream.target.anchor,
                },
                "is_feedback": stream.is_feedback,
            }
            for stream in projection.streams
        ],
    }
    return payload
