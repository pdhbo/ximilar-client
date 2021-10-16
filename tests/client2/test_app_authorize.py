# pylint: disable=missing-module-docstring,missing-function-docstring
import pytest

from ximilar.client2.app import ClientApp
from ximilar.client2 import endpoint


def test_is_resource_accessible_ok_returns_true(ximilar_endpoint):
    ximilar_endpoint.post.return_value = {}
    app = ClientApp(ximilar=ximilar_endpoint)

    result = app.is_resource_accessible("resource")

    assert result
    ximilar_endpoint.post.assert_called_once_with("authorization/v2/authorize", args={"service": "resource"})


def test_is_resource_accessible_status_401_returns_false(ximilar_endpoint):
    ximilar_endpoint.post.side_effect = endpoint.Error("", code=401)
    app = ClientApp(ximilar=ximilar_endpoint)

    result = app.is_resource_accessible("resource")

    assert not result
    ximilar_endpoint.post.assert_called_once_with("authorization/v2/authorize", args={"service": "resource"})


def test_is_resource_accessible_other_exception_raised(ximilar_endpoint):
    ximilar_endpoint.post.side_effect = endpoint.Error("Error", code=500)
    app = ClientApp(ximilar=ximilar_endpoint)

    with pytest.raises(endpoint.Error) as error_info:
        app.is_resource_accessible("resource")

    assert str(error_info.value) == "Error"
    assert error_info.value.code == 500
