# pylint: disable=missing-module-docstring,missing-function-docstring
import pytest

from ximilar.client2 import endpoint


@pytest.mark.parametrize("method", ["get", "post", "put", "delete"])
def test_adds_workspace_to_args(ximilar_endpoint, method):
    client = endpoint.Workspace("ws", ximilar=ximilar_endpoint)
    getattr(client, method)("resource", args={"key1": "value1"})

    getattr(ximilar_endpoint, method).assert_called_with("resource", args={"workspace": "ws", "key1": "value1"})


@pytest.mark.parametrize("method", ["get", "post", "put", "delete"])
def test_adds_workspace_to_no_args(ximilar_endpoint, method):
    client = endpoint.Workspace("ws", ximilar=ximilar_endpoint)
    getattr(client, method)("resource", args=None)

    getattr(ximilar_endpoint, method).assert_called_with("resource", args={"workspace": "ws"})


def test_creates_suffixed_workspace_endpoint(ximilar_endpoint):
    client = endpoint.Workspace("ws", ximilar=ximilar_endpoint).sub("suffix")

    ximilar_endpoint.sub.assert_called_with("suffix")
    assert isinstance(client, endpoint.Workspace)
    assert client.workspace_id == "ws"
