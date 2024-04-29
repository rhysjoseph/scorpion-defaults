"""This module provides the CLI Base."""

# src/cli/cli.py

from typing import Optional

import typer

from src import __app_name__, __version__
from src.cli import net, scorpion
from src.settings import software

app = typer.Typer()
app.add_typer(net.app, name="net")
app.add_typer(scorpion.app, name="scorpion")


@app.command()
def update():
    confirm = typer.confirm("This will update all software to current version. OK?")
    if not confirm:
        print("Aborting...")
        raise typer.Abort()
    print("Updating Software")
    software.update()


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application's version and exit.",
        callback=_version_callback,
        is_eager=True,
    )
) -> None:
    return
