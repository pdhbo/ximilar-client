"""
This module provide a function to simplify client creation by using
environment variables.
"""
import os
from ximilar.client2.app import ClientApp


def from_env():
    """
    Create a ClientApp using value of XIMILAR_TOKEN environment variable as
    a token and value of XIMILAR_WORKSPACE as a workspace. If XIMILAR_WORKSPACE
    variable is not set it uses the default workspace.
    """
    token = os.environ.get("XIMILAR_TOKEN")
    if token is None:
        raise Exception("No XIMILAR_TOKEN var")
    app = ClientApp(token=token)

    workspace = os.environ.get("XIMILAR_WORKSPACE")
    if workspace is None:
        return app
    return app.workspace_by_name(workspace)
