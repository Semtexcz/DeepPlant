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
            ProcessStep(id="A", function="source", ports=[ProcessPort(id="out")]),
            ProcessStep(id="B", function="sink", ports=[ProcessPort(id="in")]),
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
            ProcessStep(id="A", function="source", ports=[ProcessPort(id="out")]),
            ProcessStep(id="B", function="sink", ports=[ProcessPort(id="in")]),
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
                    {"id": "A", "function": "source"},
                    {"id": "A", "function": "sink"},
                ]
            }
        )


def test_duplicate_process_stream_ids_fail() -> None:
    with pytest.raises(ValidationError, match="duplicate ProcessStream id"):
        ProcessModel.model_validate(
            {
                "steps": [
                    {"id": "A", "function": "t", "ports": [{"id": "in"}, {"id": "out"}]},
                    {"id": "B", "function": "t", "ports": [{"id": "in"}, {"id": "out"}]},
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
                {"id": "X", "function": "source", "ports": [{"id": "out"}]},
                {"id": "Y", "function": "sink", "ports": [{"id": "in"}]},
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
            function="mix",
            ports=[ProcessPort(id="inlet"), ProcessPort(id="inlet")],
        )


def test_same_process_port_id_on_different_steps_is_allowed() -> None:
    model = ProcessModel(
        steps=[
            ProcessStep(id="A", function="source", ports=[ProcessPort(id="inlet")]),
            ProcessStep(id="B", function="sink", ports=[ProcessPort(id="inlet")]),
        ]
    )

    assert [port.id for port in model.steps[0].ports] == ["inlet"]
    assert [port.id for port in model.steps[1].ports] == ["inlet"]


def test_stream_source_with_unknown_step_fails() -> None:
    with pytest.raises(ValidationError, match="streams\\[0\\].source: unknown step 'X-999'"):
        ProcessModel.model_validate(
            {
                "steps": [
                    {"id": "A", "function": "t", "ports": [{"id": "out"}]},
                    {"id": "B", "function": "t", "ports": [{"id": "in"}]},
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
                    {"id": "A", "function": "t", "ports": [{"id": "out"}]},
                    {"id": "B", "function": "t", "ports": [{"id": "in"}]},
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
                    {"id": "A", "function": "t", "ports": [{"id": "out"}]},
                    {"id": "B", "function": "t", "ports": [{"id": "in"}]},
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
                    {"id": "A", "function": "t", "ports": [{"id": "out"}]},
                    {"id": "B", "function": "t", "ports": [{"id": "in"}]},
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
                    {"id": "A", "function": "t", "ports": [{"id": "in"}, {"id": "out"}]},
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
                {"id": "A", "function": "t", "ports": [{"id": "in"}, {"id": "out"}]},
                {"id": "B", "function": "t", "ports": [{"id": "in"}, {"id": "out"}]},
                {"id": "C", "function": "t", "ports": [{"id": "in"}, {"id": "out"}]},
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
                {"id": "A", "function": "feed", "ports": [{"id": "out"}]},
                {"id": "B", "function": "recycle", "ports": [{"id": "out"}]},
                {
                    "id": "MIX",
                    "function": "mix",
                    "ports": [{"id": "in_a"}, {"id": "in_b"}, {"id": "out"}],
                },
                {"id": "C", "function": "consumer", "ports": [{"id": "in"}]},
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
                {"id": "A", "function": "feed", "ports": [{"id": "out"}]},
                {
                    "id": "SPLIT",
                    "function": "split",
                    "ports": [{"id": "in"}, {"id": "out_b"}, {"id": "out_c"}],
                },
                {"id": "B", "function": "consumer", "ports": [{"id": "in"}]},
                {"id": "C", "function": "consumer", "ports": [{"id": "in"}]},
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
        ProcessStep(id=blank, function="source")


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_blank_process_step_function_fails(blank: str) -> None:
    with pytest.raises(ValidationError):
        ProcessStep(id="A", function=blank)


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
        ProcessStep.model_validate({"id": "A", "function": "t", "medium": "water"})


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


# --- ProcessStep.function semantics (ADR-0009) --------------------------------


def test_process_step_engineering_function_is_valid_and_open() -> None:
    # Canonical engineering functions are simple, DeepPlant-native concepts.
    for function in ("pumping", "mixing", "heat_exchange", "splitting_material"):
        step = ProcessStep(id="X", function=function, ports=[ProcessPort(id="p")])
        assert step.function == function
    # The vocabulary is deliberately open: arbitrary non-empty strings stay legal.
    step = ProcessStep(id="X", function="catalytic_upgrading")
    assert step.function == "catalytic_upgrading"
    # "unspecified" is a legal semantic value: the step exists, its engineering
    # function has not yet been specified.
    step = ProcessStep(id="PS-vessel", function="unspecified")
    assert step.function == "unspecified"


def test_process_step_function_is_required() -> None:
    with pytest.raises(ValidationError):
        ProcessStep.model_validate({"id": "A", "ports": []})


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_blank_process_step_function_fails_as_required(blank: str) -> None:
    with pytest.raises(ValidationError):
        ProcessStep(id="A", function=blank)


def test_process_step_function_is_not_a_presentation_field() -> None:
    # A ProcessStep carries only id/function/name/ports; symbol-role and
    # symbol-pack presentation concepts must not enter the canonical model.
    step = ProcessStep(id="A", function="pumping", ports=[ProcessPort(id="out")])
    dumped = step.model_dump()
    assert set(dumped) == {"id", "function", "name", "ports"}


def test_stale_process_step_type_field_is_rejected() -> None:
    # Models use extra="forbid", so legacy `type` YAML/dicts must fail rather
    # than silently acquiring an ambiguous meaning (intentional pre-1.0 break).
    with pytest.raises(ValidationError):
        ProcessStep.model_validate({"id": "A", "type": "pump", "ports": []})
