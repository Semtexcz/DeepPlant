from pathlib import Path

import pytest

from deepplant import load_plant
from deepplant.io import PlantLoadError
from deepplant.model import Equipment, Plant, PlantModel

EXAMPLE = Path(__file__).parents[1] / "examples" / "minimal-process" / "plant.yaml"


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
