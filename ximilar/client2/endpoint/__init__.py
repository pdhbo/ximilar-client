"""
This is an internal module, providing abstractions over HTTP endpoints.
Those simplify working with HTTP nodes and hides details about their implementation.
"""
from .http import Http
from .protocol import Ximilar
from .error import Error
from .default import Default
from .workspace import Workspace
