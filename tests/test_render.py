"""Deterministic behaviour tests for the headless process SVG renderer.

The renderer is the first runtime consumer of the pack-aware SVG symbol +
anchor contract (ADR-0008): it derives a standalone SVG process/PFD diagram
from a semantic ``ProcessModel`` only, through an explicitly chosen built-in
symbol pack. These tests prefer public-behaviour and invariant assertions over
private implementation details.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from copy import deepcopy
from importlib import resources
from pathlib import Path
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

import pytest

from deepplant import (
    ProcessRenderError,
    load_plant,
    render_process_svg,
)
from deepplant import (
    render as render_module,
)
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

# PS-vessel has engineering function "unspecified" (ADR-0009). The committed
# realistic diagram draws it as a vessel through an explicit transient
# presentation override, exactly like the renderer API call documented in the
# example README.
REALISTIC_SYMBOL_ROLE_OVERRIDES = {"PS-vessel": "vessel"}

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
ANCHOR_GROUP_ID = "deepplant-anchors"


def _svg_root(document: str) -> Element:
    return ElementTree.fromstring(document)


def _local_name(element: Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _step(step_id: str, function: str, ports: list[str], name: str | None = None) -> ProcessStep:
    return ProcessStep(
        id=step_id,
        function=function,
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
    """Elements indexed by an attribute that is expected to be unique.

    A duplicated value now fails loudly instead of silently keeping the first
    element, so "exactly once" tests genuinely detect duplicate groups.
    """
    found: dict[str, Element] = {}
    for element in root.iter():
        value = element.get(attribute)
        if value is not None:
            assert value not in found, f"duplicate {attribute}={value!r}"
            found[value] = element
    return found


def _attribute_values(root: Element, attribute: str) -> list[str]:
    """All values of an exact data attribute in document order."""
    values: list[str] = []
    for element in root.iter():
        value = element.get(attribute)
        if value is not None:
            values.append(value)
    return values


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


def _render(
    process: ProcessModel,
    pack: str = "basic",
    overrides: Mapping[str, str] | None = None,
) -> str:
    return render_process_svg(process, symbol_pack=pack, symbol_role_overrides=overrides)


def _model_with_process(steps: list[ProcessStep], streams: list[ProcessStream]) -> PlantModel:
    return PlantModel(plant=Plant(id="demo"), process=ProcessModel(steps=steps, streams=streams))


def _realistic_model() -> PlantModel:
    return load_plant(str(REALISTIC_EXAMPLE))


def _realistic_svg() -> str:
    """Render the realistic fragment the way the committed golden SVG was made."""
    model = _realistic_model()
    assert model.process is not None
    return render_process_svg(
        model.process,
        symbol_pack="basic",
        symbol_role_overrides=REALISTIC_SYMBOL_ROLE_OVERRIDES,
    )


# ---------------------------------------------------------------------------
# Pack resolution and runtime resources
# ---------------------------------------------------------------------------


def test_basic_pack_is_resolvable_at_runtime() -> None:
    model = _model_with_process(
        steps=[_step("P-1", "pumping", ["suction", "discharge"])], streams=[]
    )
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


def test_unspecified_function_without_override_raises_a_clear_error() -> None:
    # ``unspecified`` is a legal semantic function (ADR-0009) but has no
    # default presentation symbol role: rendering it without an explicit
    # override is a presentation error, not a semantic-model error.
    model = _model_with_process(steps=[_step("R-1", "unspecified", [])], streams=[])
    assert model.process is not None
    with pytest.raises(ProcessRenderError) as exc_info:
        _render(model.process)
    message = str(exc_info.value)
    assert "R-1" in message
    assert "unspecified" in message
    assert "basic" in message
    assert "no presentation symbol role could be resolved" in message


# ---------------------------------------------------------------------------
# Realistic process fragment
# ---------------------------------------------------------------------------


def test_realistic_fragment_renders_successfully() -> None:
    document = _realistic_svg()
    assert document.endswith("\n")
    assert document.startswith("<svg")
    assert "PS-pump" in document
    assert "S-004" in document
    # The physical bootstrap layer (including FV-101) must stay out of the
    # generated process diagram.
    assert "FV-101" not in document
    assert "P-101" not in document


def test_output_is_valid_xml_svg() -> None:
    root = _svg_root(_realistic_svg())
    assert root.tag == f"{{{SVG_NAMESPACE}}}svg"
    assert root.get("viewBox") is not None
    assert root.get("width") is not None
    assert root.get("height") is not None


def test_rendering_is_byte_for_byte_deterministic() -> None:
    first = _realistic_svg()
    assert _realistic_svg() == first
    # A freshly loaded semantic model from the same YAML gives identical output.
    assert _realistic_svg() == first


def test_every_step_appears_exactly_once_in_steps_layer() -> None:
    root = _svg_root(_realistic_svg())
    expected_ids = {
        "PS-feed",
        "PS-mix",
        "PS-pump",
        "PS-hx",
        "PS-split",
        "PS-vessel",
        "PS-consumer",
    }
    step_values = _attribute_values(root, "data-deepplant-step")
    assert set(step_values) == expected_ids
    assert all(step_values.count(step_id) == 1 for step_id in expected_ids)
    step_groups = _groups(root, "data-deepplant-step")
    for _step_id, group in step_groups.items():
        assert _local_name(group) == "g"
        assert group.get("transform") is not None


def test_every_stream_appears_exactly_once_in_streams_layer() -> None:
    root = _svg_root(_realistic_svg())
    expected_ids = {f"S-00{number}" for number in range(1, 8)}
    stream_values = _attribute_values(root, "data-deepplant-stream")
    assert set(stream_values) == expected_ids
    assert all(stream_values.count(stream_id) == 1 for stream_id in expected_ids)


def test_correct_symbol_role_is_selected_from_basic_pack() -> None:
    # Roles are resolved at the presentation boundary (ADR-0009): default
    # engineering-function policy, plus the explicit PS-vessel override.
    role_by_step = {
        "PS-feed": "source",
        "PS-mix": "mixing",
        "PS-pump": "pump",
        "PS-hx": "heat_exchanger",
        "PS-split": "splitting",
        "PS-vessel": "vessel",
        "PS-consumer": "sink",
    }
    root = _svg_root(_realistic_svg())
    step_groups = _groups(root, "data-deepplant-step")

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
    root = _svg_root(_realistic_svg())
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
    # The first declared split output (out_vessel) targets the upper row, so
    # PS-vessel renders above PS-consumer even though the consumer id sorts
    # lexicographically first.
    assert vessel_y < consumer_y
    assert end_006[1] < end_007[1]


def test_recycle_feedback_is_routed_on_a_lane_below_all_steps() -> None:
    root = _svg_root(_realistic_svg())
    step_groups = _groups(root, "data-deepplant-step")
    stream_groups = _groups(root, "data-deepplant-stream")

    lowest_symbol_y = max(_translate(group)[1] + 100 for group in step_groups.values())
    recycle_points = _stream_points(stream_groups["S-002"])
    assert max(point[1] for point in recycle_points) > lowest_symbol_y
    # The recycle returns to the mixing step, which lies to the left.
    assert recycle_points[-1][0] < recycle_points[0][0]


def test_arrowheads_show_stream_direction_toward_the_target() -> None:
    root = _svg_root(_realistic_svg())
    stream_groups = _groups(root, "data-deepplant-stream")
    for stream_id, group in stream_groups.items():
        arrow = [child for child in group if _local_name(child) == "polygon"]
        assert len(arrow) == 1, stream_id
        points_text = arrow[0].get("points")
        assert points_text is not None
        tip = points_text.split()[0].split(",")
        assert (float(tip[0]), float(tip[1])) == _stream_points(group)[-1]


def test_no_duplicate_ids_are_introduced_by_repeated_symbol_composition() -> None:
    document = _realistic_svg()
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
    document = _render(model.process, overrides=REALISTIC_SYMBOL_ROLE_OVERRIDES)
    assert "PS-vessel" in document
    assert "Process Vessel Function" in document
    root = _svg_root(document)
    label_groups = _groups(root, "data-deepplant-step-label")
    assert set(label_groups) == {step.id for step in model.process.steps}


def test_committed_realistic_fragment_svg_matches_renderer_output() -> None:
    expected = GOLDEN_SVG.read_text(encoding="utf-8")
    assert expected.endswith("\n")
    assert _realistic_svg() == expected


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
    model = _model_with_process(steps=[_step("A-1", "unspecified", ["in", "out"])], streams=[])
    assert model.process is not None
    # An unspecified function renders only with an explicit presentation role.
    document = _render(model.process, overrides={"A-1": "vessel"})
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


def test_root_first_feedback_detection_handles_awkward_step_declaration_order() -> None:
    # Graph semantics: FEED -> MIX -> VESSEL stays forward and VESSEL -> MIX is
    # the recycle (feedback) edge. Declaring the steps inside the cycle first
    # must not flip that reading: DFS roots come from topology (zero incoming),
    # never from declaration order or engineering function.
    model = _model_with_process(
        steps=[
            _step("VESSEL", "unspecified", ["in", "out"]),
            _step("MIX", "mixing", ["in", "out"]),
            _step("FEED", "source", ["out"]),
        ],
        streams=[
            _stream("S-001", "FEED", "out", "MIX", "in"),
            _stream("S-002", "MIX", "out", "VESSEL", "in"),
            _stream("S-003", "VESSEL", "out", "MIX", "in"),
        ],
    )
    assert model.process is not None
    root = _svg_root(_render(model.process, overrides={"VESSEL": "vessel"}))
    stream_groups = _groups(root, "data-deepplant-stream")
    assert set(stream_groups) == {"S-001", "S-002", "S-003"}
    step_groups = _groups(root, "data-deepplant-step")
    feed_x, _ = _translate(step_groups["FEED"])
    mix_x, _ = _translate(step_groups["MIX"])
    vessel_x, _ = _translate(step_groups["VESSEL"])
    assert feed_x < mix_x < vessel_x
    lowest_symbol_y = max(_translate(group)[1] + 100 for group in step_groups.values())
    # S-003 (vessel -> mix) is the back edge on a dedicated return lane; the
    # feed/mix/vessel chain stays on ordinary forward routes.
    forward_001 = _stream_points(stream_groups["S-001"])
    forward_002 = _stream_points(stream_groups["S-002"])
    feedback_003 = _stream_points(stream_groups["S-003"])
    assert max(point[1] for point in forward_001) <= lowest_symbol_y
    assert max(point[1] for point in forward_002) <= lowest_symbol_y
    assert max(point[1] for point in feedback_003) > lowest_symbol_y


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
            _step("SPLIT", "splitting_material", ["in", "out"]),
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


# ---------------------------------------------------------------------------
# Runtime symbol-parser contract validation (through the public render API)
# ---------------------------------------------------------------------------


def _write_pack_asset(tmp_path: Path, role: str, svg_text: str) -> Path:
    pack = tmp_path / "assets" / "symbols" / "process" / "basic"
    pack.mkdir(parents=True, exist_ok=True)
    (pack / f"{role}.svg").write_text(svg_text, encoding="utf-8")
    return pack


def _use_pack(monkeypatch: pytest.MonkeyPatch, pack: Path) -> None:
    """Point the pack resolver at a temporary pack for one test."""

    def resolve(_pack: str) -> Path:
        return pack

    monkeypatch.setattr(render_module, "_pack_directory", resolve)


def test_runtime_parser_accepts_top_level_non_group_geometry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The documented SVG contract permits top-level path/line/polyline/etc.
    # geometry; the renderer must not silently demand a wrapping <g>.
    pack = _write_pack_asset(
        tmp_path,
        "source",
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<path id="flame" d="M 0 50 H 100" stroke="currentColor" fill="none"/>'
        '<g id="deepplant-anchors">'
        '<circle id="anchor-out-0" cx="100" cy="50" r="1" fill="none" stroke="none"/>'
        "</g></svg>",
    )
    _use_pack(monkeypatch, pack)
    model = _model_with_process(steps=[_step("FEED", "source", ["out"])], streams=[])
    assert model.process is not None
    document = _render(model.process)
    assert "<path" in document
    assert 'id="flame"' not in document
    assert 'data-deepplant-step="FEED"' in document


def test_anchor_xml_child_order_does_not_define_presentation_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # anchor-out-1 is serialized before anchor-out-0; numeric anchor id must
    # still define the ordered slots (0 upper, 1 lower) for stream routing.
    pack = _write_pack_asset(
        tmp_path,
        "source",
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<g id="deepplant-anchors">'
        '<circle id="anchor-out-0" cx="100" cy="50" r="1" fill="none" stroke="none"/>'
        "</g></svg>",
    )
    _write_pack_asset(
        tmp_path,
        "splitting",
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<g id="deepplant-anchors">'
        '<circle id="anchor-in-0" cx="0" cy="50" r="1" fill="none" stroke="none"/>'
        '<circle id="anchor-out-1" cx="100" cy="70" r="1" fill="none" stroke="none"/>'
        '<circle id="anchor-out-0" cx="100" cy="30" r="1" fill="none" stroke="none"/>'
        "</g></svg>",
    )
    _write_pack_asset(
        tmp_path,
        "sink",
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<g id="deepplant-anchors">'
        '<circle id="anchor-in-0" cx="0" cy="50" r="1" fill="none" stroke="none"/>'
        "</g></svg>",
    )
    model = _model_with_process(
        steps=[
            _step("FEED", "source", ["out"]),
            _step("SPLIT", "splitting_material", ["in", "out_vessel", "out_branch"]),
            _step("A", "sink", ["in"]),
            _step("B", "sink", ["in"]),
        ],
        streams=[
            _stream("S-0", "FEED", "out", "SPLIT", "in"),
            _stream("S-A", "SPLIT", "out_vessel", "A", "in"),
            _stream("S-B", "SPLIT", "out_branch", "B", "in"),
        ],
    )
    _use_pack(monkeypatch, pack)
    assert model.process is not None
    document = _render(model.process)
    root = _svg_root(document)
    stream_groups = _groups(root, "data-deepplant-stream")
    start_a = _stream_points(stream_groups["S-A"])[0]
    start_b = _stream_points(stream_groups["S-B"])[0]
    end_a = _stream_points(stream_groups["S-A"])[-1]
    end_b = _stream_points(stream_groups["S-B"])[-1]
    # First declared split port (out_vessel) takes the upper numeric slot even
    # though it was serialized second inside the anchors group.
    assert start_a[0] == start_b[0]
    assert start_a[1] < start_b[1]
    assert end_a[1] < end_b[1]


def test_duplicate_anchor_numeric_index_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # anchor-out-0 and anchor-out-00 are distinct ids but share numeric index 0.
    pack = _write_pack_asset(
        tmp_path,
        "splitting",
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<g id="deepplant-anchors">'
        '<circle id="anchor-in-0" cx="0" cy="50" r="1" fill="none" stroke="none"/>'
        '<circle id="anchor-out-0" cx="100" cy="30" r="1" fill="none" stroke="none"/>'
        '<circle id="anchor-out-00" cx="100" cy="70" r="1" fill="none" stroke="none"/>'
        "</g></svg>",
    )
    _use_pack(monkeypatch, pack)
    model = _model_with_process(steps=[_step("SPLIT", "splitting_material", ["in"])], streams=[])
    assert model.process is not None
    with pytest.raises(ProcessRenderError, match="duplicate"):
        _render(model.process)


def test_anchor_coordinates_outside_canonical_viewbox_are_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pack = _write_pack_asset(
        tmp_path,
        "source",
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<g id="deepplant-anchors">'
        '<circle id="anchor-out-0" cx="100" cy="110" r="1" fill="none" stroke="none"/>'
        "</g></svg>",
    )
    _use_pack(monkeypatch, pack)
    model = _model_with_process(steps=[_step("FEED", "source", ["out"])], streams=[])
    assert model.process is not None
    with pytest.raises(ProcessRenderError, match="outside the canonical"):
        _render(model.process)


# ---------------------------------------------------------------------------
# Presentation symbol-role resolution (ADR-0009)
# ---------------------------------------------------------------------------


def _asset_geometry_children(role: str) -> list[Element]:
    asset_text = (
        resources.files("deepplant")
        .joinpath("assets", "symbols", "process", "basic", f"{role}.svg")
        .read_text(encoding="utf-8")
    )
    asset_root = ElementTree.fromstring(asset_text)
    return [
        _strip_ids(child)
        for child in asset_root
        if not (_local_name(child) == "g" and child.get("id") == ANCHOR_GROUP_ID)
    ]


def _step_uses_role(document: str, step_id: str, role: str) -> None:
    root = _svg_root(document)
    group = _groups(root, "data-deepplant-step")[step_id]
    actual_children = list(group)
    expected_children = _asset_geometry_children(role)
    assert len(actual_children) == len(expected_children), step_id
    for actual, expected in zip(actual_children, expected_children, strict=False):
        assert ElementTree.tostring(actual) == ElementTree.tostring(expected), step_id


@pytest.mark.parametrize(
    ("function", "expected_role"),
    [
        ("source", "source"),
        ("sink", "sink"),
        ("mixing", "mixing"),
        ("splitting_material", "splitting"),
        ("pumping", "pump"),
        ("heat_exchange", "heat_exchanger"),
    ],
)
def test_default_presentation_policy_maps_functions_to_roles(
    function: str, expected_role: str
) -> None:
    # No override needed: the renderer's default function -> role policy resolves
    # known engineering functions automatically (ADR-0009).
    model = _model_with_process(steps=[_step("STEP", function, ["in", "out"])], streams=[])
    assert model.process is not None
    document = _render(model.process)
    _step_uses_role(document, "STEP", expected_role)


def test_unspecified_function_renders_through_explicit_override() -> None:
    # function="unspecified" has no default role; an explicit per-step override
    # supplies the presentation role for this render call only.
    model = _model_with_process(
        steps=[_step("PS-vessel", "unspecified", ["in", "out"])], streams=[]
    )
    assert model.process is not None
    document = _render(model.process, overrides={"PS-vessel": "vessel"})
    _step_uses_role(document, "PS-vessel", "vessel")


def test_explicit_override_takes_precedence_over_default_function_mapping() -> None:
    # function="pumping" defaults to role "pump"; the explicit override must win.
    model = _model_with_process(steps=[_step("P-1", "pumping", ["in", "out"])], streams=[])
    assert model.process is not None
    document = _render(model.process, overrides={"P-1": "mixing"})
    _step_uses_role(document, "P-1", "mixing")


def test_override_for_unknown_step_id_raises_process_render_error() -> None:
    model = _model_with_process(
        steps=[_step("A", "source", ["out"]), _step("B", "sink", ["in"])],
        streams=[_stream("S-1", "A", "out", "B", "in")],
    )
    assert model.process is not None
    with pytest.raises(ProcessRenderError, match="unknown step id 'GHOST'"):
        _render(model.process, overrides={"GHOST": "vessel"})


def test_blank_override_role_raises_process_render_error() -> None:
    model = _model_with_process(steps=[_step("A", "unspecified", ["in"])], streams=[])
    assert model.process is not None
    with pytest.raises(ProcessRenderError, match="blank"):
        _render(model.process, overrides={"A": "   "})


def test_override_role_missing_from_selected_pack_raises_process_render_error() -> None:
    model = _model_with_process(steps=[_step("A", "unspecified", ["in", "out"])], streams=[])
    assert model.process is not None
    with pytest.raises(ProcessRenderError) as exc_info:
        _render(model.process, overrides={"A": "reactor"})
    message = str(exc_info.value)
    assert "A" in message
    assert "unspecified" in message
    assert "reactor" in message
    assert "basic" in message


def test_semantic_model_is_not_mutated_by_presentation_overrides() -> None:
    model = _model_with_process(steps=[_step("A", "unspecified", [])], streams=[])
    assert model.process is not None
    _render(model.process, overrides={"A": "vessel"})
    step = model.process.steps[0]
    assert step.function == "unspecified"
    assert not hasattr(step, "type")
    assert step.model_dump() == {"id": "A", "function": "unspecified", "name": None, "ports": []}
