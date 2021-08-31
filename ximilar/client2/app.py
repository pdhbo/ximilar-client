"""
This module provides a user-facing class which is a main entry point
for working with Ximilar services.
"""
from typing import Optional
from ximilar.client2.endpoints import AppEndpoint, EndpointError, XimilarEndpoint, HttpEndpoint
from ximilar.client2 import api

# pylint: disable=too-few-public-methods
class ClientApp:
    """Provides the main entry point for working with Ximilar services"""

    def __init__(
        self,
        *,
        endpoint: Optional[AppEndpoint] = None,
        token: str = None,
        jwttoken: str = None,
        base_url: str = api.PRODUCTION_SERVER,
        timeout: int = 90,
    ):
        if endpoint is not None:
            self._endpoint = endpoint
        else:
            http_endpoint = HttpEndpoint(base_url, timeout=timeout)
            self._endpoint = XimilarEndpoint(token=token, jwttoken=jwttoken, endpoint=http_endpoint)

    def is_resource_accessible(self, resource: str):
        """Check if the user identified by token can access specific Ximilar resource"""
        try:
            self._authorize({"service": resource})
            return True
        except EndpointError as error:
            if error.code == 401:
                return False
            raise error

    def _authorize(self, args):
        return self._endpoint.post(api.AUTHORIZE, args=args)
