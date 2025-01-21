"""API Interface to Evertz Scorpion"""

from src.mcm.session import Session


class Call(Session):
    """Creates a requests session to the Evertz Scorpion api"""

    def get_channels(self):
        """GET request

        """

        self.url.path = f"{self.version}channels/config/.json"

        return self._request("GET")

    def monitor_channel(self, channel_id, state="on"):
        """GET request

        """
        command="monitor"
        if (state == "off"):
            command="unMonitor"
        
        self.url.path = f"{self.version}channels/command/{command}/{channel_id}/.json"
   
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