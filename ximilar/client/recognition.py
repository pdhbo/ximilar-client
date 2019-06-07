import requests

from ximilar.client import RestClient
from ximilar.client.constants import *


LABEL_ENDPOINT = "recognition/v2/label/"
TASK_ENDPOINT = "recognition/v2/task/"
MODEL_ENDPOINT = "recognition/v2/model/"
IMAGE_ENDPOINT = "recognition/v2/training-image/"
CLASSIFY_ENDPOINT = "recognition/v2/classify/"
WORKSPACE_ENDPOINT = "account/v2/workspace/"


class RecognitionClient(RestClient):
    """
    Base Client for Ximilar Custom Image Recognition Service.
    """

    def __init__(
        self,
        token,
        endpoint=ENDPOINT,
        workspace=DEFAULT_WORKSPACE,
        max_image_size=512,
        resource_name=CUSTOM_IMAGE_RECOGNITION,
    ):
        self.workspace = workspace  # this must be set before calling supers
        super(RecognitionClient, self).__init__(
            token=token, endpoint=endpoint, max_image_size=max_image_size, resource_name=resource_name
        )

    def get(self, api_endpoint, data=None, params=None):
        """
        Calling get request to the API.
        """
        return super().get(api_endpoint, data=data, params=self.add_workspace(params, api_endpoint))

    def post(self, api_endpoint, data=None, files=None, params=None, method=requests.post):
        """
        Calling post request to the API.
        """
        return super().post(api_endpoint, data=self.add_workspace(data), files=files, params=params, method=method)

    def put(self, api_endpoint, data=None, files=None, params=None):
        """
        Calling put request to the API.
        """
        return super().put(api_endpoint, data=self.add_workspace(data), files=files, params=params)

    def delete(self, api_endpoint, data=None, params=None):
        """
        Calling delete request to the API.
        """
        return super().delete(api_endpoint, data=data, params=self.add_workspace(params))

    def add_workspace(self, data, url=None):
        """
        Add workspace uuid to the data.
        :param data: dictionary/json data which will be send to endpoint
        :return: modified json data with workspace
        """

        if self.workspace != DEFAULT_WORKSPACE:
            if data is None:
                data = {}

            # if workspace is already in url then do not create the param
            if url is not None and self.workspace not in url:
                data[WORKSPACE] = self.workspace
            elif url is None:
                data[WORKSPACE] = self.workspace
        return data

    def get_workspaces(self):
        """
        Get all workspaces accessed by user.
        """
        workspaces, status = self.get_all_paginated_items(WORKSPACE_ENDPOINT)

        if not workspaces and status[STATUS] == STATUS_ERROR:
            return None, status

        return [Workspace(self.token, self.endpoint, w_json) for w_json in workspaces], RESULT_OK

    def get_task(self, task_id):
        """
        Getting recognition task by the id/uuid.
        """
        task_json = self.get(TASK_ENDPOINT + task_id)
        if ID not in task_json:
            status = {STATUS: task_json[DETAIL]} if DETAIL in task_json else {STATUS: "Not Found"}
            return None, status
        return Task(self.token, self.endpoint, task_json), RESULT_OK

    def get_label(self, label_id):
        """
        Getting recognition label by the id/uuid.
        """
        label_json = self.get(LABEL_ENDPOINT + label_id)
        if ID not in label_json:
            return None, {STATUS: "label with id not found"}
        return Label(self.token, self.endpoint, label_json), RESULT_OK

    def get_model(self, model_id):
        """
        Getting recognition model by the id/uuid.
        """
        model_json = self.get(MODEL_ENDPOINT + model_id)
        if ID not in model_json:
            status = {STATUS: model_json[DETAIL]} if DETAIL in model_json else {STATUS: "Not Found"}
            return None, status
        return Model(self.token, self.endpoint, model_json), RESULT_OK

    def get_image(self, image_id):
        """
        Getting recognition image by the id/uuid.
        """
        image_json = self.get(IMAGE_ENDPOINT + image_id)
        if ID not in image_json:
            return None, {STATUS: "image with id not found"}
        return Image(self.token, self.endpoint, image_json), RESULT_OK

    def get_all_tasks(self, suffix=""):
        """
        Get all tasks of the user(user is specified by client key).
        :return: List of Tasks
        """
        tasks, status = self.get_all_paginated_items(TASK_ENDPOINT + suffix)

        if not tasks and status[STATUS] == STATUS_ERROR:
            return None, status

        return [Task(self.token, self.endpoint, t_json) for t_json in tasks], RESULT_OK

    def get_all_labels(self, suffix=""):
        """
        Get all labels of the user(user is specified by client key).
        :return: List of labels
        """
        labels, status = self.get_all_paginated_items(LABEL_ENDPOINT + suffix)

        if not labels and status[STATUS] == STATUS_ERROR:
            return None, status

        return [Label(self.token, self.endpoint, l_json) for l_json in labels], RESULT_OK

    def get_tasks_by_name(self, name):
        """
        Get all tasks with the name.
        """
        tasks, result = self.get_all_tasks()

        tasks_to_return = []
        if result[STATUS] == STATUS_OK:
            for task in tasks:
                if task.name == name:
                    tasks_to_return.append(task)
        else:
            return None, result

        if len(tasks_to_return) > 0:
            return tasks_to_return, result

        return None, {STATUS: "Task with this name not found!"}

    def get_training_images(self, page_url=None, verification=None):
        """
        Get paginated result of images from workspace.
        :param page_url: optional, select the specific page of images, default first page
        :param verification: optional, integer which says how many verifications should have the images
        :return: (list of images, next_page)
        """
        url = (
            page_url.replace(self.endpoint, "").replace(self.endpoint.replace("https", "http"), "")
            if page_url
            else IMAGE_ENDPOINT + "?page=1"
        )
        url += "&verification=" + str(verification) if verification is not None else ""

        result = self.get(url)
        return (
            [Image(self.token, self.endpoint, image_json) for image_json in result[RESULTS]],
            result[NEXT],
            RESULT_OK,
        )

    def get_labels_by_substring(self, name):
        """
        Return all labels of the workspace which contains the substring.
        """
        labels, result = self.get_all_labels(suffix="?search=" + name)

        if len(labels) > 0:
            return labels, result
        else:
            return None, {STATUS: "No labels found"}

    def remove_model(self, model_id):
        """
        Remove recognition model by id/uuid.
        """
        return self.delete(MODEL_ENDPOINT + model_id + "/")

    def remove_task(self, task_id):
        """
        Remove recognition task by id/uuid.
        """
        return self.delete(TASK_ENDPOINT + task_id + "/")

    def remove_label(self, label_id):
        """
        Remove recognition label by id/uuid.
        """
        return self.delete(LABEL_ENDPOINT + label_id)

    def remove_image(self, image_id):
        """
        Remove recognition image by id/uuid.
        """
        return self.delete(IMAGE_ENDPOINT + image_id)

    def create_task(self, name, task_type=MULTI_CLASS):
        """
        Create task with given name.
        :param name: name of the task
        :param task_type: 'multi_class' (CATEGORIZATION default) or 'multi_label' (TAGGING)
        :return: Task object, status
        """
        data = {NAME: name, TASK_TYPE: task_type}
        task_json = self.post(TASK_ENDPOINT, data=data)
        if ID not in task_json:
            msg = task_json[DETAIL] if DETAIL in task_json else "unexpected error"
            return None, {STATUS: msg}
        return Task(self.token, self.endpoint, task_json), RESULT_OK

    def create_label(self, name, description=None, label_type=CATEGORY):
        """
        Create label with given name.
        :param name: name of the label
        :param label_type: type of label to create (category or tag)
        :return: Label object, status
        """
        data = {NAME: name, LABEL_TYPE: label_type, DESCRIPTION: description}
        label_json = self.post(LABEL_ENDPOINT, data=data)
        if ID not in label_json:
            return None, {STATUS: "unexpected error"}
        return Label(self.token, self.endpoint, label_json), RESULT_OK

    def upload_images(self, records):
        """
        Upload one or more files and add labels to them.
        :param records: list of dictionaries with labels and one of '_base64', '_file', '_url'
                        specify noresize: True to save image without (default False)
                       [{'_file': '__FILE_PATH__', 'labels': ['__UUID_1__', '__UUID_2__'], noresize: False}, ...]
        :return: image, status
        """
        images = []
        worst_status = RESULT_OK
        for record in records:
            files, data = None, None
            noresize = NORESIZE in record and record[NORESIZE]
            metadata = record[META_DATA] if META_DATA in record and record[META_DATA] else {}

            if FILE in record:
                # We cannot send files to request along with json data (for workspace)
                # That is why we load image from disk to base64 representation
                data = {
                    "base64": self.load_base64_file(record[FILE], resize=not noresize),
                    NORESIZE: noresize,
                    META_DATA: metadata,
                }
            elif BASE64 in record:
                data = {"base64": record[BASE64].decode("utf-8"), NORESIZE: noresize, META_DATA: metadata}
            elif URL in record:
                data = {
                    "base64": self.load_url_image(record[URL], resize=not noresize),
                    NORESIZE: noresize,
                    META_DATA: metadata,
                }

            image_json = self.post(IMAGE_ENDPOINT, files=files, data=data)
            if ID not in image_json:
                worst_status = {STATUS: "image not uploaded " + str(record)}
                continue

            image = Image(self.token, self.endpoint, image_json)

            if LABELS in record:
                for label_id in record[LABELS]:
                    image.add_label(label_id)

            images.append(image)
        return images, worst_status


