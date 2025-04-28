"""API Interface to Evertz Scorpion"""

from src.prism.session import Session


class Call(Session):
    """Creates a requests session to the Evertz Scorpion api"""

    def get_channels(self):
        """GET request

        """

        self.url.path = f"{self.version}getpresets"

        return self._request("GET")

    def load_preset(self, number):
        """GET request

        """


        self.url.path =  f"{self.version}local/A_2110"
   
        return self._request("GET")
    

    def monitor_all_channels(self, state="on"):
        """GET request

        """
        command="monitor"
        if (state == "off"):
            command="unMonitor"
        channel_ids = [source['ChannelSource']['id'] for source in self.get_channels()]
        for channel_id in channel_ids:            
            self.url.path = f"{self.version}channels/command/{command}/{channel_id}/.json"
            self._request("GET")
        return 