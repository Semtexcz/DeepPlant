# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""YAML loading boundary for DeepPlant plant models.

YAML and file I/O stay outside the semantic domain model (ADR-0004). Every
expected failure mode raises :class:`PlantLoadError` with a concise message so
callers such as the CLI can report normal user errors without raw tracebacks.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from deepplant.model import PlantModel

__all__ = ["PlantLoadError", "load_plant"]


class PlantLoadError(Exception):
    """Raised when a plant YAML file cannot be read or validated."""


def load_plant(path: str | Path) -> PlantModel:
    """Load and validate a DeepPlant plant model from a YAML file."""
    source = Path(path)

    try:
        text = source.read_text(encoding="utf-8")
    except OSError as exc:
        reason = exc.strerror or str(exc)
        raise PlantLoadError(f"cannot read plant file '{source}': {reason}") from exc

    try:
        document: object = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise PlantLoadError(f"invalid YAML in '{source}': {_first_line(exc)}") from exc

    if document is None:
        raise PlantLoadError(f"invalid DeepPlant model in '{source}': empty document")
    if not isinstance(document, dict):
        kind = type(document).__name__
        raise PlantLoadError(
            f"invalid DeepPlant model in '{source}': top level must be a mapping, got {kind}"
        )

    try:
        return PlantModel.model_validate(document)
    except ValidationError as exc:
        raise PlantLoadError(
            f"invalid DeepPlant model in '{source}': {_format_validation_errors(exc)}"
        ) from exc


def _first_line(exc: BaseException) -> str:
    lines = str(exc).strip().splitlines()
    return lines[0] if lines else type(exc).__name__


def _format_validation_errors(exc: ValidationError) -> str:
    parts: list[str] = []
    for error in exc.errors(include_url=False):
        location = ".".join(str(part) for part in error["loc"])
        context = error.get("ctx")
        cause: object = context.get("error") if context else None
        if isinstance(cause, BaseException):
            message = str(cause)
        else:
            message = error["msg"]
        parts.append(f"{location}: {message}" if location else message)
    return "; ".join(parts)
