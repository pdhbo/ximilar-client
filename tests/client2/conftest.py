# pylint: disable=missing-module-docstring,missing-function-docstring
import pytest
from .helpers import EndpointWrapper


@pytest.fixture(name="ximilar_endpoint")
def ximilar_endpoint_fixture(mocker):
    return EndpointWrapper(mocker.patch("ximilar.client2.endpoint.default.Default", autospec=True))
