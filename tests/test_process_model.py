import pytest
from pydantic import ValidationError

from deepplant.model import (
    ProcessModel,
    ProcessPort,
    ProcessRef,
    ProcessStep,
    ProcessStream,
)


def test_valid_chain_model() -> None:
    model = ProcessModel(
        steps=[
            ProcessStep(id="A", type="source", ports=[ProcessPort(id="out")]),
            ProcessStep(id="B", type="sink", ports=[ProcessPort(id="in")]),
        ],
        streams=[
            ProcessStream(
                id="S-1",
                name="A to B",
                source=ProcessRef(step="A", port="out"),
                target=ProcessRef(step="B", port="in"),
            )
        ],
    )

    assert [step.id for step in model.steps] == ["A", "B"]
    assert model.steps[0].ports[0].id == "out"
    assert model.streams[0].id == "S-1"
    assert model.streams[0].name == "A to B"
    assert (model.streams[0].source.step, model.streams[0].source.port) == ("A", "out")
    assert (model.streams[0].target.step, model.streams[0].target.port) == ("B", "in")


def test_process_model_may_be_empty() -> None:
    model = ProcessModel()

    assert model.steps == []
    assert model.streams == []


def test_process_optional_names_default_to_none() -> None:
    model = ProcessModel(
        steps=[
            ProcessStep(id="A", type="source", ports=[ProcessPort(id="out")]),
            ProcessStep(id="B", type="sink", ports=[ProcessPort(id="in")]),
        ],
        streams=[
            ProcessStream(
                id="S-1",
                source=ProcessRef(step="A", port="out"),
                target=ProcessRef(step="B", port="in"),
            )
        ],
    )

    assert model.steps[0].name is None
    assert model.streams[0].name is None


def test_duplicate_process_step_ids_fail() -> None:
    with pytest.raises(ValidationError, match="duplicate ProcessStep id"):
        ProcessModel.model_validate(
            {
                "steps": [
                    {"id": "A", "type": "source"},
                    {"id": "A", "type": "sink"},
                ]
            }
        )


def test_duplicate_process_stream_ids_fail() -> None:
    with pytest.raises(ValidationError, match="duplicate ProcessStream id"):
        ProcessModel.model_validate(
            {
                "steps": [
                    {"id": "A", "type": "t", "ports": [{"id": "in"}, {"id": "out"}]},
                    {"id": "B", "type": "t", "ports": [{"id": "in"}, {"id": "out"}]},
                ],
                "streams": [
                    {
                        "id": "S-1",
                        "source": {"step": "A", "port": "out"},
                        "target": {"step": "B", "port": "in"},
                    },
                    {
                        "id": "S-1",
                        "source": {"step": "B", "port": "out"},
                        "target": {"step": "A", "port": "in"},
                    },
                ],
            }
        )


def test_step_and_stream_may_share_the_same_id() -> None:
    model = ProcessModel.model_validate(
        {
            "steps": [
                {"id": "X", "type": "source", "ports": [{"id": "out"}]},
                {"id": "Y", "type": "sink", "ports": [{"id": "in"}]},
            ],
            "streams": [
                {
                    "id": "X",
                    "source": {"step": "X", "port": "out"},
                    "target": {"step": "Y", "port": "in"},
                }
            ],
        }
    )

    assert model.steps[0].id == "X"
    assert model.streams[0].id == "X"


def test_duplicate_process_port_ids_on_same_step_fail() -> None:
    with pytest.raises(ValidationError, match="duplicate port id"):
        ProcessStep(
            id="A",
            type="mix",
            ports=[ProcessPort(id="inlet"), ProcessPort(id="inlet")],
        )


def test_same_process_port_id_on_different_steps_is_allowed() -> None:
    model = ProcessModel(
        steps=[
            ProcessStep(id="A", type="source", ports=[ProcessPort(id="inlet")]),
            ProcessStep(id="B", type="sink", ports=[ProcessPort(id="inlet")]),
        ]
    )

    assert [port.id for port in model.steps[0].ports] == ["inlet"]
    assert [port.id for port in model.steps[1].ports] == ["inlet"]


