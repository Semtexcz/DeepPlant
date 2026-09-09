# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _distribution_version

from deepplant.io import PlantLoadError, PlantSaveError, load_plant, save_plant
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
from deepplant.render import ProcessRenderError, render_process_svg

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
    "PlantSaveError",
    "Port",
    "PortRef",
    "ProcessModel",
    "ProcessPort",
    "ProcessRef",
    "ProcessRenderError",
    "ProcessStep",
    "ProcessStream",
    "load_plant",
    "render_process_svg",
    "save_plant",
]
