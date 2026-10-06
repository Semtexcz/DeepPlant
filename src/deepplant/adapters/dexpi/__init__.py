# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Narrow DEXPI 2.0.0 Process interoperability adapter.

An adapter boundary, not canonical domain logic (ADR-0002, ADR-0003): DEXPI is
an external representation converted into (and, where semantically honest,
back out of) the canonical `ProcessModel`. It exposes the same public surface
the former single `deepplant.adapters.dexpi` module provided; the
implementation is organized by capability:

- `target`: the pinned DEXPI target metadata and adapter errors;
- `mapping`: the explicit semantic mapping tables;
- `xml`: XML envelope helpers and structural validation;
- `importer`: DEXPI XML -> `ProcessModel`;
- `exporter`: `ProcessModel` -> deterministic DEXPI XML.
"""

from __future__ import annotations

from deepplant.adapters.dexpi.exporter import (
    export_dexpi_process,
    validate_dexpi_xml_structure,
)
from deepplant.adapters.dexpi.importer import (
    import_dexpi_process,
    import_dexpi_process_xml,
)
from deepplant.adapters.dexpi.target import (
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
)

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
