from typing import Annotated

import typer

from src.scorpion.api import Session

app = typer.Typer()


@app.command()
def get(
    host: Annotated[str, typer.Argument(help="IP or hostname for device")],
    parameter: Annotated[str, typer.Argument(help="Parameter")],
):
    session = Session(host=host)
    session.get(parameter)


if __name__ == "__main__":
    app()
