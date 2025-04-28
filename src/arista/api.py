"""API Interface to Arista"""

from src.arista.session import Session
import pyeapi


class Call:
    """Creates a requests session to the Arista api"""

    def __init__(self) -> None:
        self.interfaces = self._list_interfaces()

    def _list_interfaces(self):
        node = pyeapi.connect_to("onetwentyeight")
        return node.enable(["show interfaces"])

    def get_status(self):
        """
        Extracts interface names and their status from a list of dictionaries.

        Args:
            data: A list of dictionaries containing network interface information.

        Returns:
            A dictionary with interface names as keys and interfaceStatus as values.
        """
        interface_status_dict = {}

        for item in self.interfaces:
            interfaces = item["result"]["interfaces"]
            for interface_name, interface_data in interfaces.items():
                interface_status_dict[interface_name] = interface_data[
                    "interfaceStatus"
                ]
        return interface_status_dict

    def get_port(self, port: int):
        """GET request"""

        self.url.path = f"{self.version}"
        node = pyeapi.connect_to("onetwentyeight")
        return node.config(["interface Ethernet10", "shutdown"])
        # data = {
        #     "jsonrpc": "2.0",
        #     "method": "runCmds",
        #     "params": {
        #         "version": 1,
        #         "cmds": [f"show interfaces Ethernet {port}"],
        #         "format": "json",
        #         "timestamps": False,
        #         "autoComplete": False,
        #         "expandAliases": False,
        #         "stopOnError": True,
        #         "streaming": False,
        #         "includeErrorDetail": False,
        #     },
        #     "id": "EapiExplorer-1",
        # }
        # return self._request("POST", json_data=data)

    def enable_port(self, port_name: str, enable: bool = True):
        """GET request"""
        node = pyeapi.connect_to("onetwentyeight")
        shutdown = "no shutdown" if enable else "shutdown"
        return node.config([f"interface {port_name}", shutdown])
