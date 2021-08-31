# pylint: disable=missing-module-docstring,missing-function-docstring
import pytest

from ximilar.client2.endpoints import HttpEndpoint
from .minserver import MinHTTPServer


def _reply_with_empty_dict(client):
    client.sendall(b"HTTP/1.1 200 OK\r\n")
    client.sendall(b"Content-Type: application/json\r\n")
    client.sendall(b"\r\n")
    client.sendall(b"{}")


@pytest.fixture(name="server")
def server_fixture():
    with MinHTTPServer("127.0.0.1", 4000) as server:
        server.reply = _reply_with_empty_dict
        yield server


@pytest.mark.parametrize("method", ["get", "post", "put", "delete"])
def test_returns_content_and_status(server, method):
    endpoint = HttpEndpoint(server.url())

    result = getattr(endpoint, method)("resource")

    assert f"{method.upper()} /resource HTTP" in server.request
    assert "status" in result
    assert result["status"] == 200
    assert "content-type" in result
    assert result["content-type"] == "application/json"
    assert "content" in result
    assert result["content"] == "{}"


@pytest.mark.parametrize("method", ["get", "post", "put", "delete"])
def test_sends_headers(server, method):
    endpoint = HttpEndpoint(server.url())

    getattr(endpoint, method)("resource", headers={"Header1": "value1", "Header2": "value2"})

    assert "\r\nHeader1: value1\r\n" in server.request
    assert "\r\nHeader2: value2\r\n" in server.request


@pytest.mark.parametrize("method", ["post", "put"])
def test_sends_data(server, method):
    endpoint = HttpEndpoint(server.url())

    getattr(endpoint, method)("resource", data="request body")

    assert server.request_body == "request body"


def test_sub_makes_prefix(server):
    endpoint = HttpEndpoint(server.url())
    subpoint = endpoint.sub("group/")

    subpoint.get("resource")

    assert "GET /group/resource HTTP" in server.request