class Task(RecognitionClient):
    """
    Task entity from /recognition/v2/task endpoint.
    Every task can have multiple recognition labels.
    """

    def __init__(self, token, endpoint, task_json):
        super(Task, self).__init__(token, endpoint)

        self.id = task_json[ID]
        self.name = task_json[NAME]
        self.type = task_json[TYPE]
        self.production_version = task_json[PRODUCTION_VERSION]
        self.workspace = task_json[WORKSPACE] if WORKSPACE in task_json else DEFAULT_WORKSPACE
        self.description = task_json[DESCRIPTION] if DESCRIPTION in task_json else ""

    def __str__(self):
        return self.name

    def train(self):
        """
        Create new training/model and add it to the queue.
        :return: None
        """
        return self.post(TASK_ENDPOINT + self.id + "/train/")

    def remove(self):
        """
        Delete the recognition task from ximilar.
        """
        self.remove_task(self.id)

    def get_negative_label(self):
        """
        If the task is Tagging/Multi-Label then this will return the negative label of the Task.
        """
        labels = self.get_labels()

        for label in labels:
            if label.negative_for_task:
                return label, RESULT_OK

        return None, RESULT_OK

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

    def get_label_by_name(self, name):
        """
        Get label with specified name which also belongs to this task.
        """
        labels, result = self.get_labels()
        if result[STATUS] == STATUS_OK:
            for label in labels:
                if label.name == name:
                    return label, RESULT_OK
        else:
            return None, result

        return None, {STATUS: "Label with this name not found!"}

    def classify(self, records, version=None):
        """
        Takes the images and calls the ximilar client for classifying these images on the task.

        Usage:
            client = RecognitionClient('__YOUR_API_TOKEN__')
            task, status = client.get_task('__ID_OF_TASK__')
            result = task.classify({'_url':'__SOME_IMG_URL__'})

        :param records: array of json/dicts [{'_url':'url-path'}, {'_file': ''}, {'_base64': 'base64encodeimg'}]
        :param version: optional(integer of specific version), default None/production_version
        :return: json response
        """
        records = self.preprocess_records(records)

        # version is default set to None, so ximilar will determine which one to take
        data = {RECORDS: records, TASK_ID: self.id, VERSION: version}
        return self.post(CLASSIFY_ENDPOINT, data=data)

    def add_label(self, label_id):
        """
        Add label to this task.
        :param label_id: identification of label
        :return: json/dict result
        """
        return self.post(TASK_ENDPOINT + self.id + "/add-label/", data={LABEL_ID: label_id})

    def detach_label(self, label_id):
        """
        Remove/Detach label from the task.
        :param label_id: identification of label
        :return: json/dict result
        """
        return self.post(TASK_ENDPOINT + self.id + "/remove-label/", data={LABEL_ID: label_id})


