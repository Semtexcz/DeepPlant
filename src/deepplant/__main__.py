# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import sys

import typer

from deepplant import __version__

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


def main() -> None:
    if len(sys.argv) == 1:
        sys.argv.append("--help")
    app()


if __name__ == "__main__":
    main()
