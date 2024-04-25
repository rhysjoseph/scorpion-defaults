import platform
import subprocess

from fping import FastPing

from src.scorpion.default import set_defaults


def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """

    # Option for the number of packets as a function of
    param = "-n" if platform.system().lower() == "windows" else "-c"

    # Building the command. Ex: "ping -c 1 google.com"
    command = ["fping", host]

    return subprocess.call(command) == 0


def units_online():
    units = {}
    for i in range(1, 37):
        ping_response = ping(host=f"10.244.245.{i}")
        if ping_response:
            units.update({f"SCPN6-{i:03}": 1})
        else:
            units.update({f"SCPN6-{i:03}": 0})
    print(units)


for i in range(1, 37):
    print(set_defaults(f"10.244.245.{i}"))
