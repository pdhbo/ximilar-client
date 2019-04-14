from ximilar.client import RestClient
from ximilar.client.constants import *


LABEL_ENDPOINT = "recognition/v2/label/"
TASK_ENDPOINT = "recognition/v2/task/"
MODEL_ENDPOINT = "recognition/v2/model/"
IMAGE_ENDPOINT = "recognition/v2/training-image/"
CLASSIFY_ENDPOINT = "recognition/v2/classify/"
OBJECT_ENDPOINT = "detection/v2/object/"


class RecognitionClient(RestClient):
    def __init__(self, token, endpoint=ENDPOINT, workspace=DEFAULT_WORKSPACE):
        super(RecognitionClient, self).__init__(token=token, endpoint=endpoint)

        self.workspace = workspace

    def get_task(self, task_id):
        """
        Getting task by id.
        :param task_id: id of task
        :return: Task object
        """
        task_json = self.get(TASK_ENDPOINT + task_id)
        if "id" not in task_json:
            status = {"status": task_json["detail"]} if "detail" in task_json else {"status": "Not Found"}
            return None, status
        return Task(self.token, self.endpoint, task_json), RESULT_OK

    def get_model(self, model_id):
        model_json = self.get(MODEL_ENDPOINT + model_id)
        if "id" not in model_json:
            status = {"status": model_json["detail"]} if "detail" in model_json else {"status": "Not Found"}
            return None, status
        return Model(self.token, self.endpoint, model_json), RESULT_OK

    def get_all_tasks(self, suffix=""):
        """
        Get all tasks of the user(user is specified by client key).
        :return: List of Tasks
        """
        url, tasks = TASK_ENDPOINT + suffix, []

        while True:
            result = self.get(url)

            if RESULTS not in result:
                if "detail" in result:
                    return None, {"status": result["detail"]}
                return None, {"status": "unexpected error"}

            for task_json in result[RESULTS]:
                tasks.append(Task(self.token, self.endpoint, task_json))

            if result["next"] is None:
                break

            url = result["next"].replace(self.endpoint, "").replace(self.endpoint.replace("https", "http"), "")

        return tasks, RESULT_OK

    def get_tasks_by_name(self, name):
        tasks, result = self.get_all_tasks()

        tasks_to_return = []
        if result["status"] == "OK":
            for task in tasks:
                if task.name == name:
                    tasks_to_return.append(task)
        else:
            return None, result

        if len(tasks_to_return) > 0:
            return tasks_to_return, result

        return None, {"status": "Task with this name not found!"}

    def delete_model(self, model_id):
        return self.delete(MODEL_ENDPOINT + model_id + "/")

    def delete_task(self, task_id):
        """
        Delete the task from the db.
        :param task_id: identification of task
        :return: None
        """
        return self.delete(TASK_ENDPOINT + task_id + "/")

    def create_task(self, name, task_type=MULTI_CLASS):
        """
        Create task with given name.
        :param name: name of the task
        :param task_type: 'multi_class' (default) or 'multi_label'
        :return: Task object
        """
        data = self.add_workspace({NAME: name, TASK_TYPE: task_type})
        task_json = self.post(TASK_ENDPOINT, data=data)
        if "id" not in task_json:
            msg = task_json["detail"] if "detail" in task_json else "unexpected error"
            return None, {"status": msg}
        return Task(self.token, self.endpoint, task_json), RESULT_OK

    def create_label(self, name, label_type=CATEGORY):
        """
        Create label with given name.
        :param name: name of the label
        :param label_type: type of label to create (category or tag)
        :return: Label object
        """
        data = self.add_workspace({NAME: name, LABEL_TYPE: label_type})
        label_json = self.post(LABEL_ENDPOINT, data=data)
        if "id" not in label_json:
            return None, {"status": "unexpected error"}
        return Label(self.token, self.endpoint, label_json), RESULT_OK

    def get_all_labels(self, suffix=""):
        """
        Get all labels of the user(user is specified by client key).
        :return: List of labels
        """
        url, labels = LABEL_ENDPOINT + suffix, []

        while True:
            result = self.get(url)

            for label_json in result[RESULTS]:
                labels.append(Label(self.token, self.endpoint, label_json))

            if result["next"] is None:
                break

            url = result["next"].replace(self.endpoint, "").replace(self.endpoint.replace("https", "http"), "")

        return labels, RESULT_OK

    def get_training_images(self, page_url=None, verification=None):
        """
        Get paginated result of images from workspace.
        :param page_url: optional, select the specific page of images, default first page
        :return: (list of images, next_page)
        """
        url = (
            page_url.replace(self.endpoint, "").replace(self.endpoint.replace("https", "http"), "")
            if page_url
            else IMAGE_ENDPOINT + "?page=1"
        )
        url += "&verification=" + str(verification) if verification is not None else ""
        print(url)
        result = self.get(url)
        return (
            [Image(self.token, self.endpoint, image_json) for image_json in result[RESULTS]],
            result["next"],
            RESULT_OK,
        )

    def get_label(self, label_id):
        label_json = self.get(LABEL_ENDPOINT + label_id)
        if ID not in label_json:
            return None, {"status": "label with id not found"}
        return Label(self.token, self.endpoint, label_json), RESULT_OK

    def get_labels_by_substring(self, name):
        """
        Return all labels of the workspace which contains the substring.
        :param name: name/substring of the label
        :return: list of labels, stattus
        """
        labels, result = self.get_all_labels(suffix="?search=" + name)

        if len(labels) > 0:
            return labels, result
        else:
            return None, {"status": "No labels found"}

    def get_image(self, image_id):
        image_json = self.get(IMAGE_ENDPOINT + image_id)
        if ID not in image_json:
            return None, {"status": "image with id not found"}
        return Image(self.token, self.endpoint, image_json), RESULT_OK

    def delete_label(self, label_id):
        return self.delete(LABEL_ENDPOINT + label_id)

    def delete_image(self, image_id):
        return self.delete(IMAGE_ENDPOINT + image_id)

    def upload_images(self, records):
        """
        Upload one or more files and add labels to them.
        :param record: list of dictionaries with labels and one of '_base64', '_file', '_url'
                        specify noresize: True to save image without (default False)
                       [{'_file': '__FILE_PATH__', 'labels': ['__UUID_1__', '__UUID_2__'], noresize: False}, ...]
        :return: image, status
        """
        images = []
        for record in records:
            files, data = None, None
            noresize = True if NORESIZE in record and record[NORESIZE] else False

            if FILE in record:
                files = {"img_path": open(record[FILE], "rb")}
                if noresize:
                    files[NORESIZE] = str(True)
            elif BASE64 in record:
                data = {"base64": record[BASE64].decode("utf-8"), NORESIZE: noresize}
            elif URL in record:
                # TODO: do not resize image when loading (right now we need to use self.max_size = 0)
                data = {"base64": self.load_url_image(record[URL]), NORESIZE: noresize}

            data = self.add_workspace(data)
            image_json = self.post(IMAGE_ENDPOINT, files=files, data=data)
            image, status = self.get_image(image_json["id"])

            if "labels" in record:
                for label_id in record["labels"]:
                    image.add_label(label_id)

            images.append(image)
        return images, RESULT_OK


