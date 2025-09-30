from typing import Union
from furl import furl
from pydantic import BaseModel, ConfigDict


class Url(BaseModel):
    """
    Compose URLs from components.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    scheme: Union[str, None] = "http"
    username: Union[str, None] = None
    password: Union[str, None] = None
    host: Union[str, None] = None
    port: Union[int, None] = None
    path: Union[str, None] = None
    query: Union[dict, str, None] = None
    fragment: Union[str, None] = None

    def to_string(self):
        return furl(**self.model_dump()).url