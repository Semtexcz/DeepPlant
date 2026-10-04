# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer

from deepplant import __version__
from deepplant.editor.app import (
    DEFAULT_PORT,
    EditorSetupError,
    load_editor_application,
    serve_editor,
)
from deepplant.io import PlantLoadError, load_plant

app = typer.Typer(
    help="DeepPlant - Git-native semantic engineering for process plants.",
    no_args_is_help=True,
)


@app.callback()
def cli() -> None:
    """DeepPlant - Git-native semantic engineering for process plants."""


@app.command()
def version() -> None:
    """Print the DeepPlant version."""
    typer.echo(f"DeepPlant {__version__}")


@app.command()
def validate(path: Path) -> None:
    """Validate a DeepPlant plant model YAML file."""
    try:
        model = load_plant(path)
    except PlantLoadError as exc:
        typer.echo(f"✗ {exc}", err=True)
        raise typer.Exit(code=1) from exc
    total_ports = sum(len(item.ports) for item in model.equipment)
    typer.echo("✓ valid DeepPlant model")
    typer.echo(f"✓ plant: {model.plant.id}")
    typer.echo(f"✓ equipment: {len(model.equipment)}")
    typer.echo(f"✓ ports: {total_ports}")
    typer.echo(f"✓ connections: {len(model.connections)}")


@app.command()
def ui(
    path: Path,
    symbol_role: Annotated[
        list[str] | None,
        typer.Option(
            "--symbol-role",
            help=(
                "Per-step presentation symbol role as STEP=ROLE (repeatable). "
                "A presentation override only: it is never written to the model "
                "or to YAML. The realistic fragment needs "
                "'--symbol-role PS-vessel=vessel'."
            ),
        ),
    ] = None,
    port: Annotated[
        int,
        typer.Option(help="Local port for the editor server (0 picks a free port)."),
    ] = DEFAULT_PORT,
    assets_dir: Annotated[
        Path | None,
        typer.Option(
            "--assets-dir",
            help="Directory with built editor assets. Defaults to ./apps/editor/dist.",
        ),
    ] = None,
) -> None:
    """Launch the local read-only Engineering Editor for a plant model."""
    try:
        overrides = _parse_symbol_role_overrides(symbol_role or [])
    except ValueError as exc:
        typer.echo(f"✗ {exc}", err=True)
        raise typer.Exit(code=1) from exc
    try:
        application = load_editor_application(
            path,
            symbol_role_overrides=overrides,
            assets_dir=assets_dir,
        )
    except (PlantLoadError, EditorSetupError) as exc:
        typer.echo(f"✗ {exc}", err=True)
        raise typer.Exit(code=1) from exc
    serve_editor(application, port=port, echo=typer.echo)


def _parse_symbol_role_overrides(entries: list[str]) -> dict[str, str]:
    """Parse ``--symbol-role STEP=ROLE`` entries into a presentation mapping."""
    overrides: dict[str, str] = {}
    for entry in entries:
        step_id, separator, role = entry.partition("=")
        if not separator or not step_id.strip() or not role.strip():
            raise ValueError(f"invalid --symbol-role {entry!r}: expected the form STEP=ROLE")
        overrides[step_id.strip()] = role.strip()
    return overrides


def main() -> None:
    if len(sys.argv) == 1:
        sys.argv.append("--help")
    app()


if __name__ == "__main__":
    main()
