from ximilar.client import RecognitionClient
from ximilar.client.constants import *

OBJECT_ENDPOINT = 'detection/v2/object/'


class DetectionClient(RecognitionClient):
    def __init__(self, token, endpoint=ENDPOINT, workspace=DEFAULT_WORKSPACE):
        super(DetectionClient, self).__init__(token=token, endpoint=endpoint)

        self.workspace = workspace

    def get_objects(self, page_url=None):
        """
        Get paginated result of objects.
        :param page_url: optional, select the specific page of images, default first page
        :return: (list of images, next_page)
        """
        url = page_url.replace(self.endpoint, "").replace(self.endpoint.replace("https", "http"),"") if page_url else OBJECT_ENDPOINT + "?page=1"
        result = self.get(url)
        return [DetectionObject(self.token, self.endpoint, object_json) for object_json in result[RESULTS]], result['next'], RESULT_OK

    def get_objects_of_image(self, image_id):
        result = self.get(OBJECT_ENDPOINT + "?image="+image_id)
        return [DetectionObject(self.token, self.endpoint, object_json) for object_json in result[RESULTS]], result['next'], RESULT_OK


class DetectionObject(DetectionClient):
    def __init__(self, token, endpoint, object_json):
        super(DetectionObject, self).__init__(token, endpoint)

        self.id = object_json[ID]
        self.image = object_json['image']
        self.detection_label = object_json['detection_label']
        self.data = object_json['data']
        self.recognition_labels = object_json['recognition_labels']

    def __str__(self):
        return self.detection_label["name"] + ' ' + str(self.data)
