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
        return requests.post(self.endpoint+api_endpoint, headers=self.headers, data=json.dumps(data), files=files).json()

    def delete(self, api_endpoint, data=None):
        return requests.delete(self.endpoint+api_endpoint, headers=self.headers, data=data).json()

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
        return Task(self.api_key, self.endpoint, self.get(TASK_ENDPOINT + id_task))

    def get_all_tasks(self):
        """
        Get all tasks of the user(user is specified by api key).
        :return: List of tasks
        """
        result = self.get(TASK_ENDPOINT)
        return [Task(self.api_key, self.endpoint, task_json) for task_json in result[RESULTS]]

    def delete_task(self, id_task):
        self.delete(TASK_ENDPOINT+id_task+'/')

    def create_task(self, name):
        return self.post(TASK_ENDPOINT, data={NAME: name})

    def create_label(self, name):
        return self.post(LABEL_ENDPOINT, data={NAME: name})

    def get_all_labels(self):
        """
        Get all labels of the user(user is specified by api key).
        :return: List of labels
        """
        result = self.get(LABEL_ENDPOINT)
        return [Label(self.api_key, self.endpoint, label_json) for label_json in result[RESULTS]]

    def get_label(self, id_label):
        return Label(self.api_key, self.endpoint, self.get(LABEL_ENDPOINT+id_label))

    def upload_image(self, file_path, labels):
        # TODO this method
        raise NotImplementedError

    def get_image(self, id_image):
        return Image(self.api_key, self.endpoint, self.get(IMAGE_ENDPOINT+id_image))

    def remove_image(self, id_image):
        return self.delete(IMAGE_ENDPOINT+id_image)


class Task(VizeRestClient):
    def __init__(self, api_key, endpoint, task_json):
        super(Task, self).__init__(api_key, endpoint)

        self.id = task_json[ID]
        self.name = task_json[NAME]
        self.frozen = task_json['frozen']
        self.type = task_json['type']
        self.production_version = task_json['production_version']

    def delete_task(self):
        """
        Delete the task from vize.
        :return: None
        """
        super(Task, self).delete_task(self.id)

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

    def add_label(self, id_label):
        """
        Add label to this task. If the task was already trained then it is frozen and you are not able to add new label.
        :param id_label: identification of label
        :return: json/dict result
        """
        if not self.frozen:
            return self.post(TASK_ENDPOINT+self.id+'/add-label/', data={'label_id': id_label})
        return {'status': 'error', 'message': 'cannot add label to this task, task is frozen'}

    def remove_label(self, id_label):
        """
        Remove label from the task. If the task was already trained then it is frozen and you are not able to remove it.
        :param id_label: identification of label
        :return: json/dict result
        """
        if not self.frozen:
            return self.post(TASK_ENDPOINT+self.id+'/remove-label/', data={'label_id': id_label})
        return {'status': 'error', 'message': 'cannot add label to this task, task is frozen'}


class Label(VizeRestClient):
    def __init__(self, api_key, endpoint, label_json):
        super(Label, self).__init__(api_key, endpoint)

        self.id = label_json[ID]
        self.name = label_json[NAME]

    def get_training_images(self, page_url=None):
        """
        Get paginated result of images for specific label.

        :param page_url: optional, select the specific page of images, default first page
        :return: (list of images, next_page)
        """
        url = page_url if page_url else IMAGE_ENDPOINT
        result = self.get(url)
        return [Image(self.api_key, self.endpoint, image_json) for image_json in result[RESULTS]], result['next']


class Image(VizeRestClient):
    def __init__(self, api_key, endpoint, image_json):
        super(Image, self).__init__(api_key, endpoint)

        self.id = image_json[ID]
        self.thumb_img_path = image_json['thumb_img_path']

    def get_labels(self):
        """
        Get labels assigned to this image.
        :return: list of Labels
        """
        return [Label(self.api_key, self.endpoint, label) for label in self.get(IMAGE_ENDPOINT+self.id)['labels']]

    def add_label(self, id_label):
        # todo this works but raises error
        return self.post(IMAGE_ENDPOINT + self.id + '/add-label/', data={'label_id': id_label})

    def remove_label(self, id_label):
        # todo this works but raises error
        return self.post(IMAGE_ENDPOINT + self.id + '/remove-label/', data={'label_id': id_label})


if __name__ == '__main__':
    client = VizeRestClient('')
    task = client.get_task('')
    task_labels = task.get_labels()
    result = task.classify([{'_url': 'http://www.ximilar.com/examples/dubai.jpg'}, {'_file': 'normal.jpg'}])
