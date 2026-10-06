# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Pinned DEXPI target metadata and adapter error types.

The adapter is deliberately pinned to one reviewed DEXPI release (2.0.0),
and every import is checked against the exact pinned Core/Process model URIs
at runtime so an unreviewed version fails explicitly. DEXPI is an external
representation; nothing here enters the canonical model (ADR-0002,
ADR-0003).
"""

from __future__ import annotations

import re

# --- Pinned DEXPI target ------------------------------------------------------
# Inspected 2026-09-09 from https://dexpi.org/ and
# https://gitlab.com/dexpi/Specification (releases/tags APIs and the shallow
# V2.0.0 clone). The implementation target stays deliberately pinned to V2.0.0.
# DEXPI 2.0.1 was released on 2026-09-30 but has not been reviewed for
# compatibility, so the pin does not move yet.
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
MODEL_NAME_PATTERN = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")


class DexpiImportError(ValueError):
    """Raised when DEXPI XML cannot be imported into a DeepPlant ProcessModel.

    The message distinguishes malformed XML / broken references from
    well-formed DEXPI-native content that this adapter slice does not support
    yet.
    """


class DexpiExportError(ValueError):
    """Raised when a DeepPlant ProcessModel cannot be exported honestly."""
