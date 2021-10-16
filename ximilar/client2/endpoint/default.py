"""Defines Default Ximilar endpoint working without any modifications"""
from typing import Optional, Dict, Any
import json

from .http import Http
from .error import Error


class Default:
    """
    Wrapper for HttpEndpoint, which knows how to talk to Ximilar services.
    It knows how to pass service arguments for each HTTP method.
    And it knows how to interpret the result.
    """

    def __init__(self, *, http: Http, token: str = None, jwttoken: str = None):
        if jwttoken is not None:
            self._token = "JWT " + jwttoken
        elif token is not None:
            if token.startswith("Token ") or token.startswith("JWT "):
                self._token = token
            else:
                self._token = "Token " + token
        else:
            raise Error.token_missing()

        self._http = http

    def sub(self, subpoint: str, /):
        """Creates a REST client working with a fixed part of an URL"""
        return Default(http=self._http.sub(subpoint), token=self._token)

    def get(self, suffix: str, /, *, args: Optional[Dict[str, Any]] = None):
        """Calls GET method passing args as request parameters"""
        return self._call(self._http.get, suffix, params=args)

    def post(self, suffix: str, /, *, args: Any = None):
        """Calls POST method passing args as JSON in request body"""
        return self._call(self._http.post, suffix, data=self._serialize(args))

    def put(self, suffix: str, /, *, args: Any = None):
        """Calls PUT method passing args as JSON in request body"""
        return self._call(self._http.put, suffix, data=self._serialize(args))

    def delete(self, suffix: str, /, *, args: Optional[Dict[str, Any]] = None):
        """Calls DELETE method passing args as request parameters"""
        return self._call(self._http.delete, suffix, params=args)

    def _call(self, method, suffix, **kwargs):
        return self._parse_result(
            method(
                suffix,
                **kwargs,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": self._token,
                    "User-Agent": "Ximilar Client/Python",
                },
            )
        )

    @staticmethod
    def _serialize(data):
        return json.dumps(data) if data is not None else None

    @staticmethod
    def _parse_result(result):
        if result["status"] == 204:
            return None

        if result["status"] >= 300:
            raise Error.http_error(result["status"], result["content"])

        if result["content-type"] != "application/json":
            raise Error.content_type(result["content-type"])

        return json.loads(result["content"])
