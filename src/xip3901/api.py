"""API Interface to XIP3901"""

from typing import Any, Optional

from src.xip3901.session import Session


class Call(Session):
    """Thin wrapper with REST methods, allowing per-call timeout overrides.

    Notes
    -----
    - The underlying `Session._request()` uses `self.timeout` when calling
      `requests.Session.request(...)`. To support a custom timeout per call,
      we temporarily override `self.timeout` and then restore it.
    """

    def _do(
        self,
        method: str,
        path: str,
        *,
        query: Optional[dict] = None,
        json_data: Any = None,
        timeout: Optional[float] = None,
    ):
        if timeout is None:
            return self._request(method, path, params=query, json_data=json_data)

        # Per-call timeout: temporarily override, then restore
        old_timeout = self.timeout
        try:
            self.timeout = timeout
            return self._request(method, path, params=query, json_data=json_data)
        finally:
            self.timeout = old_timeout

    def get(self, path: str, query: Optional[dict] = None, timeout: Optional[float] = None):
        return self._do("GET", path, query=query, timeout=timeout)

    def put(self, path: str, json_data: Any = None, timeout: Optional[float] = None):
        return self._do("PUT", path, json_data=json_data, timeout=timeout)

    def post(self, path: str, json_data: Any = None, timeout: Optional[float] = None):
        return self._do("POST", path, json_data=json_data, timeout=timeout)