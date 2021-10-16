"""
This module provides a user-facing class which is a main entry point
for working with Ximilar services.
"""
from typing import Optional
from ximilar.client2 import endpoint
from ximilar.client2 import api
from ximilar.client2.image import NewImage
from ximilar.client2.recognition import RecognitionClient


class ClientApp:
    """Provides the main entry point for working with Ximilar services"""

    def __init__(
        self,
        *,
        ximilar: Optional[endpoint.Ximilar] = None,
        token: str = None,
        jwttoken: str = None,
        base_url: str = api.PRODUCTION_SERVER,
        timeout: int = 90,
    ):
        if ximilar is not None:
            self._ximilar = ximilar
        else:
            http = endpoint.Http(base_url, timeout=timeout)
            self._ximilar = endpoint.Default(token=token, jwttoken=jwttoken, http=http)
        self._workspaces = None

    def workspaces(self):
        """
        List workspaces available to the user. Returns a dict where the key
        is a workspace name and the value is an id. List of workspaces is cached
        and never expires. To refresh it, recreate ClientApp.
        """
        return self._refresh_workspaces()

    def workspace_by_name(self, name: str):
        """Returns ClienApp working with the workspace specified by name"""
        workspaces = self._refresh_workspaces()

        if name not in workspaces:
            raise Exception(f"Workspace {name} doesn't exists")
        return self.workspace_by_id(workspaces[name])

    def workspace_by_id(self, workspace_id: str):
        """Returns ClienApp working with the workspace specified by id"""
        return ClientApp(ximilar=endpoint.Workspace(workspace_id, ximilar=self._ximilar))

    def is_resource_accessible(self, resource: str):
        """Check if the user identified by token can access specific Ximilar resource"""
        try:
            self._authorize({"service": resource})
            return True
        except endpoint.Error as error:
            if error.code == 401:
                return False
            raise error

    def new_image(self):
        """Configure a new image to be uploaded"""
        return NewImage(self._ximilar)

    def recognition(self):
        """Access recognition application"""
        return RecognitionClient(self._ximilar)

    def _refresh_workspaces(self):
        if self._workspaces is None:
            data = self._list_workspaces()
            self._workspaces = {workspace["name"]: workspace["id"] for workspace in data}
        return self._workspaces

    def _list_workspaces(self):
        return self._ximilar.get(api.WORKSPACE)

    def _authorize(self, args):
        return self._ximilar.post(api.AUTHORIZE, args=args)
