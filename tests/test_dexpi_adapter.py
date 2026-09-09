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
    DEXPI_CORE_MODEL_URI,
    DEXPI_INSPECTION_DATE,
    DEXPI_LICENCE,
    DEXPI_PROCESS_MODEL_URI,
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
                "function": step.function,
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


def _conformance_root() -> ET.Element:
    return ET.fromstring(_read_fixture("conformance_process.xml"))


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _set_imports(root: ET.Element, imports: list[tuple[str, str]]) -> None:
    """Replace all envelope <Import> elements with (prefix, source) pairs."""
    for child in list(root):
        if _local_name(child.tag) == "Import":
            root.remove(child)
    for prefix, source in imports:
        ET.SubElement(root, "Import", {"prefix": prefix, "source": source})


def _object_by_id(root: ET.Element, object_id: str) -> ET.Element:
    matches = [element for element in root.iter("Object") if element.get("id") == object_id]
    assert len(matches) == 1, f"expected exactly one Object id '{object_id}'"
    return matches[0]


def _add_connector_reference(
    root: ET.Element, port_object_id: str, *referenced_object_ids: str
) -> None:
    """Append one ConnectorReference to a MaterialPort for focused probes."""
    port = _object_by_id(root, port_object_id)
    ET.SubElement(
        port,
        "References",
        {
            "property": "ConnectorReference",
            "objects": " ".join(f"#{object_id}" for object_id in referenced_object_ids),
        },
    )


def _add_data_string(element: ET.Element, property_name: str, value: str = "x") -> None:
    """Append one Data/String property to an element for focused probes."""
    data = ET.SubElement(element, "Data", {"property": property_name})
    ET.SubElement(data, "String").text = value


