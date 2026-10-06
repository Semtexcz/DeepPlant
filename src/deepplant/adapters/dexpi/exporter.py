# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Serialize a `ProcessModel` to deterministic DEXPI-native XML.

Only the supported reverse-mapped subset is exported; an engineering function
without an exact DEXPI class in this slice raises `DexpiExportError` instead of
producing XML that invents engineering meaning. Generated XML `Object@id`
values are serialization mechanics excluded from semantic round-trip
comparison (ADR-0009, ADR-0012).
"""

from __future__ import annotations

import re
from xml.etree import ElementTree as ET

from deepplant.adapters.dexpi.mapping import (
    ENUM_PREFIX,
    MATERIAL_PORT_TYPE,
    MODEL_TYPE,
    REVERSE_STEP_TYPE_MAP,
    STREAM_TYPE,
    ObjectIdKey,
)
from deepplant.adapters.dexpi.target import (
    DEXPI_CORE_MODEL_URI,
    DEXPI_PROCESS_MODEL_URI,
    MODEL_NAME_PATTERN,
    DexpiExportError,
)
from deepplant.adapters.dexpi.xml import collect_object_ids, local
from deepplant.model import ProcessModel, ProcessStep, ProcessStream

# --- Export --------------------------------------------------------------------


def export_dexpi_process(
    process: ProcessModel,
    *,
    model_name: str = "ProcessModel",
    model_uri: str = "https://example.org/deepplant/process-model",
) -> str:
    """Serialize a ``ProcessModel`` to deterministic DEXPI-native XML.

    Only the supported subset is exported
    (see ``docs/dev/research/dexpi/process-adapter-spike.md``);
    ``ProcessStep.function`` values outside the explicit reverse mapping table
    raise :class:`DexpiExportError` instead of producing XML that invents
    engineering meaning. ``model_name`` / ``model_uri`` are the exchange-file
    envelope values (serialization mechanics only).

    Nominal directions on exported material ports are derived from
    ``ProcessStream`` incidence (DEXPI ``PortDirection`` is exactly
    Inlet/Outlet). A port with no incident stream, or with both an incident
    source and an incident target, cannot be exported without inventing or
    contradicting DEXPI direction semantics and raises.
    """
    if not MODEL_NAME_PATTERN.fullmatch(model_name or ""):
        raise DexpiExportError(
            f"model_name must match the DEXPI XML 'name' pattern "
            f"([A-Za-z_][A-Za-z_0-9]*), got {model_name!r}"
        )

    directions = _incidence_directions(process)
    object_ids = _deterministic_object_ids(process)

    root = ET.Element("Model", {"name": model_name, "uri": model_uri})
    ET.SubElement(
        root,
        "Import",
        {"prefix": "Core", "source": DEXPI_CORE_MODEL_URI},
    )
    ET.SubElement(
        root,
        "Import",
        {"prefix": "Process", "source": DEXPI_PROCESS_MODEL_URI},
    )
    engineering_model = ET.SubElement(root, "Object", {"type": "Core/EngineeringModel"})
    conceptual_model = ET.SubElement(
        ET.SubElement(engineering_model, "Components", {"property": "ConceptualModel"}),
        "Object",
        {"id": object_ids[("model", "ProcessModel")], "type": MODEL_TYPE},
    )

    steps_container = ET.SubElement(conceptual_model, "Components", {"property": "ProcessSteps"})
    for step in process.steps:
        _append_step(step, steps_container, directions, object_ids)

    connections_container = ET.SubElement(
        conceptual_model, "Components", {"property": "ProcessConnections"}
    )
    for stream in process.streams:
        _append_stream(stream, connections_container, object_ids)

    ET.indent(root, space="  ")
    xml_text = ET.tostring(root, encoding="unicode", xml_declaration=False)
    validate_dexpi_xml_structure(xml_text)
    return xml_text


def _incidence_directions(process: ProcessModel) -> dict[tuple[str, str], str]:
    """Derive DEXPI Inlet/Outlet per canonical (step, port) from stream incidence."""
    directions: dict[tuple[str, str], str] = {}
    for stream in process.streams:
        source = (stream.source.step, stream.source.port)
        target = (stream.target.step, stream.target.port)
        if source in directions and directions[source] != "Outlet":
            raise DexpiExportError(
                f"ProcessStream '{stream.id}': port '{source[0]}.{source[1]}' is "
                "both a stream source and target; DEXPI PortDirection has no InOut "
                "value, so DeepPlant incidence cannot be exported without inventing "
                "semantics"
            )
        directions[source] = "Outlet"
        if target in directions and directions[target] != "Inlet":
            raise DexpiExportError(
                f"ProcessStream '{stream.id}': port '{target[0]}.{target[1]}' is "
                "both a stream source and target; DEXPI PortDirection has no InOut "
                "value, so DeepPlant incidence cannot be exported without inventing "
                "semantics"
            )
        directions[target] = "Inlet"
    return directions


def _deterministic_object_ids(
    process: ProcessModel,
) -> dict[ObjectIdKey, str]:
    """Assign deterministic DEXPI XML ``id`` attributes (serialization mechanics).

    The ProcessModel envelope key ``("model", "ProcessModel")`` is allocated
    first in the same namespace as ``("step", step_id)``,
    ``("port", step_id, port_id)`` and ``("stream", stream_id)``. Generated
    ids only need to be stable, unique and valid DEXPI ``name``/``ID`` tokens;
    they are explicitly excluded from semantic round-trip comparison (see
    ``docs/dev/research/dexpi/process-adapter-spike.md``).
    """
    assigned: dict[ObjectIdKey, str] = {}
    used: set[str] = set()

    def allocate(kind: str, base: str) -> str:
        sanitized = re.sub(r"[^A-Za-z0-9_]", "_", base)
        if not sanitized or sanitized[0].isdigit():
            sanitized = f"{kind}_{sanitized}"
        candidate = sanitized
        counter = 2
        while candidate in used:
            candidate = f"{sanitized}_{counter}"
            counter += 1
        used.add(candidate)
        return candidate

    assigned[("model", "ProcessModel")] = allocate("ProcessModel", "ProcessModel1")
    for step in process.steps:
        assigned[("step", step.id)] = allocate("Step", step.id)
        for port in step.ports:
            assigned[("port", step.id, port.id)] = allocate("Port", f"{step.id}_{port.id}")
    for stream in process.streams:
        assigned[("stream", stream.id)] = allocate("Stream", stream.id)
    return assigned


def _append_step(
    step: ProcessStep,
    container: ET.Element,
    directions: dict[tuple[str, str], str],
    object_ids: dict[ObjectIdKey, str],
) -> None:
    dexpi_type = REVERSE_STEP_TYPE_MAP.get(step.function)
    if dexpi_type is None:
        raise DexpiExportError(
            f"unsupported canonical ProcessStep function '{step.function}' on step "
            f"'{step.id}': this adapter slice can only export "
            + ", ".join(sorted(REVERSE_STEP_TYPE_MAP))
            + "; DeepPlant has no exact DEXPI engineering class for other functions "
            "(e.g. heat_exchange, unspecified) in this slice"
        )
    where = f"ProcessStep '{step.id}'"
    step_element = ET.SubElement(
        container,
        "Object",
        {"id": object_ids[("step", step.id)], "type": dexpi_type},
    )
    _append_data_string(step_element, "Identifier", step.id)
    if step.name is not None:
        _append_data_string(step_element, "Label", step.name)

    ports_container = ET.SubElement(step_element, "Components", {"property": "Ports"})
    for port in step.ports:
        direction = directions.get((step.id, port.id))
        if direction is None:
            raise DexpiExportError(
                f"{where}: port '{port.id}' has no incident ProcessStream; DEXPI "
                "requires a NominalDirection on every Port and DeepPlant does not "
                "store one, so the direction cannot be derived without inventing it"
            )
        port_element = ET.SubElement(
            ports_container,
            "Object",
            {
                "id": object_ids[("port", step.id, port.id)],
                "type": MATERIAL_PORT_TYPE,
            },
        )
        _append_data_string(port_element, "Identifier", port.id)
        ET.SubElement(
            ET.SubElement(port_element, "Data", {"property": "NominalDirection"}),
            "DataReference",
            {"data": f"{ENUM_PREFIX}{direction}"},
        )


def _append_stream(
    stream: ProcessStream,
    container: ET.Element,
    object_ids: dict[ObjectIdKey, str],
) -> None:
    stream_element = ET.SubElement(
        container,
        "Object",
        {"id": object_ids[("stream", stream.id)], "type": STREAM_TYPE},
    )
    _append_data_string(stream_element, "Identifier", stream.id)
    if stream.name is None:
        ET.SubElement(ET.SubElement(stream_element, "Data", {"property": "Label"}), "Undefined")
    else:
        _append_data_string(stream_element, "Label", stream.name)
    source_id = object_ids[("port", stream.source.step, stream.source.port)]
    target_id = object_ids[("port", stream.target.step, stream.target.port)]
    ET.SubElement(
        stream_element,
        "References",
        {"objects": f"#{source_id}", "property": "Source"},
    )
    ET.SubElement(
        stream_element,
        "References",
        {"objects": f"#{target_id}", "property": "Target"},
    )


def _append_data_string(object_element: ET.Element, property_name: str, value: str) -> None:
    """Emit a single ``Data property`` with one ``String`` leaf."""
    data = ET.SubElement(object_element, "Data", {"property": property_name})
    ET.SubElement(data, "String").text = value


# --- Structural subset validation -----------------------------------------------


def validate_dexpi_xml_structure(xml_text: str) -> None:
    """Validate the produced XML structural envelope and reference integrity.

    Checks: well-formed XML, a ``<Model>`` root, globally unique non-empty XML
    ``Object@id`` values (file-local reference mechanics), local ``#`` reference
    syntax, and local reference targets resolve.

    This is **not** full DEXPI model/schema conformance. It does not validate the
    complete DEXPI class vocabulary, class/property cardinalities, RDL semantics,
    DEXPI profile constraints, or full normative conformance. The official DEXPI
    XML schema is a generic envelope schema; model-level class/multiplicity
    conformance is not enforced by it and remains an upstream clarification area
    (DEXPI 2.0.1, released 2026-09-30, has not been reviewed by DeepPlant).
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise DexpiExportError(f"produced XML is not well-formed: {exc}") from exc

    if local(root.tag) != "Model":
        raise DexpiExportError(
            f"produced DEXPI XML root must be <Model>, found <{local(root.tag)}>"
        )

    declared_ids = set(collect_object_ids(root, DexpiExportError))

    for element in root.iter("References"):
        for token in (element.get("objects") or "").split():
            if not token.startswith("#"):
                raise DexpiExportError(f"reference token '{token}' must start with '#'")
            target = token[1:]
            if target not in declared_ids:
                raise DexpiExportError(f"unresolved DEXPI reference '#{target}' in produced XML")