class Task(RecognitionClient):
    def __init__(self, token, endpoint, task_json):
        super(Task, self).__init__(token, endpoint)

        self.id = task_json[ID]
        self.name = task_json[NAME]
        self.type = task_json["type"]
        self.production_version = task_json["production_version"]
        self.workspace = task_json[WORKSPACE] if WORKSPACE in task_json else DEFAULT_WORKSPACE

    def __str__(self):
        return self.id

    def train(self):
        """
        Create new training in ximilar.ai.
        :return: None
        """
        return self.post(TASK_ENDPOINT + self.id + "/train/")

    def delete_task(self):
        """
        Delete the task from ximilar.
        :return: None
        """
        super(Task, self).delete_task(self.id)

    def get_labels(self):
        """
        Get labels of this task.
        :return: list of Labels
        """
        if "labels" in self.cache:
            return self.cache["labels"], RESULT_OK
        else:
            labels, result = self.get_all_labels(suffix="?task=" + self.id)

            if result["status"] == "OK":
                self.cache["labels"] = labels

            return self.cache["labels"], result

    def get_label_by_name(self, name):
        """
        Get label with specified name which also belongs to this task.
        """
        labels, result = self.get_labels()
        if result["status"] == "OK":
            for label in labels:
                if label.name == name:
                    return label, RESULT_OK
        else:
            return None, result

        return None, {"status": "Label with this name not found!"}

    def classify(self, records, version=None):
        """
        Takes the images and calls the ximilar client for classifying these images on the task.

        Usage:
            client = VizeRestClient('your-token')
            task = client.get_task('')
            result = task.classify({'_url':'http://example.com/client.jpg'})

        :param records: array of json/dicts [{'_url':'url-path'}, {'_file': ''}, {'_base64': 'base64encodeimg'}]
        :param version: optional(integer of specific version), default None/production_version
        :return: json response
        """
        records = self.preprocess_records(records)

        # version is default set to None, so ximilar will determine which one to take
        data = {"records": records, "task_id": self.id, "version": version}
        return self.post(CLASSIFY_ENDPOINT, data=data)

    def create_label(self, name, label_type=CATEGORY):
        """
        Creates label and adds it to this task.
        :param name: name of label to create
        :param label_type: type of label to create (category or tag)
        :return: label, status
        """
        label, result = super(Task, self).create_label(name, label_type=label_type)
        self.add_label(label.id)
        return label, RESULT_OK

    def add_label(self, label_id):
        """
        Add label to this task. If the task was already trained then it is frozen and you are not able to add new label.
        :param label_id: identification of label
        :return: json/dict result
        """
        return self.post(TASK_ENDPOINT + self.id + "/add-label/", data={"label_id": label_id})

    def detach_label(self, label_id):
        """
        Remove/Detach label from the task. If the task was already trained then it is frozen and you are not able to remove it.
        :param label_id: identification of label
        :return: json/dict result
        """
        return self.post(TASK_ENDPOINT + self.id + "/remove-label/", data={"label_id": label_id})


