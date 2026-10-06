# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Root aggregate of the semantic model and its cross-layer validation.

`PlantModel` composes the physical layer, the optional dependent piping
realization, and the optional, independently valid process graph (ADR-0006,
ADR-0011). The rules that need plant context live here: unique authored
connection identity (C1) and resolution of every piping realization to a
connection of the same model (P3). Process ids, physical ids, connection ids,
and piping ids remain separate namespaces.
"""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from deepplant.model.physical import Connection, Equipment, Plant
from deepplant.model.piping import PipingModel
from deepplant.model.process import ProcessModel
from deepplant.model.validation import find_duplicate_ids


def _default_equipment() -> list[Equipment]:
    return []


def _default_connections() -> list[Connection]:
    return []


class PlantModel(BaseModel):
    """Root container of a DeepPlant semantic model.

    Owns the physical/topology layer (``plant``, ``equipment``,
    ``connections``), the optional piping-realization submodel under ``piping``
    (ADR-0011), and, optionally, one process-domain submodel under ``process``.

    ``ProcessModel`` stays independently constructible and owns its S1-S4
    validation boundary. ``PipingModel`` is the dependent layer, so the two
    rules that need plant context live here: unique, authored connection
    identity (C1) and resolution of every realization reference to a
    connection of this same model (P3). Equipment ids, connection ids, piping
    ids, and process ids remain separate namespaces. No rule connects the
    process graph to anything else: Process ↔ physical realization stays
    undecided, so piping is valid without a ``ProcessModel`` and no process
    object is required to resolve into piping.

    ``None`` means the submodel is not authored; an explicitly present empty
    submodel is a valid value.
    """

    model_config = ConfigDict(extra="forbid")

    plant: Plant
    equipment: list[Equipment] = Field(default_factory=_default_equipment)
    connections: list[Connection] = Field(default_factory=_default_connections)
    piping: PipingModel | None = None
    process: "ProcessModel | None" = None

    @model_validator(mode="after")
    def _validate_unique_equipment_ids(self) -> Self:
        duplicates = find_duplicate_ids(item.id for item in self.equipment)
        if duplicates:
            raise ValueError(f"duplicate equipment id(s): {', '.join(duplicates)}")
        return self

    @model_validator(mode="after")
    def _validate_connection_references(self) -> Self:
        ports_by_component = {item.id: {port.id for port in item.ports} for item in self.equipment}
        errors: list[str] = []
        for index, connection in enumerate(self.connections):
            for endpoint, ref in (("source", connection.source), ("target", connection.target)):
                if ref.component not in ports_by_component:
                    errors.append(
                        f"connections[{index}].{endpoint}: unknown component '{ref.component}'"
                    )
                elif ref.port not in ports_by_component[ref.component]:
                    errors.append(
                        f"connections[{index}].{endpoint}: component '{ref.component}' has no "
                        f"port '{ref.port}'"
                    )
        if errors:
            raise ValueError("; ".join(errors))
        return self

    @model_validator(mode="after")
    def _validate_unique_connection_ids(self) -> Self:
        duplicates = find_duplicate_ids(connection.id for connection in self.connections)
        if duplicates:
            raise ValueError(f"duplicate connection id(s): {', '.join(duplicates)}")
        return self

    @model_validator(mode="after")
    def _validate_piping_connection_references(self) -> Self:
        if self.piping is None:
            return self
        known = {connection.id for connection in self.connections}
        errors: list[str] = []
        for line_index, line in enumerate(self.piping.lines):
            for segment_index, segment in enumerate(line.segments):
                for realization_index, realization in enumerate(segment.realizations):
                    if realization.connection not in known:
                        errors.append(
                            f"piping.lines[{line_index}].segments[{segment_index}]"
                            f".realizations[{realization_index}].connection: unknown "
                            f"connection '{realization.connection}'"
                        )
        if errors:
            raise ValueError("; ".join(errors))
        return self
