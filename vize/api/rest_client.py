import requests
import json
import base64

LABEL_ENDPOINT = 'v2/label/'
TASK_ENDPOINT = 'v2/task/'
IMAGE_ENDPOINT = 'v2/training-image/'
CLASSIFY_ENDPOINT = 'v2/classify/'
RESULTS = 'results'
ID = 'id'
NAME = 'name'
TASK = 'task'


class RestClient(object):
    """
    Parent class that implements HTTP GET, POST, DELETE methods with requests lib and loading images to base64.

    All objects contains API_KEY and ENDPOINT information.
    """
    def __init__(self, api_key, endpoint='https://api.vize.ximilar.com/'):
        self.api_key = api_key
        self.endpoint = endpoint
        self.headers = {'Content-Type': 'application/json',
                        'Authorization': 'Token ' + self.api_key}

    def get(self, api_endpoint, data=None):
        return requests.get(self.endpoint+api_endpoint, headers=self.headers, data=data).json()

    def post(self, api_endpoint, data=None, files=None):
        if data:
            data = json.dumps(data)

        headers = self.headers if not files else {'Authorization': 'Token ' + self.api_key}
        return requests.post(self.endpoint+api_endpoint, headers=headers, data=data, files=files).json()

    def delete(self, api_endpoint, data=None):
        return requests.delete(self.endpoint+api_endpoint, headers=self.headers, data=data)

    def load_base64_file(self, path):
        """
        Load file/image to base64.
        :param path: local path to the image
        :return: base64 encoded string
        """
        with open(path, 'rb') as file_img:
            image = base64.b64encode(file_img.read()).decode('utf-8')
        return image


class VizeRestClient(RestClient):
    def get_task(self, id_task):
        task_json = self.get(TASK_ENDPOINT + id_task)
        if 'id' not in task_json:
            return task_json
        return Task(self.api_key, self.endpoint, task_json)

    def get_all_tasks(self):
        """
        Get all tasks of the user(user is specified by api key).
        :return: List of tasks
        """
        result = self.get(TASK_ENDPOINT)

        if not RESULTS in result:
            return result

        return [Task(self.api_key, self.endpoint, task_json) for task_json in result[RESULTS]]

    def delete_task(self, id_task):
        return self.delete(TASK_ENDPOINT+id_task+'/')

    def create_task(self, name):
        task_json = self.post(TASK_ENDPOINT, data={NAME: name})
        if 'id' not in task_json:
            return task_json
        return Task(self.api_key, self.endpoint, task_json)

    def create_label(self, name):
        label_json = self.post(LABEL_ENDPOINT, data={NAME: name})
        if 'id' not in label_json:
            return label_json
        return Label(self.api_key, self.endpoint, label_json)

    def get_all_labels(self):
        """
        Get all labels of the user(user is specified by api key).
        :return: List of labels
        """
        result = self.get(LABEL_ENDPOINT)
        return [Label(self.api_key, self.endpoint, label_json) for label_json in result[RESULTS]]

    def get_label(self, id_label):
        label_json = self.get(LABEL_ENDPOINT+id_label)
        if 'id' not in label_json:
            return label_json
        return Label(self.api_key, self.endpoint, label_json)

    def get_image(self, id_image):
        image_json = self.get(IMAGE_ENDPOINT+id_image)
        if 'id' not in image_json:
            return image_json
        return Image(self.api_key, self.endpoint, image_json)

    def delete_label(self, id_label):
        self.delete(LABEL_ENDPOINT+id_label)

    def remove_image(self, id_image):
        return self.delete(IMAGE_ENDPOINT+id_image)

    def upload_image(self, file_path, label_ids=[]):
        image_json = self.post(IMAGE_ENDPOINT, files={'img_path': open(file_path, 'rb')})
        image = Image(self.api_key, self.endpoint, image_json)

        for label_id in label_ids:
            image.add_label(label_id)
        return image


