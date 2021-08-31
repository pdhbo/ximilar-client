"""
This is an internal module, providing abstractions over HTTP endpoints.
Those simplify working with HTTP nodes and hides details about their implementation.
"""
from typing import Optional, Dict, Any
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
