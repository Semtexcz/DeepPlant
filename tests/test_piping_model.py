"""Structural tests for the ADR-0011 physical piping realization layer.

C1 and P1-P5 are structural/referential rules, so they are exercised directly
on the semantic models, independently of YAML. Loader coverage lives in
``tests/test_io.py`` and canonical round-trip coverage in
``tests/test_roundtrip.py``.
"""

from typing import Literal

import pytest
from pydantic import ValidationError

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
    ProcessStep,
)


def _physical() -> tuple[dict[str, object], Connection, Connection]:
    """One small synthetic physical layer with two adjacent pump-run edges."""
    equipment = [
        Equipment(id="P-101", type="pump", ports=[Port(id="discharge"), Port(id="suction")]),
        Equipment(id="FV-101", type="control-valve", ports=[Port(id="inlet"), Port(id="outlet")]),
    ]
    first = Connection(
        id="C-001",
        source=PortRef(component="P-101", port="discharge"),
        target=PortRef(component="FV-101", port="inlet"),
    )
    second = Connection(
        id="C-002",
        source=PortRef(component="FV-101", port="outlet"),
        target=PortRef(component="P-101", port="suction"),
    )
    return {"plant": Plant(id="demo"), "equipment": equipment}, first, second


def _connection(id_: str, source: tuple[str, str], target: tuple[str, str]) -> Connection:
    return Connection(
        id=id_,
        source=PortRef(component=source[0], port=source[1]),
        target=PortRef(component=target[0], port=target[1]),
    )


def _pipe(connection: str) -> PipingRealization:
    return PipingRealization(connection=connection)


def _realization(connection: str, kind: Literal["pipe", "direct"]) -> PipingRealization:
    return PipingRealization(connection=connection, kind=kind)


def _segment(id_: str, *connections: str) -> PipingSegment:
    return PipingSegment(id=id_, realizations=[_pipe(connection) for connection in connections])


def _line(id_: str, segment: PipingSegment) -> PipingLine:
    return PipingLine(id=id_, segments=[segment])


def test_connection_gains_identity_only() -> None:
    connection = _connection("C-001", ("P-101", "discharge"), ("FV-101", "inlet"))

    assert connection.id == "C-001"
    assert connection.source == PortRef(component="P-101", port="discharge")
    assert connection.target == PortRef(component="FV-101", port="inlet")
    # Identity only: no pipe, line, segment, kind, fluid, DN, or class field.
    assert set(Connection.model_fields) == {"id", "source", "target"}


def test_plant_model_owns_identified_connections() -> None:
    fields, first, _ = _physical()
    model = PlantModel.model_validate({**fields, "connections": [first]})

    assert [connection.id for connection in model.connections] == ["C-001"]
    assert model.piping is None


def test_missing_connection_id_fails_c1() -> None:
    fields, first, _ = _physical()
    connection = first.model_dump(mode="python")
    connection.pop("id")

    with pytest.raises(ValidationError, match="id"):
        PlantModel.model_validate({**fields, "connections": [connection]})


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_blank_connection_id_fails_c1(blank: str) -> None:
    with pytest.raises(ValidationError):
        _connection(blank, ("P-101", "discharge"), ("FV-101", "inlet"))


def test_duplicate_connection_ids_fail_c1() -> None:
    fields, first, _ = _physical()

    with pytest.raises(ValidationError, match="duplicate connection id\\(s\\): C-001"):
        PlantModel.model_validate({**fields, "connections": [first, first.model_copy()]})


def test_duplicate_connection_id_error_is_deterministic() -> None:
    fields, _, _ = _physical()
    endpoint = [("P-101", "discharge"), ("FV-101", "inlet")]
    connections = [
        _connection("C-002", endpoint[0], endpoint[1]),
        _connection("C-001", endpoint[0], endpoint[1]),
        _connection("C-002", endpoint[0], endpoint[1]),
        _connection("C-001", endpoint[0], endpoint[1]),
    ]

    with pytest.raises(ValidationError, match="duplicate connection id\\(s\\): C-001, C-002"):
        PlantModel.model_validate({**fields, "connections": connections})


