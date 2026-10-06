# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Import the supported DEXPI 2.0.0 Process subset into a `ProcessModel`.

The canonical `ProcessModel` is constructed through its public Pydantic
constructors, so the normal S1-S4 invariants run on imported content. Any
DEXPI content outside the supported subset fails closed with
`DexpiImportError` naming the DEXPI class and object instead of being
silently dropped (ADR-0002, ADR-0003, ADR-0010).
"""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from pydantic import ValidationError

from deepplant.adapters.dexpi.mapping import (
    ENUM_PREFIX,
    MATERIAL_PORT_TYPE,
    MODEL_TYPE,
    PORT_COMPONENT_PROPERTIES,
    PORT_DATA_PROPERTIES,
    PORT_REFERENCE_PROPERTIES,
    STEP_COMPONENT_PROPERTIES,
    STEP_DATA_PROPERTIES,
    STEP_REFERENCE_PROPERTIES,
    STEP_TYPE_MAP,
    STREAM_COMPONENT_PROPERTIES,
    STREAM_DATA_PROPERTIES,
    STREAM_REFERENCE_PROPERTIES,
    STREAM_TYPE,
)
from deepplant.adapters.dexpi.target import (
    DEXPI_PROCESS_MODEL_URI,
    DEXPI_TARGET_VERSION,
    DexpiImportError,
)
from deepplant.adapters.dexpi.xml import (
    check_unknown_properties,
    children,
    collect_object_ids,
    data_leaves,
    describe,
    local,
    optional_label,
    require_identifier,
    require_object_id,
    require_references,
    resolve_object_id,
    validate_model_imports,
)
from deepplant.model import (
    ProcessModel,
    ProcessPort,
    ProcessRef,
    ProcessStep,
    ProcessStream,
)

# --- Import --------------------------------------------------------------------


def import_dexpi_process(source: str | Path) -> ProcessModel:
    """Import the supported DEXPI Process subset from a UTF-8 XML file."""
    path = Path(source)
    try:
        xml_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        reason = exc.strerror or str(exc)
        raise DexpiImportError(f"cannot read DEXPI file '{path}': {reason}") from exc
    return import_dexpi_process_xml(xml_text)


def import_dexpi_process_xml(xml_text: str) -> ProcessModel:
    """Import the supported DEXPI Process subset from a DEXPI XML string.

    The canonical ``ProcessModel`` is constructed through its public Pydantic
    constructors so the normal S1-S4 invariants run (step/stream id uniqueness,
    port resolution, distinct endpoints). Errors carry the DEXPI class and, when
    known, the DEXPI object id / engineering Identifier.
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise DexpiImportError(f"invalid DEXPI XML: {exc}") from exc

    if local(root.tag) != "Model":
        raise DexpiImportError(
            f"invalid DEXPI XML: root element must be <Model>, found <{local(root.tag)}>"
        )

    # Plant-only input gets a scoped diagnostic before the generic import-pin
    # error: mixed Plant + Process content is allowed (Plant objects are ignored
    # when an explicit supported ProcessModel is present), Plant-only is not.
    plant_types = sorted(
        {
            element_type
            for element in root.iter("Object")
            for element_type in [element.get("type")]
            if element_type is not None and element_type.startswith("Plant/")
        }
    )
    has_process_model = any(element.get("type") == MODEL_TYPE for element in root.iter("Object"))
    if plant_types and not has_process_model:
        raise DexpiImportError(
            "only DEXPI Plant model content is present "
            f"({', '.join(plant_types)}); Plant/P&ID import is out of scope for "
            "this adapter slice and Plant-only input must not silently become an "
            "empty ProcessModel; the supported exchange envelope requires an "
            f"<Import prefix='Process' source='{DEXPI_PROCESS_MODEL_URI}'> for "
            f"DEXPI {DEXPI_TARGET_VERSION}"
        )

    validate_model_imports(root)
    object_ids = collect_object_ids(root, DexpiImportError)
    object_types = {
        element_id: element_type
        for element_id, element in object_ids.items()
        if local(element.tag) == "Object"
        for element_type in [element.get("type")]
        if element_type
    }

    process_model_elements = [
        element for element in root.iter("Object") if element.get("type") == MODEL_TYPE
    ]
    if not process_model_elements:
        plant_types = sorted(
            {
                element_type
                for element in root.iter("Object")
                for element_type in [element.get("type")]
                if element_type is not None and element_type.startswith("Plant/")
            }
        )
        if plant_types:
            raise DexpiImportError(
                "no DEXPI Process/ProcessModel object found; only DEXPI Plant model "
                "objects are present (Plant/P&ID import is out of scope for this "
                "adapter slice): " + ", ".join(plant_types)
            )
        raise DexpiImportError("no DEXPI Process/ProcessModel object found in the DEXPI XML file")
    if len(process_model_elements) > 1:
        raise DexpiImportError(
            f"found {len(process_model_elements)} Process/ProcessModel objects; "
            "this adapter slice supports exactly one"
        )

    return _import_process_model(process_model_elements[0], object_types)


