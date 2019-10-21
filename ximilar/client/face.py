from ximilar.client import RestClient
from ximilar.client.constants import *

FACE_DETECTION_ENDPOINT = "face/v2/detect"


class FaceClient(RestClient):
    def detect(self, records):
        records = self.preprocess_records(records)
        return self.post(FACE_DETECTION_ENDPOINT, data={RECORDS: records})
