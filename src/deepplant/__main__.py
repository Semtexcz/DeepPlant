# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer

from deepplant import __version__
from deepplant.editor import DEFAULT_PORT
from deepplant.editor.launcher import (
    ASSETS_DIR_HELP,
    SYMBOL_ROLE_HELP,
    EditorLaunchError,
    run_editor,
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
        typer.Option("--symbol-role", help=SYMBOL_ROLE_HELP),
    ] = None,
    port: Annotated[
        int,
        typer.Option(help="Local port for the editor server (0 picks a free port)."),
    ] = DEFAULT_PORT,
    assets_dir: Annotated[
        Path | None,
        typer.Option("--assets-dir", help=ASSETS_DIR_HELP),
    ] = None,
) -> None:
    """Launch the local read-only Engineering Editor for a plant model."""
    try:
        run_editor(
            path,
            symbol_role_entries=symbol_role or [],
            port=port,
            assets_dir=assets_dir,
        )
    except EditorLaunchError as exc:
        typer.echo(f"✗ {exc}", err=True)
        raise typer.Exit(code=1) from exc


def main() -> None:
    if len(sys.argv) == 1:
        sys.argv.append("--help")
    app()


if __name__ == "__main__":
    main()
