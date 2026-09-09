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

__all__ = [
    "Connection",
    "Equipment",
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
    """Directed semantic topology from a source port to a target port.

    ``source`` and ``target`` record direction, so a connection is currently a
    directed semantic topological relationship from ``source`` to ``target``.
    It is only topology between the two endpoints; it is not yet a pipe,
    pipeline, process stream, signal line, or other physical engineering
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
    """Root container of a DeepPlant semantic model.

    Owns the physical/topology layer (``plant``, ``equipment``,
    ``connections``) and, optionally, one process-domain submodel under
    ``process``. ``ProcessModel`` stays independently constructible and owns
    the S1-S4 validation boundary; ``PlantModel`` does not duplicate or extend
    that internal validation and introduces no cross-layer rules between the
    physical and process graphs yet (ADR-0005). ``None`` means no process model
    is authored; an explicitly present empty ``ProcessModel`` is a valid value.
    """

    model_config = ConfigDict(extra="forbid")

    plant: Plant
    equipment: list[Equipment] = Field(default_factory=_default_equipment)
    connections: list[Connection] = Field(default_factory=_default_connections)
    process: "ProcessModel | None" = None

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


class ProcessPort(BaseModel):
    """A named connection point owned by a single process step.

    Process-port identity is local to the owning ``ProcessStep``. Within one
    ``ProcessModel``, a process endpoint is identified by the pair
    ``(step id, port id)``. A ProcessPort is a process-graph object, not an
    equipment ``Port`` and not a nozzle.
    """

    model_config = ConfigDict(extra="forbid")

    id: NonEmptyString


def _default_process_ports() -> list[ProcessPort]:
    return []


class ProcessStep(BaseModel):
    """A single step inside a process model; owns zero or more process ports.

    ``function`` is the engineering process function performed by this step
    (ADR-0009). It is deliberately an open, non-empty string: no closed
    process-function taxonomy, subclass hierarchy, or function-specific
    engineering validation exists yet. ``function`` is **not** an equipment
    class, a presentation symbol role, an SVG asset name, a DEXPI class
    identifier, or a physical realization; a pumping function may later be
    realized by one pump, several pumps, an ejector, gravity, or another
    physical solution. ``unspecified`` is a legal value meaning the step
    exists semantically but its engineering function has not yet been
    specified. Input/output roles are not stored per port; they remain derived
    from :class:`ProcessStream` endpoints where needed later.
    """

    model_config = ConfigDict(extra="forbid")

    id: NonEmptyString
    function: NonEmptyString
    name: str | None = None
    ports: list[ProcessPort] = Field(default_factory=_default_process_ports)

    @model_validator(mode="after")
    def _validate_unique_process_port_ids(self) -> Self:
        seen: set[str] = set()
        duplicates: list[str] = []
        for port in self.ports:
            if port.id in seen and port.id not in duplicates:
                duplicates.append(port.id)
            seen.add(port.id)
        if duplicates:
            raise ValueError(
                f"step '{self.id}' has duplicate port id(s): {', '.join(sorted(duplicates))}"
            )
        return self


def _default_process_steps() -> list[ProcessStep]:
    return []


class ProcessRef(BaseModel):
    """Reference to one named process port on one process step.

    ``step`` resolves only to a :class:`ProcessStep` inside a
    :class:`ProcessModel`; it never resolves to ``Equipment`` or to the
    physical-layer ``Port`` objects.
    """

    model_config = ConfigDict(extra="forbid")

    step: NonEmptyString
    port: NonEmptyString


class ProcessStream(BaseModel):
    """A directed process stream from one process port to another.

    A ProcessStream is a process-graph relationship with exactly one semantic
    source and one semantic target. It carries no flow, thermodynamic,
    composition, or physical-piping semantics in this iteration.
    """

    model_config = ConfigDict(extra="forbid")

    id: NonEmptyString
    name: str | None = None
    source: ProcessRef
    target: ProcessRef


def _default_process_streams() -> list[ProcessStream]:
    return []


class ProcessModel(BaseModel):
    """Container owning one process graph: process steps and their streams.

    ``ProcessModel`` is the independently constructible and structurally valid
    process-domain submodel (ADR-0005). Step ids and stream ids live in separate
    namespaces, so a step and a stream may share one string id. It validates
    only the structural rules S1-S4; it neither depends on the physical layer
    (``Equipment``, ``Port``, ``Connection``) nor does ``PlantModel`` duplicate
    that validation. ``PlantModel`` may own exactly one optional
    ``ProcessModel``; process and physical ids remain separate namespaces and no
    cross-layer rules exist yet.
    """

    model_config = ConfigDict(extra="forbid")

    steps: list[ProcessStep] = Field(default_factory=_default_process_steps)
    streams: list[ProcessStream] = Field(default_factory=_default_process_streams)

    @model_validator(mode="after")
    def _validate_unique_process_step_ids(self) -> Self:
        seen: set[str] = set()
        duplicates: list[str] = []
        for step in self.steps:
            if step.id in seen and step.id not in duplicates:
                duplicates.append(step.id)
            seen.add(step.id)
        if duplicates:
            raise ValueError(f"duplicate ProcessStep id(s): {', '.join(sorted(duplicates))}")
        return self

    @model_validator(mode="after")
    def _validate_unique_process_stream_ids(self) -> Self:
        seen: set[str] = set()
        duplicates: list[str] = []
        for stream in self.streams:
            if stream.id in seen and stream.id not in duplicates:
                duplicates.append(stream.id)
            seen.add(stream.id)
        if duplicates:
            raise ValueError(f"duplicate ProcessStream id(s): {', '.join(sorted(duplicates))}")
        return self

    @model_validator(mode="after")
    def _validate_process_stream_references(self) -> Self:
        ports_by_step = {step.id: {port.id for port in step.ports} for step in self.steps}
        errors: list[str] = []
        for index, stream in enumerate(self.streams):
            resolved = True
            for endpoint, ref in (("source", stream.source), ("target", stream.target)):
                if ref.step not in ports_by_step:
                    errors.append(f"streams[{index}].{endpoint}: unknown step '{ref.step}'")
                    resolved = False
                elif ref.port not in ports_by_step[ref.step]:
                    errors.append(
                        f"streams[{index}].{endpoint}: step '{ref.step}' has no port '{ref.port}'"
                    )
                    resolved = False
            if resolved and stream.source == stream.target:
                errors.append(
                    f"streams[{index}]: source and target endpoints are identical "
                    f"('{stream.source.step}.{stream.source.port}')"
                )
        if errors:
            raise ValueError("; ".join(errors))
        return self
