# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Dependent physical piping realization layer (ADR-0011).

`PipingLine` -> `PipingSegment` -> `PipingRealization` references identified
`Connection` objects instead of restating endpoints. This layer is useful on
its own; it depends on connection identity, never on the process graph, and
carries no presentation or flow semantics.
"""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from deepplant.model.validation import NonEmptyString, find_duplicate_ids


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
        duplicates = find_duplicate_ids(segment.id for segment in self.segments)
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
        duplicates = find_duplicate_ids(line.id for line in self.lines)
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
