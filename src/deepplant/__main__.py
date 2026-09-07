# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import sys
from pathlib import Path

import typer

from deepplant import __version__
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
    typer.echo("✓ valid DeepPlant model")
    typer.echo(f"✓ plant: {model.plant.id}")
    typer.echo(f"✓ equipment: {len(model.equipment)}")


def main() -> None:
    if len(sys.argv) == 1:
        sys.argv.append("--help")
    app()


if __name__ == "__main__":
    main()
