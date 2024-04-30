import json
import os
from math import ceil

from requests.exceptions import RequestException

from src.scorpion.api import Call

PARENT_DIR = os.path.dirname(os.path.realpath(__file__))
SRC_DIR = os.path.dirname(PARENT_DIR)
ROOT_DIR = os.path.dirname(SRC_DIR)


class Defaults:
    """Connects to scorpion to set or read a list of defaults"""

    def __init__(self, name, host, port=80):
        self.name = name
        self.scorpion = Call(host=host, port=port)
        self.last_octet = host.split(".")[-1]
        self.config = self._get_config()
        self.default_params = self.get_user_defaults()

    def _get_config(self):
        with open(f"{ROOT_DIR}/config/config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        return config

    @staticmethod
    def _split_dict(dict_, max_keys):
        num_dicts = ceil(len(dict_) / max_keys)
        dict_size = ceil(len(dict_) / num_dicts)
        dicts = [
            {k: dict_[k] for k in list(dict_)[i : i + dict_size]}
            for i in range(0, len(dict_), dict_size)
        ]
        return dicts

    def _send_params(self, params):
        """Splits calls into chunks of 10 and loops through"""
        responses = []
        queries = self._split_dict(params, 10)
        for split_query in queries:
            response = self.scorpion.post(query=split_query)
            # print(response)
            responses.extend(response)
        fails = [item for item in responses if item.get("error")]
        return responses, fails

    def get_user_defaults(
        self,
    ):
        """Gets parameters from config file and sets NMOS Name and unit number
        Returns:
            dict: The default parameters
        """
        with open(f"{ROOT_DIR}/config/default_params.json", encoding="utf-8") as f:
            defaults = json.load(f)

        #  Set NMOS Name to alias upper case and remove rack number
        defaults["5204"] = self.name
        #  Set unit number as last octet of trunks
        defaults["6000.0"] = f"{self.config['TRUNK_A_PREFIX']}.{self.last_octet}"
        defaults["6000.1"] = f"{self.config['TRUNK_B_PREFIX']}.{self.last_octet}"

        return defaults

    def get_current(self):
        """Returns a dictionary of lists for current status of all default values"""
        current = {"name": [], "code": [], "value": [], "default": []}

        for key, value in self.default_params.items():
            try:
                call = self.scorpion.get(key)
            except RequestException as exc:
                return f"Scorpion API Call Failed: {exc}"
            current["name"].append(call.get("name"))
            current["code"].append(call.get("id"))
            current["value"].append(call.get("value"))
            current["default"].append(value)
        return current

    def set_defaults(self, factory=False):
        #  [TODO] Add ability to set all params if Evertz does not offer a factory default
        # if factory:
        #     set_factory_defaults(scorpion)

        # Clear all routes
        clear_routes = {}
        for i in range(32):
            clear_routes.update({f"3009.{i}": "0"})
        responses, fails = self._send_params(clear_routes)

        defaults = self._send_params(self.default_params)
        responses.extend(defaults[0])
        fails.extend(defaults[1])
        return "Defaults Set"
