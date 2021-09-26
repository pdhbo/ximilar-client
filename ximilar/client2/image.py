# pylint: disable=fixme
"""Module for image support"""
import base64
from typing import Dict, Any

from ximilar.client2.endpoints import AppEndpoint


class NewImage:
    """New image configuration class"""

    def __init__(self, endpoint: AppEndpoint):
        self._endpoint = endpoint
        self._args: Dict[str, Any] = {}

    def no_resizing(self):
        """Do not do server-side resizing for that image"""
        self._args["noresize"] = True
        return self

    # TODO: looks like dup detecction dosen't work
    # def even_if_duplicate(self):
    #     self._args['force'] = True
    #     return self

    # TODO: uncomment after labels are supported
    # def with_labels(self, label_ids: List[str]):
    #     self._args['label_ids'] = label_ids
    #     return self

    def upload(self, *, file: str = None, data: str = None):
        """
        Upload image file or image data to the server.
        """
        args = self._args.copy()
        if file is not None:
            args["base64"] = self._read_file(file)
        elif data is not None:
            args["base64"] = data
        else:
            raise Exception("Either file or data must be set")

        return self._endpoint.post("recognition/v2/training-image/", args=args)

    @staticmethod
    def _read_file(filename: str):
        with open(filename, "rb") as file:
            return base64.b64encode(file.read()).decode("utf-8")