def test_realization_kind_defaults_to_pipe() -> None:
    realization = PipingRealization(connection="C-001")

    assert realization.kind == "pipe"
    assert realization.connection == "C-001"


@pytest.mark.parametrize("kind", ["pipe", "direct"])
def test_realization_accepts_the_closed_kind_vocabulary(
    kind: Literal["pipe", "direct"],
) -> None:
    assert _realization("C-001", kind).kind == kind


@pytest.mark.parametrize("kind", ["ppie", "Pipe", "pipe ", "", "direct_connection", "1"])
def test_realization_rejects_unsupported_kind(kind: str) -> None:
    with pytest.raises(ValidationError):
        PipingRealization.model_validate({"connection": "C-001", "kind": kind})


def test_realization_connection_must_not_be_blank() -> None:
    with pytest.raises(ValidationError):
        PipingRealization(connection="   ")


def test_realization_restates_no_endpoints() -> None:
    assert set(PipingRealization.model_fields) == {"connection", "kind"}


def test_unknown_realization_field_fails() -> None:
    with pytest.raises(ValidationError):
        PipingRealization.model_validate(
            {"connection": "C-001", "kind": "pipe", "nominal_diameter": "DN80"}
        )


def test_segment_holds_adr_0011_fields() -> None:
    segment = PipingSegment(
        id="SEG-1",
        segment_number="S-1",
        nominal_diameter="DN80",
        piping_class="A1A",
        fluid_code="P",
        realizations=[_pipe("C-001")],
    )

    assert set(PipingSegment.model_fields) == {
        "id",
        "segment_number",
        "nominal_diameter",
        "piping_class",
        "fluid_code",
        "realizations",
    }
    assert segment.id == "SEG-1"
    assert segment.segment_number == "S-1"


def test_segment_optional_properties_default_to_none() -> None:
    segment = _segment("SEG-1", "C-001")

    assert segment.segment_number is None
    assert segment.nominal_diameter is None
    assert segment.piping_class is None
    assert segment.fluid_code is None


def test_segment_id_is_not_derived_from_segment_number() -> None:
    segment = PipingSegment(
        id="SEG-1",
        segment_number='3"-P-101-A1A',
        realizations=[_pipe("C-001")],
    )

    assert segment.id == "SEG-1"
    assert segment.segment_number != segment.id


def test_empty_segment_fails_p5() -> None:
    with pytest.raises(ValidationError, match="must contain at least one realization"):
        PipingSegment(id="SEG-1", realizations=[])


def test_segment_with_omitted_realizations_fails_p5() -> None:
    with pytest.raises(ValidationError, match="must contain at least one realization"):
        PipingSegment(id="SEG-1")


def test_unknown_segment_field_fails() -> None:
    with pytest.raises(ValidationError):
        PipingSegment.model_validate(
            {"id": "SEG-1", "realizations": [{"connection": "C-001"}], "insulation": "hot"}
        )


def test_duplicate_segment_ids_within_one_line_fail_p2() -> None:
    with pytest.raises(
        ValidationError, match="piping line 'LINE-A' has duplicate segment id\\(s\\): SEG-1"
    ):
        PipingLine(id="LINE-A", segments=[_segment("SEG-1", "C-001"), _segment("SEG-1", "C-002")])


def test_same_segment_id_is_allowed_in_different_lines() -> None:
    model = PipingModel(
        lines=[
            _line("LINE-A", _segment("SEG-1", "C-001")),
            _line("LINE-B", _segment("SEG-1", "C-002")),
        ]
    )

    assert [segment.id for line in model.lines for segment in line.segments] == ["SEG-1", "SEG-1"]


def test_line_number_is_optional_and_never_identity() -> None:
    line = PipingLine(
        id="PL-1",
        line_number='3"-P-101-A1A',
        name="Pump Discharge",
        segments=[_segment("SEG-1", "C-001")],
    )

    assert line.id == "PL-1"
    assert line.line_number != line.id
    assert line.name == "Pump Discharge"
    assert set(PipingLine.model_fields) == {"id", "line_number", "name", "segments"}


