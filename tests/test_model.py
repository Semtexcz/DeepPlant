import pytest
from pydantic import ValidationError

from deepplant.model import Equipment, Plant, PlantModel


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
