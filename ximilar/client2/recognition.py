"""
This module provide classes that wraps access to Ximilar Recognition application
"""
from typing import Any, Dict


class RecognitionClient:
    """
    The umbrella wrapper class for everything related to Recognition application
    """

    def __init__(self, endpoint):
        self._endpoint = endpoint

    def new_tag(self, name: str, description: str = None, output_name: str = None):
        """
        Creates a new label of type tag on the server
        """
        return self._new_label({"name": name, "type": "tag", "description": description, "output_name": output_name})

    def label(self, label_id: str):
        """
        Returns a structure with all the label properties
        """
        return RecognitionLabel(self._endpoint, label_id=label_id)

    def _new_label(self, args):
        return self._endpoint.post("recognition/v2/label/", args=args)


class RecognitionLabel:
    """
    Wrapper for Ximial Recognition application's label object
    """

    def __init__(self, endpoint, label_id: str = None, json: Dict[str, Any] = None):
        self._endpoint = endpoint
        if json is not None:
            self._from_json(json)
        elif id is not None:
            self._id = label_id

    def __getattr__(self, item):
        if item == "_data":
            self._data = self._load_data()
        raise AttributeError(self, item)

    def _load_data(self):
        data = self._endpoint.get(f"/recognition/v2/label/{self._id}/")
        self._from_json(data)

    def _from_json(self, data):
        self._data["id"] = data["id"]
        self._data["name"] = data["name"]
        self._data["type"] = data["type"]
        if "description" in data:
            self._data["description"] = data["description"]
        self._data["outputname"] = data["output_name"]