def test_line_number_is_not_required() -> None:
    assert _line("PL-1", _segment("SEG-1", "C-001")).line_number is None


def test_duplicate_line_numbers_are_allowed() -> None:
    """Line identity is ``id``; no uniqueness rule is invented for line numbers."""
    lines = [
        PipingLine(
            id=id_,
            line_number="SHARED-NUMBER",
            segments=[_segment("SEG-1", connection)],
        )
        for id_, connection in (("LINE-A", "C-001"), ("LINE-B", "C-002"))
    ]

    assert [line.line_number for line in PipingModel(lines=lines).lines] == [
        "SHARED-NUMBER",
        "SHARED-NUMBER",
    ]


def test_unknown_line_field_fails() -> None:
    with pytest.raises(ValidationError):
        PipingLine.model_validate(
            {
                "id": "PL-1",
                "segments": [{"id": "SEG-1", "realizations": [{"connection": "C-001"}]}],
                "fluid_code": "P",
            }
        )


def test_duplicate_line_ids_fail_p1() -> None:
    with pytest.raises(ValidationError, match="duplicate PipingLine id\\(s\\): LINE-A"):
        PipingModel(
            lines=[
                _line("LINE-A", _segment("SEG-1", "C-001")),
                _line("LINE-A", _segment("SEG-2", "C-002")),
            ]
        )


def test_duplicate_realization_across_lines_fails_p4() -> None:
    with pytest.raises(
        ValidationError, match="duplicate realization connection reference\\(s\\): C-001"
    ):
        PipingModel(
            lines=[
                _line("LINE-A", _segment("SEG-1", "C-001")),
                _line("LINE-B", _segment("SEG-7", "C-001")),
            ]
        )


def test_duplicate_realization_across_segments_of_one_line_fails_p4() -> None:
    with pytest.raises(
        ValidationError, match="duplicate realization connection reference\\(s\\): C-001"
    ):
        PipingModel(
            lines=[
                PipingLine(
                    id="LINE-A", segments=[_segment("SEG-1", "C-001"), _segment("SEG-2", "C-001")]
                )
            ]
        )


def test_several_distinct_realizations_in_one_segment_are_allowed() -> None:
    line = _line("PL-1", _segment("SEG-1", "C-001", "C-002"))

    assert [item.connection for item in line.segments[0].realizations] == ["C-001", "C-002"]


def test_empty_piping_model_is_valid() -> None:
    model = PlantModel(plant=Plant(id="demo"), piping=PipingModel())

    assert model.piping is not None
    assert model.piping.lines == []


def test_unknown_piping_model_field_fails() -> None:
    with pytest.raises(ValidationError):
        PipingModel.model_validate({"lines": [], "systems": []})


def test_mutable_defaults_are_not_shared_between_instances() -> None:
    first_line = PipingLine(id="LINE-A")
    second_line = PipingLine(id="LINE-B")
    first_line.segments.append(_segment("SEG-1", "C-001"))

    first_model = PipingModel()
    second_model = PipingModel()
    first_model.lines.append(first_line)

    assert second_line.segments == []
    assert second_model.lines == []


def _piping(*connections: str) -> dict[str, object]:
    return {
        "lines": [
            {
                "id": "PL-1",
                "segments": [
                    {"id": f"SEG-{index}", "realizations": [{"connection": connection}]}
                    for index, connection in enumerate(connections, start=1)
                ],
            }
        ]
    }


def test_dangling_realization_reference_fails_p3() -> None:
    fields, first, _ = _physical()

    with pytest.raises(ValidationError, match="unknown connection 'C-999'"):
        PlantModel.model_validate({**fields, "connections": [first], "piping": _piping("C-999")})


def test_p3_error_names_the_owning_realization() -> None:
    fields, first, _ = _physical()

    with pytest.raises(ValidationError) as exc_info:
        PlantModel.model_validate({**fields, "connections": [first], "piping": _piping("C-999")})

    message = str(exc_info.value)
    assert "piping.lines[0].segments[0].realizations[0].connection" in message
    assert "unknown connection 'C-999'" in message


