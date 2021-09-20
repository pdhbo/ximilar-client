# pylint: disable=missing-module-docstring,missing-function-docstring
import pytest

from ximilar.client2.app import ClientApp
from .helpers import EndpointWrapper


@pytest.fixture(name="ximilar_endpoint")
def ximilar_endpoint_fixture(mocker):
    return EndpointWrapper(mocker.patch("ximilar.client2.endpoints.XimilarEndpoint", autospec=True))


server_response = [
    {"id": "id1", "name": "name1", "created": "date1", "owner": "user1", "meta_data": None, "is_default": True},
    {"id": "id2", "name": "name2", "created": "date2", "owner": "user2", "meta_data": None, "is_default": False},
]


def test_workspaces_returns_map(ximilar_endpoint):
    ximilar_endpoint.get.return_value = server_response
    app = ClientApp(endpoint=ximilar_endpoint)

    result = app.workspaces()

    assert result == {"name1": "id1", "name2": "id2"}
    ximilar_endpoint.get.assert_called_once_with("account/v2/workspace/")


def test_workspaces_double_call_returns_cache(ximilar_endpoint):
    ximilar_endpoint.get.return_value = server_response
    app = ClientApp(endpoint=ximilar_endpoint)

    app.workspaces()
    app.workspaces()

    ximilar_endpoint.get.assert_called_once_with("account/v2/workspace/")


def test_workspaces_passes_error_through(ximilar_endpoint):
    ximilar_endpoint.get.side_effect = Exception("some error")
    app = ClientApp(endpoint=ximilar_endpoint)

    with pytest.raises(Exception) as error_info:
        app.workspaces()
    assert str(error_info.value) == "some error"


def test_workspace_by_id_returns_app_with_workspace_endpoint(ximilar_endpoint):
    ximilar_endpoint.get.return_value = server_response
    app = ClientApp(endpoint=ximilar_endpoint)

    result = app.workspace_by_id("id1")

    result.is_resource_accessible("resource")
    ximilar_endpoint.post.assert_called_once_with(
        "authorization/v2/authorize", args={"service": "resource", "workspace": "id1"}
    )


def test_workspace_by_name_returns_app_with_workspace_endpoint(ximilar_endpoint):
    ximilar_endpoint.get.return_value = server_response
    app = ClientApp(endpoint=ximilar_endpoint)

    result = app.workspace_by_name("name2")

    ximilar_endpoint.get.return_value = {}
    result.is_resource_accessible("resource")
    ximilar_endpoint.post.assert_called_once_with(
        "authorization/v2/authorize", args={"service": "resource", "workspace": "id2"}
    )


def test_workspace_by_name_name_does_not_exist_throws_error(ximilar_endpoint):
    ximilar_endpoint.get.return_value = server_response
    app = ClientApp(endpoint=ximilar_endpoint)

    with pytest.raises(Exception) as error_info:
        app.workspace_by_name("name3")
    assert str(error_info.value) == "Workspace name3 doesn't exists"
