# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""DeepPlant semantic domain model.

This package is the product core (ADR-0002). It exposes the same public
surface the former single `deepplant.model` module provided; the
implementation is organized by capability:

- `validation`: shared field and validation primitives;
- `physical`: plant, equipment, ports, and connections;
- `piping`: physical piping realization over identified connections;
- `process`: the process graph (S1-S4);
- `plant`: the root aggregate and its cross-layer validation.

It imports nothing consumer-specific: no CLI, YAML, file I/O, rendering, or
any other consumer concern.
"""

from deepplant.model.physical import Connection, Equipment, Plant, Port, PortRef
from deepplant.model.piping import (
    PipingLine,
    PipingModel,
    PipingRealization,
    PipingSegment,
)
from deepplant.model.plant import PlantModel
from deepplant.model.process import (
    ProcessModel,
    ProcessPort,
    ProcessRef,
    ProcessStep,
    ProcessStream,
)

__all__ = [
    "Connection",
    "Equipment",
    "PipingLine",
    "PipingModel",
    "PipingRealization",
    "PipingSegment",
    "Plant",
    "PlantModel",
    "Port",
    "PortRef",
    "ProcessModel",
    "ProcessPort",
    "ProcessRef",
    "ProcessStep",
    "ProcessStream",
]
