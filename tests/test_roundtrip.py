import re
from collections.abc import Callable
from pathlib import Path

import pytest

from deepplant import PlantLoadError, PlantSaveError, load_plant, save_plant
from deepplant.model import (
    Connection,
    Equipment,
    PipingLine,
    PipingModel,
    PipingRealization,
    PipingSegment,
    Plant,
    PlantModel,
    Port,
    PortRef,
    ProcessModel,
    ProcessPort,
    ProcessRef,
    ProcessStep,
    ProcessStream,
)

EXAMPLE_MINIMAL = Path(__file__).parents[1] / "examples" / "minimal-process" / "plant.yaml"
EXAMPLE_PROCESS = Path(__file__).parents[1] / "examples" / "process-graph" / "plant.yaml"
EXAMPLE_REALISTIC = (
    Path(__file__).parents[1] / "examples" / "realistic-process-fragment" / "plant.yaml"
)

MINIMAL_YAML = "plant:\n  id: demo\nequipment: []\nconnections: []\n"


def _minimal() -> PlantModel:
    return PlantModel(plant=Plant(id="demo"))


def _physical_topology() -> PlantModel:
    return PlantModel(
        plant=Plant(id="demo", name="Feed System"),
        equipment=[
            Equipment(
                id="T-101",
                type="tank",
                name="Feed Tank",
                ports=[Port(id="outlet")],
            ),
            Equipment(
                id="P-101",
                type="pump",
                name="Feed Pump",
                ports=[Port(id="suction"), Port(id="discharge")],
            ),
        ],
        connections=[
            Connection(
                id="C-001",
                source=PortRef(component="T-101", port="outlet"),
                target=PortRef(component="P-101", port="suction"),
            )
        ],
    )


def _process_graph() -> PlantModel:
    return PlantModel(
        plant=Plant(id="demo", name="Process Graph Example"),
        process=ProcessModel(
            steps=[
                ProcessStep(
                    id="FEED", function="source", name="Feed", ports=[ProcessPort(id="out")]
                ),
                ProcessStep(
                    id="PUMP",
                    function="pumping",
                    name="Transfer Pump",
                    ports=[ProcessPort(id="suction"), ProcessPort(id="discharge")],
                ),
                ProcessStep(
                    id="PRODUCT", function="sink", name="Product", ports=[ProcessPort(id="in")]
                ),
            ],
            streams=[
                ProcessStream(
                    id="S-001",
                    source=ProcessRef(step="FEED", port="out"),
                    target=ProcessRef(step="PUMP", port="suction"),
                ),
                ProcessStream(
                    id="S-002",
                    source=ProcessRef(step="PUMP", port="discharge"),
                    target=ProcessRef(step="PRODUCT", port="in"),
                ),
            ],
        ),
    )


def _combined() -> PlantModel:
    return PlantModel(
        plant=Plant(id="demo", name="Combined Plant"),
        equipment=[
            Equipment(id="T-101", type="tank", name="Feed Tank", ports=[Port(id="outlet")]),
            Equipment(
                id="P-101",
                type="pump",
                name="Feed Pump",
                ports=[Port(id="suction"), Port(id="discharge")],
            ),
        ],
        connections=[
            Connection(
                id="C-001",
                source=PortRef(component="T-101", port="outlet"),
                target=PortRef(component="P-101", port="suction"),
            )
        ],
        process=ProcessModel(
            steps=[
                ProcessStep(id="FEED", function="source", ports=[ProcessPort(id="out")]),
                ProcessStep(
                    id="P-101",
                    function="pumping",
                    ports=[ProcessPort(id="suction"), ProcessPort(id="discharge")],
                ),
                ProcessStep(id="PRODUCT", function="sink", ports=[ProcessPort(id="in")]),
            ],
            streams=[
                ProcessStream(
                    id="S-001",
                    source=ProcessRef(step="FEED", port="out"),
                    target=ProcessRef(step="P-101", port="suction"),
                ),
                ProcessStream(
                    id="S-002",
                    source=ProcessRef(step="P-101", port="discharge"),
                    target=ProcessRef(step="PRODUCT", port="in"),
                ),
            ],
        ),
    )


