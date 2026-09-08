from deepplant import (
    Connection,
    Port,
    PortRef,
    ProcessModel,
    ProcessPort,
    ProcessRef,
    ProcessStep,
    ProcessStream,
    __version__,
)


def test_version() -> None:
    assert __version__ == "0.1.0"


def test_public_api_exposes_ports_and_connections() -> None:
    connection = Connection(
        source=PortRef(component="T-101", port="outlet"),
        target=PortRef(component="P-101", port="suction"),
    )

    assert Port(id="outlet").id == "outlet"
    assert connection.source.component == "T-101"
    assert connection.target.port == "suction"


def test_public_api_exposes_process_models() -> None:
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

    assert isinstance(model, ProcessModel)
    assert model.steps[1].ports[0].id == "in"
    assert model.streams[0].source.step == "A"
