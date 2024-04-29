import os
import subprocess

# from src.display import show
from src.net import adaptor


def _run_process(commands):
    return subprocess.run(commands, check=False, cwd="$HOME/ct-flows")


def update():
    print("Updating...")
    # show.text("Updating...")
    _run_process(["git", "fetch", "--all"])
    _run_process(["git", "reset", "--hard", "origin/master"])
    _run_process(["chmod", "+x", "$HOME/ct-flows/scripts/update.sh"])
    _run_process(["$HOME/ct-flows/scripts/update.sh"])
    print("Update complete.")
    return


def factory_reset():
    print("Resetting...")
    # show.text("Factory Resetting...")
    address = adaptor.Address()
    address.factory_reset()
    _run_process(["sudo", "reboot"])
    print("Reset complete.")
    return
