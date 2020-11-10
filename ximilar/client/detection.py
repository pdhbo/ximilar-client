from ximilar.client import RecognitionClient
from ximilar.client.recognition import Image, IMAGE_ENDPOINT
from ximilar.client.constants import *
from ximilar.client.recognition import Image, IMAGE_ENDPOINT

OBJECT_ENDPOINT = "detection/v2/object/"
LABEL_ENDPOINT = "detection/v2/label/"
TASK_ENDPOINT = "detection/v2/task/"
DETECT_ENDPOINT = "detection/v2/detect/"


class DetectionClient(RecognitionClient):
    def __init__(
        self,
        token,
        endpoint=ENDPOINT,
        workspace=DEFAULT_WORKSPACE,
        max_image_size=1024,
        resource_name=CUSTOM_OBJECT_DETECTION,
    ):
        super(DetectionClient, self).__init__(
            token=token,
            endpoint=endpoint,
            workspace=workspace,
            max_image_size=max_image_size,
            resource_name=resource_name,
        )
        self.PREDICT_ENDPOINT = DETECT_ENDPOINT

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
        return DetectionTask(self.token, self.endpoint, task_json, self.max_image_size), RESULT_OK

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
        Get paginated result of all Detection Objects in your workspace.
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
        Get all Detection Objects which are located on image.
        :param image_id: uuid of image
        :return: list, result
        """
        objects, status = self.get_all_paginated_items(OBJECT_ENDPOINT + "?image=" + image_id)

        if not objects and status[STATUS] == STATUS_ERROR:
            return None, status

        return [DetectionObject(self.token, self.endpoint, o_json) for o_json in objects], RESULT_OK

    def get_all_tasks(self, suffix=""):
        """
        Get all Detection Tasks of the user(user is specified by client key).
        :return: List of Tasks
        """
        tasks, status = self.get_all_paginated_items(TASK_ENDPOINT + suffix)

        if not tasks and status[STATUS] == STATUS_ERROR:
            return None, status

        return [DetectionTask(self.token, self.endpoint, t_json, self.max_image_size) for t_json in tasks], RESULT_OK

    def get_all_labels(self, suffix=""):
        """
        Get all Detection Labels of the user(user is specified by client key).
        :return: List of labels
        """
        labels, status = self.get_all_paginated_items(LABEL_ENDPOINT + suffix)

        if not labels and status[STATUS] == STATUS_ERROR:
            return None, status

        return [DetectionLabel(self.token, self.endpoint, l_json) for l_json in labels], RESULT_OK

    def create_task(self, name, description=None):
        """
        Create detection task with given name.
        :param name: name of the task
        :param description: description of the label
        :return: Task object, status
        """
        task_json = self.post(TASK_ENDPOINT, data={NAME: name, DESCRIPTION: description})
        if ID not in task_json:
            msg = task_json[DETAIL] if DETAIL in task_json else "unexpected error"
            return None, {STATUS: msg}
        return DetectionTask(self.token, self.endpoint, task_json, self.max_image_size), RESULT_OK

    def create_label(self, name, description=None, color="#FFFFFF"):
        """
        Create detection label with given name.
        :param name: name of the label
        :param description: description of the label
        :param color: color (hexadecimal color code) of the label
        :return: Label object, status
        """
        label_json = self.post(LABEL_ENDPOINT, data={NAME: name, DESCRIPTION: description, COLOR: color})
        if ID not in label_json:
            return None, {STATUS: "unexpected error"}
        return DetectionLabel(self.token, self.endpoint, label_json), RESULT_OK

    def create_object(self, label_id, image_id, data, meta_data=None):
        """
        Create detection object on some image with some label and coordinates.
        :param label_id: id of detection label
        :param image_id: id of image
        :param data: [xmin, ymin, xmax, ymax] represent bounding box
        :param meta_data: json/dict of additional meta data
        :return: DetectionObject
        """
        label_json = self.post(
            OBJECT_ENDPOINT, data={DETECTION_LABEL: label_id, IMAGE: image_id, DATA: data, META_DATA: meta_data}
        )
        if ID not in label_json:
            return None, {STATUS: "unexpected error"}
        return DetectionObject(self.token, self.endpoint, label_json), RESULT_OK

    def upload_images(self, records):
        """
        Upload one or more files and add objects associated with them.
        :param records: list of dictionaries with objects and one of '_base64', '_file', '_url'
                        specify noresize: True to save image without (default False)
                        [
                            {
                                '_file': '__FILE_PATH__',
                                'objects': [
                                    'detection_label': '__UUID__'
                                    'data': [__xmin__, __ymin__, __xmax__, __ymax__],
                                    'metadata': {__metadata__}
                                ],
                                'noresize': False,
                             },
                             ...
                        ]
        :return: image, status
        """
        images = []
        worst_status = RESULT_OK
        for record in records:
            files, data = None, None
            noresize = NORESIZE in record and record[NORESIZE]
            noresize_on_server = noresize or self.max_image_size > 1024
            metadata = record[META_DATA] if META_DATA in record and record[META_DATA] else {}
            test_image = record[TEST_IMAGE] if TEST_IMAGE in record else False

            data = self._create_image_data(record, noresize, noresize_on_server, test_image, metadata)

            image_json = self.post(IMAGE_ENDPOINT, files=files, data=data)

            if image_json is None:
                worst_status = {STATUS: "image not uploaded " + str(record)}
                continue
            elif ID not in image_json:
                worst_status = {STATUS: "image not uploaded " + str(record)}
                continue

            image = Image(self.token, self.endpoint, image_json)

            if OBJECTS in record:
                for object in record[OBJECTS]:
                    self.create_object(object[DETECTION_LABEL], image.id, object[DATA], object[META_DATA])

            images.append(image)
        return images, worst_status

    def construct_data(self, records=[], task_id=None, version=None, store_images=None):
        if len(records) == 0:
            raise Exception("Please specify at least one record in detect method!")

        if task_id is None:
            raise Exception("Please specify task")

        data = {RECORDS: self.preprocess_records(records), TASK_ID: task_id, VERSION: version}

        if store_images:
            data[STORE_IMAGES] = True

        return data

    def detect_on_task(self, records=[], task_id=None, version=None):
        """
        Takes the images and calls the ximilar client for detection these images on the task.

        Usage:
            client = DetectionClient('__YOUR_API_TOKEN__')
            result = client.detect_on_task({'_url':'__SOME_IMG_URL__'}, task_id="__UUID__")

        :param records: array of json/dicts [{'_url':'url-path'}, {'_file': ''}, {'_base64': 'base64encodeimg'}]
        :param task_id: id of task 
        :param version: optional(integer of specific version), default None/production_version
        :return: json response
        """
        # version is default set to None, so ximilar will determine which one to take
        data = self.construct_data(records=records, task_id=task_id, version=version)
        result = self.post(self.PREDICT_ENDPOINT, data=data)

        self.check_json_status(result)
        return result


class DetectionTask(DetectionClient):
    def __init__(self, token, endpoint, task_json, max_image_size):
        super(DetectionTask, self).__init__(token, endpoint, max_image_size=max_image_size, resource_name=None)

        self.id = task_json[ID]
        self.name = task_json[NAME]
        self.description = task_json[DESCRIPTION] if DESCRIPTION in task_json else ""
        self.workspace = task_json[WORKSPACE] if WORKSPACE in task_json else DEFAULT_WORKSPACE

    def train(self):
        """
        Create new training/model and add it to the queue.
        :return: None
        """
        return self.post(TASK_ENDPOINT + self.id + "/train/")

    def remove(self):
        """
        Removes Detection Task.
        """
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

            if result[STATUS] == STATUS_OK:
                self.cache[LABELS] = labels

            return self.cache[LABELS], result

    def add_negative_image(self, image_id):
        """
        Add negative image to the detection task
        :param image_id: negative image ID to link with detection task
        :return: json/dict result
        """
        return self.post(TASK_ENDPOINT + self.id + "/add-image/", data={IMAGE_ID: image_id})

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

    def to_json(self):
        labels, status = self.get_labels()
        return {TASK_ID: self.id, NAME: self.name, LABELS: [label.id for label in labels]}


class DetectionLabel(DetectionClient):
    """
    DetectionLabel entity from /detection/v2/label endpoint.
    DetectionLabel is connected to DetectionTasks and can also have Recognition Tasks.
    """

    def __init__(self, token, endpoint, label_json):
        super(DetectionLabel, self).__init__(token, endpoint, resource_name=None)

        self.id = label_json[ID]
        self.name = label_json[NAME]
        self.description = label_json[DESCRIPTION] if DESCRIPTION in label_json else ""
        self.workspace = label_json[WORKSPACE] if WORKSPACE in label_json else DEFAULT_WORKSPACE
        self.recognition_tasks = label_json[RECOGNITION_TASKS] if RECOGNITION_TASKS in label_json else None
        self.color = label_json[COLOR]
        self.output_name = (
            label_json[OUTPUT_NAME] if OUTPUT_NAME in label_json and label_json[OUTPUT_NAME] else self.name
        )

    def __str__(self):
        return self.name

    def remove(self):
        """
        Removes detection label.
        """
        return self.remove_label(self.id)

    def get_images(self):
        images, status = self.get_all_paginated_items(IMAGE_ENDPOINT + "?detection_labels=" + self.id)
        if not images and status[STATUS] == STATUS_ERROR:
            return None, status
        return [Image(self.token, self.endpoint, image) for image in images], RESULT_OK

    def get_training_images(self, page_url=None, verification=None):
        """
        Get paginated result of images for specific label.

        :param page_url: optional, select the specific page of images, default first page
        :return: (list of images, next_page)
        """
        if page_url is None:
            page_url = IMAGE_ENDPOINT + "?detection_labels=" + self.id

        return super().get_training_images(page_url=page_url, verification=verification)

    def add_recognition_task(self, task_id):
        """
        Add recognition task to this label.
        :param label_id: identification of label
        :return: json/dict result
        """
        return self.post(LABEL_ENDPOINT + self.id + "/add-task/", data={TASK_ID: task_id})

    def detach_recognition_task(self, task_id):
        """
        Remove/Detach recognition task from label.
        :param label_id: identification of label
        :return: json/dict result
        """
        return self.post(LABEL_ENDPOINT + self.id + "/remove-task/", data={TASK_ID: task_id})

    def to_json(self):
        return {LABEL_ID: self.id, NAME: self.name, RECOGNITION_TASKS: self.recognition_tasks}


class DetectionObject(DetectionClient):
    """
    Object/Bounding Box entity from /detection/v2/object endpoint.
    Every Object is located on some image and represents some detection label with coordinates (data).
    Coordinates are [xmin, ymin, xmax, ymax].
    Every object can also contain recognition labels.
    """

    def __init__(self, token, endpoint, object_json):
        super(DetectionObject, self).__init__(token, endpoint, resource_name=None)

        self.id = object_json[ID]
        self.image = object_json[IMAGE]
        self.detection_label = object_json[DETECTION_LABEL]
        self.data = object_json[DATA]
        self.recognition_labels = object_json[RECOGNITION_LABELS]
        # if the meta data was downloaded from the server, this field is never None
        self.meta_data = (
            None if META_DATA not in object_json else (object_json[META_DATA] if object_json[META_DATA] else {})
        )

    def remove(self):
        """
        Removes detection object.
        """
        return self.remove_object(self.id)

    def add_recognition_label(self, label_id):
        """
        Add recognition label to the object.
        :param label_id: id (uuid) of label
        :return: result
        """
        return self.post(OBJECT_ENDPOINT + self.id + "/add-label/", data={LABEL_ID: label_id})

    def detach_recognition_label(self, label_id):
        """
        Detach recognition label from the object.
        :param label_id: id (uuid) of label
        :return: result
        """
        return self.post(OBJECT_ENDPOINT + self.id + "/remove-label/", data={LABEL_ID: label_id})

    def _ensure_meta_data(self):
        """
        If the meta_data were not downloaded yet, do so
        """
        if not self.meta_data:
            self.meta_data = self.get(OBJECT_ENDPOINT + self.id)[META_DATA]
        if not self.meta_data:
            self.meta_data = {}

    def get_meta_data(self):
        """
        Return the image meta data (dictionary) or empty dictionary
        :return: None is never returned
        """
        self._ensure_meta_data()
        return self.meta_data

    def add_meta_data(self, meta_data):
        """
        Add some meta data to image (extends already present meta data).
        """
        self._ensure_meta_data()
        if meta_data is None or not isinstance(meta_data, dict):
            raise Exception("Please specify dictionary of meta_data as param!")

        new_data = dict(list(self.meta_data.items()) + list(meta_data.items()))
        result = self.put(
            OBJECT_ENDPOINT + self.id,
            data={DATA: self.data, DETECTION_LABEL: self.detection_label[ID], META_DATA: new_data},
        )
        self.meta_data = result[META_DATA]
        return True

    def clear_meta_data(self):
        """
        Clear all meta data of image.
        """
        result = self.put(
            OBJECT_ENDPOINT + self.id, data={DATA: self.data, DETECTION_LABEL: self.detection_label[ID], META_DATA: {}}
        )
        self.meta_data = result[META_DATA]
        return True

    def to_json(self):
        return {
            IMAGE: self.image,
            ID: self.id,
            DETECTION_LABEL: self.detection_label,
            DATA: self.data,
            LABELS: self.recognition_labels,
            META_DATA: self.meta_data,
        }

    def get_bbox(self):
        return self.data

    def __str__(self):
        return self.id + " " + self.detection_label
