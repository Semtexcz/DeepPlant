# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Explicit DEXPI <-> canonical semantic mapping tables.

The mapping is an explicit, reviewable contract and is never derived from the
DEXPI class name: the supported Process subset, its reverse export mapping,
and the property vocabularies each object class may carry. Canonical
DeepPlant functions stay canonical; DEXPI class identifiers are not adopted
(ADR-0009, ADR-0012).
"""

from __future__ import annotations

# Deterministic object-id map key: ("step", id), ("port", step_id, port_id), or
# ("stream", id).
ObjectIdKey = tuple[str, str] | tuple[str, str, str]


# --- Supported DEXPI 2.0.0 Process subset (explicit, never generic) -----------
# Keys are the full DEXPI XML ``type`` values. Values are the canonical
# DeepPlant ``ProcessStep.function`` engineering functions produced by the
# mapping (ADR-0009). The mapping table is the spike contract; it is never
# derived from the DEXPI class name, and DeepPlant-native function vocabulary
# (``pumping``, ``splitting_material``, ...) stays canonical rather than
# adopting DEXPI class identifiers.
MODEL_TYPE = "Process/ProcessModel"
MATERIAL_PORT_TYPE = "Process/Process.MaterialPort"
STREAM_TYPE = "Process/Process.Stream"

STEP_TYPE_MAP: dict[str, str] = {
    "Process/Process.Source": "source",
    "Process/Process.Sink": "sink",
    "Process/Process.Mixing": "mixing",
    "Process/Process.SplittingMaterial": "splitting_material",
    "Process/Process.Pumping": "pumping",
}

# Reverse (DeepPlant -> DEXPI) mapping. Since ADR-0009 ``ProcessStep.function``
# is an engineering classification, reverse export is an
# engineering-classification assertion for functions with an unambiguous DEXPI
# class in this adapter slice. ``pumping -> Pumping`` is asserted for
# material-port-only pumping steps (the energy-port / driver, ``Head``,
# ``Method``, and ``VolumeFlow`` semantics DEXPI Pumping may carry are not owned
# by DeepPlant and would be rejected explicitly if present). ``heat_exchange``
# stays canonical-only (see docs/dev/research/dexpi/exchanging-thermal-energy.md,
# Issue #22): DEXPI ``ExchangingThermalEnergy`` couples two or more material
# flows through one step and requires a mandatory ``Method: HeatExchangeMethod``.
# If an explicit thermal-energy / utility connection is modelled, DEXPI represents
# it with ``ThermalEnergyPort``/``ThermalEnergyFlow`` rather than a material
# ``Stream``. Canonical ``ProcessStep`` cannot express those semantics yet, so no
# automatic mapping is claimed in either direction. ``unspecified`` and other
# non-mapped functions stay unexportable.
REVERSE_STEP_TYPE_MAP: dict[str, str] = {
    "source": "Process/Process.Source",
    "sink": "Process/Process.Sink",
    "mixing": "Process/Process.Mixing",
    "splitting_material": "Process/Process.SplittingMaterial",
    "pumping": "Process/Process.Pumping",
}

ENUM_PREFIX = "Process/Enumerations.PortDirection."

# Data properties that carry only annotation metadata. Present values are
# ignored and documented as lossy (Description), or mapped onto canonical
# fields (Identifier -> id, Label -> name, NominalDirection -> incidence
# consistency check). Everything else that is present is rejected.
STEP_DATA_PROPERTIES = frozenset({"Identifier", "Label", "Description"})
STEP_COMPONENT_PROPERTIES = frozenset({"Ports", "SubProcessSteps"})
STEP_REFERENCE_PROPERTIES: frozenset[str] = frozenset()
PORT_DATA_PROPERTIES = frozenset({"Identifier", "NominalDirection", "Description"})
PORT_COMPONENT_PROPERTIES: frozenset[str] = frozenset()
PORT_REFERENCE_PROPERTIES = frozenset({"ConnectorReference"})
STREAM_DATA_PROPERTIES = frozenset({"Identifier", "Label", "Description"})
STREAM_COMPONENT_PROPERTIES: frozenset[str] = frozenset()
STREAM_REFERENCE_PROPERTIES = frozenset({"Source", "Target"})