def test_stream_source_with_unknown_step_fails() -> None:
    with pytest.raises(ValidationError, match="streams\\[0\\].source: unknown step 'X-999'"):
        ProcessModel.model_validate(
            {
                "steps": [
                    {"id": "A", "type": "t", "ports": [{"id": "out"}]},
                    {"id": "B", "type": "t", "ports": [{"id": "in"}]},
                ],
                "streams": [
                    {
                        "id": "S-1",
                        "source": {"step": "X-999", "port": "out"},
                        "target": {"step": "B", "port": "in"},
                    }
                ],
            }
        )


def test_stream_target_with_unknown_step_fails() -> None:
    with pytest.raises(ValidationError, match="streams\\[0\\].target: unknown step 'X-999'"):
        ProcessModel.model_validate(
            {
                "steps": [
                    {"id": "A", "type": "t", "ports": [{"id": "out"}]},
                    {"id": "B", "type": "t", "ports": [{"id": "in"}]},
                ],
                "streams": [
                    {
                        "id": "S-1",
                        "source": {"step": "A", "port": "out"},
                        "target": {"step": "X-999", "port": "in"},
                    }
                ],
            }
        )


def test_stream_source_with_unknown_port_fails() -> None:
    with pytest.raises(
        ValidationError, match="streams\\[0\\].source: step 'A' has no port 'missing'"
    ):
        ProcessModel.model_validate(
            {
                "steps": [
                    {"id": "A", "type": "t", "ports": [{"id": "out"}]},
                    {"id": "B", "type": "t", "ports": [{"id": "in"}]},
                ],
                "streams": [
                    {
                        "id": "S-1",
                        "source": {"step": "A", "port": "missing"},
                        "target": {"step": "B", "port": "in"},
                    }
                ],
            }
        )


def test_stream_target_with_unknown_port_fails() -> None:
    with pytest.raises(
        ValidationError, match="streams\\[0\\].target: step 'B' has no port 'missing'"
    ):
        ProcessModel.model_validate(
            {
                "steps": [
                    {"id": "A", "type": "t", "ports": [{"id": "out"}]},
                    {"id": "B", "type": "t", "ports": [{"id": "in"}]},
                ],
                "streams": [
                    {
                        "id": "S-1",
                        "source": {"step": "A", "port": "out"},
                        "target": {"step": "B", "port": "missing"},
                    }
                ],
            }
        )


def test_stream_with_identical_source_and_target_endpoints_fails() -> None:
    with pytest.raises(ValidationError, match="source and target endpoints are identical"):
        ProcessModel.model_validate(
            {
                "steps": [
                    {"id": "A", "type": "t", "ports": [{"id": "in"}, {"id": "out"}]},
                ],
                "streams": [
                    {
                        "id": "S-1",
                        "source": {"step": "A", "port": "out"},
                        "target": {"step": "A", "port": "out"},
                    }
                ],
            }
        )


def test_recycle_cycle_is_allowed() -> None:
    model = ProcessModel.model_validate(
        {
            "steps": [
                {"id": "A", "type": "t", "ports": [{"id": "in"}, {"id": "out"}]},
                {"id": "B", "type": "t", "ports": [{"id": "in"}, {"id": "out"}]},
                {"id": "C", "type": "t", "ports": [{"id": "in"}, {"id": "out"}]},
            ],
            "streams": [
                {
                    "id": "S-1",
                    "source": {"step": "A", "port": "out"},
                    "target": {"step": "B", "port": "in"},
                },
                {
                    "id": "S-2",
                    "source": {"step": "B", "port": "out"},
                    "target": {"step": "C", "port": "in"},
                },
                {
                    "id": "S-3",
                    "source": {"step": "C", "port": "out"},
                    "target": {"step": "A", "port": "in"},
                },
            ],
        }
    )

    assert len(model.steps) == 3
    assert len(model.streams) == 3


