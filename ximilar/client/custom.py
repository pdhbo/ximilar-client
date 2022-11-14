from ximilar.client.recognition import RecognitionClient
from ximilar.client.constants import *


class CustomPredictClient(RecognitionClient):
    def __init__(self, token, endpoint=ENDPOINT, resource_name="custom-model"):
        super().__init__(token=token, endpoint=endpoint, resource_name=resource_name)
        self.PREDICT_ENDPOINT = "custom/v2/predict"

    def predict(self, records, task_id, version=None):
        """
        Takes the images and calls the ximilar client for extracting custom outputs.
        """
        # version is default set to None, so ximilar will determine which one to take
        data = self.construct_data(records=records, task_id=task_id, version=version)
        result = self.post(self.PREDICT_ENDPOINT, data=data)

        self.check_json_status(result)
        return result
