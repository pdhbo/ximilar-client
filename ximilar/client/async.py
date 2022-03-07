import requests
import json

from ximilar.client import RecognitionClient
from ximilar.client.constants import *
from ximilar.client.exceptions import XimilarClientInvalidDataException


REQUEST_ENDPOINT = "account/v2/request/"


class AsyncRClient(RecognitionClient):
    def __init__(
        self, token, endpoint=ENDPOINT, workspace=DEFAULT_WORKSPACE,
    ):
        super().__init__(
            token=token, endpoint=endpoint, workspace=workspace, resource_name=None,
        )

    def get_request(self, id):
        result = self.get(REQUEST_ENDPOINT + id)
        return AsynchronousRequest(self.token, self.endpoint, self.workspace, result), STATUS_OK

    def submit(self, request, type, **kwargs):
        data = request
        data["type"] = type
        data.update(kwargs)
        result = self.post(REQUEST_ENDPOINT, data=data)
        return AsynchronousRequest(self.token, self.endpoint, self.workspace, result)


class AsynchronousRequest(AsyncRClient):
    def __init__(self, token, endpoint, workspace, async_json):
        super().__init__(token, endpoint=endpoint, workspace=workspace)

        self.id = async_json["id"]
        self.status = async_json["status"]
        self.type = async_json["type"]
        self.response = async_json["response"] if "response" in async_json else None

    def __str__(self) -> str:
        return self.id

    def update(self):
        if self.response is None:
            if self.check_status() == "DONE":
                request, _ = self.get_request(self.id)
                self.status = request.status
                self.response = request.response
                return True
        return False

    def check_status(self):
        result = self.get(REQUEST_ENDPOINT + self.id + "/status")
        self.status = result["status"]
        return self.status
