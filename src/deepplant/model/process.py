# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Process graph layer of the semantic model (ADR-0002, ADR-0005, ADR-0009).

The independently constructible process-domain submodel: `ProcessStep` with
its `ProcessPort`s, and binary directed `ProcessStream`s between them. It
owns the S1-S4 structural boundary and depends on neither the physical layer
nor any presentation concept (ADR-0009).
"""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from deepplant.model.validation import NonEmptyString, find_duplicate_ids


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
        duplicates = find_duplicate_ids(port.id for port in self.ports)
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
        duplicates = find_duplicate_ids(step.id for step in self.steps)
        if duplicates:
            raise ValueError(f"duplicate ProcessStep id(s): {', '.join(duplicates)}")
        return self

    @model_validator(mode="after")
    def _validate_unique_process_stream_ids(self) -> Self:
        duplicates = find_duplicate_ids(stream.id for stream in self.streams)
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
