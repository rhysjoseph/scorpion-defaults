import json
import re
from math import ceil

from src.scorpion.api import Call


def parse_ranges(string):
    matches = re.findall(r"\[(\d+)\.\.(\d+)\]", string)
    return matches


def _split_dict(dict_, max_keys):
    num_dicts = ceil(len(dict_) / max_keys)
    dict_size = ceil(len(dict_) / num_dicts)
    dicts = [
        {k: dict_[k] for k in list(dict_)[i : i + dict_size]}
        for i in range(0, len(dict_), dict_size)
    ]
    return dicts


def set_factory_defaults(scorpion):
    with open("src/scorpion/parameters_reference.json", "r") as f:
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


def get_user_defaults():
    with open("src/scorpion/default_parameters.json", encoding="utf-8") as f:
        defaults = json.load(f)
    return defaults

def get_nmos_name(name):
    name = name.upper()
    name = name.split("-")
    return f"{name[0]}-{name[2]}", name[2]


def default_routes():
    routes = {}
    for i in range(32):
        if 4 <= i <= 11:
            routes.update({f"3009.{i}": f"{i+1+12}"})
        elif 16 <= i <= 23:
            routes.update({f"3009.{i}": f"{i+1-12}"})
        else:
            routes.update({f"3009.{i}": "0"})
    return routes


def send_params(scorpion, params):
    responses = []
    queries = _split_dict(params, 10)
    for split_query in queries:
        response = scorpion.post(query=split_query)
        print(response)
        responses.extend(response)
    fails = [item for item in responses if item.get("error")]

    return responses, fails


def set_defaults(host, port=80, factory=False):
    try:
        scorpion = Call(host=host, port=port)
    except Exception:
        return f"Scorpion not found: {host}"
    try:
        alias_name = scorpion.get("55").get("value")
    except Exception:
        return "API Not Enabled!"

    if factory:
        set_factory_defaults(scorpion)
    defaults = get_user_defaults()

    defaults["5204"], unit_number = get_nmos_name(alias_name)
    defaults["6000.0"] = f"{defaults['6000.0']}{int(unit_number)}"
    defaults["6000.1"] = f"{defaults['6000.1']}{int(unit_number)}"

    for i in range(32):
        defaults.update({f"3009.{i}": "0"})
    responses, fails = send_params(scorpion, defaults)
    routes = default_routes()
    routes_response = send_params(scorpion, routes)
    responses.extend(routes_response[0])
    fails.extend(routes_response[1])
    return "Defaults Set"


def get_current(host, port=80):
    current = {"name": [], "code": [], "value": [], "default": []}
    try:
        scorpion = Call(host=host, port=port)
    except Exception as exc:
        return f"Scorpion Not Found!: \n{exc}"

    defaults = get_user_defaults()
    try:
        alias_name = scorpion.get("55").get("value")
    except Exception as exc:
        return f"Failed (Maybe API Enable??): {exc}"
    defaults["5204"], unit_number = get_nmos_name(alias_name)
    defaults["6000.0"] = f"{defaults['6000.0']}{int(unit_number)}"
    defaults["6000.1"] = f"{defaults['6000.1']}{int(unit_number)}"

    for key, value in defaults.items():
        try:
            call = scorpion.get(key)
        except Exception:
            return False
        current["name"].append(call.get("name"))
        current["code"].append(call.get("id"))
        current["value"].append(call.get("value"))
        current["default"].append(value)
    return current