def _piping_realization() -> PlantModel:
    """Physical topology plus the piping layer, including a direct realization.

    Two lines deliberately share the segment id ``SEG-1`` (segment identity is
    owner-local) and one of them deliberately omits every optional property, so
    the round-trip covers present and absent optionals.
    """
    return PlantModel(
        plant=Plant(id="demo", name="Piping Realization"),
        equipment=[
            Equipment(id="P-101", type="pump", ports=[Port(id="discharge"), Port(id="suction")]),
            Equipment(
                id="FV-101", type="control-valve", ports=[Port(id="inlet"), Port(id="outlet")]
            ),
        ],
        connections=[
            Connection(
                id="C-001",
                source=PortRef(component="P-101", port="discharge"),
                target=PortRef(component="FV-101", port="inlet"),
            ),
            Connection(
                id="C-002",
                source=PortRef(component="FV-101", port="outlet"),
                target=PortRef(component="P-101", port="suction"),
            ),
        ],
        piping=PipingModel(
            lines=[
                PipingLine(
                    id="LINE-A",
                    line_number='3"-P-101-A1A',
                    segments=[
                        PipingSegment(
                            id="SEG-1",
                            segment_number="S-1",
                            nominal_diameter="DN80",
                            piping_class="A1A",
                            fluid_code="P",
                            realizations=[PipingRealization(connection="C-001")],
                        )
                    ],
                ),
                PipingLine(
                    id="LINE-B",
                    name="Line Without Optional Properties",
                    segments=[
                        PipingSegment(
                            id="SEG-1",
                            realizations=[PipingRealization(connection="C-002", kind="direct")],
                        )
                    ],
                ),
            ]
        ),
    )


def _empty_process() -> PlantModel:
    return PlantModel(plant=Plant(id="demo"), process=ProcessModel())


def _optional_names_present() -> PlantModel:
    return PlantModel(
        plant=Plant(id="demo", name="Named Plant"),
        equipment=[
            Equipment(id="T-101", type="tank", name="Named Tank", ports=[Port(id="outlet")])
        ],
        process=ProcessModel(
            steps=[
                ProcessStep(
                    id="FEED", function="source", name="Named Feed", ports=[ProcessPort(id="out")]
                ),
                ProcessStep(
                    id="PRODUCT",
                    function="sink",
                    name="Named Product",
                    ports=[ProcessPort(id="in")],
                ),
            ],
            streams=[
                ProcessStream(
                    id="S-001",
                    name="Named Stream",
                    source=ProcessRef(step="FEED", port="out"),
                    target=ProcessRef(step="PRODUCT", port="in"),
                )
            ],
        ),
    )


def _optional_names_absent() -> PlantModel:
    return PlantModel(
        plant=Plant(id="demo"),
        equipment=[Equipment(id="T-101", type="tank", ports=[Port(id="outlet")])],
        process=ProcessModel(
            steps=[ProcessStep(id="FEED", function="source", ports=[ProcessPort(id="out")])],
            streams=[],
        ),
    )


def _unicode_names() -> PlantModel:
    return PlantModel(
        plant=Plant(id="demo", name="Pivovar Čechy – výrobní linka"),
        equipment=[
            Equipment(
                id="V-101", type="tank", name="Varna – nerezová nádrž", ports=[Port(id="outlet")]
            )
        ],
        process=ProcessModel(
            steps=[
                ProcessStep(
                    id="VAR",
                    function="boiling",
                    name="Výrobní kotel α",
                    ports=[ProcessPort(id="out")],
                ),
                ProcessStep(
                    id="CHL",
                    function="cooling",
                    name="Chladič mladiny",
                    ports=[ProcessPort(id="in")],
                ),
            ],
            streams=[
                ProcessStream(
                    id="S-001",
                    name="Horká mladina → chladič",
                    source=ProcessRef(step="VAR", port="out"),
                    target=ProcessRef(step="CHL", port="in"),
                )
            ],
        ),
    )


