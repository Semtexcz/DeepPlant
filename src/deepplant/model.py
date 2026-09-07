# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Semantic domain model for DeepPlant plants.

This module is the product core (ADR-0002). It must not import the CLI, YAML,
file I/O, rendering, or any other consumer-specific concern.

Semantic input is fail-fast: models forbid unknown fields, and semantic strings
such as ids and equipment types must be non-empty, non-whitespace values.
"""

from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

__all__ = ["Connection", "Equipment", "Plant", "PlantModel", "Port", "PortRef"]

NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Plant(BaseModel):
    """A process plant being engineered."""

    model_config = ConfigDict(extra="forbid")

    id: NonEmptyString
    name: str | None = None


class Port(BaseModel):
    """A named connection point owned by a single equipment item.

    Port identity is local to the owning equipment: the same id may exist on
    different equipment items, and a globally resolvable endpoint is the pair
    ``(component id, port id)``.
    """

    model_config = ConfigDict(extra="forbid")

    id: NonEmptyString


def _default_ports() -> list[Port]:
    return []


class Equipment(BaseModel):
    """A single equipment item inside a plant; owns zero or more ports."""

    model_config = ConfigDict(extra="forbid")

    id: NonEmptyString
    type: NonEmptyString
    name: str | None = None
    ports: list[Port] = Field(default_factory=_default_ports)

    @model_validator(mode="after")
    def _validate_unique_port_ids(self) -> Self:
        seen: set[str] = set()
        duplicates: list[str] = []
        for port in self.ports:
            if port.id in seen and port.id not in duplicates:
                duplicates.append(port.id)
            seen.add(port.id)
        if duplicates:
            raise ValueError(
                f"equipment '{self.id}' has duplicate port id(s): {', '.join(sorted(duplicates))}"
            )
        return self


class PortRef(BaseModel):
    """Reference to one named port on one component.

    ``component`` currently resolves only to :class:`Equipment`. The generic name
    keeps the reference format stable if further semantic component types gain
    ports later.
    """

    model_config = ConfigDict(extra="forbid")

    component: NonEmptyString
    port: NonEmptyString


class Connection(BaseModel):
    """Semantic topology between a source port and a target port.

    A connection is only topology between the two endpoints. It is not yet a
    pipe, pipeline, process stream, signal line, or other physical engineering
    object and carries no engineering properties in this iteration.
    """

    model_config = ConfigDict(extra="forbid")

    source: PortRef
    target: PortRef


def _default_connections() -> list[Connection]:
    return []


def _default_equipment() -> list[Equipment]:
    return []


class PlantModel(BaseModel):
    """Root container of a DeepPlant semantic model."""

    model_config = ConfigDict(extra="forbid")

    plant: Plant
    equipment: list[Equipment] = Field(default_factory=_default_equipment)
    connections: list[Connection] = Field(default_factory=_default_connections)

    @model_validator(mode="after")
    def _validate_unique_equipment_ids(self) -> Self:
        seen: set[str] = set()
        duplicates: list[str] = []
        for item in self.equipment:
            if item.id in seen and item.id not in duplicates:
                duplicates.append(item.id)
            seen.add(item.id)
        if duplicates:
            raise ValueError(f"duplicate equipment id(s): {', '.join(sorted(duplicates))}")
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