def _import_process_model(model_element: ET.Element, object_types: dict[str, str]) -> ProcessModel:
    where = describe(model_element)
    # Fail closed on unsupported ProcessModel-level semantic content. Only the
    # explicitly supported populated collections are ProcessSteps and
    # ProcessConnections; unknown empty Components/References wrappers carry no
    # semantics and may be tolerated, anything populated is rejected.
    check_unknown_properties(
        model_element,
        where,
        frozenset(),
        frozenset({"ProcessSteps", "ProcessConnections"}),
        frozenset(),
    )
    steps: list[ProcessStep] = []
    streams: list[ProcessStream] = []
    canonical_step_ids: set[str] = set()
    canonical_stream_ids: set[str] = set()
    port_by_object_id: dict[str, tuple[str, str]] = {}
    port_connector_tokens: dict[str, list[str]] = {}
    stream_by_object_id: dict[str, tuple[str, str, str]] = {}
    port_direction: dict[tuple[str, str], str] = {}
    pending_streams: list[ET.Element] = []

    for component in children(model_element, "Components"):
        prop = component.get("property")
        if prop == "ProcessSteps":
            for step_element in children(component, "Object"):
                _collect_step(
                    step_element,
                    steps,
                    canonical_step_ids,
                    port_by_object_id,
                    port_connector_tokens,
                    port_direction,
                )
        elif prop == "ProcessConnections":
            pending_streams.extend(children(component, "Object"))
        elif prop is not None and list(component):
            raise DexpiImportError(
                f"unsupported DEXPI ProcessModel Components property '{prop}': "
                "material data libraries and other ProcessModel content are not part "
                "of this adapter slice"
            )

    for stream_element in pending_streams:
        _collect_stream(
            stream_element,
            streams,
            canonical_stream_ids,
            port_by_object_id,
            stream_by_object_id,
            port_direction,
        )

    # Cross-checks that need the full material graph.
    _validate_connector_references(
        port_by_object_id,
        port_connector_tokens,
        stream_by_object_id,
        port_direction,
        object_types,
    )

    try:
        return ProcessModel(steps=steps, streams=streams)
    except ValidationError as exc:
        raise DexpiImportError(
            f"imported model failed canonical ProcessModel validation: {exc}"
        ) from exc


def _collect_step(
    step_element: ET.Element,
    steps: list[ProcessStep],
    canonical_step_ids: set[str],
    port_by_object_id: dict[str, tuple[str, str]],
    port_connector_tokens: dict[str, list[str]],
    port_direction: dict[tuple[str, str], str],
) -> None:
    where = describe(step_element)
    dexpi_type = step_element.get("type")
    canonical_function = STEP_TYPE_MAP.get(dexpi_type or "")
    if canonical_function is None:
        raise DexpiImportError(
            f"unsupported DEXPI ProcessStep class '{dexpi_type}' ({where}): this "
            "adapter slice supports only "
            + ", ".join(sorted(STEP_TYPE_MAP))
            + "; no generic class-name conversion is performed"
        )

    check_unknown_properties(
        step_element,
        where,
        STEP_DATA_PROPERTIES,
        STEP_COMPONENT_PROPERTIES,
        STEP_REFERENCE_PROPERTIES,
    )

    step_id = require_identifier(step_element, where)
    if step_id in canonical_step_ids:
        raise DexpiImportError(
            f"duplicate imported canonical ProcessStep id '{step_id}' "
            f"(DEXPI {where}); DEXPI engineering Identifiers are not unique in this file"
        )
    canonical_step_ids.add(step_id)
    name = optional_label(step_element, where)

    ports: list[ProcessPort] = []
    port_ids_in_step: set[str] = set()
    for component in children(step_element, "Components"):
        prop = component.get("property")
        if prop == "Ports":
            for port_element in children(component, "Object"):
                _collect_port(
                    port_element,
                    step_id,
                    where,
                    ports,
                    port_ids_in_step,
                    port_by_object_id,
                    port_connector_tokens,
                    port_direction,
                )
        elif prop == "SubProcessSteps" and list(component):
            raise DexpiImportError(
                f"{where}: nested DEXPI ProcessSteps (SubProcessSteps) are not "
                "supported; DeepPlant ProcessModel has no step hierarchy"
            )

    steps.append(ProcessStep(id=step_id, function=canonical_function, name=name, ports=ports))


