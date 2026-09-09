from pathlib import Path

from deepplant import load_plant
from deepplant.model import Equipment, PlantModel, ProcessModel

EXAMPLE = Path(__file__).parents[1] / "examples" / "realistic-process-fragment" / "plant.yaml"

EXPECTED_EQUIPMENT_IDS = ["T-101", "P-101", "FV-101", "E-101", "V-101"]

EXPECTED_STEP_IDS = [
    "PS-feed",
    "PS-mix",
    "PS-pump",
    "PS-hx",
    "PS-split",
    "PS-vessel",
    "PS-consumer",
]

EXPECTED_STREAM_IDS = [f"S-00{number}" for number in range(1, 8)]

# id -> (source step, source port, target step, target port)
EXPECTED_STREAMS: dict[str, tuple[str, str, str, str]] = {
    "S-001": ("PS-feed", "out_feed", "PS-mix", "in_fresh"),
    "S-002": ("PS-vessel", "out_recycle", "PS-mix", "in_recycle"),
    "S-003": ("PS-mix", "out_mixed", "PS-pump", "suction"),
    "S-004": ("PS-pump", "discharge", "PS-hx", "in_side_A"),
    "S-005": ("PS-hx", "out_side_A", "PS-split", "in"),
    "S-006": ("PS-split", "out_vessel", "PS-vessel", "in"),
    "S-007": ("PS-split", "out_branch", "PS-consumer", "in"),
}

# Truthful physical/bootstrap subset: only directly known adjacency. The
# mixing tee, splitting tee, and recycle piping are intentionally not jumped
# over by Connections.
EXPECTED_PHYSICAL_CONNECTIONS = {
    ("P-101", "discharge", "FV-101", "inlet"),
    ("FV-101", "outlet", "E-101", "process_inlet"),
}


def _model() -> PlantModel:
    return load_plant(str(EXAMPLE))


def _process(model: PlantModel) -> ProcessModel:
    assert model.process is not None
    return model.process


def _equipment(model: PlantModel, equipment_id: str) -> Equipment:
    matches = [item for item in model.equipment if item.id == equipment_id]
    assert len(matches) == 1
    return matches[0]


def _stream_edges(model: PlantModel) -> dict[str, tuple[str, str, str, str]]:
    process = _process(model)
    return {
        stream.id: (
            stream.source.step,
            stream.source.port,
            stream.target.step,
            stream.target.port,
        )
        for stream in process.streams
    }


def _graph_has_cycle(model: PlantModel) -> bool:
    process = _process(model)
    adjacency: dict[str, list[str]] = {}
    for stream in process.streams:
        adjacency.setdefault(stream.source.step, []).append(stream.target.step)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(step: str) -> bool:
        if step in visiting:
            return True
        if step in visited:
            return False
        visiting.add(step)
        for target in adjacency.get(step, []):
            if visit(target):
                return True
        visiting.remove(step)
        visited.add(step)
        return False

    return any(visit(step) for step in adjacency)


def _reachable_steps(model: PlantModel, start: str) -> set[str]:
    process = _process(model)
    adjacency: dict[str, list[str]] = {}
    for stream in process.streams:
        adjacency.setdefault(stream.source.step, []).append(stream.target.step)

    seen: set[str] = set()
    stack = [start]
    while stack:
        step = stack.pop()
        for target in adjacency.get(step, []):
            if target not in seen:
                seen.add(target)
                stack.append(target)
    return seen


def test_realistic_example_loads_through_the_public_loader() -> None:
    model = _model()

    assert model.plant.id == "demo"
    assert model.plant.name == "Realistic Process Fragment"
    assert [item.id for item in model.equipment] == EXPECTED_EQUIPMENT_IDS
    process = _process(model)
    assert len(process.steps) == 7
    assert len(process.streams) == 7


def test_process_graph_contains_the_expected_seven_steps() -> None:
    process = _process(_model())

    assert [step.id for step in process.steps] == EXPECTED_STEP_IDS
    assert [step.function for step in process.steps] == [
        "source",
        "mixing",
        "pumping",
        "heat_exchange",
        "splitting_material",
        "unspecified",
        "sink",
    ]


def test_process_streams_match_the_documented_topology() -> None:
    process = _process(_model())

    assert [stream.id for stream in process.streams] == EXPECTED_STREAM_IDS
    assert _stream_edges(_model()) == EXPECTED_STREAMS


def test_recycle_forms_a_valid_graph_cycle() -> None:
    model = _model()

    edges = _stream_edges(model)
    assert edges["S-002"][:2] == ("PS-vessel", "out_recycle")
    assert edges["S-002"][2:] == ("PS-mix", "in_recycle")
    assert "PS-mix" in _reachable_steps(model, "PS-vessel")
    assert "PS-vessel" in _reachable_steps(model, "PS-mix")
    assert _graph_has_cycle(model)


