"""Creates a requests session to the XIP3901 REST API"""

import json
from typing import Optional

import requests
from pydantic import BaseModel, ConfigDict

from src.xip3901.utils import Url


class Session(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    scheme: str = "http"
    host: Optional[str] = None
    port: int = 80
    version: str = "/api/v1/"
    timeout: float = 3.0

    session: Optional[requests.Session] = None
    url: Optional[Url] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session = requests.Session()
        self.url = Url(scheme=self.scheme, host=self.host, port=self.port, path=self.version)

    def _process_response(self, response: requests.Response):
        response.raise_for_status()
        try:
            return response.json()
        except Exception:
            return {"status": response.status_code, "text": response.text}

    def _request(self, http_method: str, path: str, params=None, json_data=None):
        self.url.path = f"{self.version}{path.lstrip('/')}"
        response = self.session.request(
            http_method,
            self.url.to_string(),
            params=params,
            json=json.loads(json_data) if isinstance(json_data, str) else json_data,
            timeout=self.timeout,
        )
        return self._process_response(response)