"""Deterministic behaviour tests for the headless process SVG renderer.

The renderer is the first runtime consumer of the pack-aware SVG symbol +
anchor contract (ADR-0008): it derives a standalone SVG process/PFD diagram
from a semantic ``ProcessModel`` only, through an explicitly chosen built-in
symbol pack. These tests prefer public-behaviour and invariant assertions over
private implementation details.
"""

from __future__ import annotations

import re
from copy import deepcopy
from importlib import resources
from pathlib import Path
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

import pytest

from deepplant import ProcessRenderError, load_plant, render_process_svg
from deepplant.model import (
    Plant,
    PlantModel,
    ProcessModel,
    ProcessPort,
    ProcessRef,
    ProcessStep,
    ProcessStream,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REALISTIC_EXAMPLE = REPO_ROOT / "examples" / "realistic-process-fragment" / "plant.yaml"
GOLDEN_SVG = REPO_ROOT / "examples" / "realistic-process-fragment" / "process.svg"

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
ANCHOR_GROUP_ID = "deepplant-anchors"


def _svg_root(document: str) -> Element:
    return ElementTree.fromstring(document)


def _local_name(element: Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _step(step_id: str, step_type: str, ports: list[str], name: str | None = None) -> ProcessStep:
    return ProcessStep(
        id=step_id,
        type=step_type,
        name=name,
        ports=[ProcessPort(id=port_id) for port_id in ports],
    )


def _stream(
    stream_id: str,
    source: str,
    source_port: str,
    target: str,
    target_port: str,
) -> ProcessStream:
    return ProcessStream(
        id=stream_id,
        source=ProcessRef(step=source, port=source_port),
        target=ProcessRef(step=target, port=target_port),
    )


def _groups(root: Element, attribute: str) -> dict[str, Element]:
    """First element per unique value of a data attribute (document order)."""
    found: dict[str, Element] = {}
    for element in root.iter():
        value = element.get(attribute)
        if value is not None and value not in found:
            found[value] = element
    return found


def _translate(group: Element) -> tuple[float, float]:
    transform = group.get("transform")
    assert transform is not None
    match = re.fullmatch(r"translate\(([0-9.+-]+) ([0-9.+-]+)\)", transform)
    assert match is not None, transform
    return float(match.group(1)), float(match.group(2))


def _stream_points(stream_group: Element) -> list[tuple[float, float]]:
    for child in stream_group:
        if _local_name(child) == "polyline":
            points_text = child.get("points")
            assert points_text is not None
            points: list[tuple[float, float]] = []
            for pair in points_text.split():
                x_text, y_text = pair.split(",")
                points.append((float(x_text), float(y_text)))
            return points
    raise AssertionError("stream group has no polyline")


def _strip_ids(element: Element) -> Element:
    copy = deepcopy(element)
    for node in copy.iter():
        if "id" in node.attrib:
            del node.attrib["id"]
    return copy


def _render(process: ProcessModel, pack: str = "basic") -> str:
    return render_process_svg(process, symbol_pack=pack)


def _model_with_process(steps: list[ProcessStep], streams: list[ProcessStream]) -> PlantModel:
    return PlantModel(plant=Plant(id="demo"), process=ProcessModel(steps=steps, streams=streams))


def _realistic_model() -> PlantModel:
    return load_plant(str(REALISTIC_EXAMPLE))


# ---------------------------------------------------------------------------
# Pack resolution and runtime resources
# ---------------------------------------------------------------------------


def test_basic_pack_is_resolvable_at_runtime() -> None:
    model = _model_with_process(steps=[_step("P-1", "pump", ["suction", "discharge"])], streams=[])
    assert model.process is not None
    document = _render(model.process)
    assert 'data-deepplant-step="P-1"' in document


def test_builtin_assets_are_accessible_through_package_resources() -> None:
    directory = resources.files("deepplant").joinpath("assets", "symbols", "process", "basic")
    assert directory.joinpath("pump.svg").is_file()
    for role in (
        "source",
        "mixing",
        "pump",
        "heat_exchanger",
        "splitting",
        "vessel",
        "sink",
    ):
        text = directory.joinpath(f"{role}.svg").read_text(encoding="utf-8")
        assert ANCHOR_GROUP_ID in text
        assert 'viewBox="0 0 100 100"' in text


def test_unknown_symbol_pack_raises_clear_error() -> None:
    model = _model_with_process(steps=[], streams=[])
    assert model.process is not None
    with pytest.raises(ProcessRenderError, match="symbol pack"):
        _render(model.process, pack="not-a-pack")


def test_missing_role_in_pack_raises_clear_error() -> None:
    model = _model_with_process(steps=[_step("R-1", "reactor", [])], streams=[])
    assert model.process is not None
    with pytest.raises(ProcessRenderError, match="reactor"):
        _render(model.process)


# ---------------------------------------------------------------------------
# Realistic process fragment
# ---------------------------------------------------------------------------


def test_realistic_fragment_renders_successfully() -> None:
    model = _realistic_model()
    assert model.process is not None
    document = _render(model.process)
    assert document.endswith("\n")
    assert document.startswith("<svg")
    assert "PS-pump" in document
    assert "S-004" in document
    # The physical bootstrap layer (including FV-101) must stay out of the
    # generated process diagram.
    assert "FV-101" not in document
    assert "P-101" not in document


def test_output_is_valid_xml_svg() -> None:
    model = _realistic_model()
    assert model.process is not None
    root = _svg_root(_render(model.process))
    assert root.tag == f"{{{SVG_NAMESPACE}}}svg"
    assert root.get("viewBox") is not None
    assert root.get("width") is not None
    assert root.get("height") is not None


def test_rendering_is_byte_for_byte_deterministic() -> None:
    model = _realistic_model()
    assert model.process is not None
    first = _render(model.process)
    assert _render(model.process) == first
    # A freshly loaded semantic model from the same YAML gives identical output.
    reloaded = _realistic_model()
    assert reloaded.process is not None
    assert _render(reloaded.process) == first


def test_every_step_appears_exactly_once_in_steps_layer() -> None:
    model = _realistic_model()
    assert model.process is not None
    root = _svg_root(_render(model.process))
    step_groups = _groups(root, "data-deepplant-step")
    assert set(step_groups) == {
        "PS-feed",
        "PS-mix",
        "PS-pump",
        "PS-hx",
        "PS-split",
        "PS-vessel",
        "PS-consumer",
    }
    for _step_id, group in step_groups.items():
        assert _local_name(group) == "g"
        assert group.get("transform") is not None


def test_every_stream_appears_exactly_once_in_streams_layer() -> None:
    model = _realistic_model()
    assert model.process is not None
    root = _svg_root(_render(model.process))
    stream_groups = _groups(root, "data-deepplant-stream")
    assert set(stream_groups) == {f"S-00{number}" for number in range(1, 8)}


def test_correct_symbol_role_is_selected_from_basic_pack() -> None:
    model = _realistic_model()
    assert model.process is not None
    root = _svg_root(_render(model.process))
    step_groups = _groups(root, "data-deepplant-step")
    role_by_step = {step.id: step.type for step in model.process.steps}

    for step_id, group in step_groups.items():
        asset_text = (
            resources.files("deepplant")
            .joinpath(
                "assets",
                "symbols",
                "process",
                "basic",
                f"{role_by_step[step_id]}.svg",
            )
            .read_text(encoding="utf-8")
        )
        asset_root = ElementTree.fromstring(asset_text)
        expected_children = [
            _strip_ids(child)
            for child in asset_root
            if not (_local_name(child) == "g" and child.get("id") == ANCHOR_GROUP_ID)
        ]
        actual_children = list(group)
        assert len(actual_children) == len(expected_children), step_id
        for actual, expected in zip(actual_children, expected_children, strict=False):
            assert ElementTree.tostring(actual) == ElementTree.tostring(expected), step_id


def test_incoming_and_outgoing_streams_use_the_correct_anchor_direction() -> None:
    model = _realistic_model()
    assert model.process is not None
    root = _svg_root(_render(model.process))
    step_groups = _groups(root, "data-deepplant-step")
    stream_groups = _groups(root, "data-deepplant-stream")

    mix_x, _ = _translate(step_groups["PS-mix"])
    vessel_x, vessel_y = _translate(step_groups["PS-vessel"])
    consumer_x, consumer_y = _translate(step_groups["PS-consumer"])
    split_x, _ = _translate(step_groups["PS-split"])

    # S-001 (in_fresh, first mixing port) ends at the upper mixing input;
    # S-002 (in_recycle, second mixing port) ends at the lower one.
    end_001 = _stream_points(stream_groups["S-001"])[-1]
    end_002 = _stream_points(stream_groups["S-002"])[-1]
    assert end_001[0] == mix_x
    assert end_002[0] == mix_x
    assert end_001[1] < end_002[1]

    # S-006/S-007 start at the splitting output anchors (upper for the first
    # declared outgoing port, lower for the second) and end at their targets.
    start_006 = _stream_points(stream_groups["S-006"])[0]
    start_007 = _stream_points(stream_groups["S-007"])[0]
    assert start_006[0] == split_x + 100
    assert start_007[0] == split_x + 100
    assert start_006[1] < start_007[1]
    end_006 = _stream_points(stream_groups["S-006"])[-1]
    end_007 = _stream_points(stream_groups["S-007"])[-1]
    assert end_006[0] == vessel_x
    assert end_007[0] == consumer_x
    assert end_006[1] == vessel_y + 50
    assert end_007[1] == consumer_y + 50


def test_recycle_feedback_is_routed_on_a_lane_below_all_steps() -> None:
    model = _realistic_model()
    assert model.process is not None
    root = _svg_root(_render(model.process))
    step_groups = _groups(root, "data-deepplant-step")
    stream_groups = _groups(root, "data-deepplant-stream")

    lowest_symbol_y = max(_translate(group)[1] + 100 for group in step_groups.values())
    recycle_points = _stream_points(stream_groups["S-002"])
    assert max(point[1] for point in recycle_points) > lowest_symbol_y
    # The recycle returns to the mixing step, which lies to the left.
    assert recycle_points[-1][0] < recycle_points[0][0]


def test_arrowheads_show_stream_direction_toward_the_target() -> None:
    model = _realistic_model()
    assert model.process is not None
    root = _svg_root(_render(model.process))
    stream_groups = _groups(root, "data-deepplant-stream")
    for stream_id, group in stream_groups.items():
        arrow = [child for child in group if _local_name(child) == "polygon"]
        assert len(arrow) == 1, stream_id
        points_text = arrow[0].get("points")
        assert points_text is not None
        tip = points_text.split()[0].split(",")
        assert (float(tip[0]), float(tip[1])) == _stream_points(group)[-1]


def test_no_duplicate_ids_are_introduced_by_repeated_symbol_composition() -> None:
    model = _realistic_model()
    assert model.process is not None
    document = _render(model.process)
    assert document.count('data-deepplant-step="PS-pump"') == 1
    root = _svg_root(document)
    seen: set[str] = set()
    for element in root.iter():
        value = element.get("id")
        if value is not None:
            assert value not in seen, value
            seen.add(value)


def test_step_and_stream_labels_make_the_diagram_inspectable() -> None:
    model = _realistic_model()
    assert model.process is not None
    document = _render(model.process)
    assert "PS-vessel" in document
    assert "Process Vessel Function" in document
    root = _svg_root(document)
    label_groups = _groups(root, "data-deepplant-step-label")
    assert set(label_groups) == {step.id for step in model.process.steps}


def test_committed_realistic_fragment_svg_matches_renderer_output() -> None:
    model = _realistic_model()
    assert model.process is not None
    expected = GOLDEN_SVG.read_text(encoding="utf-8")
    assert expected.endswith("\n")
    assert _render(model.process) == expected


# ---------------------------------------------------------------------------
# Empty / trivial / disconnected / cyclic graphs
# ---------------------------------------------------------------------------


def test_empty_process_renders_a_valid_minimal_svg() -> None:
    model = _model_with_process(steps=[], streams=[])
    assert model.process is not None
    document = _render(model.process)
    root = _svg_root(document)
    assert root.tag == f"{{{SVG_NAMESPACE}}}svg"
    assert root.get("viewBox") is not None
    assert 'data-deepplant-layer="streams"' in document


def test_isolated_step_renders() -> None:
    model = _model_with_process(steps=[_step("A-1", "vessel", ["in", "out"])], streams=[])
    assert model.process is not None
    document = _render(model.process)
    root = _svg_root(document)
    step_groups = _groups(root, "data-deepplant-step")
    assert set(step_groups) == {"A-1"}


def test_source_to_sink_chain_renders() -> None:
    model = _model_with_process(
        steps=[
            _step("FEED", "source", ["out"]),
            _step("SINK", "sink", ["in"]),
        ],
        streams=[_stream("S-001", "FEED", "out", "SINK", "in")],
    )
    assert model.process is not None
    document = _render(model.process)
    root = _svg_root(document)
    stream_groups = _groups(root, "data-deepplant-stream")
    assert set(stream_groups) == {"S-001"}
    points = _stream_points(stream_groups["S-001"])
    assert points[0] != points[-1]


def test_disconnected_components_render_deterministically() -> None:
    model = _model_with_process(
        steps=[
            _step("FEED", "source", ["out"]),
            _step("SINK", "sink", ["in"]),
            _step("B-FEED", "source", ["out"]),
            _step("B-SINK", "sink", ["in"]),
        ],
        streams=[
            _stream("S-001", "FEED", "out", "SINK", "in"),
            _stream("S-002", "B-FEED", "out", "B-SINK", "in"),
        ],
    )
    assert model.process is not None
    first = _render(model.process)
    assert _render(model.process) == first
    step_groups = _groups(_svg_root(first), "data-deepplant-step")
    assert set(step_groups) == {"FEED", "SINK", "B-FEED", "B-SINK"}


def test_cyclic_recycle_graph_renders() -> None:
    # Feed -> mix -> vessel with vessel -> mix as the feedback (recycle) edge.
    model = _model_with_process(
        steps=[
            _step("FEED", "source", ["out"]),
            _step("MIX", "mixing", ["in", "out"]),
            _step("VESSEL", "vessel", ["in", "out"]),
        ],
        streams=[
            _stream("S-001", "FEED", "out", "MIX", "in"),
            _stream("S-002", "MIX", "out", "VESSEL", "in"),
            _stream("S-003", "VESSEL", "out", "MIX", "in"),
        ],
    )
    assert model.process is not None
    root = _svg_root(_render(model.process))
    stream_groups = _groups(root, "data-deepplant-stream")
    assert set(stream_groups) == {"S-001", "S-002", "S-003"}
    step_groups = _groups(root, "data-deepplant-step")
    lowest_symbol_y = max(_translate(group)[1] + 100 for group in step_groups.values())
    # The vessel -> mix stream is a back edge on a dedicated return lane.
    assert max(point[1] for point in _stream_points(stream_groups["S-003"])) > lowest_symbol_y


# ---------------------------------------------------------------------------
# Renderer-only presentation compatibility errors
# ---------------------------------------------------------------------------


def test_insufficient_input_anchors_raises_a_clear_error() -> None:
    model = _model_with_process(
        steps=[
            _step("A", "source", ["out"]),
            _step("B", "source", ["out"]),
            _step("C", "source", ["out"]),
            _step("MIX", "mixing", ["in"]),
        ],
        streams=[
            _stream("S-1", "A", "out", "MIX", "in"),
            _stream("S-2", "B", "out", "MIX", "in"),
            _stream("S-3", "C", "out", "MIX", "in"),
        ],
    )
    assert model.process is not None
    with pytest.raises(ProcessRenderError) as excinfo:
        _render(model.process)
    message = str(excinfo.value)
    assert "MIX" in message
    assert "mixing" in message
    assert "basic" in message
    assert "incoming" in message
    assert "2 available" in message


def test_insufficient_output_anchors_raises_a_clear_error() -> None:
    model = _model_with_process(
        steps=[
            _step("FEED", "source", ["out"]),
            _step("SPLIT", "splitting", ["in", "out"]),
            _step("A", "sink", ["in"]),
            _step("B", "sink", ["in"]),
            _step("C", "sink", ["in"]),
        ],
        streams=[
            _stream("S-0", "FEED", "out", "SPLIT", "in"),
            _stream("S-1", "SPLIT", "out", "A", "in"),
            _stream("S-2", "SPLIT", "out", "B", "in"),
            _stream("S-3", "SPLIT", "out", "C", "in"),
        ],
    )
    assert model.process is not None
    with pytest.raises(ProcessRenderError) as excinfo:
        _render(model.process)
    message = str(excinfo.value)
    assert "SPLIT" in message
    assert "splitting" in message
    assert "outgoing" in message
    assert "2 available" in message


def test_multiple_streams_sharing_one_port_use_stable_stream_id_order() -> None:
    # Both incoming streams share the same semantic mixing port; there is no
    # presentation direction on ProcessPort, so stream id is the tie-breaker.
    model = _model_with_process(
        steps=[
            _step("FEED-B", "source", ["out"]),
            _step("FEED-A", "source", ["out"]),
            _step("MIX", "mixing", ["in"]),
        ],
        streams=[
            _stream("S-B", "FEED-B", "out", "MIX", "in"),
            _stream("S-A", "FEED-A", "out", "MIX", "in"),
        ],
    )
    assert model.process is not None
    root = _svg_root(_render(model.process))
    stream_groups = _groups(root, "data-deepplant-stream")
    end_a = _stream_points(stream_groups["S-A"])[-1]
    end_b = _stream_points(stream_groups["S-B"])[-1]
    # Both end at the mixing left edge; S-A (smaller id) takes the upper
    # anchor-in-0 slot and S-B the lower anchor-in-1 slot.
    assert end_a[0] == end_b[0]
    assert end_a[1] < end_b[1]
