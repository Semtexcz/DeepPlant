import pytest
from pydantic import ValidationError

from deepplant.model import Connection, Equipment, Plant, PlantModel, Port, PortRef


def test_valid_model_from_objects() -> None:
    model = PlantModel(
        plant=Plant(id="demo", name="Minimal Process"),
        equipment=[
            Equipment(id="T-101", type="tank", name="Feed Tank"),
            Equipment(id="P-101", type="pump", name="Feed Pump"),
        ],
    )

    assert model.plant.id == "demo"
    assert model.plant.name == "Minimal Process"


def test_multiple_equipment_items() -> None:
    model = PlantModel(
        plant=Plant(id="demo"),
        equipment=[
            Equipment(id="T-101", type="tank"),
            Equipment(id="P-101", type="pump"),
            Equipment(id="H-101", type="heat-exchanger"),
        ],
    )

    assert len(model.equipment) == 3
    assert [item.id for item in model.equipment] == ["T-101", "P-101", "H-101"]


def test_equipment_list_may_be_empty() -> None:
    model = PlantModel(plant=Plant(id="demo"))

    assert model.equipment == []


def test_optional_names_default_to_none() -> None:
    model = PlantModel(plant=Plant(id="demo"), equipment=[Equipment(id="T-101", type="tank")])

    assert model.plant.name is None
    assert model.equipment[0].name is None


def test_missing_required_fields_fail() -> None:
    with pytest.raises(ValidationError):
        PlantModel.model_validate({})


def test_empty_plant_id_fails() -> None:
    with pytest.raises(ValidationError):
        PlantModel(plant=Plant(id=""), equipment=[])


def test_missing_plant_id_fails() -> None:
    with pytest.raises(ValidationError):
        PlantModel.model_validate({"plant": {"name": "No id"}, "equipment": []})


def test_empty_equipment_id_fails() -> None:
    with pytest.raises(ValidationError):
        PlantModel(
            plant=Plant(id="demo"),
            equipment=[Equipment(id="", type="tank")],
        )


def test_missing_equipment_id_fails() -> None:
    with pytest.raises(ValidationError):
        PlantModel.model_validate(
            {
                "plant": {"id": "demo"},
                "equipment": [{"type": "tank"}],
            }
        )


def test_duplicate_equipment_ids_fail() -> None:
    with pytest.raises(ValidationError, match="duplicate equipment id"):
        PlantModel(
            plant=Plant(id="demo"),
            equipment=[
                Equipment(id="T-101", type="tank"),
                Equipment(id="T-101", type="pump"),
            ],
        )


def test_unknown_top_level_field_fails() -> None:
    with pytest.raises(ValidationError):
        PlantModel.model_validate(
            {
                "plant": {"id": "demo"},
                "equipment": [],
                "equipmnt": [],
            }
        )


def test_unknown_plant_field_fails() -> None:
    with pytest.raises(ValidationError):
        PlantModel.model_validate(
            {
                "plant": {"id": "demo", "unknown_field": "value"},
                "equipment": [],
            }
        )


def test_unknown_equipment_field_fails() -> None:
    with pytest.raises(ValidationError):
        PlantModel.model_validate(
            {
                "plant": {"id": "demo"},
                "equipment": [{"id": "P-101", "type": "pump", "nam": "Feed Pump"}],
            }
        )


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_blank_plant_id_fails(blank: str) -> None:
    with pytest.raises(ValidationError):
        PlantModel(plant=Plant(id=blank), equipment=[])


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_blank_equipment_id_fails(blank: str) -> None:
    with pytest.raises(ValidationError):
        PlantModel(
            plant=Plant(id="demo"),
            equipment=[Equipment(id=blank, type="tank")],
        )


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_blank_equipment_type_fails(blank: str) -> None:
    with pytest.raises(ValidationError):
        PlantModel(
            plant=Plant(id="demo"),
            equipment=[Equipment(id="P-101", type=blank)],
        )


def test_semantic_strings_are_stripped() -> None:
    model = PlantModel(
        plant=Plant(id="  demo  "),
        equipment=[Equipment(id="  P-101  ", type="  pump  ")],
    )

    assert model.plant.id == "demo"
    assert model.equipment[0].id == "P-101"
    assert model.equipment[0].type == "pump"