ROUND_TRIP_MODELS: list[tuple[str, Callable[[], PlantModel]]] = [
    ("minimal-plant", _minimal),
    ("physical-topology", _physical_topology),
    ("process-graph", _process_graph),
    ("combined-physical-and-process", _combined),
    ("empty-process-model", _empty_process),
    ("piping-realization", _piping_realization),
    ("optional-names-present", _optional_names_present),
    ("optional-names-absent", _optional_names_absent),
    ("unicode-names", _unicode_names),
]


@pytest.mark.parametrize(
    "build",
    [build for _, build in ROUND_TRIP_MODELS],
    ids=[case_id for case_id, _ in ROUND_TRIP_MODELS],
)
def test_semantic_round_trip(tmp_path: Path, build: Callable[[], PlantModel]) -> None:
    model = build()
    path = tmp_path / "plant.yaml"

    save_plant(model, path)
    loaded = load_plant(path)

    assert loaded == model


def test_minimal_model_serializes_to_canonical_yaml(tmp_path: Path) -> None:
    path = tmp_path / "plant.yaml"

    save_plant(_minimal(), path)

    text = path.read_text(encoding="utf-8")
    assert text == MINIMAL_YAML
    assert "process" not in text


def test_none_optional_values_are_omitted(tmp_path: Path) -> None:
    path = tmp_path / "plant.yaml"

    save_plant(
        PlantModel(
            plant=Plant(id="demo"),
            equipment=[Equipment(id="T-101", type="tank", ports=[Port(id="outlet")])],
        ),
        path,
    )

    text = path.read_text(encoding="utf-8")
    assert "name" not in text
    assert "null" not in text


def test_none_process_is_omitted_from_yaml(tmp_path: Path) -> None:
    path = tmp_path / "plant.yaml"

    save_plant(_minimal(), path)

    text = path.read_text(encoding="utf-8")
    assert "process" not in text


def test_empty_process_model_remains_present(tmp_path: Path) -> None:
    path = tmp_path / "plant.yaml"

    save_plant(_empty_process(), path)

    text = path.read_text(encoding="utf-8")
    assert text == MINIMAL_YAML + "process:\n  steps: []\n  streams: []\n"

    loaded = load_plant(path)
    assert isinstance(loaded.process, ProcessModel)
    assert loaded == _empty_process()


def test_field_order_follows_model_declaration_order(tmp_path: Path) -> None:
    path = tmp_path / "plant.yaml"

    save_plant(_combined(), path)

    text = path.read_text(encoding="utf-8")
    root_keys = ["plant:", "equipment:", "connections:", "process:"]
    positions = [text.index(key) for key in root_keys]
    assert positions == sorted(positions)

    process_start = text.index("process:")
    steps = text.index("steps:", process_start)
    streams = text.index("streams:", process_start)
    assert steps < streams


def test_saving_same_model_is_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first.yaml"
    second = tmp_path / "second.yaml"

    save_plant(_combined(), first)
    save_plant(_combined(), second)

    assert first.read_bytes() == second.read_bytes()
    assert first.read_text(encoding="utf-8").endswith("\n")


def test_unicode_names_are_written_as_utf8_text(tmp_path: Path) -> None:
    path = tmp_path / "plant.yaml"

    save_plant(_unicode_names(), path)

    text = path.read_text(encoding="utf-8")
    assert "Pivovar Čechy – výrobní linka" in text
    assert "Horká mladina → chladič" in text
    assert "\\u" not in text


def test_null_process_yaml_round_trips_as_omitted_process(tmp_path: Path) -> None:
    source = tmp_path / "source.yaml"
    source.write_text("plant:\n  id: demo\nprocess: null\n", encoding="utf-8")

    model = load_plant(source)
    assert model.process is None

    path = tmp_path / "plant.yaml"
    save_plant(model, path)

    text = path.read_text(encoding="utf-8")
    assert text == MINIMAL_YAML
    assert "process" not in text
    assert load_plant(path) == model


