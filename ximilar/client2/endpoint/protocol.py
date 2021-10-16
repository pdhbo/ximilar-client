"""Defines protocol for Ximialr endpoint"""

from typing import Optional, Dict, Any, Protocol, TypeVar

Cls = TypeVar("Cls", bound="Ximilar")


class Ximilar(Protocol):
    """Protocol for endpoint classes able to work with Ximilar servers"""

    def sub(self, subpoint: str, /) -> Cls:
        """Creates a REST client working with a fixed part of an URL"""

    def get(self, suffix: str, /, *, args: Optional[Dict[str, Any]] = None):
        """Calls GET method passing args as request parameters"""

    def post(self, suffix: str, /, *, args: Any = None):
        """Calls POST method passing args as JSON in request body"""

    def put(self, suffix: str, /, *, args: Any = None):
        """Calls PUT method passing args as JSON in request body"""

    def delete(self, suffix: str, /, *, args: Optional[Dict[str, Any]] = None):
        """Calls DELETE method passing args as request parameters"""
