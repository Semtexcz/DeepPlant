# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Framework-independent Engineering Editor application layer (Issues #75, #79).

This module owns the read-only editor state for one loaded DeepPlant project:
projection views, validation reporting, canonical symbol resolution, and built-SPA
asset resolution. It is deliberately usable and testable from plain Python: it
imports no FastAPI, Starlette, or Uvicorn, and it never depends on the HTTP
transport in :mod:`deepplant.editor.api`.

Dependency direction (one-way)::

    deepplant.editor.api  (FastAPI/Uvicorn transport)
        ↓
    deepplant.editor.application  (this module)
        ↓
    projection / renderer / semantic model

Semantic validity is always the ordinary DeepPlant loader verdict. A
``EditorProjectionView`` with no ``projection`` is a limitation of the Process/PFD
view only; it never recasts a semantically valid model as invalid.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from deepplant.editor.projection import (
    ProcessPfdProjection,
    ProcessPfdProjectionError,
    ValidationStatus,
    project_process_pfd,
    projection_to_dict,
)
from deepplant.io import load_plant
from deepplant.model import PlantModel
from deepplant.render import ProcessRenderError, read_process_symbol_svg

__all__ = [
    "EditorApplication",
    "EditorProjectionView",
    "EditorSetupError",
    "load_editor_application",
    "resolve_assets_dir",
]

#: Directory name holding the built SPA inside the application bundle.
PACKAGED_SPA_DIRNAME: str = "dist"

#: Path from the repository root to the development SPA build.
_CHECKOUT_SPA_PARTS: tuple[str, ...] = ("apps", "editor", "dist")


class EditorSetupError(Exception):
    """Raised when the local editor cannot be started for the selected project."""


@dataclass(frozen=True)
class EditorProjectionView:
    """Transport-neutral result of projecting one model to a Process/PFD view.

    ``validation`` always reflects the semantic verdict from the ordinary
    DeepPlant loader. A missing ``projection`` is therefore a limitation of this
    view only: it never recasts a semantically valid model as invalid, and the
    separate ``error`` carries the presentation failure text.
    """

    validation: ValidationStatus
    projection: ProcessPfdProjection | None
    error: str | None

    @property
    def projectable(self) -> bool:
        return self.projection is not None

    def to_envelope(self) -> dict[str, object]:
        """Return the JSON-ready response envelope shared by every transport."""
        envelope: dict[str, object] = {
            "validation": {
                "valid": self.validation.valid,
                "message": self.validation.message,
            },
            "projection": None if self.projection is None else projection_to_dict(self.projection),
        }
        if self.error is not None:
            envelope["error"] = self.error
        return envelope


@dataclass(frozen=True)
class EditorApplication:
    """Read-only local application state for one loaded DeepPlant project."""

    project_path: Path
    model: PlantModel
    assets_dir: Path
    symbol_pack: str = "basic"
    symbol_role_overrides: Mapping[str, str] | None = None

    def projection_view(self) -> EditorProjectionView:
        """Project the loaded model to a Process/PFD view result.

        Semantic validation truth comes from :func:`load_plant`: this application
        only exists after that loader returned a valid ``PlantModel``. A
        Process/PFD projection or rendering error is therefore reported
        separately, as a limitation of this view.
        """
        try:
            projection = project_process_pfd(
                self.model,
                symbol_pack=self.symbol_pack,
                symbol_role_overrides=self.symbol_role_overrides,
            )
        except (ProcessPfdProjectionError, ProcessRenderError) as exc:
            return EditorProjectionView(
                validation=ValidationStatus(valid=True, message="Valid"),
                projection=None,
                error=str(exc),
            )
        return EditorProjectionView(
            validation=projection.validation,
            projection=projection,
            error=None,
        )

    def symbol_svg(self, symbol_role: str) -> str:
        """Return the canonical packaged SVG text for one symbol role."""
        return read_process_symbol_svg(self.symbol_pack, symbol_role)


def resolve_assets_dir(explicit: Path | None) -> Path | None:
    """Return the directory holding the built editor assets, or ``None``.

    Resolution order:

    1. an explicit ``--assets-dir`` path (development and testing);
    2. the SPA shipped inside the application bundle
       (``deepplant/editor/dist``), which the standalone packaging stage maps
       into the frozen application and which the base Python wheel never
       carries;
    3. the development checkout build, resolved from this module's location
       rather than the current working directory.

    A candidate only counts when it actually contains ``index.html``, so a
    missing build is reported honestly instead of serving an empty canvas. No
    candidate depends on the process working directory, so a packaged
    application never falls back to a checkout by accident.
    """
    for candidate in _asset_dir_candidates(explicit):
        if (candidate / "index.html").is_file():
            return candidate
    return None


def _asset_dir_candidates(explicit: Path | None) -> Iterator[Path]:
    """Yield built-SPA candidates in resolution order."""
    if explicit is not None:
        yield explicit
        return
    packaged = _packaged_assets_dir()
    if packaged is not None:
        yield packaged
    yield _checkout_assets_dir()


def _packaged_assets_dir() -> Path | None:
    """Return the SPA carried by the application itself, or ``None``.

    The assets are held as a package resource, using the same
    ``importlib.resources`` mechanism as the canonical symbol pack, so the
    application never names a packaging tool and works from a frozen bundle the
    same way it works from an installed distribution. Only a real filesystem
    directory can back static file serving.
    """
    candidate = resources.files("deepplant.editor").joinpath(PACKAGED_SPA_DIRNAME)
    if isinstance(candidate, Path) and candidate.is_dir():
        return candidate
    return None


def _checkout_assets_dir() -> Path:
    """Return the source-checkout SPA build path, derived from this module.

    The path is computed from the installed module's own location, so an
    ordinary source run finds ``apps/editor/dist`` no matter which directory it
    was started from. In an installed wheel the derived path simply does not
    exist.
    """
    # .../src/deepplant/editor/application.py -> repository root
    return Path(__file__).resolve().parents[3].joinpath(*_CHECKOUT_SPA_PARTS)


def load_editor_application(
    project_path: Path,
    *,
    symbol_role_overrides: Mapping[str, str] | None = None,
    symbol_pack: str = "basic",
    assets_dir: Path | None = None,
) -> EditorApplication:
    """Load one project through the DeepPlant loader and resolve editor assets.

    Raises:
        PlantLoadError: If the project file cannot be read or validated. The
            message is the normal DeepPlant user-facing error text.
        EditorSetupError: If the built editor assets cannot be found.
    """
    model = load_plant(project_path)
    resolved_assets = resolve_assets_dir(assets_dir)
    if resolved_assets is None:
        raise EditorSetupError(
            "editor frontend assets were not found; in a source checkout build them "
            "first with `make frontend-build` (or `cd apps/editor && pnpm build`), "
            "otherwise pass an explicit --assets-dir. A standalone DeepPlant Editor "
            "application always carries them."
        )
    return EditorApplication(
        project_path=Path(project_path),
        model=model,
        assets_dir=resolved_assets,
        symbol_pack=symbol_pack,
        symbol_role_overrides=symbol_role_overrides,
    )