def test_combined_model_keeps_physical_and_process_layers(tmp_path: Path) -> None:
    path = tmp_path / "plant.yaml"

    save_plant(_combined(), path)
    loaded = load_plant(path)

    assert loaded == _combined()
    assert [item.id for item in loaded.equipment] == ["T-101", "P-101"]
    assert [port.id for port in loaded.equipment[0].ports] == ["outlet"]
    connection = loaded.connections[0]
    assert connection.source == PortRef(component="T-101", port="outlet")
    assert connection.target == PortRef(component="P-101", port="suction")

    assert loaded.process is not None
    process = loaded.process
    assert [step.id for step in process.steps] == ["FEED", "P-101", "PRODUCT"]
    assert (process.streams[0].source.step, process.streams[0].source.port) == ("FEED", "out")
    assert (process.streams[1].target.step, process.streams[1].target.port) == ("PRODUCT", "in")


def test_save_to_missing_directory_raises_plant_save_error(tmp_path: Path) -> None:
    target = tmp_path / "missing" / "plant.yaml"

    with pytest.raises(PlantSaveError) as exc_info:
        save_plant(_minimal(), target)

    message = str(exc_info.value)
    assert "cannot write plant file" in message
    assert str(target) in message


@pytest.mark.parametrize(
    "example",
    [EXAMPLE_MINIMAL, EXAMPLE_PROCESS, EXAMPLE_REALISTIC],
    ids=["minimal-process", "process-graph", "realistic-process-fragment"],
)
def test_existing_example_yaml_round_trips(tmp_path: Path, example: Path) -> None:
    model = load_plant(str(example))
    path = tmp_path / "plant.yaml"

    save_plant(model, str(path))

    assert load_plant(str(path)) == model
    assert path.read_text(encoding="utf-8").endswith("\n")


# --- ProcessStep.function YAML migration (ADR-0009, intentional pre-1.0 break) --


def test_yaml_load_uses_function_and_save_emits_function_not_type(tmp_path: Path) -> None:
    source = tmp_path / "source.yaml"
    source.write_text(
        "plant:\n"
        "  id: demo\n"
        "process:\n"
        "  steps:\n"
        "    - id: FEED\n"
        "      function: source\n"
        "      ports:\n"
        "        - id: out\n"
        "    - id: PUMP\n"
        "      function: pumping\n"
        "      ports:\n"
        "        - id: suction\n"
        "        - id: discharge\n"
        "    - id: SINK\n"
        "      function: sink\n"
        "      ports:\n"
        "        - id: in\n"
        "  streams:\n"
        "    - id: S-001\n"
        "      source: {step: FEED, port: out}\n"
        "      target: {step: PUMP, port: suction}\n"
        "    - id: S-002\n"
        "      source: {step: PUMP, port: discharge}\n"
        "      target: {step: SINK, port: in}\n",
        encoding="utf-8",
    )

    model = load_plant(source)
    assert model.process is not None
    assert [step.function for step in model.process.steps] == ["source", "pumping", "sink"]

    path = tmp_path / "plant.yaml"
    save_plant(model, path)
    text = path.read_text(encoding="utf-8")

    assert "function: source" in text
    assert "function: pumping" in text
    assert re.search(r"(?m)^\s+type:", text) is None
    loaded = load_plant(path)
    assert loaded == model


def test_stale_process_step_type_yaml_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "legacy.yaml"
    source.write_text(
        "plant:\n"
        "  id: demo\n"
        "process:\n"
        "  steps:\n"
        "    - id: P-101\n"
        "      type: pump\n"
        "      ports: []\n"
        "  streams: []\n",
        encoding="utf-8",
    )

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(source)
    message = str(exc_info.value)
    assert "steps.0.type" in message
    assert "extra" in message.lower() or "type" in message


# --- Piping realization round-trip (ADR-0011) --------------------------------


def test_none_piping_is_omitted_from_yaml(tmp_path: Path) -> None:
    path = tmp_path / "plant.yaml"

    save_plant(_minimal(), path)

    assert "piping" not in path.read_text(encoding="utf-8")