def test_valid_ports_load_and_connection_resolves() -> None:
    model = PlantModel(
        plant=Plant(id="demo", name="Minimal Process"),
        equipment=[
            Equipment(id="T-101", type="tank", ports=[Port(id="outlet")]),
            Equipment(id="P-101", type="pump", ports=[Port(id="suction"), Port(id="discharge")]),
        ],
        connections=[
            Connection(
                source=PortRef(component="T-101", port="outlet"),
                target=PortRef(component="P-101", port="suction"),
            )
        ],
    )

    assert [port.id for port in model.equipment[0].ports] == ["outlet"]
    assert [port.id for port in model.equipment[1].ports] == ["suction", "discharge"]
    assert len(model.connections) == 1
    connection = model.connections[0]
    assert (connection.source.component, connection.source.port) == ("T-101", "outlet")
    assert (connection.target.component, connection.target.port) == ("P-101", "suction")


def test_equipment_defaults_to_no_ports_and_model_to_no_connections() -> None:
    model = PlantModel(plant=Plant(id="demo"), equipment=[Equipment(id="T-101", type="tank")])

    assert model.equipment[0].ports == []
    assert model.connections == []


def test_same_port_id_on_different_equipment_is_allowed() -> None:
    model = PlantModel(
        plant=Plant(id="demo"),
        equipment=[
            Equipment(id="T-101", type="tank", ports=[Port(id="outlet")]),
            Equipment(id="T-102", type="tank", ports=[Port(id="outlet")]),
        ],
    )

    assert [port.id for port in model.equipment[0].ports] == ["outlet"]
    assert [port.id for port in model.equipment[1].ports] == ["outlet"]


def test_duplicate_port_ids_on_same_equipment_fail() -> None:
    with pytest.raises(ValidationError, match="duplicate port id"):
        Equipment(
            id="T-101",
            type="tank",
            ports=[Port(id="outlet"), Port(id="outlet")],
        )


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_blank_port_id_fails(blank: str) -> None:
    with pytest.raises(ValidationError):
        Equipment(id="T-101", type="tank", ports=[Port(id=blank)])


def test_unknown_port_field_fails() -> None:
    with pytest.raises(ValidationError):
        Port.model_validate({"id": "outlet", "nozzle": "N1"})


def test_unknown_port_ref_field_fails() -> None:
    with pytest.raises(ValidationError):
        PortRef.model_validate({"component": "T-101", "port": "outlet", "direction": "out"})


def test_unknown_connection_field_fails() -> None:
    with pytest.raises(ValidationError):
        Connection.model_validate(
            {
                "source": {"component": "T-101", "port": "outlet"},
                "target": {"component": "P-101", "port": "suction"},
                "medium": "water",
            }
        )


def test_connection_source_with_unknown_component_fails() -> None:
    with pytest.raises(
        ValidationError, match="connections\\[0\\].source: unknown component 'X-999'"
    ):
        PlantModel.model_validate(
            {
                "plant": {"id": "demo"},
                "equipment": [{"id": "T-101", "type": "tank", "ports": [{"id": "outlet"}]}],
                "connections": [
                    {
                        "source": {"component": "X-999", "port": "outlet"},
                        "target": {"component": "T-101", "port": "outlet"},
                    }
                ],
            }
        )


def test_connection_target_with_unknown_component_fails() -> None:
    with pytest.raises(
        ValidationError, match="connections\\[0\\].target: unknown component 'X-999'"
    ):
        PlantModel.model_validate(
            {
                "plant": {"id": "demo"},
                "equipment": [{"id": "T-101", "type": "tank", "ports": [{"id": "outlet"}]}],
                "connections": [
                    {
                        "source": {"component": "T-101", "port": "outlet"},
                        "target": {"component": "X-999", "port": "outlet"},
                    }
                ],
            }
        )


def test_connection_source_with_unknown_port_fails() -> None:
    with pytest.raises(ValidationError, match="component 'T-101' has no port 'missing'"):
        PlantModel.model_validate(
            {
                "plant": {"id": "demo"},
                "equipment": [{"id": "T-101", "type": "tank", "ports": [{"id": "outlet"}]}],
                "connections": [
                    {
                        "source": {"component": "T-101", "port": "missing"},
                        "target": {"component": "T-101", "port": "outlet"},
                    }
                ],
            }
        )


def test_connection_target_with_unknown_port_fails() -> None:
    with pytest.raises(ValidationError, match="component 'T-101' has no port 'missing'"):
        PlantModel.model_validate(
            {
                "plant": {"id": "demo"},
                "equipment": [{"id": "T-101", "type": "tank", "ports": [{"id": "outlet"}]}],
                "connections": [
                    {
                        "source": {"component": "T-101", "port": "outlet"},
                        "target": {"component": "T-101", "port": "missing"},
                    }
                ],
            }
        )
