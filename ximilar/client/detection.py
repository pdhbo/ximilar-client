from ximilar.client import RecognitionClient
from ximilar.client.constants import *

OBJECT_ENDPOINT = "detection/v2/object/"
LABEL_ENDPOINT = "detection/v2/label/"
TASK_ENDPOINT = "detection/v2/task/"
DETECT_ENDPOINT = "detection/v2/detect/"


class DetectionClient(RecognitionClient):
    def __init__(self, token, endpoint=ENDPOINT, workspace_id=DEFAULT_WORKSPACE):
        super(DetectionClient, self).__init__(token=token, endpoint=endpoint, workspace_id=workspace_id)

    def get_object(self, object_id):
        """
        Getting Bounding Box/Detection Object by id.
        :param object_id: uuid
        :return: object, status
        """
        object_json = self.get(OBJECT_ENDPOINT + object_id)
        if ID not in object_json:
            status = {STATUS: object_json[DETAIL]} if DETAIL in object_json else {STATUS: "Not Found"}
            return None, status
        return DetectionObject(self.token, self.endpoint, object_json), RESULT_OK

    def get_label(self, label_id):
        """
        Getting Bounding Box/Detection Object by id.
        :param object_id: uuid
        :return: object, status
        """
        label_json = self.get(LABEL_ENDPOINT + label_id)
        if ID not in label_json:
            return None, {STATUS: "label with id not found"}
        return DetectionLabel(self.token, self.endpoint, label_json), RESULT_OK

    def get_task(self, task_id):
        """
        Getting Detection Task by id.
        :param object_id: uuid
        :return: task, status
        """
        task_json = self.get(TASK_ENDPOINT + task_id)
        if ID not in task_json:
            status = {STATUS: task_json[DETAIL]} if DETAIL in task_json else {STATUS: "Not Found"}
            return None, status
        return DetectionTask(self.token, self.endpoint, task_json), RESULT_OK

    def get_model(self, model_id):
        pass

    def remove_object(self, object_id):
        """
        Removes detection object by id/uuid.
        """
        return self.delete(OBJECT_ENDPOINT + object_id)

    def remove_label(self, label_id):
        """
        Removes detection label by id/uuid.
        """
        return self.delete(LABEL_ENDPOINT + label_id)

    def remove_task(self, task_id):
        """
        Removes detection task by id/uuid.
        """
        return self.delete(TASK_ENDPOINT + task_id)

    def remove_model(self, object_id):
        pass

    def get_objects(self, page_url=None):
        """
        Get paginated result of objects.
        :param page_url: optional, select the specific page of images, default first page
        :return: (list of images, next_page)
        """
        url = (
            page_url.replace(self.endpoint, "").replace(self.endpoint.replace("https", "http"), "")
            if page_url
            else OBJECT_ENDPOINT + "?page=1"
        )
        result = self.get(url)
        return (
            [DetectionObject(self.token, self.endpoint, object_json) for object_json in result[RESULTS]],
            result[NEXT],
            RESULT_OK,
        )

    def get_objects_of_image(self, image_id):
        """
        Get all objects which are located on image
        :param image_id: uuid of image
        :return: list, next_page, result
        """
        result = self.get(OBJECT_ENDPOINT + "?image=" + image_id)
        return (
            [DetectionObject(self.token, self.endpoint, object_json) for object_json in result[RESULTS]],
            result[NEXT],
            RESULT_OK,
        )

    def get_all_labels(self):
        """
        Get all labels of the user(user is specified by client key).
        :return: List of labels
        """
        url, labels = LABEL_ENDPOINT, []

        while True:
            result = self.get(url)

            for label_json in result[RESULTS]:
                labels.append(DetectionLabel(self.token, self.endpoint, label_json))

            if result[NEXT] is None:
                break

            url = result[NEXT].replace(self.endpoint, "").replace(self.endpoint.replace("https", "http"), "")

        return labels, RESULT_OK

    def create_task(self, name):
        """
        Create detection task with given name.
        :param name: name of the task
        :return: Task object, status
        """
        task_json = self.post(TASK_ENDPOINT, data={NAME: name})
        if ID not in task_json:
            msg = task_json[DETAIL] if DETAIL in task_json else "unexpected error"
            return None, {STATUS: msg}
        return DetectionTask(self.token, self.endpoint, task_json), RESULT_OK

    def create_label(self, name):
        """
        Create detection label with given name.
        :param name: name of the label
        :return: Label object, status
        """
        label_json = self.post(LABEL_ENDPOINT, data={NAME: name})
        if ID not in label_json:
            return None, {STATUS: "unexpected error"}
        return DetectionLabel(self.token, self.endpoint, label_json), RESULT_OK

    def create_object(self, label_id, image_id, data):
        """
        Create detection object on some image with some label and coordinates.
        :param name: name of the label
        :return: Label object, status
        """
        label_json = self.post(OBJECT_ENDPOINT, data={LABEL_ID: label_id, IMAGE_ID: image_id, "data": data})
        if ID not in label_json:
            return None, {STATUS: "unexpected error"}
        return DetectionObject(self.token, self.endpoint, label_json), RESULT_OK


