from collections.abc import Callable
from pathlib import Path

import pytest

from deepplant import PlantSaveError, load_plant, save_plant
from deepplant.model import (
    Connection,
    Equipment,
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
                ProcessStep(id="FEED", type="source", name="Feed", ports=[ProcessPort(id="out")]),
                ProcessStep(
                    id="PUMP",
                    type="pump",
                    name="Transfer Pump",
                    ports=[ProcessPort(id="suction"), ProcessPort(id="discharge")],
                ),
                ProcessStep(
                    id="PRODUCT", type="sink", name="Product", ports=[ProcessPort(id="in")]
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
                source=PortRef(component="T-101", port="outlet"),
                target=PortRef(component="P-101", port="suction"),
            )
        ],
        process=ProcessModel(
            steps=[
                ProcessStep(id="FEED", type="source", ports=[ProcessPort(id="out")]),
                ProcessStep(
                    id="P-101",
                    type="pump",
                    ports=[ProcessPort(id="suction"), ProcessPort(id="discharge")],
                ),
                ProcessStep(id="PRODUCT", type="sink", ports=[ProcessPort(id="in")]),
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
                    id="FEED", type="source", name="Named Feed", ports=[ProcessPort(id="out")]
                ),
                ProcessStep(
                    id="PRODUCT", type="sink", name="Named Product", ports=[ProcessPort(id="in")]
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
            steps=[ProcessStep(id="FEED", type="source", ports=[ProcessPort(id="out")])],
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
                    id="VAR", type="kettle", name="Výrobní kotel α", ports=[ProcessPort(id="out")]
                ),
                ProcessStep(
                    id="CHL", type="cooler", name="Chladič mladiny", ports=[ProcessPort(id="in")]
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
