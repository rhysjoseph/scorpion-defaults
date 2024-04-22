"""Entry point script."""

# src/cli/__init__.py

from src import __app_name__
from src.cli import cli


def main():
    cli.app(prog_name=__app_name__)


if __name__ == "__main__":
    main()