def test_mixing_has_two_incoming_and_one_outgoing_stream() -> None:
    process = _process(_model())
    incoming = [stream for stream in process.streams if stream.target.step == "PS-mix"]
    outgoing = [stream for stream in process.streams if stream.source.step == "PS-mix"]

    assert len(incoming) == 2
    assert len(outgoing) == 1
    assert {stream.source.step for stream in incoming} == {"PS-feed", "PS-vessel"}
    assert {stream.id for stream in outgoing} == {"S-003"}


def test_splitting_has_one_incoming_and_two_outgoing_streams() -> None:
    process = _process(_model())
    incoming = [stream for stream in process.streams if stream.target.step == "PS-split"]
    outgoing = [stream for stream in process.streams if stream.source.step == "PS-split"]

    assert len(incoming) == 1
    assert len(outgoing) == 2
    assert {stream.id for stream in incoming} == {"S-005"}
    assert {stream.target.step for stream in outgoing} == {"PS-vessel", "PS-consumer"}


def test_mixing_and_splitting_have_no_equipment_counterpart() -> None:
    model = _model()
    equipment_ids = {item.id for item in model.equipment}
    step_ids = {step.id for step in _process(model).steps}

    assert {"PS-mix", "PS-split"} <= step_ids
    assert {"PS-mix", "PS-split"}.isdisjoint(equipment_ids)


def test_fv101_is_the_inline_flow_control_valve_without_a_process_step() -> None:
    model = _model()
    fv = _equipment(model, "FV-101")
    equipment_ids = {item.id for item in model.equipment}
    step_ids = {step.id for step in _process(model).steps}

    assert "FV-101" in equipment_ids
    assert "FV-101" not in step_ids
    # Neutral documented role: inline control valve between pump and exchanger.
    assert fv.name == "Flow Control Valve"
    assert [port.id for port in fv.ports] == ["inlet", "outlet"]


def test_vessel_recycle_outlet_is_unconnected_in_the_bootstrap_graph() -> None:
    model = _model()
    vessel = _equipment(model, "V-101")
    port_ids = {port.id for port in vessel.ports}

    assert "recycle_outlet" in port_ids
    assert "bottoms_outlet" not in port_ids
    assert not any(
        (connection.source.component == "V-101" and connection.source.port == "recycle_outlet")
        or (connection.target.component == "V-101" and connection.target.port == "recycle_outlet")
        for connection in model.connections
    )


def test_physical_bootstrap_layer_has_equipment_ports_and_connections() -> None:
    model = _model()

    assert sum(len(item.ports) for item in model.equipment) == 9
    actual = {
        (
            connection.source.component,
            connection.source.port,
            connection.target.component,
            connection.target.port,
        )
        for connection in model.connections
    }
    assert actual == EXPECTED_PHYSICAL_CONNECTIONS


def test_process_and_equipment_id_namespaces_stay_independent(tmp_path: Path) -> None:
    """A shared id string across both namespaces is allowed through the loader.

    This asserts there is no cross-layer id constraint, not that the example
    relies on one. The fixture itself keeps the two id sets disjoint.
    """
    path = tmp_path / "plant.yaml"
    path.write_text(
        "plant:\n"
        "  id: demo\n"
        "equipment:\n"
        "  - id: P-101\n"
        "    type: pump\n"
        "    ports:\n"
        "      - id: discharge\n"
        "process:\n"
        "  steps:\n"
        "    - id: P-101\n"
        "      function: pumping\n"
        "      ports:\n"
        "        - id: discharge\n"
        "  streams: []\n",
        encoding="utf-8",
    )

    model = load_plant(path)

    assert [item.id for item in model.equipment] == ["P-101"]
    assert [step.id for step in _process(model).steps] == ["P-101"]


def test_ps_vessel_is_semantically_unspecified_not_a_vessel_role() -> None:
    """The realistic fragment keeps PS-vessel semantically honest (ADR-0009).

    The fragment's drawing shows a vessel, but a vessel is a
    physical/presentation description. Without evidence for storage, reaction,
    separation, holding, buffering, residence, or another engineering function,
    the canonical model must say ``unspecified`` — never the presentation role.
    """
    process = _process(_model())
    vessel = next(step for step in process.steps if step.id == "PS-vessel")

    assert vessel.function == "unspecified"
    assert vessel.function != "vessel"
    assert not hasattr(vessel, "type")


def test_all_process_steps_declare_canonical_engineering_functions() -> None:
    process = _process(_model())
    function_by_step = {step.id: step.function for step in process.steps}

    assert function_by_step == {
        "PS-feed": "source",
        "PS-mix": "mixing",
        "PS-pump": "pumping",
        "PS-hx": "heat_exchange",
        "PS-split": "splitting_material",
        "PS-vessel": "unspecified",
        "PS-consumer": "sink",
    }
