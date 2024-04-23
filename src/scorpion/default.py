import json
import re

from src.scorpion.api import Call


def parse_ranges(string):
    matches = re.findall(r"\[(\d+)\.\.(\d+)\]", string)
    return matches


def set_factory_defaults(scorpion):
    with open("src/scorpion/parameters.json", "r") as f:
        parameters = json.load(f)
    for key in parameters:
        control_indexes = parameters[key].get("control-indexes")
        if "has indexes:" in control_indexes:
            controls = parse_ranges(control_indexes)
            if len(controls) == 1:
                top = controls[0][1]
                if top == "7":
                    for i in range(int(top)):
                        print(scorpion.post(f"{key}.{i}"))
        else:
            print(scorpion.post(key))


factory_defaults = ["115"]
factory_defaults_8 = ["6659"]
defaults = {
    "59": 1,  # fpga to 2110
    "5100": 127,  # network_ptp_domain
    "120": 1,  # time_source
    "122": -7,  # time_offset
    "123": 0,  # time_daylight
    "124": "10.244.240.1",  # time_server
    "5200": 1,  # nmos_support
    "5201": 1,  # nmos_dns
    "5202": "testsuite.nmos.tv",  # nmos_domain
    "5203": "172.16.126.121",  # nmos_name_server
    "5204": "get_name",  # nmos_device_name
    "5206": 1,  # nmos_endpoint
    "6000.0": "10.101.245.",  # trunk_ip
    "6001.0": "255.255.0.0",  # trunk_net_mask
    "6002.0": "10.101.0.1",  # trunk_gateway
    "6018.0": 2,  # data rate
    "6000.1": "10.102.245.",  # trunk_ip
    "6001.1": "255.255.0.0",  # trunk_net_mask
    "6002.1": "10.102.0.1",  # trunk_gateway
    "6018.1": 2,  # data rate
    "165": 1,  # ref sync source
    "6213.0": 1,  # input video redundancy mode non-invertive
    "6213.1": 1,
    "6213.2": 1,
    "6213.3": 1,
    "6213.4": 1,
    "6213.5": 1,
    "6213.6": 1,
    "6213.7": 1,
    "6659.0": 1,  # output audio mapping pair
    "6659.1": 1,
    "6659.2": 1,
    "6659.3": 1,
    "6659.4": 1,
    "6659.5": 1,
    "6659.6": 1,
    "6659.7": 1,
}


def get_nmos_name(scorpion):
    name = scorpion.get("55").get("value")
    name = name.upper()
    name = name.split("-")
    return f"{name[0]}-{name[2]}", name[2]


def set_defaults(host, port=80, factory=False):
    scorpion = Call(host=host, port=port)
    if factory:
        set_factory_defaults(scorpion)
    defaults["5204"], unit_number = get_nmos_name(scorpion)
    defaults["6000.0"] = f"{defaults['6000.0']}{unit_number}"
    defaults["6000.1"] = f"{defaults['6000.1']}{unit_number}"
    for key, value in defaults.items():
        print(scorpion.post({key: value}))
    return "Defaults Set"
