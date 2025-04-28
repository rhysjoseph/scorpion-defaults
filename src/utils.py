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
    if response == 0:
        return True
    else:
        return False


def discover_devices(scorpions, mcms, switches):
    devices = scorpions | mcms | switches
    status = {}
    for device in devices:
        ip_address = devices[device]
        if ping(ip_address):
            status[device] = True
        else:
            status[device] = False
    print(status)
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
