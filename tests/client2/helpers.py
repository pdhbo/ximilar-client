"""Helper function and classes for tests. Reduce code duplication."""
from dataclasses import dataclass


@dataclass
class EndpointWrapper:
    """
    Simplifies access to patched endpoint's methods. Instead of addressing
    them as endpoint.init.return_value.xxx it is enough to use endpoint.xxx.
    """

    def __init__(self, patched_object):
        self.init = patched_object
        self.sub = self.init.return_value.sub
        self.get = self.init.return_value.get
        self.post = self.init.return_value.post
        self.put = self.init.return_value.put
        self.delete = self.init.return_value.delete