def test_mixing_topology_is_structurally_allowed() -> None:
    model = ProcessModel.model_validate(
        {
            "steps": [
                {"id": "A", "type": "feed", "ports": [{"id": "out"}]},
                {"id": "B", "type": "recycle", "ports": [{"id": "out"}]},
                {
                    "id": "MIX",
                    "type": "mix",
                    "ports": [{"id": "in_a"}, {"id": "in_b"}, {"id": "out"}],
                },
                {"id": "C", "type": "consumer", "ports": [{"id": "in"}]},
            ],
            "streams": [
                {
                    "id": "S-1",
                    "source": {"step": "A", "port": "out"},
                    "target": {"step": "MIX", "port": "in_a"},
                },
                {
                    "id": "S-2",
                    "source": {"step": "B", "port": "out"},
                    "target": {"step": "MIX", "port": "in_b"},
                },
                {
                    "id": "S-3",
                    "source": {"step": "MIX", "port": "out"},
                    "target": {"step": "C", "port": "in"},
                },
            ],
        }
    )

    assert [stream.source.step for stream in model.streams] == ["A", "B", "MIX"]


def test_splitting_topology_is_structurally_allowed() -> None:
    model = ProcessModel.model_validate(
        {
            "steps": [
                {"id": "A", "type": "feed", "ports": [{"id": "out"}]},
                {
                    "id": "SPLIT",
                    "type": "split",
                    "ports": [{"id": "in"}, {"id": "out_b"}, {"id": "out_c"}],
                },
                {"id": "B", "type": "consumer", "ports": [{"id": "in"}]},
                {"id": "C", "type": "consumer", "ports": [{"id": "in"}]},
            ],
            "streams": [
                {
                    "id": "S-1",
                    "source": {"step": "A", "port": "out"},
                    "target": {"step": "SPLIT", "port": "in"},
                },
                {
                    "id": "S-2",
                    "source": {"step": "SPLIT", "port": "out_b"},
                    "target": {"step": "B", "port": "in"},
                },
                {
                    "id": "S-3",
                    "source": {"step": "SPLIT", "port": "out_c"},
                    "target": {"step": "C", "port": "in"},
                },
            ],
        }
    )

    assert [stream.target.step for stream in model.streams] == ["SPLIT", "B", "C"]


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_blank_process_step_id_fails(blank: str) -> None:
    with pytest.raises(ValidationError):
        ProcessStep(id=blank, type="source")


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_blank_process_step_type_fails(blank: str) -> None:
    with pytest.raises(ValidationError):
        ProcessStep(id="A", type=blank)


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_blank_process_port_id_fails(blank: str) -> None:
    with pytest.raises(ValidationError):
        ProcessPort(id=blank)


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_blank_process_ref_step_fails(blank: str) -> None:
    with pytest.raises(ValidationError):
        ProcessRef(step=blank, port="out")


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_blank_process_ref_port_fails(blank: str) -> None:
    with pytest.raises(ValidationError):
        ProcessRef(step="A", port=blank)


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_blank_process_stream_id_fails(blank: str) -> None:
    with pytest.raises(ValidationError):
        ProcessStream(
            id=blank,
            source=ProcessRef(step="A", port="out"),
            target=ProcessRef(step="B", port="in"),
        )


def test_unknown_process_port_field_fails() -> None:
    with pytest.raises(ValidationError):
        ProcessPort.model_validate({"id": "out", "direction": "out"})


def test_unknown_process_step_field_fails() -> None:
    with pytest.raises(ValidationError):
        ProcessStep.model_validate({"id": "A", "type": "t", "medium": "water"})


def test_unknown_process_ref_field_fails() -> None:
    with pytest.raises(ValidationError):
        ProcessRef.model_validate({"step": "A", "port": "out", "nozzle": "N1"})


def test_unknown_process_stream_field_fails() -> None:
    with pytest.raises(ValidationError):
        ProcessStream.model_validate(
            {
                "id": "S-1",
                "source": {"step": "A", "port": "out"},
                "target": {"step": "B", "port": "in"},
                "flow": 1.0,
            }
        )


def test_unknown_process_model_field_fails() -> None:
    with pytest.raises(ValidationError):
        ProcessModel.model_validate({"steps": [], "streams": [], "process": {}})