def test_piping_layer_round_trips_semantically(tmp_path: Path) -> None:
    model = _piping_realization()
    path = tmp_path / "plant.yaml"

    save_plant(model, path)
    loaded = load_plant(path)

    assert loaded == model
    assert loaded.piping is not None
    lines = loaded.piping.lines
    assert [line.id for line in lines] == ["LINE-A", "LINE-B"]
    assert (lines[0].line_number, lines[1].line_number) == ('3"-P-101-A1A', None)
    assert (lines[0].name, lines[1].name) == (None, "Line Without Optional Properties")
    # Same segment id in both lines: identity is owner-local, not global.
    assert [line.segments[0].id for line in lines] == ["SEG-1", "SEG-1"]
    assert lines[0].segments[0].segment_number == "S-1"
    assert lines[0].segments[0].nominal_diameter == "DN80"
    assert lines[0].segments[0].piping_class == "A1A"
    assert lines[0].segments[0].fluid_code == "P"
    assert lines[1].segments[0].segment_number is None
    assert [
        (line.segments[0].realizations[0].connection, line.segments[0].realizations[0].kind)
        for line in lines
    ] == [
        ("C-001", "pipe"),
        ("C-002", "direct"),
    ]


def test_saved_piping_emits_the_default_kind_explicitly(tmp_path: Path) -> None:
    """The canonical serializer keeps the default; only semantics must round-trip."""
    path = tmp_path / "plant.yaml"

    save_plant(_piping_realization(), path)
    text = path.read_text(encoding="utf-8")

    assert "kind: pipe" in text
    assert "kind: direct" in text


def test_yaml_with_omitted_kind_round_trips_as_pipe(tmp_path: Path) -> None:
    source = tmp_path / "source.yaml"
    source.write_text(
        "plant:\n"
        "  id: demo\n"
        "equipment:\n"
        "  - id: T-101\n"
        "    type: tank\n"
        "    ports:\n"
        "      - id: outlet\n"
        "connections:\n"
        "  - id: C-001\n"
        "    source: {component: T-101, port: outlet}\n"
        "    target: {component: T-101, port: outlet}\n"
        "piping:\n"
        "  lines:\n"
        "    - id: PL-1\n"
        "      segments:\n"
        "        - id: SEG-1\n"
        "          realizations:\n"
        "            - connection: C-001\n",
        encoding="utf-8",
    )

    model = load_plant(source)
    assert model.piping is not None
    assert model.piping.lines[0].segments[0].realizations[0].kind == "pipe"

    path = tmp_path / "plant.yaml"
    save_plant(model, path)

    assert load_plant(path) == model


def test_absent_piping_optionals_are_omitted_from_yaml(tmp_path: Path) -> None:
    path = tmp_path / "plant.yaml"

    save_plant(_piping_realization(), path)
    text = path.read_text(encoding="utf-8")

    # LINE-B authors no line_number and its segment authors no properties.
    assert text.count("line_number") == 1
    assert text.count("segment_number") == 1
    assert text.count("nominal_diameter") == 1
    assert text.count("piping_class") == 1
    assert text.count("fluid_code") == 1
    assert "null" not in text


def test_piping_precedes_process_in_saved_field_order(tmp_path: Path) -> None:
    model = _piping_realization()
    model.process = ProcessModel(
        steps=[
            ProcessStep(id="FEED", function="source", ports=[ProcessPort(id="out")]),
            ProcessStep(id="SINK", function="sink", ports=[ProcessPort(id="in")]),
        ],
        streams=[
            ProcessStream(
                id="S-001",
                source=ProcessRef(step="FEED", port="out"),
                target=ProcessRef(step="SINK", port="in"),
            )
        ],
    )
    path = tmp_path / "plant.yaml"

    save_plant(model, path)
    text = path.read_text(encoding="utf-8")

    root_keys = ["plant:", "equipment:", "connections:", "piping:", "process:"]
    positions = [text.index(key) for key in root_keys]
    assert positions == sorted(positions)
    assert load_plant(path) == model
