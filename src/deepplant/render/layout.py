# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Deterministic process/PFD layout and placement geometry.

Graph analysis (incidence, feedback classification, layered columns,
topology-derived rows) and the transient placement DTOs a non-SVG consumer
reads through `compute_process_pfd_layout`. Layout is presentation geometry,
never semantic data (ADR-0003); the semantic `ProcessModel` is never mutated.
"""

from __future__ import annotations

import heapq
from collections.abc import Iterator, Mapping
from dataclasses import dataclass

from deepplant.model import ProcessModel, ProcessStep, ProcessStream
from deepplant.render import symbols
from deepplant.render.symbols import (
    SYMBOL_SIZE,
    Point,
    ProcessRenderError,
    SymbolVariant,
)

# Renderer-internal presentation geometry: symbols are placed on a
# deterministic grid of fixed pitch with a fixed outer margin. These are
# implementation heuristics, not engineering semantics.
COLUMN_PITCH = 250.0
ROW_PITCH = 180.0
MARGIN = 40.0


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


@dataclass(frozen=True)
class ProcessPfdAnchor:
    """One ordered pack anchor slot in symbol-local coordinates.

    Coordinates live on the canonical ``0 0 100 100`` pack viewBox. An anchor is
    a presentation slot (``anchor-in-N`` / ``anchor-out-N``), not a semantic
    ``ProcessPort`` (ADR-0008): ``SVG anchor != ProcessPort``.
    """

    index: int
    x: float
    y: float


@dataclass(frozen=True)
class ProcessPfdStepPlacement:
    """Transient presentation placement of one process step."""

    step_id: str
    symbol_role: str
    layer: int
    row: int
    x: float
    y: float
    in_anchors: tuple[ProcessPfdAnchor, ...]
    out_anchors: tuple[ProcessPfdAnchor, ...]


@dataclass(frozen=True)
class ProcessPfdStreamPlacement:
    """Transient presentation placement of one process stream endpoint pair."""

    stream_id: str
    source_step: str
    source_port: str
    source_anchor: int
    target_step: str
    target_port: str
    target_anchor: int
    is_feedback: bool


@dataclass(frozen=True)
class ProcessPfdLayout:
    """Presentation layout for a process/PFD view of one :class:`ProcessModel`.

    This is presentation geometry derived from the semantic process graph and an
    explicitly chosen symbol pack (ADR-0003, ADR-0008, ADR-0009). It carries no
    semantic state, is never stored on the semantic model, and never touches
    YAML or any view file.
    """

    symbol_pack: str
    symbol_size: float
    steps: tuple[ProcessPfdStepPlacement, ...]
    streams: tuple[ProcessPfdStreamPlacement, ...]


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


def ordered_outgoing(streams: list[ProcessStream], step: ProcessStep) -> list[ProcessStream]:
    """Outgoing streams in stable (port order, stream id) order."""
    return sorted(
        (stream for stream in streams if stream.source.step == step.id),
        key=lambda stream: (_port_index(step, stream.source.port), stream.id),
    )


def ordered_incoming(streams: list[ProcessStream], step: ProcessStep) -> list[ProcessStream]:
    """Incoming streams in stable (port order, stream id) order."""
    return sorted(
        (stream for stream in streams if stream.target.step == step.id),
        key=lambda stream: (_port_index(step, stream.target.port), stream.id),
    )


def detect_feedback(
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


def assign_layers(
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


def place_steps_and_assign(
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
    row_by_id = _assign_rows(process, incoming, layers)
    out_index, in_index = _assign_anchor_indices(
        process, pack, variant_by_role, role_by_step, outgoing, incoming
    )
    placed, placed_by_id = _place_steps(process, layers, row_by_id, role_by_step, variant_by_role)
    return placed, placed_by_id, out_index, in_index


def _assign_rows(
    process: ProcessModel, incoming: dict[str, list[ProcessStream]], layers: dict[str, int]
) -> dict[str, int]:
    """Assign each step a row within its column from incoming forward topology.

    The row key is (upstream row, upstream output-port order, stream id), with
    target declaration order and step id as deterministic fallbacks.
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
    return row_by_id


def _assign_anchor_indices(
    process: ProcessModel,
    pack: str,
    variant_by_role: dict[str, SymbolVariant],
    role_by_step: Mapping[str, str],
    outgoing: dict[str, list[ProcessStream]],
    incoming: dict[str, list[ProcessStream]],
) -> tuple[dict[str, int], dict[str, int]]:
    """Map each stream onto a stable anchor index, validating anchor capacity."""
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
    return out_index, in_index