class Task(VizeRestClient):
    def __init__(self, api_key, endpoint, task_json):
        super(Task, self).__init__(api_key, endpoint)

        self.id = task_json[ID]
        self.name = task_json[NAME]
        self.type = task_json['type']
        self.production_version = task_json['production_version']

    def __str__(self):
        return self.id

    def train(self):
        return self.post(TASK_ENDPOINT+self.id+'/train/')

    def delete_task(self):
        """
        Delete the task from vize.
        :return: None
        """
        super(Task, self).delete_task(self.id)

    def get_all_labels(self):
        return self.get_labels()

    def get_labels(self):
        """
        Get labels of this task.
        :return: list of Labels
        """
        result = self.get(LABEL_ENDPOINT+'?task='+self.id)
        return [Label(self.api_key, self.endpoint, label_json) for label_json in result[RESULTS]]

    def classify(self, records, version=None):
        """
        Takes the images and calls the vize api for classifying these images on the task.

        Usage:
            client = VizeRestClient('your-token')
            task = client.get_task('')
            result = task.classify({'_url':'http://example.com/test.jpg'})

        :param records: array of json/dicts [{'_url':'url-path'}, {'_file': ''}, {'_base64': 'base64encodeimg'}]
        :param version: optional(integer of specific version), default None/production_version
        :return: json response
        """
        for record in records:
            if '_file' in record:
                record['_base64'] = self.load_base64_file(record['_file'])

        data = {'records': records, 'task_id': self.id, 'version': version if version else self.production_version}
        return self.post(CLASSIFY_ENDPOINT, data=data)

    def create_label(self, name):
        """
        Creates label and adds it to this task.
        :param name:
        :return:
        """
        label = super(Task, self).create_label(name)
        self.add_label(label.id)
        return label

    def add_label(self, id_label):
        """
        Add label to this task. If the task was already trained then it is frozen and you are not able to add new label.
        :param id_label: identification of label
        :return: json/dict result
        """
        return self.post(TASK_ENDPOINT+self.id+'/add-label/', data={'label_id': id_label})

    def remove_label(self, id_label):
        """
        Remove/Detach label from the task. If the task was already trained then it is frozen and you are not able to remove it.
        :param id_label: identification of label
        :return: json/dict result
        """
        return self.post(TASK_ENDPOINT+self.id+'/remove-label/', data={'label_id': id_label})


class Label(VizeRestClient):
    def __init__(self, api_key, endpoint, label_json):
        super(Label, self).__init__(api_key, endpoint)

        self.id = label_json[ID]
        self.name = label_json[NAME]

    def __str__(self):
        return self.id

    def get_training_images(self, page_url=None):
        """
        Get paginated result of images for specific label.

        :param page_url: optional, select the specific page of images, default first page
        :return: (list of images, next_page)
        """
        url = page_url if page_url else IMAGE_ENDPOINT + '?label='+self.id
        result = self.get(url)
        return [Image(self.api_key, self.endpoint, image_json) for image_json in result[RESULTS]], result['next']

    def upload_image(self, file_path):
        image_json = self.post(IMAGE_ENDPOINT, files={'img_path': open(file_path, 'rb')})
        image = Image(self.api_key, self.endpoint, image_json)
        image.add_label(self.id)
        return image


class Image(VizeRestClient):
    def __init__(self, api_key, endpoint, image_json):
        super(Image, self).__init__(api_key, endpoint)

        self.id = image_json[ID]
        self.thumb_img_path = image_json['thumb_img_path']

    def __str__(self):
        return self.thumb_img_path

    def get_labels(self):
        """
        Get labels assigned to this image.
        :return: list of Labels
        """
        return [Label(self.api_key, self.endpoint, label) for label in self.get(IMAGE_ENDPOINT+self.id)['labels']]

    def add_label(self, id_label):
        return self.post(IMAGE_ENDPOINT + self.id + '/add-label/', data={'label_id': id_label})

    def remove_label(self, id_label):
        return self.post(IMAGE_ENDPOINT + self.id + '/remove-label/', data={'label_id': id_label})