class Model(RecognitionClient):
    def __init__(self, token, endpoint, model_json):
        super(Model, self).__init__(token, endpoint)

        self.id = model_json[ID]
        self.task_id = model_json["task"]
        self.task_name = model_json["task_name"]
        self.version = model_json["version"]
        self.train_status = model_json["train_status"]

    def delete_model(self):
        """
        Delete the model from ximilar.
        :return: None
        """
        super(Model, self).delete_model(self.id)


class Label(RecognitionClient):
    def __init__(self, token, endpoint, label_json):
        super(Label, self).__init__(token, endpoint)

        self.id = label_json[ID]
        self.name = label_json[NAME]
        self.tasks_count = label_json[TASKS_COUNT] if TASKS_COUNT in label_json else 0
        self.negative_for_task = label_json[NEGATIVE_FOR_TASK] if NEGATIVE_FOR_TASK in label_json else None
        self.workspace = label_json[WORKSPACE] if WORKSPACE in label_json else DEFAULT_WORKSPACE
        self.images_count = label_json[IMAGES_COUNT] if IMAGES_COUNT in label_json else 0

    def __str__(self):
        return self.id

    def wipe_label(self):
        """
        Delete label and all images associated with this label.
        :return: None
        """
        self.delete(LABEL_ENDPOINT + self.id + "/wipe")

    def merge_label(self, label_b):
        """
        Get all photos of label_b and remove the label_b. Add this label to all the photos.
        This will lead to merging these two labels.
        """
        next_page, images = None, []
        while True:
            images_m, next_page, status = label_b.get_training_images(page_url=next_page)
            for image in images_m:
                images.append(image)

            if not next_page:
                break

        for image in images:
            image.remove_label(label_b.id)
            image.add_label(self.id)

    def get_images_count(self):
        """
        Get count of the images connected to this label.
        :return:
        """
        label_json = self.get(LABEL_ENDPOINT + self.id)

        if IMAGES_COUNT in label_json:
            self.images_count = label_json[IMAGES_COUNT]

        return self.images_count

    def get_training_images(self, page_url=None):
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
            result["next"],
            RESULT_OK,
        )

    def upload_images(self, records):
        """
        Upload image to the ximilar.com and adding label to this image.
        :param records: list of files with _url, _base64, _file.
        :return: None
        """
        for i in range(len(records)):
            if "labels" in records[i]:
                records[i]["labels"].append(self.id)
            else:
                records[i]["labels"] = [self.id]
        return super(Label, self).upload_images(records)

    def detach_image(self, image_id):
        """
        Remove/Detach label from the image.
        :param label_id: id of label
        :return: result
        """
        return self.post(IMAGE_ENDPOINT + image_id + "/remove-label/", data={"label_id": self.id})

    def delete_label(self):
        """
        Delete the image from ximilar.
        :return: None
        """
        return super(Label, self).delete_label(self.id)


class Image(RecognitionClient):
    def __init__(self, token, endpoint, image_json):
        super(Image, self).__init__(token, endpoint)

        self.id = image_json[ID]
        self.img_path = image_json["img_path"]
        self.thumb_img_path = image_json["thumb_img_path"]
        self.verifyCount = image_json["verifyCount"]
        self.workspace = image_json[WORKSPACE] if WORKSPACE in image_json else DEFAULT_WORKSPACE
        self._file = None

    def __str__(self):
        return self.thumb_img_path

    def delete_image(self):
        """
        Delete the image from ximilar.
        :return: None
        """
        return super(Image, self).delete_image(self.id)

    def get_labels(self):
        """
        Get labels assigned to this image.
        :return: list of Labels
        """
        if "labels" not in self.cache:
            labels = [Label(self.token, self.endpoint, label) for label in self.get(IMAGE_ENDPOINT + self.id)["labels"]]
        else:
            labels = self.cache["labels"]

        return labels, RESULT_OK

    def add_label(self, label_id):
        """
        Add label to the image.
        :param label_id: id of label
        :return: result
        """
        return self.post(IMAGE_ENDPOINT + self.id + "/add-label/", data={"label_id": label_id})

    def detach_label(self, label_id):
        """
        Remove/Detach label from the image.
        :param label_id: id of label
        :return: result
        """
        return self.post(IMAGE_ENDPOINT + self.id + "/remove-label/", data={"label_id": label_id})

    def download_image(self, destination=""):
        self._file = super().download_image(self.img_path, destination=destination)
