"""
This module provide classes that wraps access to Ximilar Recognition application
"""
from typing import Any, Dict


class Label:
    """
    Wrapper for Ximial Recognition application's label object
    """

    def __init__(self, endpoint, label_id: str = None, json: Dict[str, Any] = None):
        self._endpoint = endpoint
        if json is not None:
            self._id = json["id"]
            self._data = self._extract_from(json)
        elif id is not None:
            self._id = label_id

    def id(self) -> str:  # pylint: disable=invalid-name
        """Returns the id of the label"""
        return self._id

    def name(self) -> str:
        """Returns the name of the label"""
        return self._data["name"]

    def type(self) -> str:
        """Returns the type of the label"""
        return self._data["type"]

    def description(self) -> str:
        """Returns the description of the label"""
        return self._data["description"]

    def output_name(self) -> str:
        """Returns the output name of the label"""
        return self._data["output_name"]

    def images_count(self) -> int:
        """Returns the number of images associated with the label"""
        return self._data["images_count"]

    def tasks_count(self) -> int:
        """Returns the number of tasks associated with the label"""
        return self._data["tasks_count"]

    def objects_count(self) -> int:
        """Returns the number of objects associated with the label"""
        return self._data["objects_count"]

    def negative_for_task(self) -> Any:
        """Returns unknown shit"""
        return self._data["negative_for_task"]

    def wipe(self) -> None:
        """
        Delete label and all images associated with this label.
        """
        self._endpoint.delete(f"recognition/v2/label/{self._id}/wipe")

    def delete(self) -> None:
        """
        Delete label.
        """
        self._endpoint.delete(f"recognition/v2/label/{self._id}")

    @staticmethod
    def _extract_from(data) -> Dict[str, Any]:
        return {
            "name": data["name"],
            "type": data["type"],
            "description": data.get("description", None) or "",
            "output_name": data.get("output_name", None) or data["name"],
            "images_count": data.get("images_count", 0),
            "tasks_count": data.get("tasks_count", 0),
            "objects_count": data.get("objects_count", 0),
            "negative_for_task": data.get("negative_for_task", None),
        }

    def __getattr__(self, item):
        if item == "_data":
            reply = self._endpoint.get(f"recognition/v2/label/{self._id}/")
            self._data = self._extract_from(reply)
            return self._data
        raise AttributeError(self, item)


class RecognitionClient:
    """
    The umbrella wrapper class for everything related to Recognition application
    """

    def __init__(self, endpoint):
        self._endpoint = endpoint

    def new_tag(self, name: str, /, *, description: str = None, output_name: str = None) -> Label:
        """
        Creates a new label of type tag on the server
        """
        reply = self._new_label({"name": name, "type": "tag", "description": description, "output_name": output_name})
        return Label(self._endpoint, json=reply)

    def new_category(self, name: str, /, *, description: str = None, output_name: str = None) -> Label:
        """
        Creates a new label of type category on the server
        """
        reply = self._new_label(
            {"name": name, "type": "category", "description": description, "output_name": output_name}
        )
        return Label(self._endpoint, json=reply)

    def label(self, label_id: str, /):
        """
        Returns a structure with all the label properties
        """
        return Label(self._endpoint, label_id=label_id)

    def _new_label(self, args):
        return self._endpoint.post("recognition/v2/label/", args=args)
