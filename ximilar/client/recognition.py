from ximilar.client import RestClient
from ximilar.client.constants import TASK, NAME, ID, RESULTS, TASKS_COUNT, RESULT_OK, FILE, URL, BASE64

LABEL_ENDPOINT = 'recognition/v2/label/'
TASK_ENDPOINT = 'recognition/v2/task/'
IMAGE_ENDPOINT = 'recognition/v2/training-image/'
CLASSIFY_ENDPOINT = 'recognition/v2/classify/'


class RecognitionClient(RestClient):
    def get_task(self, task_id):
        """
        Getting task by id.
        :param task_id: id of task
        :return: Task object
        """
        task_json = self.get(TASK_ENDPOINT + task_id)
        if 'id' not in task_json:
            return None, {'status': 'Not Found'}
        return Task(self.token, self.endpoint, task_json), RESULT_OK

    def get_all_tasks(self, suffix=''):
        """
        Get all tasks of the user(user is specified by client key).
        :return: List of Tasks
        """
        url, tasks = TASK_ENDPOINT+suffix, []

        while True:
            result = self.get(url)

            if RESULTS not in result:
                return None, {'status': 'unexpected error'}

            for task_json in result[RESULTS]:
                tasks.append(Task(self.token, self.endpoint, task_json))

            if result['next'] is None:
                break

            url = result['next'].replace(self.endpoint, "").replace(self.endpoint.replace("https", "http"), "")

        return tasks, RESULT_OK

    def get_task_by_name(self, name):
        tasks, result = self.get_all_tasks()

        if result['status'] == 'OK':
            for task in tasks:
                if task.name == name:
                    return task, result
        else:
            return None, result
        return None, {'status': 'Task with this name not found!'}

    def delete_task(self, task_id):
        """
        Delete the task from the db.
        :param task_id: identification of task
        :return: None
        """
        return self.delete(TASK_ENDPOINT + task_id + '/')

    def create_task(self, name):
        """
        Create task with given name.
        :param name: name of the task
        :return: Task object
        """
        task_json = self.post(TASK_ENDPOINT, data={NAME: name})
        if 'id' not in task_json:
            msg = task_json['detail'] if 'detail' in task_json else 'unexpected error'
            return None, {'status': msg}
        return Task(self.token, self.endpoint, task_json), RESULT_OK

    def create_label(self, name):
        """
        Create label with given name.
        :param name: name of the label
        :return: Label object
        """
        label_json = self.post(LABEL_ENDPOINT, data={NAME: name})
        if 'id' not in label_json:
            return None, {'status': 'unexpected error'}
        return Label(self.token, self.endpoint, label_json), RESULT_OK

    def get_all_labels(self, suffix=''):
        """
        Get all labels of the user(user is specified by client key).
        :return: List of labels
        """
        url, labels = LABEL_ENDPOINT+suffix, []

        while True:
            result = self.get(url)

            for label_json in result[RESULTS]:
                labels.append(Label(self.token, self.endpoint, label_json))

            if result['next'] is None:
                break

            url = result['next'].replace(self.endpoint, "").replace(self.endpoint.replace("https", "http"), "")

        return labels, RESULT_OK

    def get_label(self, label_id):
        label_json = self.get(LABEL_ENDPOINT + label_id)
        if ID not in label_json:
            return None, {'status': 'label with id not found'}
        return Label(self.token, self.endpoint, label_json), RESULT_OK

    def get_image(self, image_id):
        image_json = self.get(IMAGE_ENDPOINT + image_id)
        if ID not in image_json:
            return None, {'status': 'image with id not found'}
        return Image(self.token, self.endpoint, image_json), RESULT_OK

    def delete_label(self, label_id):
        self.delete(LABEL_ENDPOINT + label_id)

    def delete_image(self, image_id):
        return self.delete(IMAGE_ENDPOINT + image_id)

    def upload_images(self, records):
        """
        Upload one or more files and add labels to them.
        :param record: list of dictionaries with labels and one of '_base64', '_file', '_url'
                       [{'_file': '__FILE_PATH__', 'labels': ['__UUID_1__', '__UUID_2__']}, ...]
        :return: image, status
        """
        images = []
        for record in records:
            files, data = None, None

            if FILE in record:
                files = {'img_path': open(record[FILE], 'rb')}
            elif BASE64 in record:
                data = {'base64': record[BASE64].decode("utf-8")}
            elif URL in record:
                data = {'base64': self.load_url_image(record[URL])}

            image_json = self.post(IMAGE_ENDPOINT, files=files, data=data)
            image, status = self.get_image(image_json['id'])

            if 'labels' in record:
                for label_id in record['labels']:
                    image.add_label(label_id)

            images.append(image)
        return images, RESULT_OK


