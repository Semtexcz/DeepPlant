# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""DEXPI XML envelope parsing helpers and structural validation.

Standard-library XML access plus the fail-closed structural checks shared by
the importer and exporter: property-vocabulary checking, reference-token
handling, file-local object-id collection, and pinned-envelope model-import
validation.
"""

from __future__ import annotations

from xml.etree import ElementTree as ET

from deepplant.adapters.dexpi.target import (
    DEXPI_CORE_MODEL_URI,
    DEXPI_PROCESS_MODEL_URI,
    DEXPI_TARGET_VERSION,
    DexpiImportError,
)

# --- Small XML helpers ---------------------------------------------------------


def local(tag: str) -> str:
    """Return the namespace-free local name of an ElementTree tag."""
    return tag.rsplit("}", 1)[-1]


def children(element: ET.Element, local_name: str) -> list[ET.Element]:
    """Direct children of ``element`` whose local tag equals ``local_name``."""
    return [child for child in element if local(child.tag) == local_name]


def describe(object_element: ET.Element) -> str:
    """Human-readable DEXPI object identity for diagnostics."""
    obj_id = object_element.get("id")
    obj_type = object_element.get("type")
    identifier = "unknown"
    for data in children(object_element, "Data"):
        if data.get("property") != "Identifier":
            continue
        for leaf in data:
            identifier = (leaf.text or "").strip() or "undefined"
            break
        break
    label = obj_id if obj_id is not None else identifier
    return f"{obj_type} (xml id '{label}', Identifier '{identifier}')"


def data_leaves(object_element: ET.Element, property_name: str) -> list[str | None]:
    """Scalar values of ``Data property=<property_name>`` in document order.

    ``None`` marks an explicit ``<Undefined/>`` value; strings are the text of
    scalar leaves or the ``data`` attribute of ``DataReference`` leaves.
    """
    leaves: list[str | None] = []
    for data in children(object_element, "Data"):
        if data.get("property") != property_name:
            continue
        for leaf in data:
            tag = local(leaf.tag)
            if tag == "Undefined":
                leaves.append(None)
            elif tag == "DataReference":
                leaves.append(leaf.get("data"))
            else:
                leaves.append((leaf.text or "").strip())
    return leaves


def require_identifier(object_element: ET.Element, where: str) -> str:
    """Read the required DEXPI engineering ``Identifier`` data property."""
    leaves = data_leaves(object_element, "Identifier")
    if len(leaves) != 1:
        raise DexpiImportError(
            f"{where}: expected exactly one Data property 'Identifier', found {len(leaves)}"
        )
    value = leaves[0]
    if value is None or not value.strip():
        raise DexpiImportError(f"{where}: Data property 'Identifier' must be a non-empty string")
    return value


def optional_label(object_element: ET.Element, where: str) -> str | None:
    """Read the optional DEXPI ``Label`` data property (None means absent/undefined)."""
    leaves = data_leaves(object_element, "Label")
    if not leaves:
        return None
    if len(leaves) != 1:
        raise DexpiImportError(
            f"{where}: expected at most one Data property 'Label', found {len(leaves)}"
        )
    value = leaves[0]
    return value if value else None


def require_references(object_element: ET.Element, property_name: str, where: str) -> str:
    """Read a single-valued DEXPI reference property, returning the raw IDREF token."""
    tokens: list[str] = []
    for reference in children(object_element, "References"):
        if reference.get("property") != property_name:
            continue
        tokens.extend((reference.get("objects") or "").split())
    if len(tokens) != 1:
        raise DexpiImportError(
            f"{where}: expected exactly one reference in '{property_name}', found {len(tokens)}"
        )
    return tokens[0]


def check_unknown_properties(
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
        tag = local(child.tag)
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


def resolve_object_id(token: str, where: str) -> str:
    """Strip the ``#`` prefix of a DEXPI IDREF token."""
    if not token.startswith("#"):
        raise DexpiImportError(f"{where}: DEXPI reference '{token}' must start with '#'")
    return token[1:]


def collect_object_ids(root: ET.Element, error_type: type[Exception]) -> dict[str, ET.Element]:
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


def require_object_id(object_element: ET.Element, where: str) -> str:
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


def validate_model_imports(root: ET.Element) -> None:
    """Validate the pinned Core/Process 2.0.0 imports of a DEXPI XML envelope."""
    imports = [element for element in root if local(element.tag) == "Import"]
    _validate_required_model_import(imports, prefix="Core", expected_uri=DEXPI_CORE_MODEL_URI)
    _validate_required_model_import(imports, prefix="Process", expected_uri=DEXPI_PROCESS_MODEL_URI)
