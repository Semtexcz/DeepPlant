# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""YAML serialization boundary for DeepPlant plant models.

YAML and file I/O stay outside the semantic domain model (ADR-0004). Loading
validates YAML through Pydantic into typed models; saving serializes a
:class:`PlantModel` to canonical, semantic YAML. Expected failure modes raise
:class:`PlantLoadError` or :class:`PlantSaveError` with a concise message so
callers such as the CLI can report normal user errors without raw tracebacks.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from deepplant.model import PlantModel

__all__ = ["PlantLoadError", "PlantSaveError", "load_plant", "save_plant"]


class PlantLoadError(Exception):
    """Raised when a plant YAML file cannot be read or validated."""


class PlantSaveError(Exception):
    """Raised when a plant YAML file cannot be written."""


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


def save_plant(model: PlantModel, path: str | Path) -> None:
    """Serialize ``model`` to canonical, semantic UTF-8 YAML at ``path``.

    ``load_plant(save_plant(model))`` is semantically equal to ``model``.
    Serialization is canonical, not textual: comments, quoting, blank lines,
    anchors, aliases, and the original key style are deliberately not
    preserved. Optional fields whose value is ``None`` are omitted, a
    ``process`` value of ``None`` is omitted as a missing ``process`` key, and
    an explicitly empty ``ProcessModel`` stays present. Keys follow the Pydantic
    model declaration order, so the output is deterministic.
    """
    destination = Path(path)
    document = model.model_dump(mode="python", exclude_none=True)
    text = yaml.safe_dump(document, sort_keys=False, allow_unicode=True)
    if not text.endswith("\n"):
        text += "\n"
    try:
        destination.write_text(text, encoding="utf-8")
    except OSError as exc:
        reason = exc.strerror or str(exc)
        raise PlantSaveError(f"cannot write plant file '{destination}': {reason}") from exc


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
