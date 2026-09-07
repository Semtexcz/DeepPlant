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

__all__ = ["Equipment", "Plant", "PlantModel"]

NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Plant(BaseModel):
    """A process plant being engineered."""

    model_config = ConfigDict(extra="forbid")

    id: NonEmptyString
    name: str | None = None


class Equipment(BaseModel):
    """A single equipment item inside a plant."""

    model_config = ConfigDict(extra="forbid")

    id: NonEmptyString
    type: NonEmptyString
    name: str | None = None


def _default_equipment() -> list[Equipment]:
    return []


class PlantModel(BaseModel):
    """Root container of a DeepPlant semantic model."""

    model_config = ConfigDict(extra="forbid")

    plant: Plant
    equipment: list[Equipment] = Field(default_factory=_default_equipment)

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