def _exportable_subset_model() -> ProcessModel:
    """Canonical model over the deliberately symmetric reverse-export subset.

    Since ADR-0009 the canonical model stores engineering functions, and the
    reverse map asserts functions ``source``/``sink``/``mixing``/
    ``splitting_material``/``pumping`` onto their DEXPI classes. Unspecified
    and other functions without an exact DEXPI class stay unexportable.
    """
    steps = [
        ProcessStep(id="A", function="source", ports=[ProcessPort(id="out")]),
        ProcessStep(
            id="B",
            function="mixing",
            ports=[ProcessPort(id="in"), ProcessPort(id="mixed")],
        ),
        ProcessStep(
            id="C",
            function="splitting_material",
            ports=[ProcessPort(id="in"), ProcessPort(id="out_a"), ProcessPort(id="out_b")],
        ),
        ProcessStep(id="D", function="sink", ports=[ProcessPort(id="in")]),
        ProcessStep(id="E", function="sink", ports=[ProcessPort(id="in")]),
    ]
    streams = [
        ProcessStream(
            id="S-1",
            name="Feed",
            source=ProcessRef(step="A", port="out"),
            target=ProcessRef(step="B", port="in"),
        ),
        ProcessStream(
            id="S-2",
            source=ProcessRef(step="B", port="mixed"),
            target=ProcessRef(step="C", port="in"),
        ),
        ProcessStream(
            id="S-3",
            source=ProcessRef(step="C", port="out_a"),
            target=ProcessRef(step="D", port="in"),
        ),
        ProcessStream(
            id="S-4",
            source=ProcessRef(step="C", port="out_b"),
            target=ProcessRef(step="E", port="in"),
        ),
    ]
    return ProcessModel(steps=steps, streams=streams)


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
    assert [step.function for step in model.steps] == [
        "source",
        "mixing",
        "pumping",
        "splitting_material",
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


# --- XML Object@id trust boundary (fix 3/4/21) ---------------------------------


def test_duplicate_port_object_id_fails_before_reference_resolution() -> None:
    # Two different ports share one file-local id and a stream references it.
    text = (
        _read_fixture("conformance_process.xml")
        .replace('id="Port_FEED_out_feed"', 'id="Port_DUP"')
        .replace('id="Port_MIX_in_fresh"', 'id="Port_DUP"')
    )
    with pytest.raises(DexpiImportError) as exc_info:
        import_dexpi_process_xml(text)
    message = str(exc_info.value)
    assert "duplicate DEXPI XML Object id 'Port_DUP'" in message
    assert "globally unique" in message


def test_duplicate_stream_object_id_fails() -> None:
    text = (
        _read_fixture("conformance_process.xml")
        .replace('id="Stream_S001"', 'id="Stream_DUP"')
        .replace('id="Stream_S002"', 'id="Stream_DUP"')
    )
    with pytest.raises(DexpiImportError, match="duplicate DEXPI XML Object id 'Stream_DUP'"):
        import_dexpi_process_xml(text)


def test_duplicate_object_id_across_different_object_kinds_fails() -> None:
    # A ProcessStep and a MaterialPort share the same file-local id. Object@id
    # is a single global file-local reference namespace, unlike canonical
    # engineering Identifiers (step vs stream namespaces in ProcessModel).
    text = (
        _read_fixture("conformance_process.xml")
        .replace('id="Step_FEED"', 'id="Shared_ID"')
        .replace('id="Port_FEED_out_feed"', 'id="Shared_ID"')
    )
    with pytest.raises(DexpiImportError, match="duplicate DEXPI XML Object id 'Shared_ID'"):
        import_dexpi_process_xml(text)


def test_referenced_material_port_without_object_id_fails_clearly() -> None:
    root = _conformance_root()
    _object_by_id(root, "Port_FEED_out_feed").attrib.pop("id")
    with pytest.raises(DexpiImportError, match="Object@id"):
        import_dexpi_process_xml(ET.tostring(root, encoding="unicode"))


def test_referenced_material_port_with_blank_object_id_fails_clearly() -> None:
    root = _conformance_root()
    _object_by_id(root, "Port_FEED_out_feed").set("id", "   ")
    with pytest.raises(DexpiImportError, match="Object@id"):
        import_dexpi_process_xml(ET.tostring(root, encoding="unicode"))


# --- ConnectorReference validation (fix 8/9/10) --------------------------------


def test_connector_reference_absent_remains_tolerated() -> None:
    # The pinned upstream model leaves Port.ConnectorReference multiplicity
    # unresolved, so supported fixtures without a ConnectorReference stay valid.
    model = _import_fixture("conformance_process.xml")
    assert len(model.steps) == 5


def test_valid_connector_reference_to_matching_stream_succeeds() -> None:
    root = _conformance_root()
    # FEED.out is S-001's Source (Outlet); MIX-101.in_fresh is S-001's Target.
    _add_connector_reference(root, "Port_FEED_out_feed", "Stream_S001")
    _add_connector_reference(root, "Port_MIX_in_fresh", "Stream_S001")
    model = import_dexpi_process_xml(ET.tostring(root, encoding="unicode"))
    assert [stream.id for stream in model.streams] == [
        "S-001",
        "S-002",
        "S-003",
        "S-004",
        "S-005",
    ]


def test_unresolved_connector_reference_fails() -> None:
    root = _conformance_root()
    _add_connector_reference(root, "Port_FEED_out_feed", "Port_MISSING")
    with pytest.raises(DexpiImportError) as exc_info:
        import_dexpi_process_xml(ET.tostring(root, encoding="unicode"))
    message = str(exc_info.value)
    assert "ConnectorReference" in message
    assert "#Port_MISSING" in message
    assert "Process/Process.Stream" in message


def test_connector_reference_to_process_step_fails() -> None:
    root = _conformance_root()
    _add_connector_reference(root, "Port_FEED_out_feed", "Step_MIX101")
    with pytest.raises(DexpiImportError) as exc_info:
        import_dexpi_process_xml(ET.tostring(root, encoding="unicode"))
    message = str(exc_info.value)
    assert "Process/Process.Stream" in message
    assert "Process/Process.Mixing" in message


def test_connector_reference_to_material_port_fails() -> None:
    root = _conformance_root()
    _add_connector_reference(root, "Port_FEED_out_feed", "Port_MIX_out_mixed")
    with pytest.raises(DexpiImportError) as exc_info:
        import_dexpi_process_xml(ET.tostring(root, encoding="unicode"))
    message = str(exc_info.value)
    assert "Process/Process.Stream" in message
    assert "MaterialPort" in message


def test_inconsistent_connector_reference_incidence_fails() -> None:
    # FEED.out is an Outlet Source of S-001; declaring a ConnectorReference to
    # S-002 (whose Source is a different port) is inconsistent with incidence.
    root = _conformance_root()
    _add_connector_reference(root, "Port_FEED_out_feed", "Stream_S002")
    with pytest.raises(DexpiImportError) as exc_info:
        import_dexpi_process_xml(ET.tostring(root, encoding="unicode"))
    message = str(exc_info.value)
    assert "inconsistent with stream incidence" in message
    assert "S-002" in message
    assert "Source" in message


def test_malformed_connector_reference_syntax_fails() -> None:
    root = _conformance_root()
    port = _object_by_id(root, "Port_FEED_out_feed")
    ET.SubElement(
        port,
        "References",
        {"property": "ConnectorReference", "objects": "Stream_S001"},
    )
    with pytest.raises(DexpiImportError, match="must start with '#'"):
        import_dexpi_process_xml(ET.tostring(root, encoding="unicode"))


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
        assert set(step) == {"id", "function", "name", "ports"}
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
        assert step.function in {"source", "sink"}

    # A Plant-only file is rejected, never silently converted to an empty model.
    with pytest.raises(DexpiImportError, match="Plant") as exc_info:
        _import_fixture("plant_only.xml")
    assert "out of scope" in str(exc_info.value)


# --- Pinned DEXPI 2.0.0 model import validation (fix 1/2/20) ------------------


def test_pinned_2000_core_and_process_imports_succeed() -> None:
    root = _conformance_root()
    model = import_dexpi_process_xml(ET.tostring(root, encoding="unicode"))
    assert isinstance(model, ProcessModel)


def test_missing_process_import_fails_explicitly() -> None:
    root = _conformance_root()
    _set_imports(root, [("Core", DEXPI_CORE_MODEL_URI)])
    with pytest.raises(DexpiImportError, match="unsupported DEXPI model import") as exc_info:
        import_dexpi_process_xml(ET.tostring(root, encoding="unicode"))
    message = str(exc_info.value)
    assert DEXPI_PROCESS_MODEL_URI in message
    assert "prefix='Process'" in message
    assert "DEXPI 2.0.0" in message


def test_wrong_process_prefix_fails_explicitly() -> None:
    root = _conformance_root()
    _set_imports(
        root,
        [
            ("Core", DEXPI_CORE_MODEL_URI),
            ("Proc", DEXPI_PROCESS_MODEL_URI),
        ],
    )
    with pytest.raises(DexpiImportError, match="unsupported DEXPI model import") as exc_info:
        import_dexpi_process_xml(ET.tostring(root, encoding="unicode"))
    message = str(exc_info.value)
    assert DEXPI_PROCESS_MODEL_URI in message
    assert "prefix='Proc'" in message


def test_wrong_process_version_uri_fails_explicitly() -> None:
    root = _conformance_root()
    _set_imports(
        root,
        [
            ("Core", DEXPI_CORE_MODEL_URI),
            ("Process", "https://data.dexpi.org/models/2.0.1/Process.xml"),
        ],
    )
    with pytest.raises(DexpiImportError, match="unsupported DEXPI model import") as exc_info:
        import_dexpi_process_xml(ET.tostring(root, encoding="unicode"))
    message = str(exc_info.value)
    assert DEXPI_PROCESS_MODEL_URI in message
    assert "2.0.1" in message
    assert "supported target version is DEXPI 2.0.0" in message


def test_duplicate_conflicting_process_imports_fail_explicitly() -> None:
    root = _conformance_root()
    _set_imports(
        root,
        [
            ("Core", DEXPI_CORE_MODEL_URI),
            ("Process", DEXPI_PROCESS_MODEL_URI),
            ("Process", "https://data.dexpi.org/models/2.0.1/Process.xml"),
        ],
    )
    with pytest.raises(DexpiImportError, match="unsupported DEXPI model import") as exc_info:
        import_dexpi_process_xml(ET.tostring(root, encoding="unicode"))
    message = str(exc_info.value)
    assert DEXPI_PROCESS_MODEL_URI in message
    assert "prefix='Process', source=" in message


def test_missing_core_import_fails_explicitly() -> None:
    root = _conformance_root()
    _set_imports(root, [("Process", DEXPI_PROCESS_MODEL_URI)])
    with pytest.raises(DexpiImportError, match="unsupported DEXPI model import") as exc_info:
        import_dexpi_process_xml(ET.tostring(root, encoding="unicode"))
    message = str(exc_info.value)
    assert DEXPI_CORE_MODEL_URI in message
    assert "prefix='Core'" in message


def test_unrelated_plant_import_is_allowed_with_supported_process() -> None:
    root = _conformance_root()
    _set_imports(
        root,
        [
            ("Core", DEXPI_CORE_MODEL_URI),
            ("Plant", "https://data.dexpi.org/models/2.0.0/Plant.xml"),
            ("Process", DEXPI_PROCESS_MODEL_URI),
        ],
    )
    model = import_dexpi_process_xml(ET.tostring(root, encoding="unicode"))
    assert [step.id for step in model.steps] == [
        "FEED",
        "MIX-101",
        "P-101",
        "SPLIT-101",
        "SINK",
    ]


# --- Fail-closed ProcessModel / property parsing (fix 5/6/7/22) ----------------


def test_unknown_process_model_data_property_fails() -> None:
    root = _conformance_root()
    _add_data_string(_object_by_id(root, "ProcessModel1"), "Pressure", "10.0")
    with pytest.raises(DexpiImportError, match="unsupported Data property 'Pressure'"):
        import_dexpi_process_xml(ET.tostring(root, encoding="unicode"))


def test_populated_unsupported_process_model_components_fail() -> None:
    root = _conformance_root()
    model = _object_by_id(root, "ProcessModel1")
    compositions = ET.SubElement(model, "Components", {"property": "Compositions"})
    ET.SubElement(compositions, "Object", {"id": "Comp_1", "type": "Process/Process.Composition"})
    with pytest.raises(DexpiImportError, match="unsupported Components property 'Compositions'"):
        import_dexpi_process_xml(ET.tostring(root, encoding="unicode"))


def test_unexpected_direct_object_child_of_process_model_fails() -> None:
    root = _conformance_root()
    model = _object_by_id(root, "ProcessModel1")
    ET.SubElement(model, "Object", {"type": "Process/Process.SomeStep"})
    with pytest.raises(DexpiImportError, match="unexpected direct <Object> child"):
        import_dexpi_process_xml(ET.tostring(root, encoding="unicode"))


def test_unknown_empty_process_model_wrappers_are_tolerated() -> None:
    root = _conformance_root()
    model = _object_by_id(root, "ProcessModel1")
    ET.SubElement(model, "Components", {"property": "MaterialStates"})
    ET.SubElement(model, "References", {"property": "SomeRole", "objects": ""})
    # Empty wrappers carry no semantics and are documented as tolerated; a
    # populated wrapper of the same name would still be rejected above.
    model_imported = import_dexpi_process_xml(ET.tostring(root, encoding="unicode"))
    assert len(model_imported.steps) == 5


def test_pumping_with_unsupported_head_property_fails() -> None:
    root = _conformance_root()
    _add_data_string(_object_by_id(root, "Step_P101"), "Head", "45.0")
    with pytest.raises(DexpiImportError) as exc_info:
        import_dexpi_process_xml(ET.tostring(root, encoding="unicode"))
    message = str(exc_info.value)
    assert "unsupported Data property 'Head'" in message
    assert "P-101" in message


def test_stream_with_unsupported_property_fails() -> None:
    root = _conformance_root()
    _add_data_string(_object_by_id(root, "Stream_S001"), "Temperature", "80.0")
    with pytest.raises(DexpiImportError, match="unsupported Data property 'Temperature'"):
        import_dexpi_process_xml(ET.tostring(root, encoding="unicode"))


def test_material_port_with_unsupported_property_fails() -> None:
    root = _conformance_root()
    _add_data_string(_object_by_id(root, "Port_FEED_out_feed"), "MassFlow", "12.5")
    with pytest.raises(DexpiImportError, match="unsupported Data property 'MassFlow'"):
        import_dexpi_process_xml(ET.tostring(root, encoding="unicode"))


# --- Export evidence (task tests 17-21) ----------------------------------------


def test_export_is_deterministic() -> None:
    model = _exportable_subset_model()
    exported_once = export_dexpi_process(model)
    exported_twice = export_dexpi_process(model)
    assert exported_once == exported_twice


def test_exported_xml_is_well_formed() -> None:
    model = _exportable_subset_model()
    exported = export_dexpi_process(model)
    root = ET.fromstring(exported)
    assert root.tag == "Model"
    assert root.get("name") == "ProcessModel"


def _identifier_by_xml_object_id(root: ET.Element, object_id: str) -> str | None:
    """Read the Identifier of a unique exported Object for identity assertions."""
    object_element = _object_by_id(root, object_id)
    for data in object_element.findall("Data"):
        if data.get("property") == "Identifier":
            string = data.find("String")
            return string.text if string is not None else None
    return None


def test_export_process_model_xml_id_collision_preserves_engineering_identifier() -> None:
    model = ProcessModel(
        steps=[
            ProcessStep(id="ProcessModel1", function="source", ports=[ProcessPort(id="out")]),
            ProcessStep(id="SINK", function="sink", ports=[ProcessPort(id="in")]),
        ],
        streams=[
            ProcessStream(
                id="S-1",
                source=ProcessRef(step="ProcessModel1", port="out"),
                target=ProcessRef(step="SINK", port="in"),
            )
        ],
    )

    root = ET.fromstring(export_dexpi_process(model))
    object_ids = [element.get("id") for element in root.iter("Object") if element.get("id")]
    assert len(object_ids) == len(set(object_ids))

    source = next(
        element
        for element in root.iter("Object")
        if element.get("type") == "Process/Process.Source"
    )
    assert source.get("id") != "ProcessModel1"
    assert _identifier_by_xml_object_id(root, source.get("id") or "") == "ProcessModel1"


def test_export_resolves_sanitized_xml_id_collisions_without_changing_identifiers() -> None:
    model = ProcessModel(
        steps=[
            ProcessStep(id="A-B", function="source", ports=[ProcessPort(id="out")]),
            ProcessStep(id="A_B", function="source", ports=[ProcessPort(id="out")]),
            ProcessStep(id="SINK-A", function="sink", ports=[ProcessPort(id="in")]),
            ProcessStep(id="SINK_B", function="sink", ports=[ProcessPort(id="in")]),
        ],
        streams=[
            ProcessStream(
                id="S-1",
                source=ProcessRef(step="A-B", port="out"),
                target=ProcessRef(step="SINK-A", port="in"),
            ),
            ProcessStream(
                id="S-2",
                source=ProcessRef(step="A_B", port="out"),
                target=ProcessRef(step="SINK_B", port="in"),
            ),
        ],
    )

    exported = export_dexpi_process(model)
    assert exported == export_dexpi_process(model)
    root = ET.fromstring(exported)
    source_steps = [
        element
        for element in root.iter("Object")
        if element.get("type") == "Process/Process.Source"
    ]
    assert [element.get("id") for element in source_steps] == ["A_B", "A_B_2"]
    assert [
        _identifier_by_xml_object_id(root, element.get("id") or "") for element in source_steps
    ] == [
        "A-B",
        "A_B",
    ]


def test_exported_xml_passes_structural_subset_validation() -> None:
    model = _exportable_subset_model()
    exported = export_dexpi_process(model)
    validate_dexpi_xml_structure(exported)  # must not raise
    assert "Process/ProcessModel" in exported
    assert "Process/Process.MaterialPort" in exported
    assert "Process/Process.Stream" in exported
    assert "Process/Enumerations.PortDirection.Outlet" in exported
    # S-2..S-4 have no name; their ProcessConnection.Label must be Undefined.
    root = ET.fromstring(exported)
    labels = [
        leaf
        for data in root.iter("Data")
        if data.get("property") == "Label"
        for leaf in data
        if leaf.tag.rsplit("}", 1)[-1] == "Undefined"
    ]
    assert len(labels) == 3


def test_semantic_roundtrip_preserves_fingerprint() -> None:
    model = _exportable_subset_model()
    exported = export_dexpi_process(model)
    reimported = import_dexpi_process_xml(exported)
    assert semantic_fingerprint(model) == semantic_fingerprint(reimported)


def test_material_only_pumping_reverse_exports_and_round_trips() -> None:
    # ADR-0009: canonical function="pumping" is an engineering classification,
    # so the reverse map may assert "pumping -> Process/Process.Pumping" for a
    # material-port-only pumping step (no driver energy port, no Head/Method/
    # VolumeFlow invented). The conformance fixture's P-101 is exactly such a
    # step, so a full import -> export -> import semantic round trip is the
    # executable evidence.
    imported = _import_fixture("conformance_process.xml")
    pump = next(step for step in imported.steps if step.function == "pumping")
    assert pump.id == "P-101"

    exported = export_dexpi_process(imported)
    assert "Process/Process.Pumping" in exported

    reimported = import_dexpi_process_xml(exported)
    assert semantic_fingerprint(imported) == semantic_fingerprint(reimported)
    re_pump = next(step for step in reimported.steps if step.id == "P-101")
    assert re_pump.function == "pumping"


def test_export_of_unsupported_functions_fails_explicitly() -> None:
    base = _exportable_subset_model()
    # heat_exchange has no exact DEXPI class in this slice (DEXPI
    # ExchangingThermalEnergy couples flows canonical cannot express), and
    # unspecified is honest semantic uncertainty; neither may be forced.
    for unsupported_function in ("heat_exchange", "unspecified"):
        model = ProcessModel(
            steps=[
                *base.steps,
                ProcessStep(
                    id="EXTRA",
                    function=unsupported_function,
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
        with pytest.raises(
            DexpiExportError, match="unsupported canonical ProcessStep function"
        ) as exc:
            export_dexpi_process(model)
        assert unsupported_function in str(exc.value)


def test_export_rejects_port_without_incident_stream() -> None:
    model = ProcessModel(
        steps=[
            ProcessStep(
                id="A",
                function="source",
                ports=[ProcessPort(id="out"), ProcessPort(id="unused")],
            ),
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
    with pytest.raises(DexpiExportError, match="no incident ProcessStream"):
        export_dexpi_process(model)


def test_export_rejects_bidirectional_port() -> None:
    model = ProcessModel(
        steps=[
            ProcessStep(
                id="A",
                function="source",
                ports=[ProcessPort(id="loop")],
            ),
            ProcessStep(id="B", function="sink", ports=[ProcessPort(id="in")]),
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
