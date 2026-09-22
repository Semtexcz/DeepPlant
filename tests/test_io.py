from pathlib import Path

import pytest

from deepplant import load_plant
from deepplant.io import PlantLoadError
from deepplant.model import (
    Connection,
    Equipment,
    PipingModel,
    PipingRealization,
    PipingSegment,
    Plant,
    PlantModel,
    Port,
    PortRef,
    ProcessModel,
    ProcessRef,
)

EXAMPLE = Path(__file__).parents[1] / "examples" / "minimal-process" / "plant.yaml"
PROCESS_EXAMPLE = Path(__file__).parents[1] / "examples" / "process-graph" / "plant.yaml"


def write(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "plant.yaml"
    path.write_text(content, encoding="utf-8")
    return path


def test_example_yaml_loads() -> None:
    model = load_plant(str(EXAMPLE))

    assert model.plant.id == "demo"
    assert model.plant.name == "Minimal Process"
    assert len(model.equipment) == 2
    assert [item.id for item in model.equipment] == ["T-101", "P-101"]
    assert model.equipment[0].type == "tank"
    assert model.equipment[1].type == "pump"
    assert [port.id for port in model.equipment[0].ports] == ["outlet"]
    assert [port.id for port in model.equipment[1].ports] == ["suction", "discharge"]
    assert len(model.connections) == 1
    connection = model.connections[0]
    assert (connection.source.component, connection.source.port) == ("T-101", "outlet")
    assert (connection.target.component, connection.target.port) == ("P-101", "suction")


def test_process_example_yaml_loads_and_resolves() -> None:
    model = load_plant(str(PROCESS_EXAMPLE))

    assert model.plant.id == "demo"
    assert isinstance(model.process, ProcessModel)
    assert model.process is not None
    assert [step.id for step in model.process.steps] == ["FEED", "PUMP", "PRODUCT"]
    assert [port.id for port in model.process.steps[1].ports] == ["suction", "discharge"]
    assert [stream.id for stream in model.process.streams] == ["S-001", "S-002"]
    first = model.process.streams[0]
    assert isinstance(first.source, ProcessRef)
    assert (first.source.step, first.source.port) == ("FEED", "out")
    assert (first.target.step, first.target.port) == ("PUMP", "suction")
    second = model.process.streams[1]
    assert (second.source.step, second.source.port) == ("PUMP", "discharge")
    assert (second.target.step, second.target.port) == ("PRODUCT", "in")


def test_yaml_without_process_loads_with_none_process(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
equipment: []
connections: []
""",
    )

    model = load_plant(path)

    assert model.process is None


def test_yaml_with_null_process_loads_with_none_process(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
process: null
""",
    )

    model = load_plant(path)

    assert model.process is None


def test_yaml_with_empty_process_loads_empty_process_model(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
process: {}
""",
    )

    model = load_plant(path)

    assert isinstance(model.process, ProcessModel)
    assert model.process is not None
    assert model.process.steps == []
    assert model.process.streams == []


def test_duplicate_process_step_ids_in_yaml_fail_cleanly(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
process:
  steps:
    - id: FEED
      function: source
    - id: FEED
      function: source
""",
    )

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "invalid DeepPlant model" in str(exc_info.value)
    assert "duplicate ProcessStep id" in str(exc_info.value)


def test_duplicate_process_stream_ids_in_yaml_fail_cleanly(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
process:
  steps:
    - id: FEED
      function: source
      ports:
        - id: out
    - id: PRODUCT
      function: sink
      ports:
        - id: in
  streams:
    - id: S-001
      source:
        step: FEED
        port: out
      target:
        step: PRODUCT
        port: in
    - id: S-001
      source:
        step: PRODUCT
        port: in
      target:
        step: FEED
        port: out
""",
    )

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "invalid DeepPlant model" in str(exc_info.value)
    assert "duplicate ProcessStream id" in str(exc_info.value)


def test_unknown_process_step_in_yaml_fails_cleanly(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
process:
  steps:
    - id: FEED
      function: source
      ports:
        - id: out
    - id: PRODUCT
      function: sink
      ports:
        - id: in
  streams:
    - id: S-001
      source:
        step: X-999
        port: out
      target:
        step: PRODUCT
        port: in
""",
    )

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "invalid DeepPlant model" in str(exc_info.value)
    assert "unknown step 'X-999'" in str(exc_info.value)


def test_unknown_process_port_in_yaml_fails_cleanly(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
process:
  steps:
    - id: FEED
      function: source
      ports:
        - id: out
    - id: PRODUCT
      function: sink
      ports:
        - id: in
  streams:
    - id: S-001
      source:
        step: FEED
        port: missing
      target:
        step: PRODUCT
        port: in
""",
    )

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "invalid DeepPlant model" in str(exc_info.value)
    assert "step 'FEED' has no port 'missing'" in str(exc_info.value)


def test_identical_source_and_target_endpoints_in_yaml_fail_cleanly(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
process:
  steps:
    - id: FEED
      function: source
      ports:
        - id: out
  streams:
    - id: S-001
      source:
        step: FEED
        port: out
      target:
        step: FEED
        port: out
""",
    )

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "invalid DeepPlant model" in str(exc_info.value)
    assert "source and target endpoints are identical" in str(exc_info.value)


def test_unknown_process_field_in_yaml_fails_cleanly(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
process:
  steps: []
  strems: []
""",
    )

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "invalid DeepPlant model" in str(exc_info.value)
    assert "not permitted" in str(exc_info.value)


def test_load_returns_typed_ports_and_connections(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
equipment:
  - id: T-101
    type: tank
    ports:
      - id: outlet
connections:
  - id: C-001
    source:
      component: T-101
      port: outlet
    target:
      component: T-101
      port: outlet
""",
    )

    model = load_plant(path)

    assert isinstance(model.equipment[0].ports[0], Port)
    connection = model.connections[0]
    assert isinstance(connection, Connection)
    assert connection.id == "C-001"
    assert isinstance(connection.source, PortRef)
    assert isinstance(connection.target, PortRef)


def test_connection_with_unknown_component_in_yaml_fails_cleanly(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
equipment:
  - id: T-101
    type: tank
    ports:
      - id: outlet
connections:
  - id: C-001
    source:
      component: X-999
      port: outlet
    target:
      component: T-101
      port: outlet
""",
    )

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "invalid DeepPlant model" in str(exc_info.value)
    assert "connections[0].source: unknown component 'X-999'" in str(exc_info.value)


def test_connection_with_unknown_port_in_yaml_fails_cleanly(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
equipment:
  - id: T-101
    type: tank
    ports:
      - id: outlet
connections:
  - id: C-001
    source:
      component: T-101
      port: missing
    target:
      component: T-101
      port: outlet
""",
    )

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "invalid DeepPlant model" in str(exc_info.value)
    assert "connections[0].source: component 'T-101' has no port 'missing'" in str(exc_info.value)


def test_unknown_port_field_in_yaml_fails_cleanly(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
equipment:
  - id: T-101
    type: tank
    ports:
      - id: outlet
        nozzle: N1
""",
    )

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "invalid DeepPlant model" in str(exc_info.value)
    assert "not permitted" in str(exc_info.value)


def test_load_returns_typed_domain_model(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
equipment:
  - id: T-101
    type: tank
""",
    )

    model = load_plant(path)

    assert isinstance(model, PlantModel)
    assert isinstance(model.plant, Plant)
    assert isinstance(model.equipment[0], Equipment)


def test_missing_plant_id_in_yaml_fails_cleanly(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  name: Minimal Process
equipment: []
""",
    )

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "invalid DeepPlant model" in str(exc_info.value)
    assert "plant" in str(exc_info.value)


def test_empty_equipment_id_in_yaml_fails_cleanly(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
equipment:
  - id: ""
    type: tank
""",
    )

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "invalid DeepPlant model" in str(exc_info.value)
    assert "at least 1 character" in str(exc_info.value)


def test_duplicate_equipment_ids_in_yaml_fail_cleanly(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
equipment:
  - id: T-101
    type: tank
  - id: T-101
    type: pump
""",
    )

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "duplicate equipment id" in str(exc_info.value)


def test_invalid_yaml_syntax_fails_cleanly(tmp_path: Path) -> None:
    path = write(tmp_path, "plant: [unclosed\n  id: demo\n")

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "invalid YAML" in str(exc_info.value)


def test_nonexistent_file_fails_cleanly(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist.yaml"

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(missing)

    assert "cannot read plant file" in str(exc_info.value)


def test_empty_file_fails_cleanly(tmp_path: Path) -> None:
    path = write(tmp_path, "")

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "empty document" in str(exc_info.value)


def test_top_level_scalar_fails_cleanly(tmp_path: Path) -> None:
    path = write(tmp_path, "just a string\n")

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "top level must be a mapping" in str(exc_info.value)


def test_unknown_top_level_key_in_yaml_fails_cleanly(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
equipment: []
equipmnt: []
""",
    )

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "invalid DeepPlant model" in str(exc_info.value)
    assert "not permitted" in str(exc_info.value)


def test_unknown_plant_field_in_yaml_fails_cleanly(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
  unknown_field: value
equipment: []
""",
    )

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "invalid DeepPlant model" in str(exc_info.value)
    assert "not permitted" in str(exc_info.value)


def test_unknown_equipment_field_in_yaml_fails_cleanly(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
equipment:
  - id: P-101
    type: pump
    nam: Feed Pump
""",
    )

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "invalid DeepPlant model" in str(exc_info.value)
    assert "not permitted" in str(exc_info.value)


def test_whitespace_plant_id_in_yaml_fails_cleanly(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: "   "
equipment: []
""",
    )

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "at least 1 character" in str(exc_info.value)


def test_whitespace_equipment_type_in_yaml_fails_cleanly(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
equipment:
  - id: P-101
    type: "   "
""",
    )

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "at least 1 character" in str(exc_info.value)


# --- Piping realization layer (ADR-0011) -------------------------------------

PIPING_SOURCE = """
plant:
  id: demo
equipment:
  - id: P-101
    type: pump
    ports:
      - id: discharge
      - id: suction
  - id: FV-101
    type: control-valve
    ports:
      - id: inlet
      - id: outlet
connections:
  - id: C-001
    source:
      component: P-101
      port: discharge
    target:
      component: FV-101
      port: inlet
  - id: C-002
    source:
      component: FV-101
      port: outlet
    target:
      component: P-101
      port: suction
piping:
  lines:
    - id: PL-P101-DISCHARGE
      line_number: 3"-P-101-A1A
      segments:
        - id: SEG-1
          segment_number: S-1
          nominal_diameter: DN80
          piping_class: A1A
          fluid_code: P
          realizations:
            - connection: C-001
            - connection: C-002
              kind: direct
"""


def test_piping_section_loads_through_the_loader(tmp_path: Path) -> None:
    model = load_plant(write(tmp_path, PIPING_SOURCE))

    assert isinstance(model.piping, PipingModel)
    piping = model.piping
    assert piping is not None
    assert [line.id for line in piping.lines] == ["PL-P101-DISCHARGE"]
    line = piping.lines[0]
    assert line.line_number == '3"-P-101-A1A'
    assert line.name is None
    segment = line.segments[0]
    assert isinstance(segment, PipingSegment)
    assert (segment.id, segment.segment_number) == ("SEG-1", "S-1")
    assert (segment.nominal_diameter, segment.piping_class) == ("DN80", "A1A")
    assert segment.fluid_code == "P"
    assert isinstance(segment.realizations[0], PipingRealization)
    assert [(item.connection, item.kind) for item in segment.realizations] == [
        ("C-001", "pipe"),
        ("C-002", "direct"),
    ]
    assert model.process is None


def test_connection_ids_load_from_yaml(tmp_path: Path) -> None:
    model = load_plant(write(tmp_path, PIPING_SOURCE))

    assert [
        (connection.id, connection.source.component, connection.target.component)
        for connection in model.connections
    ] == [("C-001", "P-101", "FV-101"), ("C-002", "FV-101", "P-101")]


def test_piping_yaml_without_kind_loads_as_pipe(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
equipment:
  - id: T-101
    type: tank
    ports:
      - id: outlet
connections:
  - id: C-001
    source:
      component: T-101
      port: outlet
    target:
      component: T-101
      port: outlet
piping:
  lines:
    - id: PL-1
      segments:
        - id: SEG-1
          realizations:
            - connection: C-001
""",
    )

    model = load_plant(path)

    assert model.piping is not None
    realization = model.piping.lines[0].segments[0].realizations[0]
    assert realization.kind == "pipe"
    assert model.piping.lines[0].line_number is None
    assert model.piping.lines[0].segments[0].segment_number is None


def test_yaml_without_piping_loads_with_none_piping(tmp_path: Path) -> None:
    path = write(tmp_path, "plant:\n  id: demo\nequipment: []\nconnections: []\n")

    assert load_plant(path).piping is None


def test_yaml_with_null_piping_loads_with_none_piping(tmp_path: Path) -> None:
    assert load_plant(write(tmp_path, "plant:\n  id: demo\npiping: null\n")).piping is None


def test_yaml_with_empty_piping_loads_empty_piping_model(tmp_path: Path) -> None:
    model = load_plant(write(tmp_path, "plant:\n  id: demo\npiping: {}\n"))

    assert isinstance(model.piping, PipingModel)
    piping = model.piping
    assert piping is not None
    assert piping.lines == []


def test_missing_connection_id_in_yaml_fails_cleanly(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
equipment:
  - id: T-101
    type: tank
    ports:
      - id: outlet
connections:
  - source:
      component: T-101
      port: outlet
    target:
      component: T-101
      port: outlet
""",
    )

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "invalid DeepPlant model" in str(exc_info.value)
    assert "connections.0.id" in str(exc_info.value)


def test_duplicate_connection_ids_in_yaml_fail_cleanly(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
equipment:
  - id: T-101
    type: tank
    ports:
      - id: outlet
connections:
  - id: C-001
    source:
      component: T-101
      port: outlet
    target:
      component: T-101
      port: outlet
  - id: C-001
    source:
      component: T-101
      port: outlet
    target:
      component: T-101
      port: outlet
""",
    )

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "duplicate connection id(s): C-001" in str(exc_info.value)


def test_dangling_realization_reference_in_yaml_fails_cleanly(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
equipment:
  - id: T-101
    type: tank
    ports:
      - id: outlet
connections:
  - id: C-001
    source:
      component: T-101
      port: outlet
    target:
      component: T-101
      port: outlet
piping:
  lines:
    - id: PL-1
      segments:
        - id: SEG-1
          realizations:
            - connection: C-999
""",
    )

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "invalid DeepPlant model" in str(exc_info.value)
    assert "unknown connection 'C-999'" in str(exc_info.value)


def test_empty_segment_realizations_in_yaml_fail_cleanly(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
piping:
  lines:
    - id: PL-1
      segments:
        - id: SEG-1
          realizations: []
""",
    )

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "must contain at least one realization" in str(exc_info.value)


def test_unsupported_realization_kind_in_yaml_fails_cleanly(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
piping:
  lines:
    - id: PL-1
      segments:
        - id: SEG-1
          realizations:
            - connection: C-001
              kind: ppie
""",
    )

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "invalid DeepPlant model" in str(exc_info.value)
    assert "kind" in str(exc_info.value)


def test_unknown_piping_field_in_yaml_fails_cleanly(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
plant:
  id: demo
piping:
  lines:
    - id: PL-1
      segments:
        - id: SEG-1
          realizations:
            - connection: C-001
              kind: pipe
              insulation: hot
""",
    )

    with pytest.raises(PlantLoadError) as exc_info:
        load_plant(path)

    assert "invalid DeepPlant model" in str(exc_info.value)
    assert "not permitted" in str(exc_info.value)
