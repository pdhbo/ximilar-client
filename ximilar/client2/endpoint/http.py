"""Defines HTTP endpoint"""
from typing import Optional, Dict, Any
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from requests import Session, Request


class Http:
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
        return Http(self._url + suffix, timeout=self._timeout)

    def get(self, suffix: str, /, *, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None):
        """Performs HTTP GET with specified parameters"""
        return self._call(Session.get, suffix, params=params, headers=headers)

    def post(self, suffix: str, /, *, data: Any = None, headers: Optional[Dict[str, str]] = None):
        """Performs HTTP POST with specified data as request body"""
        return self._call(Session.post, suffix, data=data, headers=headers)

    def put(self, suffix: str, /, *, data: Any = None, headers: Optional[Dict[str, str]] = None):
        """Performs HTTP PUT with specified data as request body"""
        return self._call(Session.put, suffix, data=data, headers=headers)

    def delete(
        self, suffix: str, /, *, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None
    ):
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
        if Http.debug_mode:
            Http._dump_reply(result)
        return {
            "status": result.status_code,
            "content-type": result.headers.get("content-type"),
            "content": result.text,
        }

    @staticmethod
    def _dump_reply(result):
        start_marker = "-----------REPLY-----------"
        status = f"CODE: '{result.status_code}'"
        content_type = f"Content-Type: '{result.headers.get('content-type')}'"
        print(f"{start_marker}\n{status}\n{content_type}\n{result.text}\n\n")
