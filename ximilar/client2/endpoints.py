"""
This is an internal module, providing abstractions over HTTP endpoints.
Those simplify working with HTTP nodes and hides details about their implementation.
"""
from typing import Optional, Dict, Any, Protocol, TypeVar
import json
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from requests import Session, Request

HttpHeaders = Optional[Dict[str, str]]


class HttpEndpoint:
    """
    This class represents HTTP endpoint on the client side. It works with fixed
    URL and provides means to call GET, POST, PUT or DELETE methods of HTTP
    protocol.
    """

    debug_mode = False

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
        if self.debug_mode:
            self._dump_request(http_method, suffix, **rest)

        adapter = HTTPAdapter(max_retries=Retry(total=5, backoff_factor=5))
        session = Session()
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return self._format_result(http_method(session, self._url + suffix, timeout=self._timeout, **rest))

    def _dump_request(self, http_method, suffix, /, **rest):
        req = Request(http_method.__name__.upper(), self._url + suffix, **rest)
        prepared = req.prepare()
        start_marker = "-----------START-----------"
        headers = "\n".join(f"{k}: {v}" for k, v in prepared.headers.items())
        print(f"{start_marker}\n{prepared.method} {prepared.url}\n{headers}\n\n{prepared.body}\n\n")

    @staticmethod
    def _format_result(result):
        if HttpEndpoint.debug_mode:
            HttpEndpoint._dump_reply(result)
        return {"status": result.status_code, "content-type": result.headers["content-type"], "content": result.text}

    @staticmethod
    def _dump_reply(result):
        start_marker = "-----------REPLY-----------"
        status = f"CODE: {result.status_code}"
        content_type = f"Content-Type: {result.headers['content-type']}"
        print(f"{start_marker}\n{status}\n{content_type}\n{result.text}\n\n")


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


Cls = TypeVar("Cls", bound="AppEndpoint")


class AppEndpoint(Protocol):
    """Protocol for endpoint classes able to work with Ximilar servers"""

    def sub(self, subpoint: str, /) -> Cls:
        """Creates a REST client working with a fixed part of an URL"""

    def get(self, suffix: str, /, *, args: Optional[Dict[str, Any]] = None):
        """Calls GET method passing args as request parameters"""

    def post(self, suffix: str, /, *, args: Any = None):
        """Calls POST method passing args as JSON in request body"""

    def put(self, suffix: str, /, *, args: Any = None):
        """Calls PUT method passing args as JSON in request body"""

    def delete(self, suffix: str, /, *, args: Optional[Dict[str, Any]] = None):
        """Calls DELETE method passing args as request parameters"""


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


class WorkspaceEndpoint:
    """
    Wrapper for the XimilarEndpoint. It provides exactly the same interface, so
    it can be used interchangeably with the original one. WorkspaceEndpint adds
    a "workspace" argument to each call. You can even wrap another
    WorkspaceEndpoint with WorkspaceEndpint. The outermost one has precedence.
    """

    def __init__(self, workspace_id: str, /, *, endpoint: AppEndpoint):
        self.name = workspace_id
        self.endpoint = endpoint

    def sub(self, subpoint, /):
        """Creates a WorkspaceEndpoint working with a fixed part of an URL"""
        return WorkspaceEndpoint(self.name, endpoint=self.endpoint.sub(subpoint))

    def get(self, suffix: str, /, *, args: Optional[Dict[str, Any]] = None):
        """Calls GET method passing args as request parameters"""
        return self._call(self.endpoint.get, suffix, args)

    def post(self, suffix: str, /, *, args=None):
        """Calls POST method passing args as JSON in request body"""
        return self._call(self.endpoint.post, suffix, args)

    def put(self, suffix: str, /, *, args=None):
        """Calls PUT method passing args as JSON in request body"""
        return self._call(self.endpoint.put, suffix, args)

    def delete(self, suffix: str, /, *, args: Optional[Dict[str, Any]] = None):
        """Calls DELETE method passing args as request parameters"""
        return self._call(self.endpoint.delete, suffix, args)

    def _call(self, method, suffix, args):
        real_args = {"workspace": self.name}
        if args is not None:
            real_args.update(args)
        return method(suffix, args=real_args)