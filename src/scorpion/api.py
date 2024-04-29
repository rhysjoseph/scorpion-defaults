"""API Interface to Evertz Scorpion"""

from src.scorpion.session import Session


class Call(Session):
    """Creates a requests session to the Evertz Scorpion api"""

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
