# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Narrow DEXPI 2.x Process interoperability adapter (evidence spike).

This module is an adapter boundary, not canonical domain logic (ADR-0002,
ADR-0003). DEXPI is an external representation::

    DEXPI XML (Process model subset)
        |
        v
    deepplant.adapters.dexpi
        |
        v
    deepplant.model.ProcessModel

Only the DEXPI **Process** model slice is implemented and only for an explicit
material subset (see ``docs/dexpi-process-spike.md``):

- DEXPI ``Source`` / ``Sink`` / ``Mixing`` / ``SplittingMaterial`` /
  ``Pumping`` ProcessStep classes with **material ports only**;
- DEXPI ``Stream`` connections between ``MaterialPort`` objects;
- DEXPI engineering ``Identifier`` data (mapped deterministically onto the
  DeepPlant ``id`` fields) and ``Label`` (mapped onto ``name``).

Everything else is rejected with an explicit :class:`DexpiImportError` /
:class:`DexpiExportError` rather than silently dropped or collapsed into a
``ProcessStream`` (in particular ``EnergyFlow`` and ``InformationFlow`` are
never imported as material streams). No Proteus XML, no Plant/P&ID model, no
graphics, and no presentation data are handled here.

The target DEXPI release is pinned to the latest stable tagged release
``V2.0.0`` (commit ``260c81c51039789a6148a98af4c6caf23f87a3e2``). At runtime the
import preflight also requires exactly the pinned Core/Process model URIs
(``https://data.dexpi.org/models/2.0.0/Core.xml`` and ``.../Process.xml``), so
an unsupported DEXPI model version fails explicitly until deliberately reviewed.
Declared ``Port.ConnectorReference`` values are validated when present; the
exporter covers only the deliberately symmetric canonical subset (no reverse
``pump -> Pumping`` assertion). See ``docs/dexpi-process-spike.md`` for the
release research, the mapping matrix, identity semantics, fixture provenance,
and export-feasibility assessment.
"""

from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree as ET

from pydantic import ValidationError

from deepplant.model import ProcessModel, ProcessPort, ProcessRef, ProcessStep, ProcessStream

__all__ = [
    "DEXPI_CORE_MODEL_URI",
    "DEXPI_INSPECTION_DATE",
    "DEXPI_LICENCE",
    "DEXPI_PROCESS_MODEL_URI",
    "DEXPI_SOURCE_URL",
    "DEXPI_TARGET_REVISION",
    "DEXPI_TARGET_TAG",
    "DEXPI_TARGET_VERSION",
    "DexpiExportError",
    "DexpiImportError",
    "export_dexpi_process",
    "import_dexpi_process",
    "import_dexpi_process_xml",
    "validate_dexpi_xml_structure",
]

# --- Pinned official DEXPI 2.x target -----------------------------------------
# Inspected 2026-09-09 from https://dexpi.org/ and
# https://gitlab.com/dexpi/Specification (releases/tags APIs and the shallow
# V2.0.0 clone). V2.0.0 is the latest stable release; DEXPI 2.0.1 was reported
# on dexpi.org (2026-08-25) as "being prepared" but is not yet released, so the
# stable release remains the implementation target.
DEXPI_TARGET_VERSION = "2.0.0"
DEXPI_TARGET_TAG = "V2.0.0"
DEXPI_TARGET_REVISION = "260c81c51039789a6148a98af4c6caf23f87a3e2"
DEXPI_SOURCE_URL = "https://gitlab.com/dexpi/Specification"
DEXPI_LICENCE = "CC BY 4.0"
DEXPI_INSPECTION_DATE = "2026-09-09"

# Pinned exchange envelope model URIs. The adapter intentionally accepts only
# these exact 2.0.0 model URIs at runtime: unsupported DEXPI model versions
# fail explicitly until they have been deliberately reviewed.
DEXPI_CORE_MODEL_URI = "https://data.dexpi.org/models/2.0.0/Core.xml"
DEXPI_PROCESS_MODEL_URI = "https://data.dexpi.org/models/2.0.0/Process.xml"

# DEXPI XML 'name' pattern (xsd:name / ID): letter or underscore first, then
# letters/digits/underscores.
_MODEL_NAME_PATTERN = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")


class DexpiImportError(ValueError):
    """Raised when DEXPI XML cannot be imported into a DeepPlant ProcessModel.

    The message distinguishes malformed XML / broken references from
    well-formed DEXPI-native content that this adapter slice does not support
    yet.
    """


class DexpiExportError(ValueError):
    """Raised when a DeepPlant ProcessModel cannot be exported honestly."""


# Deterministic object-id map key: ("step", id), ("port", step_id, port_id), or
# ("stream", id).
_ObjectIdKey = tuple[str, str] | tuple[str, str, str]


# --- Supported DEXPI 2.x Process subset (explicit, never generic) -------------
# Keys are the full DEXPI XML ``type`` values. Values are the canonical
# DeepPlant ``ProcessStep.type`` strings produced by the mapping. The mapping
# table is the spike contract; it is never derived from the DEXPI class name.
_MODEL_TYPE = "Process/ProcessModel"
_MATERIAL_PORT_TYPE = "Process/Process.MaterialPort"
_STREAM_TYPE = "Process/Process.Stream"

_STEP_TYPE_MAP: dict[str, str] = {
    "Process/Process.Source": "source",
    "Process/Process.Sink": "sink",
    "Process/Process.Mixing": "mixing",
    "Process/Process.SplittingMaterial": "splitting",
    "Process/Process.Pumping": "pump",
}

# Reverse (DeepPlant -> DEXPI) mapping. Deliberately excludes "pump": DEXPI
# ``Pumping -> type="pump"`` is a lossy import normalization (DEXPI Pumping may
# carry an energy port / driver semantics, Head, Method, VolumeFlow that
# DeepPlant does not store), and canonical type="pump" currently doubles as a
# presentation role. ``pump`` is therefore documented as importable
# normalization, not yet safely exportable classification, until the next
# ProcessStep.type semantics slice. ``heat_exchanger``/``vessel`` have no
# unambiguous DEXPI engineering class at all and stay unexportable.
_REVERSE_STEP_TYPE_MAP: dict[str, str] = {
    "source": "Process/Process.Source",
    "sink": "Process/Process.Sink",
    "mixing": "Process/Process.Mixing",
    "splitting": "Process/Process.SplittingMaterial",
}

_ENUM_PREFIX = "Process/Enumerations.PortDirection."

# Data properties that carry only annotation metadata. Present values are
# ignored and documented as lossy (Description), or mapped onto canonical
# fields (Identifier -> id, Label -> name, NominalDirection -> incidence
# consistency check). Everything else that is present is rejected.
_STEP_DATA_PROPERTIES = frozenset({"Identifier", "Label", "Description"})
_STEP_COMPONENT_PROPERTIES = frozenset({"Ports", "SubProcessSteps"})
_STEP_REFERENCE_PROPERTIES: frozenset[str] = frozenset()
_PORT_DATA_PROPERTIES = frozenset({"Identifier", "NominalDirection", "Description"})
_PORT_COMPONENT_PROPERTIES: frozenset[str] = frozenset()
_PORT_REFERENCE_PROPERTIES = frozenset({"ConnectorReference"})
_STREAM_DATA_PROPERTIES = frozenset({"Identifier", "Label", "Description"})
_STREAM_COMPONENT_PROPERTIES: frozenset[str] = frozenset()
_STREAM_REFERENCE_PROPERTIES = frozenset({"Source", "Target"})


# --- Small XML helpers ---------------------------------------------------------


def _local(tag: str) -> str:
    """Return the namespace-free local name of an ElementTree tag."""
    return tag.rsplit("}", 1)[-1]


def _children(element: ET.Element, local_name: str) -> list[ET.Element]:
    """Direct children of ``element`` whose local tag equals ``local_name``."""
    return [child for child in element if _local(child.tag) == local_name]


def _describe(object_element: ET.Element) -> str:
    """Human-readable DEXPI object identity for diagnostics."""
    obj_id = object_element.get("id")
    obj_type = object_element.get("type")
    identifier = "unknown"
    for data in _children(object_element, "Data"):
        if data.get("property") != "Identifier":
            continue
        for leaf in data:
            identifier = (leaf.text or "").strip() or "undefined"
            break
        break
    label = obj_id if obj_id is not None else identifier
    return f"{obj_type} (xml id '{label}', Identifier '{identifier}')"


def _data_leaves(object_element: ET.Element, property_name: str) -> list[str | None]:
    """Scalar values of ``Data property=<property_name>`` in document order.

    ``None`` marks an explicit ``<Undefined/>`` value; strings are the text of
    scalar leaves or the ``data`` attribute of ``DataReference`` leaves.
    """
    leaves: list[str | None] = []
    for data in _children(object_element, "Data"):
        if data.get("property") != property_name:
            continue
        for leaf in data:
            tag = _local(leaf.tag)
            if tag == "Undefined":
                leaves.append(None)
            elif tag == "DataReference":
                leaves.append(leaf.get("data"))
            else:
                leaves.append((leaf.text or "").strip())
    return leaves


def _require_identifier(object_element: ET.Element, where: str) -> str:
    """Read the required DEXPI engineering ``Identifier`` data property."""
    leaves = _data_leaves(object_element, "Identifier")
    if len(leaves) != 1:
        raise DexpiImportError(
            f"{where}: expected exactly one Data property 'Identifier', found {len(leaves)}"
        )
    value = leaves[0]
    if value is None or not value.strip():
        raise DexpiImportError(f"{where}: Data property 'Identifier' must be a non-empty string")
    return value


def _optional_label(object_element: ET.Element, where: str) -> str | None:
    """Read the optional DEXPI ``Label`` data property (None means absent/undefined)."""
    leaves = _data_leaves(object_element, "Label")
    if not leaves:
        return None
    if len(leaves) != 1:
        raise DexpiImportError(
            f"{where}: expected at most one Data property 'Label', found {len(leaves)}"
        )
    value = leaves[0]
    return value if value else None


def _require_references(object_element: ET.Element, property_name: str, where: str) -> str:
    """Read a single-valued DEXPI reference property, returning the raw IDREF token."""
    tokens: list[str] = []
    for reference in _children(object_element, "References"):
        if reference.get("property") != property_name:
            continue
        tokens.extend((reference.get("objects") or "").split())
    if len(tokens) != 1:
        raise DexpiImportError(
            f"{where}: expected exactly one reference in '{property_name}', found {len(tokens)}"
        )
    return tokens[0]


def _check_unknown_properties(
    object_element: ET.Element,
    where: str,
    allowed_data: frozenset[str],
    allowed_components: frozenset[str],
    allowed_references: frozenset[str],
) -> None:
    """Fail on DEXPI content that this adapter slice cannot honestly ignore.

    Empty ``Components``/``References`` wrappers with an unknown property are
    treated as absent (no semantics to lose); any actual content is rejected.
    """
    for child in object_element:
        tag = _local(child.tag)
        if tag == "Data":
            prop = child.get("property")
            if prop not in allowed_data:
                raise DexpiImportError(f"{where}: unsupported Data property '{prop}'")
        elif tag == "Components":
            prop = child.get("property")
            if prop not in allowed_components and list(child):
                raise DexpiImportError(f"{where}: unsupported Components property '{prop}'")
        elif tag == "References":
            prop = child.get("property")
            objects = (child.get("objects") or "").strip()
            if prop not in allowed_references and objects:
                raise DexpiImportError(f"{where}: unsupported References property '{prop}'")
        elif tag == "Object":
            raise DexpiImportError(
                f"{where}: unexpected direct <Object> child; Object children belong "
                "inside supported Components wrappers in this adapter subset"
            )
        else:
            raise DexpiImportError(f"{where}: unexpected element <{tag}>")


def _resolve_object_id(token: str, where: str) -> str:
    """Strip the ``#`` prefix of a DEXPI IDREF token."""
    if not token.startswith("#"):
        raise DexpiImportError(f"{where}: DEXPI reference '{token}' must start with '#'")
    return token[1:]


def _collect_object_ids(root: ET.Element, error_type: type[Exception]) -> dict[str, ET.Element]:
    """Collect every non-empty XML ``id`` attribute, rejecting duplicates.

    XML ids are file-local reference mechanics, never canonical identity. A
    duplicate id makes file-local reference resolution ambiguous, so both import
    preflight and exported-structure validation reject duplicates instead of
    letting a later assignment silently win.
    """
    declared: dict[str, ET.Element] = {}
    for element in root.iter():
        element_id = (element.get("id") or "").strip()
        if not element_id:
            continue
        if element_id in declared:
            raise error_type(
                f"duplicate DEXPI XML Object id '{element_id}': file-local object "
                "ids must be globally unique for unambiguous reference resolution"
            )
        declared[element_id] = element
    return declared


def _require_object_id(object_element: ET.Element, where: str) -> str:
    """Require a usable non-empty file-local XML identity for a referenceable object."""
    object_id = (object_element.get("id") or "").strip()
    if not object_id:
        raise DexpiImportError(
            f"{where}: a referenceable DEXPI Object requires a non-empty XML "
            "Object@id for file-local reference resolution"
        )
    return object_id


def _validate_required_model_import(
    imports: list[ET.Element], *, prefix: str, expected_uri: str
) -> None:
    """Require exactly one exact pinned model import for ``prefix``.

    Unrelated package imports (for example ``Plant``) are ignored unless they
    share the pinned prefix/source and therefore create an ambiguity.
    """
    relevant = [
        element
        for element in imports
        if element.get("prefix") == prefix or element.get("source") == expected_uri
    ]
    exact = [
        element
        for element in relevant
        if element.get("prefix") == prefix and element.get("source") == expected_uri
    ]
    if len(exact) == 1 and len(relevant) == 1:
        return
    observed = (
        ", ".join(
            f"prefix={element.get('prefix')!r}, source={element.get('source')!r}"
            for element in relevant
        )
        or "no matching <Import> element"
    )
    raise DexpiImportError(
        f"unsupported DEXPI model import for prefix {prefix!r}: expected exactly "
        f"one <Import prefix={prefix!r} source={expected_uri!r}>; observed "
        f"{observed}; supported target version is DEXPI {DEXPI_TARGET_VERSION}"
    )


def _validate_model_imports(root: ET.Element) -> None:
    """Validate the pinned Core/Process 2.0.0 imports of a DEXPI XML envelope."""
    imports = [element for element in root if _local(element.tag) == "Import"]
    _validate_required_model_import(imports, prefix="Core", expected_uri=DEXPI_CORE_MODEL_URI)
    _validate_required_model_import(imports, prefix="Process", expected_uri=DEXPI_PROCESS_MODEL_URI)


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

    if _local(root.tag) != "Model":
        raise DexpiImportError(
            f"invalid DEXPI XML: root element must be <Model>, found <{_local(root.tag)}>"
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
    has_process_model = any(element.get("type") == _MODEL_TYPE for element in root.iter("Object"))
    if plant_types and not has_process_model:
        raise DexpiImportError(
            "only DEXPI Plant model content is present "
            f"({', '.join(plant_types)}); Plant/P&ID import is out of scope for "
            "this adapter slice and Plant-only input must not silently become an "
            "empty ProcessModel; the supported exchange envelope requires an "
            f"<Import prefix='Process' source='{DEXPI_PROCESS_MODEL_URI}'> for "
            f"DEXPI {DEXPI_TARGET_VERSION}"
        )

    _validate_model_imports(root)
    object_ids = _collect_object_ids(root, DexpiImportError)
    object_types = {
        element_id: element_type
        for element_id, element in object_ids.items()
        if _local(element.tag) == "Object"
        for element_type in [element.get("type")]
        if element_type
    }

    process_model_elements = [
        element for element in root.iter("Object") if element.get("type") == _MODEL_TYPE
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
    where = _describe(model_element)
    # Fail closed on unsupported ProcessModel-level semantic content. Only the
    # explicitly supported populated collections are ProcessSteps and
    # ProcessConnections; unknown empty Components/References wrappers carry no
    # semantics and may be tolerated, anything populated is rejected.
    _check_unknown_properties(
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

    for component in _children(model_element, "Components"):
        prop = component.get("property")
        if prop == "ProcessSteps":
            for step_element in _children(component, "Object"):
                _collect_step(
                    step_element,
                    steps,
                    canonical_step_ids,
                    port_by_object_id,
                    port_connector_tokens,
                    port_direction,
                )
        elif prop == "ProcessConnections":
            pending_streams.extend(_children(component, "Object"))
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
    where = _describe(step_element)
    dexpi_type = step_element.get("type")
    canonical_type = _STEP_TYPE_MAP.get(dexpi_type or "")
    if canonical_type is None:
        raise DexpiImportError(
            f"unsupported DEXPI ProcessStep class '{dexpi_type}' ({where}): this "
            "adapter slice supports only "
            + ", ".join(sorted(_STEP_TYPE_MAP))
            + "; no generic class-name conversion is performed"
        )

    _check_unknown_properties(
        step_element,
        where,
        _STEP_DATA_PROPERTIES,
        _STEP_COMPONENT_PROPERTIES,
        _STEP_REFERENCE_PROPERTIES,
    )

    step_id = _require_identifier(step_element, where)
    if step_id in canonical_step_ids:
        raise DexpiImportError(
            f"duplicate imported canonical ProcessStep id '{step_id}' "
            f"(DEXPI {where}); DEXPI engineering Identifiers are not unique in this file"
        )
    canonical_step_ids.add(step_id)
    name = _optional_label(step_element, where)

    ports: list[ProcessPort] = []
    port_ids_in_step: set[str] = set()
    for component in _children(step_element, "Components"):
        prop = component.get("property")
        if prop == "Ports":
            for port_element in _children(component, "Object"):
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

    steps.append(ProcessStep(id=step_id, type=canonical_type, name=name, ports=ports))


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
    where = f"port of {step_where}: {_describe(port_element)}"
    dexpi_type = port_element.get("type")
    if dexpi_type != _MATERIAL_PORT_TYPE:
        raise DexpiImportError(
            f"unsupported DEXPI port class '{dexpi_type}' ({where}): only "
            f"{_MATERIAL_PORT_TYPE} is imported in this slice; energy/information "
            "ports belong to EnergyFlow/InformationFlow semantics that must not be "
            "collapsed into material ProcessPorts"
        )

    _check_unknown_properties(
        port_element,
        where,
        _PORT_DATA_PROPERTIES,
        _PORT_COMPONENT_PROPERTIES,
        _PORT_REFERENCE_PROPERTIES,
    )

    port_id = _require_identifier(port_element, where)
    if port_id in port_ids_in_step:
        raise DexpiImportError(
            f"duplicate ProcessPort id '{port_id}' within ProcessStep '{step_id}' "
            f"(DEXPI {where}); DEXPI port Identifiers must be unique within one "
            "ProcessStep for a lossless canonical mapping"
        )
    port_ids_in_step.add(port_id)

    direction = _read_port_direction(port_element, where)
    port_direction[(step_id, port_id)] = direction

    object_id = _require_object_id(port_element, where)
    port_by_object_id[object_id] = (step_id, port_id)

    # DEXPI 2.0.0 leaves Port.ConnectorReference multiplicity unresolved
    # (``TODO check multiplicities``), so absent ConnectorReference is tolerated;
    # every token actually declared is validated after the material graph exists.
    connector_tokens: list[str] = []
    for reference in _children(port_element, "References"):
        if reference.get("property") == "ConnectorReference":
            connector_tokens.extend((reference.get("objects") or "").split())
    if connector_tokens:
        port_connector_tokens[object_id] = connector_tokens

    ports.append(ProcessPort(id=port_id))


def _read_port_direction(port_element: ET.Element, where: str) -> str:
    leaves = _data_leaves(port_element, "NominalDirection")
    if len(leaves) != 1 or leaves[0] is None:
        raise DexpiImportError(
            f"{where}: required Data property 'NominalDirection' must be exactly "
            "one PortDirection enumeration reference"
        )
    literal = str(leaves[0])
    if not literal.startswith(_ENUM_PREFIX):
        raise DexpiImportError(
            f"{where}: unexpected NominalDirection reference '{literal}'; expected "
            f"'{_ENUM_PREFIX}<Inlet|Outlet>'"
        )
    direction = literal[len(_ENUM_PREFIX) :]
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
    where = _describe(stream_element)
    dexpi_type = stream_element.get("type")
    if dexpi_type != _STREAM_TYPE:
        raise DexpiImportError(
            f"unsupported DEXPI connection class '{dexpi_type}' ({where}): only "
            f"{_STREAM_TYPE} (material flow) maps to ProcessStream in this slice; "
            "EnergyFlow/InformationFlow and their subclasses must not be silently "
            "imported as material ProcessStreams"
        )

    _check_unknown_properties(
        stream_element,
        where,
        _STREAM_DATA_PROPERTIES,
        _STREAM_COMPONENT_PROPERTIES,
        _STREAM_REFERENCE_PROPERTIES,
    )

    stream_id = _require_identifier(stream_element, where)
    if stream_id in canonical_stream_ids:
        raise DexpiImportError(
            f"duplicate imported canonical ProcessStream id '{stream_id}' "
            f"(DEXPI {where}); DEXPI engineering Identifiers are not unique in this file"
        )
    canonical_stream_ids.add(stream_id)
    name = _optional_label(stream_element, where)

    source_token = _require_references(stream_element, "Source", where)
    target_token = _require_references(stream_element, "Target", where)
    source_object_id = _resolve_object_id(source_token, where)
    target_object_id = _resolve_object_id(target_token, where)

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
            connector_object_id = _resolve_object_id(
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


# --- Export --------------------------------------------------------------------


def export_dexpi_process(
    process: ProcessModel,
    *,
    model_name: str = "ProcessModel",
    model_uri: str = "https://example.org/deepplant/process-model",
) -> str:
    """Serialize a ``ProcessModel`` to deterministic DEXPI-native XML.

    Only the supported subset is exported (see ``docs/dexpi-process-spike.md``);
    step types outside the explicit reverse mapping table raise
    :class:`DexpiExportError` instead of producing XML that invents engineering
    meaning. ``model_name`` / ``model_uri`` are the exchange-file envelope
    values (serialization mechanics only).

    Nominal directions on exported material ports are derived from
    ``ProcessStream`` incidence (DEXPI ``PortDirection`` is exactly
    Inlet/Outlet). A port with no incident stream, or with both an incident
    source and an incident target, cannot be exported without inventing or
    contradicting DEXPI direction semantics and raises.
    """
    if not _MODEL_NAME_PATTERN.fullmatch(model_name or ""):
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
        {"id": "ProcessModel1", "type": _MODEL_TYPE},
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
) -> dict[_ObjectIdKey, str]:
    """Assign deterministic DEXPI XML ``id`` attributes (serialization mechanics).

    Keys are ``("step", step_id)``, ``("port", step_id, port_id)`` and
    ``("stream", stream_id)``. Generated ids only need to be stable, unique and
    valid DEXPI ``name``/``ID`` tokens; they are explicitly excluded from
    semantic round-trip comparison (see ``docs/dexpi-process-spike.md``).
    """
    assigned: dict[_ObjectIdKey, str] = {}
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
    object_ids: dict[_ObjectIdKey, str],
) -> None:
    dexpi_type = _REVERSE_STEP_TYPE_MAP.get(step.type)
    if dexpi_type is None:
        raise DexpiExportError(
            f"unsupported canonical ProcessStep type '{step.type}' on step "
            f"'{step.id}': this adapter slice can only export "
            + ", ".join(sorted(_REVERSE_STEP_TYPE_MAP))
            + "; DeepPlant currently has no separate engineering classification "
            "to map other roles (e.g. heat_exchanger, vessel) onto an exact "
            "DEXPI class"
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
                "type": _MATERIAL_PORT_TYPE,
            },
        )
        _append_data_string(port_element, "Identifier", port.id)
        ET.SubElement(
            ET.SubElement(port_element, "Data", {"property": "NominalDirection"}),
            "DataReference",
            {"data": f"{_ENUM_PREFIX}{direction}"},
        )


def _append_stream(
    stream: ProcessStream,
    container: ET.Element,
    object_ids: dict[_ObjectIdKey, str],
) -> None:
    stream_element = ET.SubElement(
        container,
        "Object",
        {"id": object_ids[("stream", stream.id)], "type": _STREAM_TYPE},
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
    """Deterministic structural-subset validation of produced DEXPI XML.

    Checks: well-formed XML, a ``<Model>`` root, globally unique non-empty XML
    ``Object@id`` values (file-local reference mechanics), resolvable
    ``#``-prefixed references, and the supported structural subset vocabulary.

    This is **not** full DEXPI model/schema conformance. It does not check full
    DEXPI model cardinalities, complete class semantics, RDL constraints, DEXPI
    profile constraints, or full normative conformance. The official DEXPI XML
    schema is a generic envelope schema; model-level class/multiplicity
    conformance is not enforced by it and remains under upstream clarification
    for DEXPI 2.0.1, so this is labelled exactly as structural subset validation
    in ``docs/dexpi-process-spike.md``.
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise DexpiExportError(f"produced XML is not well-formed: {exc}") from exc

    if _local(root.tag) != "Model":
        raise DexpiExportError(
            f"produced DEXPI XML root must be <Model>, found <{_local(root.tag)}>"
        )

    declared_ids = set(_collect_object_ids(root, DexpiExportError))

    for element in root.iter("References"):
        for token in (element.get("objects") or "").split():
            if not token.startswith("#"):
                raise DexpiExportError(f"reference token '{token}' must start with '#'")
            target = token[1:]
            if target not in declared_ids:
                raise DexpiExportError(f"unresolved DEXPI reference '#{target}' in produced XML")
