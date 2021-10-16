"""Defines Ximilar endpoint working with specific workspace"""
from typing import Optional, Dict, Any

from .protocol import Ximilar


class Workspace:
    """
    Wrapper for the XimilarEndpoint. It provides exactly the same interface, so
    it can be used interchangeably with the original one. WorkspaceEndpint adds
    a "workspace" argument to each call. You can even wrap another
    WorkspaceEndpoint with WorkspaceEndpint. The outermost one has precedence.
    """

    def __init__(self, workspace_id: str, /, *, ximilar: Ximilar):
        self.workspace_id = workspace_id
        self._ximilar = ximilar

    def sub(self, subpoint, /):
        """Creates a WorkspaceEndpoint working with a fixed part of an URL"""
        return Workspace(self.workspace_id, ximilar=self._ximilar.sub(subpoint))

    def get(self, suffix: str, /, *, args: Optional[Dict[str, Any]] = None):
        """Calls GET method passing args as request parameters"""
        return self._call(self._ximilar.get, suffix, args)

    def post(self, suffix: str, /, *, args=None):
        """Calls POST method passing args as JSON in request body"""
        return self._call(self._ximilar.post, suffix, args)

    def put(self, suffix: str, /, *, args=None):
        """Calls PUT method passing args as JSON in request body"""
        return self._call(self._ximilar.put, suffix, args)

    def delete(self, suffix: str, /, *, args: Optional[Dict[str, Any]] = None):
        """Calls DELETE method passing args as request parameters"""
        return self._call(self._ximilar.delete, suffix, args)

    def _call(self, method, suffix, args):
        real_args = {"workspace": self.workspace_id}
        if args is not None:
            real_args.update(args)
        return method(suffix, args=real_args)
