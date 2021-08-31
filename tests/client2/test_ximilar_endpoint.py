# pylint: disable=missing-module-docstring,missing-function-docstring
from dataclasses import dataclass
from unittest.mock import ANY
import json
import pytest

from ximilar.client2.endpoints import XimilarEndpoint, EndpointError


@pytest.fixture(name="http_endpoint")
def http_endpoint_fixture(mocker):
    @dataclass
    class _wrapper:
        def __init__(self):
            self.init = mocker.patch("ximilar.client2.endpoints.HttpEndpoint", autospec=True)
            self.sub = self.init.return_value.sub
            self.get = self.init.return_value.get
            self.post = self.init.return_value.post
            self.put = self.init.return_value.put
            self.delete = self.init.return_value.delete

    return _wrapper()


@pytest.fixture(name="json_endpoint")
def json_endpoint_fixture(http_endpoint):
    default_result = {"status": 200, "content-type": "application/json", "content": "{}"}
    http_endpoint.get.return_value = default_result
    http_endpoint.post.return_value = default_result
    http_endpoint.put.return_value = default_result
    http_endpoint.delete.return_value = default_result
    return http_endpoint


@pytest.fixture(name="client")
def client_fixture(http_endpoint):
    return XimilarEndpoint(token="anything", endpoint=http_endpoint)


def test_creates_suffixed_endpoint(http_endpoint):
    XimilarEndpoint(token="anything", endpoint=http_endpoint).sub("service/v2")

    http_endpoint.sub.assert_called_with("service/v2")


def test_sets_correct_auth_header_for_normal_token(json_endpoint):
    client = XimilarEndpoint(token="token", endpoint=json_endpoint)
    client.get("resource")

    json_endpoint.get.assert_called_with(
        ANY,
        params=ANY,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Token token",
            "User-Agent": "Ximilar Client/Python",
        },
    )


def test_sets_correct_auth_header_for_jwt_token(json_endpoint):
    client = XimilarEndpoint(jwttoken="token", endpoint=json_endpoint)
    client.get("resource")

    json_endpoint.get.assert_called_with(
        ANY,
        params=ANY,
        headers={
            "Content-Type": "application/json",
            "Authorization": "JWT token",
            "User-Agent": "Ximilar Client/Python",
        },
    )


@pytest.mark.parametrize("method", ["get", "post", "put", "delete"])
def test_returns_parsed_json(json_endpoint, client, method):
    getattr(json_endpoint, method).return_value["content"] = '{"key1": "value1", "key2": "value2"}'

    assert getattr(client, method)("resource") == {"key1": "value1", "key2": "value2"}


@pytest.mark.parametrize("method", ["get", "post", "put", "delete"])
def test_returns_none_on_204(json_endpoint, client, method):
    getattr(json_endpoint, method).return_value["status"] = 204

    assert getattr(client, method)("anything") is None


@pytest.mark.parametrize("method", ["get", "delete"])
def test_passes_args_as_params(json_endpoint, client, method):
    getattr(client, method)("resource", args={"key1": "value1"})

    getattr(json_endpoint, method).assert_called_with("resource", params={"key1": "value1"}, headers=ANY)


@pytest.mark.parametrize("method", ["post", "put"])
def test_passes_args_as_data(json_endpoint, client, method):
    getattr(client, method)("resource", args={"key1": "value1"})

    getattr(json_endpoint, method).assert_called_with("resource", data='{"key1": "value1"}', headers=ANY)


@pytest.mark.parametrize("method", ["post", "put"])
def test_sends_no_body_if_no_args(json_endpoint, client, method):
    getattr(client, method)("resource")

    getattr(json_endpoint, method).assert_called_with("resource", data=None, headers=ANY)


@pytest.mark.parametrize("method", ["get", "post", "put", "delete"])
def test_throws_on_bad_status(json_endpoint, client, method):
    getattr(json_endpoint, method).return_value["status"] = 500

    with pytest.raises(EndpointError) as error_info:
        getattr(client, method)("anything")
    assert str(error_info.value) == "Error returned from HTTP layer: 500"
    assert error_info.value.code == 500


@pytest.mark.parametrize("method", ["get", "post", "put", "delete"])
def test_throws_on_bad_content_type(json_endpoint, client, method):
    getattr(json_endpoint, method).return_value["content-type"] = "text/html"

    with pytest.raises(Exception) as error_info:
        getattr(client, method)("anything")
    assert str(error_info.value) == "Unexpected response content type: text/html"


@pytest.mark.parametrize("method", ["get", "post", "put", "delete"])
def test_throws_on_invalid_json(json_endpoint, client, method):
    getattr(json_endpoint, method).return_value["content"] = "{"

    with pytest.raises(json.decoder.JSONDecodeError):
        getattr(client, method)("anything")