def _collect_port(
    port_element: ET.Element,
    step_id: str,
    step_where: str,
    ports: list[ProcessPort],
    port_ids_in_step: set[str],
    port_by_object_id: dict[str, tuple[str, str]],
    port_connector_tokens: dict[str, list[str]],
    port_direction: dict[tuple[str, str], str],
) -> None:
    where = f"port of {step_where}: {describe(port_element)}"
    dexpi_type = port_element.get("type")
    if dexpi_type != MATERIAL_PORT_TYPE:
        raise DexpiImportError(
            f"unsupported DEXPI port class '{dexpi_type}' ({where}): only "
            f"{MATERIAL_PORT_TYPE} is imported in this slice; energy/information "
            "ports belong to EnergyFlow/InformationFlow semantics that must not be "
            "collapsed into material ProcessPorts"
        )

    check_unknown_properties(
        port_element,
        where,
        PORT_DATA_PROPERTIES,
        PORT_COMPONENT_PROPERTIES,
        PORT_REFERENCE_PROPERTIES,
    )

    port_id = require_identifier(port_element, where)
    if port_id in port_ids_in_step:
        raise DexpiImportError(
            f"duplicate ProcessPort id '{port_id}' within ProcessStep '{step_id}' "
            f"(DEXPI {where}); DEXPI port Identifiers must be unique within one "
            "ProcessStep for a lossless canonical mapping"
        )
    port_ids_in_step.add(port_id)

    direction = _read_port_direction(port_element, where)
    port_direction[(step_id, port_id)] = direction

    object_id = require_object_id(port_element, where)
    port_by_object_id[object_id] = (step_id, port_id)

    # DEXPI 2.0.0 leaves Port.ConnectorReference multiplicity unresolved
    # (``TODO check multiplicities``), so absent ConnectorReference is tolerated;
    # every token actually declared is validated after the material graph exists.
    connector_tokens: list[str] = []
    for reference in children(port_element, "References"):
        if reference.get("property") == "ConnectorReference":
            connector_tokens.extend((reference.get("objects") or "").split())
    if connector_tokens:
        port_connector_tokens[object_id] = connector_tokens

    ports.append(ProcessPort(id=port_id))


def _read_port_direction(port_element: ET.Element, where: str) -> str:
    leaves = data_leaves(port_element, "NominalDirection")
    if len(leaves) != 1 or leaves[0] is None:
        raise DexpiImportError(
            f"{where}: required Data property 'NominalDirection' must be exactly "
            "one PortDirection enumeration reference"
        )
    literal = str(leaves[0])
    if not literal.startswith(ENUM_PREFIX):
        raise DexpiImportError(
            f"{where}: unexpected NominalDirection reference '{literal}'; expected "
            f"'{ENUM_PREFIX}<Inlet|Outlet>'"
        )
    direction = literal[len(ENUM_PREFIX) :]
    if direction not in {"Inlet", "Outlet"}:
        raise DexpiImportError(f"{where}: unknown PortDirection literal '{direction}'")
    return direction


