# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Physical/topology layer of the semantic model (ADR-0002, ADR-0010).

The physical plant, its equipment inventory, the ports owned by each piece
of equipment, and the directed, property-free adjacency between ports. This
layer is deliberately separate from the process graph and from piping
realization; it owns no presentation or persistence concept (ADR-0003).
"""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from deepplant.model.validation import NonEmptyString, find_duplicate_ids


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
        duplicates = find_duplicate_ids(port.id for port in self.ports)
        if duplicates:
            raise ValueError(
                f"equipment '{self.id}' has duplicate port id(s): {', '.join(duplicates)}"
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
    """Directed semantic topology from a source port to a target port.

    ``source`` and ``target`` record direction, so a connection is currently a
    directed semantic topological relationship from ``source`` to ``target``.
    It is only topology between the two endpoints; it is not a pipe, pipeline,
    process stream, signal line, or other physical engineering object and
    carries no engineering properties.

    ``id`` is canonical, authored identity (C1): it is required, must be
    non-empty, and must be unique within one :class:`PlantModel`. Identity is
    not an engineering property; it exists so the dependent piping layer
    (ADR-0011) can reference an adjacency instead of restating its endpoints.
    ``Connection`` gains identity only — never a line, segment, pipe, kind,
    fluid, or piping-class field.
    """

    model_config = ConfigDict(extra="forbid")

    id: NonEmptyString
    source: PortRef
    target: PortRef
