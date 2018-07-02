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

    All objects contains TOKEN and ENDPOINT information.
    """
    def __init__(self, token, endpoint='https://api.vize.ai/'):
        self.token = token
        self.endpoint = endpoint
        self.headers = {'Content-Type': 'application/json',
                        'Authorization': 'Token ' + self.token}

    def get(self, api_endpoint, data=None):
        """
        Call the http GET request with data.
        :param api_endpoint: endpoint path
        :param data: optional data
        :return: json response
        """
        return requests.get(self.endpoint+api_endpoint, headers=self.headers, data=data).json()

    def post(self, api_endpoint, data=None, files=None):
        """
        Call the http POST request with data.
        :param api_endpoint: endpoint path
        :param data: optional data
        :param files: optional files to upload
        :return: json response
        """
        if data:
            data = json.dumps(data)

        headers = self.headers if not files else {'Authorization': 'Token ' + self.token}
        result = requests.post(self.endpoint+api_endpoint, headers=headers, data=data, files=files)
        return result.json()

    def delete(self, api_endpoint, data=None):
        """
        Call the http DELETE request with data.
        :param api_endpoint: endpoint path
        :param data: optional data
        :return: response
        """
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
    def get_task(self, task_id):
        """
        Getting task by id.
        :param task_id: id of task
        :return: Task object
        """
        task_json = self.get(TASK_ENDPOINT + task_id)
        if 'id' not in task_json:
            raise Exception("Error getting task: " + task_id)
        return Task(self.token, self.endpoint, task_json)

    def get_all_tasks(self):
        """
        Get all tasks of the user(user is specified by api key).
        :return: List of Tasks
        """
        result = self.get(TASK_ENDPOINT)

        if not RESULTS in result:
            return result

        return [Task(self.token, self.endpoint, task_json) for task_json in result[RESULTS]]

    def get_task_by_name(self, name):
        for task in self.get_all_tasks():
            if task.name == name:
                return task

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
            raise Exception("Error creating task: " + name)
        return Task(self.token, self.endpoint, task_json)

    def create_label(self, name):
        """
        Create label with given name.
        :param name: name of the label
        :return: Label object
        """
        label_json = self.post(LABEL_ENDPOINT, data={NAME: name})
        if 'id' not in label_json:
            raise Exception("Error creating label: " + name)
        return Label(self.token, self.endpoint, label_json)

    def get_all_labels(self):
        """
        Get all labels of the user(user is specified by api key).
        :return: List of labels
        """
        result = self.get(LABEL_ENDPOINT)
        return [Label(self.token, self.endpoint, label_json) for label_json in result[RESULTS]]

    def get_label(self, label_id):
        label_json = self.get(LABEL_ENDPOINT + label_id)
        if ID not in label_json:
            raise Exception("Error getting label: " + label_id)
        return Label(self.token, self.endpoint, label_json)

    def get_image(self, image_id):
        image_json = self.get(IMAGE_ENDPOINT + image_id)
        if ID not in image_json:
            raise Exception("Error getting image: " + image_id)
        return Image(self.token, self.endpoint, image_json)

    def delete_label(self, label_id):
        self.delete(LABEL_ENDPOINT + label_id)

    def delete_image(self, image_id):
        return self.delete(IMAGE_ENDPOINT + image_id)

    def upload_image(self, file_path=None, base64=None, label_ids=[]):
        files, data = None, None

        if file_path:
            files = {'img_path': open(file_path, 'rb')}
        if base64:
            data = {'base64': base64.decode("utf-8")}

        image_json = self.post(IMAGE_ENDPOINT, files=files, data=data)
        image = self.get_image(image_json['id'])

        for label_id in label_ids:
            image.add_label(label_id)
        return image


class Task(VizeRestClient):
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
        Create new training in vize.ai.
        :return: None
        """
        return self.post(TASK_ENDPOINT+self.id+'/train/')

    def delete_task(self):
        """
        Delete the task from vize.
        :return: None
        """
        super(Task, self).delete_task(self.id)

    def get_all_labels(self):
        """
        Getting labels of this task.
        :return: list of Labels
        """
        return self.get_labels()

    def get_labels(self):
        """
        Get labels of this task.
        :return: list of Labels
        """
        result = self.get(LABEL_ENDPOINT+'?task='+self.id)
        return [Label(self.token, self.endpoint, label_json) for label_json in result[RESULTS]]

    def get_label_by_name(self, name):
        """
        Get label of this task by name.
        """
        labels = self.get_labels()
        for label in labels:
            if label.name == name:
                return label

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
            if '_file' in record and '_base64' not in record:
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

    def add_label(self, label_id):
        """
        Add label to this task. If the task was already trained then it is frozen and you are not able to add new label.
        :param label_id: identification of label
        :return: json/dict result
        """
        return self.post(TASK_ENDPOINT + self.id +'/add-label/', data={'label_id': label_id})

    def remove_label(self, label_id):
        """
        Remove/Detach label from the task. If the task was already trained then it is frozen and you are not able to remove it.
        :param label_id: identification of label
        :return: json/dict result
        """
        return self.post(TASK_ENDPOINT + self.id +'/remove-label/', data={'label_id': label_id})


class Label(VizeRestClient):
    def __init__(self, token, endpoint, label_json):
        super(Label, self).__init__(token, endpoint)

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
        return [Image(self.token, self.endpoint, image_json) for image_json in result[RESULTS]], result['next']

    def upload_image(self, file_path=None, base64=None):
        """
        Upload image to the vize.ai and adding label to this image.
        :param file_path: local path to the file
        :return: None
        """
        return super(Task, self).upload_image(file_path=file_path, base64=base64, label_ids=[self.id])

    def remove_image(self, image_id):
        """
        Remove/Detach label from the image.
        :param label_id: id of label
        :return: result
        """
        return self.post(IMAGE_ENDPOINT + image_id + '/remove-label/', data={'label_id': self.id})


class Image(VizeRestClient):
    def __init__(self, token, endpoint, image_json):
        super(Image, self).__init__(token, endpoint)

        self.id = image_json[ID]
        self.thumb_img_path = image_json['thumb_img_path']

    def __str__(self):
        return self.thumb_img_path

    def get_labels(self):
        """
        Get labels assigned to this image.
        :return: list of Labels
        """
        return [Label(self.token, self.endpoint, label) for label in self.get(IMAGE_ENDPOINT + self.id)['labels']]

    def add_label(self, label_id):
        """
        Add label to the image.
        :param label_id: id of label
        :return: result
        """
        return self.post(IMAGE_ENDPOINT + self.id + '/add-label/', data={'label_id': label_id})

    def remove_label(self, label_id):
        """
        Remove/Detach label from the image.
        :param label_id: id of label
        :return: result
        """
        return self.post(IMAGE_ENDPOINT + self.id + '/remove-label/', data={'label_id': label_id})