def _place_steps(
    process: ProcessModel,
    layers: dict[str, int],
    row_by_id: dict[str, int],
    role_by_step: Mapping[str, str],
    variant_by_role: dict[str, SymbolVariant],
) -> tuple[list[PlacedStep], dict[str, PlacedStep]]:
    """Build each placed step and its absolute anchor points on the grid."""
    placed: list[PlacedStep] = []
    placed_by_id: dict[str, PlacedStep] = {}
    for step in process.steps:
        layer = layers[step.id]
        row = row_by_id[step.id]
        x = MARGIN + layer * COLUMN_PITCH
        y = MARGIN + row * ROW_PITCH
        variant = variant_by_role[role_by_step[step.id]]
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
    return placed, placed_by_id


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


def ordered_feedback(
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


def compute_process_pfd_layout(
    process: ProcessModel,
    *,
    symbol_pack: str = "basic",
    symbol_role_overrides: Mapping[str, str] | None = None,
) -> ProcessPfdLayout:
    """Compute deterministic presentation placement for a process/PFD view.

    This exposes the renderer's existing placement and symbol-role resolution as
    reusable presentation geometry, so a non-SVG consumer (for example the local
    Engineering Editor projection) does not reimplement layout or the
    ``ProcessStep.function`` -> symbol-role presentation policy in another
    language. The result is transient presentation data (ADR-0003, ADR-0009): it
    is never stored on the semantic model, in YAML, or in any view file, and the
    input ``process`` is never mutated.

    Placement mirrors ``render_process_svg``: columns come from the layered
    forward layout, rows from the deterministic incoming-topology ordering, and
    each stream maps onto the pack's ordered ``anchor-in-N`` / ``anchor-out-N``
    slots by ``ProcessStream`` incidence.

    Raises:
        ProcessRenderError: For the same presentation failures as
            ``render_process_svg`` (unknown pack, unresolvable or invalid
            symbol role, broken pack asset contract, or anchor-capacity
            overflow).
    """
    role_by_step, variant_by_role = symbols.resolve_symbol_variants(
        process, symbol_pack, symbol_role_overrides
    )

    outgoing = {step.id: ordered_outgoing(process.streams, step) for step in process.steps}
    incoming = {step.id: ordered_incoming(process.streams, step) for step in process.steps}
    feedback_ids = set(detect_feedback(process.steps, outgoing, incoming))
    layers = assign_layers(process.steps, process.streams, outgoing, feedback_ids)
    placed, _placed_by_id, out_index, in_index = place_steps_and_assign(
        process,
        symbol_pack,
        variant_by_role,
        role_by_step,
        outgoing,
        incoming,
        layers,
    )

    return ProcessPfdLayout(
        symbol_pack=symbol_pack,
        symbol_size=SYMBOL_SIZE,
        steps=_layout_steps(placed),
        streams=_layout_streams(process, out_index, in_index, feedback_ids),
    )


def _layout_steps(placed: list[PlacedStep]) -> tuple[ProcessPfdStepPlacement, ...]:
    """Project the transient placements into the presentation step DTOs."""
    return tuple(
        ProcessPfdStepPlacement(
            step_id=position.step.id,
            symbol_role=position.symbol.role,
            layer=position.layer,
            row=position.row,
            x=position.x,
            y=position.y,
            in_anchors=tuple(
                ProcessPfdAnchor(index=index, x=anchor.x, y=anchor.y)
                for index, anchor in enumerate(position.symbol.in_anchors)
            ),
            out_anchors=tuple(
                ProcessPfdAnchor(index=index, x=anchor.x, y=anchor.y)
                for index, anchor in enumerate(position.symbol.out_anchors)
            ),
        )
        for position in placed
    )


def _layout_streams(
    process: ProcessModel,
    out_index: dict[str, int],
    in_index: dict[str, int],
    feedback_ids: set[str],
) -> tuple[ProcessPfdStreamPlacement, ...]:
    """Project each stream's endpoints and anchor indices into the DTOs."""
    return tuple(
        ProcessPfdStreamPlacement(
            stream_id=stream.id,
            source_step=stream.source.step,
            source_port=stream.source.port,
            source_anchor=out_index[stream.id],
            target_step=stream.target.step,
            target_port=stream.target.port,
            target_anchor=in_index[stream.id],
            is_feedback=stream.id in feedback_ids,
        )
        for stream in process.streams
    )
