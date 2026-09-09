# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""External interoperability adapters.

Each adapter maps an external representation into (and, where semantically
honest, back out of) the canonical DeepPlant domain model. Adapters are
consumer-specific boundaries (ADR-0002/ADR-0003): external schema shapes never
dictate canonical model fields, and adapter concerns never leak into
``deepplant.model``.

Currently only the narrow DEXPI 2.x Process adapter exists:
``deepplant.adapters.dexpi`` (see ``docs/dexpi-process-spike.md``). No generic
adapter framework is introduced yet.
"""
