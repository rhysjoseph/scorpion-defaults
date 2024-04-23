from typing import Annotated

import typer

from src.scorpion.api import Session

app = typer.Typer()


@app.command()
def get(
    host: Annotated[str, typer.Argument(help="IP or hostname for device")],
    parameter: Annotated[str, typer.Argument(help="Parameter")],
    port: Annotated[str, typer.Option(help="Port for device")] = 8000,
):
    print(host, parameter, port)
    session = Session(host=host)
    session.get(parameter)

    print("start")
    session = Session(host=host, port=port)
    print(session.token)
    print(session.get("58"))


if __name__ == "__main__":
    app()
