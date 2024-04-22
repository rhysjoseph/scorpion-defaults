from typing import Union

from furl import furl
from pydantic import BaseModel, ConfigDict, model_validator


class Url(BaseModel):
    """Creates URL from components
    kwargs:
        scheme: str
        username: str
        password: str
        host: str
        port: int
        path: str
        query: dict
        fragment: str
        url: furl

    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    scheme: Union[str, None] = "https"
    username: Union[str, None] = None
    password: Union[str, None] = None
    host: Union[str, None] = None
    port: Union[int, None] = None
    path: Union[str, None] = None
    query: Union[dict, None] = None
    fragment: Union[str, None] = None

    # @model_validator(mode="after")
    # def _check_user_password(self) -> "UserModel":
    #     if self.username:
    #         if self.password is None:
    #             raise ValueError("Username supplied so password is required")
    #     if self.password:
    #         if self.username is None:
    #             raise ValueError("Password supplied so username is required")
    #     return self

    def to_string(self):
        """Returns URL as string"""
        url = furl(**self.model_dump())
        return url.url
