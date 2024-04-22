import base64
import json
import os
import sys
from typing import Optional

import requests
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict

from src.scorpion.utils import Url

load_dotenv(override=True)


class Session(BaseModel):
    """Creates a requests session to the UBS R2 api"""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    scheme: str = "http"
    host: str = "98.188.63.196"
    port: int = None
    version: str = "v.api/apis/"
    api_limit: float = 1.0 / 4
    max_records_per_request: int = 100
    session: Optional[requests.Session] = None
    url: Optional[str] = None
    timeout: float = 5
    token: str = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session = requests.Session()
        self.url = Url(
            scheme=self.scheme,
            host=self.host,
            port=self.port,
            version=self.version,
        )
        self.token = self._get_token()
        self.session.headers.update({"jwt": self.token})

    def _get_token(
        self,
    ):
        creds = json.dumps(
            {
                "username": os.environ["SCORPION_USER"],
                "password": os.environ["SCORPION_PASS"],
            }
        ).encode("ascii")
        creds = base64.b64encode(creds)
        creds = creds.decode("ascii")
        self.url.path = f"{self.version}BT/JWTCREATE/{creds}"
        response = requests.post(
            self.url.to_string(),
            verify=False,
            timeout=5,
        )
        token = response.json()["jwt"]
        return token

    def _process_response(self, response):

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            err_msg = str(exc)
            try:
                error_dict = response.json()
            except ValueError:
                pass
            else:
                if "error" in error_dict:
                    err_msg = f"{err_msg} [Error: {error_dict['error']}]"
            print(err_msg)
            raise exc

        return response.json()

    def _request(self, http_method: str, params=None, json_data=None, files=None):
        response = self.session.request(
            http_method,
            self.url.to_string(),
            params=params,
            json=json_data,
            files=files,
            timeout=self.timeout,
        )
        return self._process_response(response)

    def get(self, path, query=None):
        """GET request
        Args:
            path (str): The path to the endpoint
            query (dict): Optional The query parameters to be sent with the request
        Returns:
            dict: The response from the server as a dictionary

        Example:
            session.get("6501.1.0")
        """

        self.url.path = f"{self.version}EV/GET/parameter/{path}"
        self.url.query = query
        return self._request("GET")

    def post(self, query=None):
        """POST request
        Args:
            path (str): The path to the endpoint
            query (dict): OptionalThe query parameters to be sent with the request
        Returns:
            dict: The response from the server as a dictionary
        """
        self.url.path = f"{self.version}EV/SET/parameter"
        self.url.query = query
        return self._request("GET")

    def set_multicast(
        self,
        flow_type="VIDEO",
        trunk="RED",
        output_index=1,
        channel_index=1,
        multicast_ip=None,
    ):
        """Sets the multicast ip address for the specified output
        Args:
            flow_type (str): The type of flow to be set
            output_index (int): The index of the output to be set
            channel_index (int): The index of the channel to be set
            multicast_ip (str): The multicast ip address to be set
        """
        match trunk:
            case "RED":
                trunk = "0"
            case "BLUE":
                trunk = "1"
            case _:
                raise ValueError("Invalid trunk")

        match flow_type:
            case "AUDIO":
                if (
                    channel_index is None
                    or multicast_ip is None
                    or output_index is None
                ):
                    raise ValueError("Invalid arguments")
                set_variables = {
                    f"6550.{output_index-1}.{channel_index-1}.{trunk}": 1,  # enable
                    f"6551.{output_index-1}.{channel_index-1}.{trunk}": multicast_ip,
                    f"6552.{output_index-1}.{trunk}": 5504,  # udp out port
                    f"6553.{output_index-1}.{trunk}": 0,  # udp source port
                    f"6555.{output_index-1}.{trunk}": 0,  # vlan disable
                    f"6556.{output_index-1}.{trunk}": 1,  # vlan id (1-4095)
                    f"6659.{output_index-1}": 1,  # 0,1,2,3 Mono, Pair, Group, 8ch
                    f"6660.{output_index-1}": 0,  # 0,1 1ms 125us
                }
            case "VIDEO":
                if multicast_ip is None or output_index is None:
                    raise ValueError("Invalid arguments")
                set_variables = {
                    f"6550.{output_index-1}.{trunk}": 1,  # enable
                    f"6501.{output_index-1}.{trunk}": multicast_ip,
                    f"6502.{output_index-1}.{trunk}": 5004,  # udp out port
                    f"6503.{output_index-1}.{trunk}": 0,  # udp source port
                    f"6505.{output_index-1}.{trunk}": 0,  # vlan disable
                    f"6506.{output_index-1}.{trunk}": 1,  # vlan id (1-4095)
                    f"6658.{output_index-1}": 0,  # UHD Essence
                }
            case "META":
                if multicast_ip is None or output_index is None:
                    raise ValueError("Invalid arguments")
                set_variables = {
                    f"6600.{output_index-1}.{trunk}": 1,  # enable
                    f"6601.{output_index-1}.{trunk}": multicast_ip,
                    f"6602.{output_index-1}.{trunk}": 5504,  # udp out port
                    f"6603.{output_index-1}.{trunk}": 0,  # udp source port
                    f"6605.{output_index-1}.{trunk}": 0,  # vlan disable
                    f"6606.{output_index-1}.{trunk}": 1,  # vlan id (1-4095)
                }
            case _:
                raise ValueError("Invalid flow type")

        return set_variables

    def build_query(
        self,
        flow_type,
        output_index,
        channel_index,
        red_multicast_ip,
        blue_multicast_ip,
    ):
        """Builds query parameters for both red and blue trunks
        Args:
            flow_type (str): The type of flow to be set
            output_index (int): The index of the output to be set
            channel_index (int): The index of the channel to be set
            red_multicast_ip (str): The multicast ip address to be set for the red trunk
            blue_multicast_ip (str): The multicast ip address to be set for the blue trunk
        Returns:
            dict: The query parameters to be sent with the request
        """

        red = self.set_multicast(
            flow_type=flow_type.upper(),
            trunk="RED",
            output_index=output_index,
            channel_index=channel_index,
            multicast_ip=red_multicast_ip,
        )
        blue = self.set_multicast(
            flow_type=flow_type.upper(),
            trunk="BLUE",
            output_index=output_index,
            channel_index=channel_index,
            multicast_ip=blue_multicast_ip,
        )

        return red | blue
