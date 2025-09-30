import json
import os

PARENT_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(PARENT_DIR)


def ping(host, timeout=0.1):
    """
    Pings a host with a specified timeout and returns True if the host is reachable,
    False otherwise.
    """
    response = os.system("ping -c 1 -W " + str(timeout) + " " + host)
    return response == 0


def discover_devices(scorpions, mcms, switches, xips=None):
    """
    Ping through dicts of name->ip and return a combined online/offline map.
    """
    xips = xips or {}
    status = {}
    for groups in (scorpions, mcms, switches, xips):
        for device, ip_address in groups.items():
            if device == "Select" or not ip_address:
                continue
            status[device] = ping(ip_address)
    return status


def get_config():
    with open(f"{ROOT_DIR}/config/config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    scorpions = _get_scorpion_unit_list(config)
    return (
        config,
        scorpions,
        config["MCM_LIST"],
        config["SWITCH_LIST"],
        config["ARISTA_LIST"],
    )


def get_xip3901_unit_list(config):
    """
    Public helper to build XIP list; mirrors the scorpion list logic.
    """
    return _get_xip3901_unit_list(config)


def _get_scorpion_unit_list(config):
    if config.get("SCORPION_RANGE"):
        start = config.get("SCORPION_RANGE").split("-")[0]
        end = config.get("SCORPION_RANGE").split("-")[1]
        scorpion_list = {"Select": ""}
        scorpion_list.update(
            {
                f"{config['SCORPION_RANGE_NAME_PFIX']}{i:03}": f"{config['CONTROL_PREFIX']}.{int(i)}"
                for i in range(int(start), int(end) + 1)
            }
        )
        return scorpion_list
    else:
        return config["SCORPION_LIST"]


def _get_xip3901_unit_list(config):
    """
    Build { 'XIP3911-001': '10.169.60.1', ... } from XIP3901_* keys.
    """
    if config.get("XIP3901_RANGE"):
        start = int(config.get("XIP3901_RANGE").split("-")[0])
        end = int(config.get("XIP3901_RANGE").split("-")[1])
        name_pfix = config.get("XIP3901_RANGE_NAME_PFIX", "XIP3911-")
        ctrl_pfix = config.get("XIP3901_CONTROL_PREFIX", "10.169.60")
        listing = {"Select": ""}
        listing.update(
            {f"{name_pfix}{i:03}": f"{ctrl_pfix}.{i}" for i in range(start, end + 1)}
        )
        return listing
    # fallback static list if provided
    return config.get("XIP3901_LIST", {"Select": ""})