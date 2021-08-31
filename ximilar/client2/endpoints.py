"""
This is an internal module, providing abstractions over HTTP endpoints.
Those simplify working with HTTP nodes and hides details about their implementation.
"""
from typing import Optional, Dict, Any
import json
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from requests import Session

HttpHeaders = Optional[Dict[str, str]]


class HttpEndpoint:
    """
    This class represents HTTP endpoint on the client side. It works with fixed
    URL and provides means to call GET, POST, PUT or DELETE methods of HTTP
    protocol.
    """

    def __init__(self, url: str, /, *, timeout: int = 90):
        self._url = url
        self._timeout = timeout

    def sub(self, suffix: str, /):
        """Creates sub-endpoint working with specified suffix, added to current url"""
        return HttpEndpoint(self._url + suffix, timeout=self._timeout)

    def get(self, suffix: str, /, *, params: Optional[Dict[str, Any]] = None, headers: HttpHeaders = None):
        """Performs HTTP GET with specified parameters"""
        return self._call(Session.get, suffix, params=params, headers=headers)

    def post(self, suffix: str, /, *, data: Any = None, headers: HttpHeaders = None):
        """Performs HTTP POST with specified data as request body"""
        return self._call(Session.post, suffix, data=data, headers=headers)

    def put(self, suffix: str, /, *, data: Any = None, headers: HttpHeaders = None):
        """Performs HTTP PUT with specified data as request body"""
        return self._call(Session.put, suffix, data=data, headers=headers)

    def delete(self, suffix: str, /, *, params: Optional[Dict[str, Any]] = None, headers: HttpHeaders = None):
        """Performs HTTP DELETE with specified parameters"""
        return self._call(Session.delete, suffix, params=params, headers=headers)

    def _call(self, http_method, suffix, /, **rest):
        adapter = HTTPAdapter(max_retries=Retry(total=5, backoff_factor=5))
        session = Session()
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return self._format_result(http_method(session, self._url + suffix, timeout=self._timeout, **rest))

    @staticmethod
    def _format_result(result):
        return {"status": result.status_code, "content-type": result.headers["content-type"], "content": result.text}


class EndpointError(Exception):
    """
    Wrapper for XimilarEndpoint errors.
    """

    def __init__(self, message: str, /, *, code: int = None, body: str = None):
        super().__init__(message)
        self.code = code
        self.body = body

    @staticmethod
    def token_missing():
        """We can't really do anything without a token"""
        return EndpointError("token or jwttoken must be present")

    @staticmethod
    def content_type(content_type):
        """XimilarEndpoint always expects JSON and it was not it."""
        return EndpointError(f"Unexpected response content type: {content_type}")

    @staticmethod
    def http_error(code, body):
        """There was an error we don't know how to interpret."""
        return EndpointError(f"Error returned from HTTP layer: {code}", code=code, body=body)


class XimilarEndpoint:
    """
    Wrapper for HttpEndpoint, which knows how to talk to Ximilar services.
    It knows how to pass service arguments for each HTTP method.
    And it knows how to interpret the result.
    """

    def __init__(self, *, endpoint: HttpEndpoint, token: str = None, jwttoken: str = None):
        if jwttoken is not None:
            self._token = "JWT " + jwttoken
        elif token is not None:
            if token.startswith("Token ") or token.startswith("JWT "):
                self._token = token
            else:
                self._token = "Token " + token
        else:
            raise EndpointError.token_missing()

        self._endpoint = endpoint

    def sub(self, subpoint: str, /):
        """Creates a REST client working with a fixed part of an URL"""
        return XimilarEndpoint(endpoint=self._endpoint.sub(subpoint), token=self._token)

    def get(self, suffix: str, /, *, args: Optional[Dict[str, Any]] = None):
        """Calls GET method passing args as request parameters"""
        return self._call(self._endpoint.get, suffix, params=args)

    def post(self, suffix: str, /, *, args: Any = None):
        """Calls POST method passing args as JSON in request body"""
        return self._call(self._endpoint.post, suffix, data=self._serialize(args))

    def put(self, suffix: str, /, *, args: Any = None):
        """Calls PUT method passing args as JSON in request body"""
        return self._call(self._endpoint.put, suffix, data=self._serialize(args))

    def delete(self, suffix: str, /, *, args: Optional[Dict[str, Any]] = None):
        """Calls DELETE method passing args as request parameters"""
        return self._call(self._endpoint.delete, suffix, params=args)

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
            raise EndpointError.http_error(result["status"], result["content"])

        if result["content-type"] != "application/json":
            raise EndpointError.content_type(result["content-type"])

        return json.loads(result["content"])