class DetectionTask(DetectionClient):
    def __init__(self, token, endpoint, task_json):
        super(DetectionTask, self).__init__(token, endpoint)

        self.id = task_json[ID]
        self.name = task_json[NAME]

    def train(self):
        """
        Create new training/model and add it to the queue.
        :return: None
        """
        return self.post(TASK_ENDPOINT + self.id + "/train/")

    def remove(self):
        self.remove_task(self.id)

    def add_label(self, label_id):
        """
        Add detection label to this task.
        :param label_id: identification of label
        :return: json/dict result
        """
        return self.post(TASK_ENDPOINT + self.id + "/add-label/", data={LABEL_ID: label_id})

    def detach_label(self, label_id):
        """
        Remove/Detach detection label from the task.
        :param label_id: identification of label
        :return: json/dict result
        """
        return self.post(TASK_ENDPOINT + self.id + "/remove-label/", data={LABEL_ID: label_id})

    def get_labels(self):
        """
        Get labels of this task.
        :return: list of Labels
        """
        if LABELS in self.cache:
            return self.cache[LABELS], RESULT_OK
        else:
            labels, result = self.get_all_labels(suffix="?task=" + self.id)

            if result[STATUS_OK] == STATUS_OK:
                self.cache[LABELS] = labels

            return self.cache[LABELS], result

    def detect(self, records, version=None):
        """
        Takes the images and calls the ximilar client for detecting these images on the task.

        Usage:
            client = DetectionClient('__YOUR_API_TOKEN__')
            task = client.get_task('__TASK_ID__')
            result = task.detect({'_url':'__URL__'})

        :param records: array of json/dicts [{'_url':'url-path'}, {'_file': ''}, {'_base64': 'base64encodeimg'}]
        :param version: optional(integer of specific version), default None/production_version
        :return: json response
        """
        records = self.preprocess_records(records)

        # version is default set to None, so ximilar will determine which one to take
        data = {RECORDS: records, TASK_ID: self.id, VERSION: version}
        return self.post(DETECT_ENDPOINT, data=data)


class DetectionLabel(DetectionClient):
    """
    DetectionLabel entity from /detection/v2/label endpoint.
    DetectionLabel is connected to DetectionTasks and can also have Recognition Tasks.
    """
    def __init__(self, token, endpoint, label_json):
        super(DetectionLabel, self).__init__(token, endpoint)

        self.id = label_json[ID]
        self.name = label_json[NAME]

    def __str__(self):
        return self.name

    def remove(self):
        pass

    def add_recognition_task(self, label_id):
        """
        Add recognition task to this label.
        :param label_id: identification of label
        :return: json/dict result
        """
        return self.post(TASK_ENDPOINT + self.id + "/add-label/", data={LABEL_ID: label_id})

    def detach_recognition_task(self, label_id):
        """
        Remove/Detach recognition task from label.
        :param label_id: identification of label
        :return: json/dict result
        """
        return self.post(TASK_ENDPOINT + self.id + "/remove-label/", data={LABEL_ID: label_id})


class DetectionObject(DetectionClient):
    """
    Object/Bounding Box entity from /detection/v2/object endpoint.
    Every Object is located on some image and represents some detection label with coordinates (data).
    Coordinates are [xmin, ymin, xmax, ymax].
    Every object can also contain recognition labels.
    """
    def __init__(self, token, endpoint, object_json):
        super(DetectionObject, self).__init__(token, endpoint)

        self.id = object_json[ID]
        self.image = object_json[IMAGE]
        self.detection_label = object_json[DETECTION_LABEL]
        self.data = object_json[DATA]
        self.recognition_labels = object_json[RECOGNITION_LABELS]

    def remove(self):
        pass

    def add_recognition_label(self, label_id):
        """
        Add recognition label to the object.
        :param label_id: id (uuid) of label
        :return: result
        """
        pass

    def detach_recognition_label(self, label_id):
        """
        Detech recognition label from the object.
        :param label_id: id (uuid) of label
        :return: result
        """
        pass

    def __str__(self):
        return self.detection_label[NAME] + " " + str(self.data)
