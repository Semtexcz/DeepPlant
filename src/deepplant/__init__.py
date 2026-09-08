# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _distribution_version

from deepplant.io import PlantLoadError, load_plant
from deepplant.model import (
    Connection,
    Equipment,
    Plant,
    PlantModel,
    Port,
    PortRef,
    ProcessModel,
    ProcessPort,
    ProcessRef,
    ProcessStep,
    ProcessStream,
)

try:
    __version__ = _distribution_version("deepplant")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "__version__",
    "Connection",
    "Equipment",
    "Plant",
    "PlantLoadError",
    "PlantModel",
    "Port",
    "PortRef",
    "ProcessModel",
    "ProcessPort",
    "ProcessRef",
    "ProcessStep",
    "ProcessStream",
    "load_plant",
]
