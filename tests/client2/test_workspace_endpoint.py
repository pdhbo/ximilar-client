# pylint: disable=missing-module-docstring,missing-function-docstring
import pytest

from ximilar.client2.endpoints import WorkspaceEndpoint
from .helpers import EndpointWrapper


@pytest.fixture(name="ximilar_endpoint")
def ximilar_endpoint_fixture(mocker):
    return EndpointWrapper(mocker.patch("ximilar.client2.endpoints.XimilarEndpoint", autospec=True))


@pytest.mark.parametrize("method", ["get", "post", "put", "delete"])
def test_adds_workspace_to_args(ximilar_endpoint, method):
    client = WorkspaceEndpoint("ws", endpoint=ximilar_endpoint)
    getattr(client, method)("resource", args={"key1": "value1"})

    getattr(ximilar_endpoint, method).assert_called_with("resource", args={"workspace": "ws", "key1": "value1"})


@pytest.mark.parametrize("method", ["get", "post", "put", "delete"])
def test_adds_workspace_to_no_args(ximilar_endpoint, method):
    client = WorkspaceEndpoint("ws", endpoint=ximilar_endpoint)
    getattr(client, method)("resource", args=None)

    getattr(ximilar_endpoint, method).assert_called_with("resource", args={"workspace": "ws"})


def test_creates_suffixed_workspace_endpoint(ximilar_endpoint):
    client = WorkspaceEndpoint("ws", endpoint=ximilar_endpoint).sub("suffix")

    ximilar_endpoint.sub.assert_called_with("suffix")
    assert isinstance(client, WorkspaceEndpoint)
    assert client.name == "ws"
