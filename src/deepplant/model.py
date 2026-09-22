# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Semantic domain model for DeepPlant plants.

This module is the product core (ADR-0002). It must not import the CLI, YAML,
file I/O, rendering, or any other consumer-specific concern.

Semantic input is fail-fast: models forbid unknown fields, and semantic strings
such as ids and equipment types must be non-empty, non-whitespace values.
"""

from collections.abc import Iterable
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

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

NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


def _find_duplicate_ids(ids: Iterable[str]) -> list[str]:
    """Return every id that occurs more than once, once each and sorted.

    Private helper only: each model keeps its own uniqueness rule, message, and
    namespace, so duplicate-id validation stays a local domain statement.
    """
    seen: set[str] = set()
    duplicates: set[str] = set()

    for id_ in ids:
        if id_ in seen:
            duplicates.add(id_)
        else:
            seen.add(id_)

    return sorted(duplicates)


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
        duplicates = _find_duplicate_ids(port.id for port in self.ports)
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


def _default_connections() -> list[Connection]:
    return []


def _default_equipment() -> list[Equipment]:
    return []


class PipingRealization(BaseModel):
    """Statement that one physical adjacency has a piping realization.

    A realization is not an edge with its own endpoints: it refers to one
    identified :class:`Connection` by id and states how that adjacency is
    realized without restating any ``PortRef`` (ADR-0011). The first-slice
    ``kind`` vocabulary is deliberately closed:

    ``kind`` omitted or ``"pipe"``
        the adjacency is pipe-realized;
    ``kind`` ``"direct"``
        the adjacency is directly realized, without a pipe body.

    No ``PipingRealization`` at all means the realization is *not modelled*,
    which stays distinct from ``kind: pipe``. No canonical ``Pipe`` class
    exists: an elementary pipe piece already has the extent of a
    ``Connection`` because inline items terminate adjacencies.
    """

    model_config = ConfigDict(extra="forbid")

    connection: NonEmptyString
    kind: Literal["pipe", "direct"] = "pipe"


def _default_realizations() -> list[PipingRealization]:
    return []


class PipingSegment(BaseModel):
    """The first-slice property boundary of a piping line.

    ``id`` is canonical identity local to the owning :class:`PipingLine`.
    ``segment_number`` is an optional human/external engineering designation
    and never becomes the canonical identity. The property strings
    (``nominal_diameter``, ``piping_class``, ``fluid_code``) are optional open
    strings: an absent property means *not specified yet*, not a default, and
    no quantity/unit typing exists yet.

    A segment must contain at least one realization (P5), because an empty
    property boundary carries no engineering statement. In this first slice a
    segment boundary must coincide with a ``Connection`` boundary;
    mid-connection property breaks (DEXPI ``PropertyBreak``) are not
    representable yet.
    """

    model_config = ConfigDict(extra="forbid")

    id: NonEmptyString
    segment_number: str | None = None
    nominal_diameter: str | None = None
    piping_class: str | None = None
    fluid_code: str | None = None
    realizations: list[PipingRealization] = Field(default_factory=_default_realizations)

    @model_validator(mode="after")
    def _validate_at_least_one_realization(self) -> Self:
        if not self.realizations:
            raise ValueError(f"segment '{self.id}' must contain at least one realization")
        return self


def _default_segments() -> list[PipingSegment]:
    return []


class PipingLine(BaseModel):
    """A piping line grouping one or more property-bounded segments.

    ``id`` is canonical line identity. ``line_number`` is an optional human
    designation (for example a company line number): it is never the canonical
    identity, is never required, and no uniqueness or syntax rule is imposed on
    it. ``name`` is optional.

    ``PipingSegment`` ids are unique within the owning line (P2) and nothing
    more, so the same segment id may legitimately appear in different lines:
    segment identity is owner-local.
    """

    model_config = ConfigDict(extra="forbid")

    id: NonEmptyString
    line_number: str | None = None
    name: str | None = None
    segments: list[PipingSegment] = Field(default_factory=_default_segments)

    @model_validator(mode="after")
    def _validate_unique_segment_ids(self) -> Self:
        duplicates = _find_duplicate_ids(segment.id for segment in self.segments)
        if duplicates:
            raise ValueError(
                f"piping line '{self.id}' has duplicate segment id(s): {', '.join(duplicates)}"
            )
        return self


def _default_lines() -> list[PipingLine]:
    return []


class PipingModel(BaseModel):
    """Optional container owning the piping realization of physical topology.

    Unlike ``ProcessModel``, ``PipingModel`` is a dependent layer (ADR-0011):
    it references :class:`Connection` objects that belong to the physical
    layer, so its connection references are resolved cross-layer by
    :class:`PlantModel` (P3). This model owns the rules that need only piping
    context: unique line identity (P1) and the first-slice invariant that one
    ``Connection`` is referenced by at most one realization across every
    segment of every line (P4). P4 is a deliberate first-slice 1:1 invariant,
    not a claim about physical engineering; parallel, as-built, and revision
    realizations are deferred.
    """

    model_config = ConfigDict(extra="forbid")

    lines: list[PipingLine] = Field(default_factory=_default_lines)

    @model_validator(mode="after")
    def _validate_unique_line_ids(self) -> Self:
        duplicates = _find_duplicate_ids(line.id for line in self.lines)
        if duplicates:
            raise ValueError(f"duplicate PipingLine id(s): {', '.join(duplicates)}")
        return self

    @model_validator(mode="after")
    def _validate_single_realization_per_connection(self) -> Self:
        seen: set[str] = set()
        duplicates: list[str] = []
        for line in self.lines:
            for segment in line.segments:
                for realization in segment.realizations:
                    if realization.connection in seen and realization.connection not in duplicates:
                        duplicates.append(realization.connection)
                    seen.add(realization.connection)
        if duplicates:
            raise ValueError(
                f"duplicate realization connection reference(s): {', '.join(sorted(duplicates))}"
            )
        return self


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
        duplicates = _find_duplicate_ids(item.id for item in self.equipment)
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
        duplicates = _find_duplicate_ids(connection.id for connection in self.connections)
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
        duplicates = _find_duplicate_ids(port.id for port in self.ports)
        if duplicates:
            raise ValueError(f"step '{self.id}' has duplicate port id(s): {', '.join(duplicates)}")
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
        duplicates = _find_duplicate_ids(step.id for step in self.steps)
        if duplicates:
            raise ValueError(f"duplicate ProcessStep id(s): {', '.join(duplicates)}")
        return self

    @model_validator(mode="after")
    def _validate_unique_process_stream_ids(self) -> Self:
        duplicates = _find_duplicate_ids(stream.id for stream in self.streams)
        if duplicates:
            raise ValueError(f"duplicate ProcessStream id(s): {', '.join(duplicates)}")
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