def _collect_stream(
    stream_element: ET.Element,
    streams: list[ProcessStream],
    canonical_stream_ids: set[str],
    port_by_object_id: dict[str, tuple[str, str]],
    stream_by_object_id: dict[str, tuple[str, str, str]],
    port_direction: dict[tuple[str, str], str],
) -> None:
    where = describe(stream_element)
    dexpi_type = stream_element.get("type")
    if dexpi_type != STREAM_TYPE:
        raise DexpiImportError(
            f"unsupported DEXPI connection class '{dexpi_type}' ({where}): only "
            f"{STREAM_TYPE} (material flow) maps to ProcessStream in this slice; "
            "EnergyFlow/InformationFlow and their subclasses must not be silently "
            "imported as material ProcessStreams"
        )

    check_unknown_properties(
        stream_element,
        where,
        STREAM_DATA_PROPERTIES,
        STREAM_COMPONENT_PROPERTIES,
        STREAM_REFERENCE_PROPERTIES,
    )

    stream_id = require_identifier(stream_element, where)
    if stream_id in canonical_stream_ids:
        raise DexpiImportError(
            f"duplicate imported canonical ProcessStream id '{stream_id}' "
            f"(DEXPI {where}); DEXPI engineering Identifiers are not unique in this file"
        )
    canonical_stream_ids.add(stream_id)
    name = optional_label(stream_element, where)

    source_token = require_references(stream_element, "Source", where)
    target_token = require_references(stream_element, "Target", where)
    source_object_id = resolve_object_id(source_token, where)
    target_object_id = resolve_object_id(target_token, where)

    for endpoint_name, object_id in (
        ("Source", source_object_id),
        ("Target", target_object_id),
    ):
        if object_id not in port_by_object_id:
            raise DexpiImportError(
                f"{where}: {endpoint_name} reference '#{object_id}' does not resolve "
                "to a DEXPI MaterialPort object imported in this file"
            )

    source_step, source_port = port_by_object_id[source_object_id]
    target_step, target_port = port_by_object_id[target_object_id]

    if port_direction[(source_step, source_port)] != "Outlet":
        raise DexpiImportError(
            f"{where}: Stream.Source port '{source_step}.{source_port}' declares "
            "NominalDirection other than Outlet; DeepPlant derives input/output "
            "purely from stream incidence and cannot represent the contradiction"
        )
    if port_direction[(target_step, target_port)] != "Inlet":
        raise DexpiImportError(
            f"{where}: Stream.Target port '{target_step}.{target_port}' declares "
            "NominalDirection other than Inlet; DeepPlant derives input/output "
            "purely from stream incidence and cannot represent the contradiction"
        )

    object_id = (stream_element.get("id") or "").strip()
    if object_id:
        stream_by_object_id[object_id] = (source_object_id, target_object_id, stream_id)

    streams.append(
        ProcessStream(
            id=stream_id,
            name=name,
            source=ProcessRef(step=source_step, port=source_port),
            target=ProcessRef(step=target_step, port=target_port),
        )
    )


def _validate_connector_references(
    port_by_object_id: dict[str, tuple[str, str]],
    port_connector_tokens: dict[str, list[str]],
    stream_by_object_id: dict[str, tuple[str, str, str]],
    port_direction: dict[tuple[str, str], str],
    object_types: dict[str, str],
) -> None:
    """Validate declared ``Port.ConnectorReference`` values.

    DEXPI 2.0.0 marks ``Port.ConnectorReference`` multiplicity with
    ``TODO check multiplicities``, so this slice does not invent a cardinality:
    absent ConnectorReference is tolerated, and every token that is present must
    resolve to a supported material ``Process/Process.Stream`` and agree with the
    port's nominal direction / stream incidence (an Outlet port must be the
    referenced stream's Source, an Inlet port its Target).
    """
    for port_object_id, tokens in port_connector_tokens.items():
        step_id, port_id = port_by_object_id[port_object_id]
        direction = port_direction[(step_id, port_id)]
        for token in tokens:
            connector_object_id = resolve_object_id(
                token, f"MaterialPort '{step_id}.{port_id}' ConnectorReference"
            )
            stream = stream_by_object_id.get(connector_object_id)
            if stream is None:
                if connector_object_id in port_by_object_id:
                    found = "a DEXPI MaterialPort, which is not a ProcessConnection"
                else:
                    found_type = object_types.get(connector_object_id)
                    found = (
                        f"DEXPI '{found_type}', which is not a supported material Stream"
                        if found_type
                        else "no such DEXPI Object"
                    )
                raise DexpiImportError(
                    f"MaterialPort '{step_id}.{port_id}' ConnectorReference "
                    f"'#{connector_object_id}' must resolve to a supported "
                    f"Process/Process.Stream; found {found}"
                )
            source_id, target_id, stream_id = stream
            role = "Source" if direction == "Outlet" else "Target"
            endpoint_id = source_id if role == "Source" else target_id
            if endpoint_id != port_object_id:
                raise DexpiImportError(
                    f"MaterialPort '{step_id}.{port_id}' ConnectorReference "
                    f"'#{connector_object_id}' is inconsistent with stream "
                    f"incidence: the port declares NominalDirection {direction} "
                    f"but is not the referenced Stream '{stream_id}' {role}"
                )