class Task(RecognitionClient):
    def __init__(self, token, endpoint, task_json):
        super(Task, self).__init__(token, endpoint)

        self.id = task_json[ID]
        self.name = task_json[NAME]
        self.type = task_json['type']
        self.production_version = task_json['production_version']

    def __str__(self):
        return self.id

    def train(self):
        """
        Create new training in ximilar.ai.
        :return: None
        """
        return self.post(TASK_ENDPOINT+self.id+'/train/')

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
        if 'labels' in self.cache:
            return self.cache['labels'], RESULT_OK
        else:
            labels, result = self.get_all_labels(suffix='?task=' + self.id)

            if result['status'] == 'OK':
                self.cache['labels'] = labels

            return self.cache['labels'], result

    def get_label_by_name(self, name):
        """
        Get label of this task by name.
        """
        labels, result = self.get_labels()
        if result['status'] == 'OK':
            for label in labels:
                if label.name == name:
                    return label, RESULT_OK
        else:
            return None, result

        return None, {'status': 'Label with this name not found!'}

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
        data = {'records': records, 'task_id': self.id, 'version': version}
        return self.post(CLASSIFY_ENDPOINT, data=data)

    def create_label(self, name):
        """
        Creates label and adds it to this task.
        :param name:
        :return:
        """
        label, result = super(Task, self).create_label(name)
        self.add_label(label.id)
        return label, RESULT_OK

    def add_label(self, label_id):
        """
        Add label to this task. If the task was already trained then it is frozen and you are not able to add new label.
        :param label_id: identification of label
        :return: json/dict result
        """
        return self.post(TASK_ENDPOINT + self.id +'/add-label/', data={'label_id': label_id})

    def detach_label(self, label_id):
        """
        Remove/Detach label from the task. If the task was already trained then it is frozen and you are not able to remove it.
        :param label_id: identification of label
        :return: json/dict result
        """
        return self.post(TASK_ENDPOINT + self.id +'/remove-label/', data={'label_id': label_id})


class Label(RecognitionClient):
    def __init__(self, token, endpoint, label_json):
        super(Label, self).__init__(token, endpoint)

        self.id = label_json[ID]
        self.name = label_json[NAME]
        self.tasks_count = label_json[TASKS_COUNT] if TASKS_COUNT in label_json else 0

    def __str__(self):
        return self.id

    def wipe_label(self):
        """
        Delete label and all images associated with this label.
        :return: None
        """
        self.delete(LABEL_ENDPOINT + self.id + '/wipe')

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

    def get_training_images(self, page_url=None):
        """
        Get paginated result of images for specific label.

        :param page_url: optional, select the specific page of images, default first page
        :return: (list of images, next_page)
        """
        url = page_url.replace(self.endpoint, "").replace(self.endpoint.replace("https", "http"), "") if page_url else IMAGE_ENDPOINT + '?label='+self.id
        result = self.get(url)
        return [Image(self.token, self.endpoint, image_json) for image_json in result[RESULTS]], result['next'], RESULT_OK

    def upload_image(self, file_path=None, base64=None):
        """
        Upload image to the ximilar.ai and adding label to this image.
        :param file_path: local path to the file
        :return: None
        """
        return super(Label, self).upload_image(file_path=file_path, base64=base64, label_ids=[self.id])

    def detach_image(self, image_id):
        """
        Remove/Detach label from the image.
        :param label_id: id of label
        :return: result
        """
        return self.post(IMAGE_ENDPOINT + image_id + '/remove-label/', data={'label_id': self.id})

    def delete_label(self):
        """
        Delete the image from ximilar.
        :return: None
        """
        super(Label, self).delete_label(self.id)


class Image(RecognitionClient):
    def __init__(self, token, endpoint, image_json):
        super(Image, self).__init__(token, endpoint)

        self.id = image_json[ID]
        self.thumb_img_path = image_json['thumb_img_path']

    def __str__(self):
        return self.thumb_img_path

    def delete_image(self):
        """
        Delete the image from ximilar.
        :return: None
        """
        super(Image, self).delete_image(self.id)

    def get_labels(self):
        """
        Get labels assigned to this image.
        :return: list of Labels
        """
        return [Label(self.token, self.endpoint, label) for label in self.get(IMAGE_ENDPOINT + self.id)['labels']], RESULT_OK

    def add_label(self, label_id):
        """
        Add label to the image.
        :param label_id: id of label
        :return: result
        """
        return self.post(IMAGE_ENDPOINT + self.id + '/add-label/', data={'label_id': label_id})

    def detach_label(self, label_id):
        """
        Remove/Detach label from the image.
        :param label_id: id of label
        :return: result
        """
        return self.post(IMAGE_ENDPOINT + self.id + '/remove-label/', data={'label_id': label_id})