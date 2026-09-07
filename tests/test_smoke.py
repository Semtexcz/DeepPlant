from deepplant import Connection, Port, PortRef, __version__


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
