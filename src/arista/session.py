"""Creates a requests session to the Arista api"""

import base64
import json
import os
from datetime import datetime, timedelta
from typing import Optional

import requests
from pydantic import BaseModel, ConfigDict

from src.mcm.utils import Url

PARENT_DIR = os.path.dirname(os.path.realpath(__file__))
SRC_DIR = os.path.dirname(PARENT_DIR)
ROOT_DIR = os.path.dirname(SRC_DIR)


class Session(BaseModel):
    """Creates a requests session to the Arista api"""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    scheme: str = "http"
    host: str = "10.244.169.128"
    # 2.0/channels/config/{id}/.json?mcm_server={mcm_server}
    port: int = None
    version: str = "command-api/"
    api_limit: float = 1.0 / 4
    max_records_per_request: int = 100
    session: Optional[requests.Session] = None
    url: Optional[str] = None
    timeout: float = 2
    config: dict = None
    token: str = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # self.token = self.config.get("SCORPION_TOKEN")
        self.session = requests.Session()
        self.session.headers = {
            "Authorization": f"Basic {self.encode_credentials('admin', 'ctUS1986!')}",
            "content-type": "application/json",
        }
        self.url = Url(
            scheme=self.scheme,
            host=self.host,
            port=self.port,
        )

    def encode_credentials(self, username, password):
        """Encodes username and password in Base64.

        Args:
            username: The username.
            password: The password.

        Returns:
            The Base64-encoded credentials string.
        """
        credentials_string = f"{username}:{password}"
        credentials_bytes = credentials_string.encode("utf-8")
        encoded_credentials = base64.b64encode(credentials_bytes).decode("utf-8")
        return encoded_credentials

    def _process_response(self, response):
        print(response)
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
        # self._refresh_token()
        return response.json()

    def _request(self, http_method: str, params=None, json_data=None, files=None):
        print(self.url.to_string())
        response = self.session.request(
            http_method,
            self.url.to_string(),
            params=params,
            json=json_data,
            files=files,
            timeout=self.timeout,
        )

        return self._process_response(response)
