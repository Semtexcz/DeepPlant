# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""DEXPI 2.x Process adapter spike tests.

These tests are the executable evidence for
``docs/dexpi-process-spike.md``. They run fully offline against committed
fixtures whose provenance is recorded in
``tests/fixtures/dexpi/2.0.0/ATTRIBUTION.md``. Assertions are semantic
(canonical ``ProcessModel`` content), not XML-layout-based.
"""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from deepplant.adapters.dexpi import (
    DEXPI_INSPECTION_DATE,
    DEXPI_LICENCE,
    DEXPI_SOURCE_URL,
    DEXPI_TARGET_REVISION,
    DEXPI_TARGET_TAG,
    DEXPI_TARGET_VERSION,
    DexpiExportError,
    DexpiImportError,
    export_dexpi_process,
    import_dexpi_process,
    import_dexpi_process_xml,
    validate_dexpi_xml_structure,
)
from deepplant.model import ProcessModel, ProcessPort, ProcessRef, ProcessStep, ProcessStream
from deepplant.render import render_process_svg

FIXTURES = Path(__file__).parent / "fixtures" / "dexpi" / "2.0.0"
FIXTURE_FILES = sorted(path.name for path in FIXTURES.glob("*.xml"))


def _read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _import_fixture(name: str) -> ProcessModel:
    return import_dexpi_process(FIXTURES / name)


def semantic_fingerprint(model: ProcessModel) -> dict[str, object]:
    """Normalized semantic fingerprint of what DeepPlant owns (task §24)."""
    return {
        "steps": [
            {
                "id": step.id,
                "type": step.type,
                "name": step.name,
                "ports": [port.id for port in step.ports],
            }
            for step in model.steps
        ],
        "streams": [
            {
                "id": stream.id,
                "name": stream.name,
                "source": (stream.source.step, stream.source.port),
                "target": (stream.target.step, stream.target.port),
            }
            for stream in model.streams
        ],
    }


# --- Target pinning and provenance (task tests 1, 2, 30) ----------------------


def test_official_target_version_is_pinned() -> None:
    assert DEXPI_TARGET_TAG == "V2.0.0"
    assert DEXPI_TARGET_VERSION == "2.0.0"
    assert DEXPI_TARGET_REVISION == "260c81c51039789a6148a98af4c6caf23f87a3e2"
    assert DEXPI_LICENCE == "CC BY 4.0"
    assert DEXPI_SOURCE_URL == "https://gitlab.com/dexpi/Specification"
    assert DEXPI_INSPECTION_DATE == "2026-09-09"

    spike_doc = (Path(__file__).resolve().parents[1] / "docs" / "dexpi-process-spike.md").read_text(
        encoding="utf-8"
    )
    assert "V2.0.0" in spike_doc
    assert DEXPI_TARGET_REVISION in spike_doc
    assert DEXPI_SOURCE_URL in spike_doc
    assert DEXPI_INSPECTION_DATE in spike_doc


def test_fixture_provenance_is_recorded() -> None:
    attribution = (FIXTURES / "ATTRIBUTION.md").read_text(encoding="utf-8")
    for required in (
        "CC BY 4.0",
        "V2.0.0",
        DEXPI_TARGET_REVISION,
        "https://gitlab.com/dexpi/Specification",
        "260c81c5",
        "2026-09-09",
    ):
        assert required in attribution
    for fixture_file in FIXTURE_FILES:
        assert f"`{fixture_file}`" in attribution


# --- Import evidence (task tests 3-10) -----------------------------------------


def test_conformance_fixture_parses() -> None:
    model = _import_fixture("conformance_process.xml")
    assert isinstance(model, ProcessModel)


def test_expected_process_steps_import() -> None:
    model = _import_fixture("conformance_process.xml")
    assert [step.id for step in model.steps] == [
        "FEED",
        "MIX-101",
        "P-101",
        "SPLIT-101",
        "SINK",
    ]
    assert [step.type for step in model.steps] == [
        "source",
        "mixing",
        "pump",
        "splitting",
        "sink",
    ]
    assert [step.name for step in model.steps] == [
        "Fresh Feed Boundary",
        "Mixing of Fresh Feed and Recycle",
        "Feed Pumping",
        "Splitting to Recycle and Product",
        "Downstream Consumer Boundary",
    ]


def test_process_step_owned_ports_import() -> None:
    model = _import_fixture("conformance_process.xml")
    expected_ports = {
        "FEED": ["out_feed"],
        "MIX-101": ["in_fresh", "in_recycle", "out_mixed"],
        "P-101": ["suction", "discharge"],
        "SPLIT-101": ["in", "out_recycle", "out_product"],
        "SINK": ["in"],
    }
    assert {step.id: [port.id for port in step.ports] for step in model.steps} == expected_ports


def test_material_streams_import() -> None:
    model = _import_fixture("conformance_process.xml")
    assert [stream.id for stream in model.streams] == [
        "S-001",
        "S-002",
        "S-003",
        "S-004",
        "S-005",
    ]
    assert [stream.name for stream in model.streams] == [
        "Fresh Feed",
        "Mixed Feed",
        None,
        "Recycle",
        "Product",
    ]


def test_source_target_references_resolve() -> None:
    model = _import_fixture("conformance_process.xml")
    by_id = {stream.id: stream for stream in model.streams}
    assert (by_id["S-001"].source.step, by_id["S-001"].source.port) == ("FEED", "out_feed")
    assert (by_id["S-001"].target.step, by_id["S-001"].target.port) == ("MIX-101", "in_fresh")
    # The recycle cycle and the mixing/splitting branch are preserved.
    assert (by_id["S-004"].source.step, by_id["S-004"].source.port) == (
        "SPLIT-101",
        "out_recycle",
    )
    assert (by_id["S-004"].target.step, by_id["S-004"].target.port) == ("MIX-101", "in_recycle")
    assert (by_id["S-005"].target.step, by_id["S-005"].target.port) == ("SINK", "in")


def test_imported_model_passes_canonical_validation() -> None:
    model = _import_fixture("conformance_process.xml")
    # Re-validating the serialized model exercises the normal S1-S4 invariants.
    ProcessModel.model_validate(model.model_dump())


def test_identifiers_map_from_engineering_identifier_not_xml_object_id() -> None:
    model = _import_fixture("conformance_process.xml")
    # XML object ids are Step_FEED/Port_FEED_out_feed/Stream_S001 in the fixture;
    # canonical ids come from the engineering Identifier data, never the object id.
    assert {step.id for step in model.steps} == {
        "FEED",
        "MIX-101",
        "P-101",
        "SPLIT-101",
        "SINK",
    }
    feed = next(step for step in model.steps if step.id == "FEED")
    assert feed.ports[0].id == "out_feed"
    assert {stream.id for stream in model.streams} == {"S-001", "S-002", "S-003", "S-004", "S-005"}


def test_repeated_import_produces_equal_models() -> None:
    first = _import_fixture("conformance_process.xml")
    second = _import_fixture("conformance_process.xml")
    assert first == second
    assert semantic_fingerprint(first) == semantic_fingerprint(second)


# --- Unsupported concepts must fail visibly (task tests 11-16) -----------------


def test_energy_flows_are_not_imported_as_process_streams() -> None:
    with pytest.raises(DexpiImportError) as exc_info:
        _import_fixture("energy_flows.xml")
    message = str(exc_info.value)
    assert "unsupported DEXPI connection class" in message
    assert "Process/Process.EnergyFlow" in message
    assert "ThermalEnergyFlow" in message or "E-001" in message


def test_information_flow_is_not_imported_as_process_stream() -> None:
    with pytest.raises(DexpiImportError, match="Process/Process.InformationFlow"):
        _import_fixture("information_flow.xml")


def test_non_material_ports_are_not_imported() -> None:
    with pytest.raises(DexpiImportError, match="ThermalEnergyPort"):
        _import_fixture("non_material_ports.xml")


def test_unresolved_references_fail_clearly() -> None:
    with pytest.raises(DexpiImportError, match="#Port_MISSING") as exc_info:
        _import_fixture("unresolved_reference.xml")
    message = str(exc_info.value)
    assert "Target" in message
    assert "S-001" in message


def test_unsupported_process_step_class_fails_clearly() -> None:
    with pytest.raises(DexpiImportError) as exc_info:
        _import_fixture("unsupported_process_step.xml")
    message = str(exc_info.value)
    assert "unsupported DEXPI ProcessStep class" in message
    assert "ReactingChemicals" in message
    assert "R-101" in message


def test_duplicate_imported_canonical_id_fails_clearly() -> None:
    with pytest.raises(DexpiImportError, match="duplicate imported canonical ProcessStep id"):
        _import_fixture("duplicate_identifier.xml")


def test_direction_contradiction_fails_clearly() -> None:
    root = ET.fromstring(_read_fixture("conformance_process.xml"))
    objects = {element.get("id"): element for element in root.iter("Object")}
    port = objects["Port_FEED_out_feed"]
    for data in port.iter("Data"):
        if data.get("property") == "NominalDirection":
            for reference in data.iter("DataReference"):
                reference.set("data", "Process/Enumerations.PortDirection.Inlet")
    # Flip the declared direction of the source port of S-001 to Inlet so the
    # DEXPI NominalDirection contradicts stream incidence. DeepPlant derives
    # direction from incidence and must reject the contradiction, not store it.
    with pytest.raises(DexpiImportError, match="declares NominalDirection other than Outlet"):
        import_dexpi_process_xml(ET.tostring(root, encoding="unicode"))


def test_no_presentation_data_enters_the_semantic_model() -> None:
    model = _import_fixture("conformance_process.xml")
    dump = model.model_dump()
    for step in dump["steps"]:
        assert set(step) == {"id", "type", "name", "ports"}
        for port in step["ports"]:
            assert set(port) == {"id"}
    for stream in dump["streams"]:
        assert set(stream) == {"id", "name", "source", "target"}
    # The fixture carries a DEXPI Description on FEED; it must not leak into the
    # canonical model (documented annotation-metadata loss).
    assert all("description" not in step for step in dump["steps"])


def test_plant_objects_are_not_imported_and_plant_only_files_fail() -> None:
    # A mixed file with a Plant stub plus a ProcessModel imports only the process.
    mixed = _import_fixture("mixed_plant_and_process.xml")
    assert [step.id for step in mixed.steps] == ["FEED", "SINK"]
    assert {stream.id for stream in mixed.streams} == {"S-001"}
    for step in mixed.steps:
        assert step.type in {"source", "sink"}

    # A Plant-only file is rejected, never silently converted to an empty model.
    with pytest.raises(DexpiImportError, match="Plant") as exc_info:
        _import_fixture("plant_only.xml")
    assert "out of scope" in str(exc_info.value)


# --- Export evidence (task tests 17-21) ----------------------------------------


def test_export_is_deterministic() -> None:
    model = _import_fixture("conformance_process.xml")
    exported_once = export_dexpi_process(model)
    exported_twice = export_dexpi_process(model)
    assert exported_once == exported_twice


def test_exported_xml_is_well_formed() -> None:
    model = _import_fixture("conformance_process.xml")
    exported = export_dexpi_process(model)
    root = ET.fromstring(exported)
    assert root.tag == "Model"
    assert root.get("name") == "ProcessModel"


def test_exported_xml_passes_structural_subset_validation() -> None:
    model = _import_fixture("conformance_process.xml")
    exported = export_dexpi_process(model)
    validate_dexpi_xml_structure(exported)  # must not raise
    assert "Process/ProcessModel" in exported
    assert "Process/Process.MaterialPort" in exported
    assert "Process/Process.Stream" in exported
    assert "Process/Enumerations.PortDirection.Outlet" in exported
    # S-003 has no name; its ProcessConnection.Label must be an explicit Undefined.
    root = ET.fromstring(exported)
    labels = [
        leaf
        for data in root.iter("Data")
        if data.get("property") == "Label"
        for leaf in data
        if leaf.tag.rsplit("}", 1)[-1] == "Undefined"
    ]
    assert len(labels) == 1


def test_semantic_roundtrip_preserves_fingerprint() -> None:
    model = _import_fixture("conformance_process.xml")
    exported = export_dexpi_process(model)
    reimported = import_dexpi_process_xml(exported)
    assert semantic_fingerprint(model) == semantic_fingerprint(reimported)


def test_export_of_unsupported_step_types_fails_explicitly() -> None:
    base = _import_fixture("conformance_process.xml")
    for unsupported_type in ("heat_exchanger", "vessel"):
        model = ProcessModel(
            steps=[
                *base.steps,
                ProcessStep(
                    id="EXTRA",
                    type=unsupported_type,
                    ports=[ProcessPort(id="in"), ProcessPort(id="out")],
                ),
            ],
            streams=[
                *base.streams,
                ProcessStream(
                    id="S-EXTRA",
                    source=ProcessRef(step="EXTRA", port="out"),
                    target=ProcessRef(step="EXTRA", port="in"),
                ),
            ],
        )
        with pytest.raises(DexpiExportError, match="unsupported canonical ProcessStep type") as exc:
            export_dexpi_process(model)
        assert unsupported_type in str(exc.value)


def test_export_rejects_port_without_incident_stream() -> None:
    model = ProcessModel(
        steps=[
            ProcessStep(
                id="A",
                type="source",
                ports=[ProcessPort(id="out"), ProcessPort(id="unused")],
            ),
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
    with pytest.raises(DexpiExportError, match="no incident ProcessStream"):
        export_dexpi_process(model)


def test_export_rejects_bidirectional_port() -> None:
    model = ProcessModel(
        steps=[
            ProcessStep(
                id="A",
                type="source",
                ports=[ProcessPort(id="loop")],
            ),
            ProcessStep(id="B", type="sink", ports=[ProcessPort(id="in")]),
        ],
        streams=[
            ProcessStream(
                id="S-1",
                source=ProcessRef(step="A", port="loop"),
                target=ProcessRef(step="B", port="in"),
            ),
            ProcessStream(
                id="S-2",
                source=ProcessRef(step="B", port="in"),
                target=ProcessRef(step="A", port="loop"),
            ),
        ],
    )
    with pytest.raises(DexpiExportError, match="both a stream source and target"):
        export_dexpi_process(model)


# --- Optional end-to-end renderer evidence (not an adapter requirement) --------


def test_imported_conformance_fixture_renders_to_svg() -> None:
    model = _import_fixture("conformance_process.xml")
    svg = render_process_svg(model)
    root = ET.fromstring(svg)
    assert root.tag == "{http://www.w3.org/2000/svg}svg"