class Model(RecognitionClient):
    """
    Model entity from /recognition/v2/mode endpoint.
    Every model represents model/neural network which is trained or waiting for training.
    """

    def __init__(self, token, endpoint, model_json):
        super(Model, self).__init__(token, endpoint)

        self.id = model_json[ID]
        self.task_id = model_json[TASK]
        self.task_name = model_json[TASK_NAME]
        self.version = model_json[VERSION]
        self.train_status = model_json[TRAIN_STATUS]

    def remove(self):
        self.delete_model(self.id)

    def __str__(self):
        return self.task_name + " (" + self.train_status + ")"


class Label(RecognitionClient):
    """
    Label entity from /recognition/v2/label endpoint.
    Every label can be assigned to multiple tasks.
    """

    def __init__(self, token, endpoint, label_json):
        super(Label, self).__init__(token, endpoint)

        self.id = label_json[ID]
        self.name = label_json[NAME]
        self.tasks_count = label_json[TASKS_COUNT] if TASKS_COUNT in label_json else 0
        self.negative_for_task = label_json[NEGATIVE_FOR_TASK] if NEGATIVE_FOR_TASK in label_json else None
        self.workspace = label_json[WORKSPACE] if WORKSPACE in label_json else DEFAULT_WORKSPACE
        self.images_count = label_json[IMAGES_COUNT] if IMAGES_COUNT in label_json else 0
        self.description = label_json[DESCRIPTION] if DESCRIPTION in label_json else ""

    def __str__(self):
        return self.name

    def wipe(self):
        """
        Delete label and all images associated with this label.
        :return: None
        """
        self.delete(LABEL_ENDPOINT + self.id + "/wipe")

    def get_images_count(self):
        """
        Get count of the images connected to this label.
        :return:
        """
        label_json = self.get(LABEL_ENDPOINT + self.id)

        if IMAGES_COUNT in label_json:
            self.images_count = label_json[IMAGES_COUNT]

        return self.images_count

    # TODO: get object count
    # TODO: get objects of given label

    def get_training_images(self, page_url=None, verification=None):
        """
        Get paginated result of images for specific label.

        :param page_url: optional, select the specific page of images, default first page
        :return: (list of images, next_page)
        """
        url = (
            page_url.replace(self.endpoint, "").replace(self.endpoint.replace("https", "http"), "")
            if page_url
            else IMAGE_ENDPOINT + "?label=" + self.id
        )
        result = self.get(url)
        return (
            [Image(self.token, self.endpoint, image_json) for image_json in result[RESULTS]],
            result[NEXT],
            RESULT_OK,
        )

    def upload_images(self, records):
        """
        Upload image to the ximilar.com and adding label to this image.
        :param records: list of files with _url, _base64, _file.
        :return: None
        """
        for i in range(len(records)):
            if LABELS in records[i]:
                records[i][LABELS].append(self.id)
            else:
                records[i][LABELS] = [self.id]
        return super(Label, self).upload_images(records)

    def detach_image(self, image_id):
        """
        Remove/Detach label from the image.
        :param image_id: id of label
        :return: result
        """
        return self.post(IMAGE_ENDPOINT + image_id + "/remove-label/", data={LABEL_ID: self.id})

    def remove(self):
        return self.remove_label(self.id)


