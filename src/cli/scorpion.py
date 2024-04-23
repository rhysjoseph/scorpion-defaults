from typing import Annotated, List
import os
import dotenv
import typer

from src.scorpion.api import Call

app = typer.Typer()
dotenv_file = dotenv.find_dotenv()
dotenv.load_dotenv(dotenv_file, override=True)

def _get_env(key):
    return f"{key}: {os.environ.get(key)}"

def _set_env(key, value):
    os.environ[key] = value
    dotenv.set_key(dotenv_file, key, os.environ[key])

@app.command()
def session(
    host: Annotated[str, typer.Argument(help="IP or hostname for device")] = None,
    port: Annotated[str, typer.Option(help="Port for device")] = 80,
):

    if host:
        _set_env("SCORPION_HOST", host)
    if port != "80":
        _set_env("SCORPION_PORT", port)
    
    print(_get_env("SCORPION_HOST"))
    print(_get_env("SCORPION_PORT"))

@app.command()
def get(
    parameter: Annotated[str, typer.Argument(help="Parameter")] = None,
    host: Annotated[str, typer.Option(help="IP or hostname for device")] = os.environ.get("SCORPION_HOST"),    
    port: Annotated[str, typer.Option(help="Port for device")] = os.environ.get("SCORPION_PORT"),
):
    call = Call(host=host, port=port)
    print(call.get(parameter))

if __name__ == "__main__":
    app()

@app.command()
def post(
    parameters: Annotated[List[str], typer.Argument(help="Parameter")] = None,
    host: Annotated[str, typer.Option(help="IP or hostname for device")] = os.environ.get("SCORPION_HOST"),    
    port: Annotated[str, typer.Option(help="Port for device")] = os.environ.get("SCORPION_PORT"),
):
    call = Call(host=host, port=port)
    query = {}
    for parameter in parameters:
        param_split = parameter.split("=")
        query.update({param_split[0] :param_split[1]})
    print(call.post(query))

if __name__ == "__main__":
    app()