def test_p3_is_scoped_to_the_same_plant() -> None:
    """A connection that is not part of this plant does not resolve."""
    fields, first, _ = _physical()

    with pytest.raises(ValidationError, match="unknown connection 'C-002'"):
        PlantModel.model_validate({**fields, "connections": [first], "piping": _piping("C-002")})


def test_realizations_resolve_against_plant_connections() -> None:
    fields, first, second = _physical()
    model = PlantModel.model_validate(
        {**fields, "connections": [first, second], "piping": _piping("C-001", "C-002")}
    )

    assert model.piping is not None
    realizations = [
        item for segment in model.piping.lines[0].segments for item in segment.realizations
    ]
    assert [(item.connection, item.kind) for item in realizations] == [
        ("C-001", "pipe"),
        ("C-002", "pipe"),
    ]


def test_unknown_piping_section_field_fails() -> None:
    fields, first, _ = _physical()

    with pytest.raises(ValidationError, match="piping"):
        PlantModel.model_validate(
            {**fields, "connections": [first], "piping": {"lines": [], "systems": []}}
        )


def test_piping_id_namespaces_stay_independent_of_equipment_ids() -> None:
    fields, first, _ = _physical()
    model = PlantModel.model_validate(
        {
            **fields,
            "connections": [first],
            "piping": {
                "lines": [
                    {
                        "id": "P-101",
                        "segments": [{"id": "P-101", "realizations": [{"connection": "C-001"}]}],
                    }
                ]
            },
        }
    )

    assert [item.id for item in model.equipment] == ["P-101", "FV-101"]
    assert model.piping is not None
    assert [line.id for line in model.piping.lines] == ["P-101"]


def test_piping_validates_without_any_process_model() -> None:
    fields, first, _ = _physical()
    model = PlantModel.model_validate(
        {**fields, "connections": [first], "piping": _piping("C-001")}
    )

    assert model.process is None
    assert model.piping is not None


def test_process_model_stays_valid_without_piping() -> None:
    model = PlantModel(
        plant=Plant(id="demo"),
        process=ProcessModel(
            steps=[
                ProcessStep(id="A", function="source", ports=[ProcessPort(id="out")]),
                ProcessStep(id="B", function="sink", ports=[ProcessPort(id="in")]),
            ]
        ),
    )

    assert model.piping is None
    process = model.process
    assert process is not None
    assert [step.id for step in process.steps] == ["A", "B"]


def test_piping_models_carry_no_process_or_presentation_fields() -> None:
    forbidden = {
        "process_ref",
        "stream_ref",
        "realized_by",
        "implements",
        "maps_to",
        "x",
        "y",
        "rotation",
        "symbol",
        "sheet",
        "route",
        "geometry",
    }
    for model in (PipingRealization, PipingSegment, PipingLine, PipingModel):
        assert forbidden.isdisjoint(set(model.model_fields)), model.__name__


def test_direct_realization_is_proven_with_a_synthetic_adjacency() -> None:
    """``kind: direct`` coverage with an explicitly synthetic pipe-less adjacency.

    The committed realistic fragment provides no evidence that any of its
    adjacencies is direct, so this test builds its own synthetic case instead of
    falsifying the example (ADR-0011).
    """
    model = PlantModel(
        plant=Plant(id="synthetic-direct"),
        equipment=[
            Equipment(id="P-201", type="pump", ports=[Port(id="discharge_flange")]),
            Equipment(id="V-201", type="vessel", ports=[Port(id="inlet_flange")]),
        ],
        connections=[
            _connection("C-201", ("P-201", "discharge_flange"), ("V-201", "inlet_flange"))
        ],
        piping=PipingModel(
            lines=[
                PipingLine(
                    id="PL-SYNTHETIC-DIRECT",
                    segments=[
                        PipingSegment(
                            id="SEG-1",
                            realizations=[_realization("C-201", "direct")],
                        )
                    ],
                )
            ]
        ),
    )

    assert model.piping is not None
    realization = model.piping.lines[0].segments[0].realizations[0]
    assert realization.kind == "direct"
    assert realization.connection == "C-201"
    assert realization.kind != "pipe"