class Image(RecognitionClient):
    """
    Image entity from /recognition/v2/image endpoint.
    Every image can have multiple recognition labels.
    """

    def __init__(self, token, endpoint, image_json):
        super(Image, self).__init__(token, endpoint)

        self.id = image_json[ID]
        self.img_path = image_json[IMG_PATH]
        self.thumb_img_path = image_json[THUMB_IMG_PATH]
        self.verifyCount = image_json[VERIFY_COUNT] if VERIFY_COUNT in image_json else -1
        self.workspace = image_json[WORKSPACE] if WORKSPACE in image_json else DEFAULT_WORKSPACE
        self.img_width = image_json[IMG_WIDTH]
        self.img_height = image_json[IMG_HEIGHT]
        self.meta_data = image_json[META_DATA] if META_DATA in image_json and image_json[META_DATA] else {}

        # file path after calling download_image on this object
        self._file = None

    def __str__(self):
        return self.thumb_img_path

    def remove(self):
        """
        Remove image from system.
        """
        return self.remove_image(self.id)

    def get_labels(self):
        """
        Get labels assigned to this image.
        :return: list of Labels
        """
        if LABELS not in self.cache:
            labels = [Label(self.token, self.endpoint, label) for label in self.get(IMAGE_ENDPOINT + self.id)[LABELS]]
        else:
            labels = self.cache[LABELS]

        return labels, RESULT_OK

    def add_label(self, label_id):
        """
        Add label to the image.
        :param label_id: id of label
        :return: result
        """
        return self.post(IMAGE_ENDPOINT + self.id + "/add-label/", data={LABEL_ID: label_id})

    def detach_label(self, label_id):
        """
        Remove/Detach label from the image.
        :param label_id: id of label
        :return: result
        """
        return self.post(IMAGE_ENDPOINT + self.id + "/remove-label/", data={LABEL_ID: label_id})

    def download(self, destination=""):
        """
        Download image to the destination and store path to the _file of the object.
        :param destination: path on the disk
        :return: path of the file locally
        """
        self._file = super().download_image(self.img_path, destination=destination)
        return self._file

    def add_meta_data(self, meta_data):
        """
        Add some meta data to image (extends already present meta data).
        """
        if meta_data is None or not isinstance(meta_data, dict):
            raise Exception("Please specify dictionary of meta_data as param!")

        new_data = dict(list(self.meta_data.items()) + list(meta_data.items()))
        result = self.put(IMAGE_ENDPOINT + self.id, data={META_DATA: new_data})
        self.meta_data = result[META_DATA]
        return True

    def clear_meta_data(self):
        """
        Clear all meta data of image.
        """
        result = self.put(IMAGE_ENDPOINT + self.id, data={META_DATA: {}})
        self.meta_data = result[META_DATA]
        return True

    def extract_object_data(self, object_bbox, image_download_dir=""):
        """
        Extracting object/bounding box data from image.
        :param object_bbox: [xmin, ymin, xmax, ymax]
        :param image_download_dir directory to download the image before cutting the object
        :return: dict / { "img_data": [[]...], "color_space": "RGB"}
        """
        assert len(object_bbox) == 4

        self.download(image_download_dir)
        image = self.cv2_imread(self._file)
        return {
            IMG_DATA: image[int(object_bbox[1]) : int(object_bbox[3]), int(object_bbox[0]) : int(object_bbox[2])],
            COLOR_SPACE: "BGR",
        }

    def verify(self, user_id):
        """
        Verify this image by some user.
        """
        return self.post("annotate/v2/verification/", data={USER: user_id, IMAGE_ID: self.id})


class Workspace(RecognitionClient):
    """
    Workspace entity. All Task, Labels and Images are mapped to some workspace.
    Every workspace has some owner.
    """

    def __init__(self, token, endpoint, workspace_json):
        super().__init__(token, endpoint, workspace_json[ID])
        self.id = workspace_json[ID]
        self.name = workspace_json[NAME]
        self.owner = workspace_json[OWNER] if OWNER in workspace_json else None

    def __str__(self):
        return "Worskpace: (%s) (%s)" % (self.name, self.id)
