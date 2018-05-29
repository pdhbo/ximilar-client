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
        with open(path, 'rb') as file_img:
            image = base64.b64encode(file_img.read()).decode('utf-8')
        return image


class VizeRestClient(RestClient):
    def get_task(self, id_task):
        return Task(self.api_key, self.endpoint, self.get(TASK_ENDPOINT + id_task))

    def get_all_tasks(self):
        result = self.get(TASK_ENDPOINT)
        return [Task(self.api_key, self.endpoint, task_json) for task_json in result[RESULTS]]

    def delete_task(self, id_task):
        self.delete(TASK_ENDPOINT+id_task+'/')

    def create_task(self, name):
        return self.post(TASK_ENDPOINT, data={NAME: name})

    def create_label(self, name):
        return self.post(LABEL_ENDPOINT, data={NAME: name})

    def get_all_labels(self):
        result = self.get(LABEL_ENDPOINT)
        return [Label(self.api_key, self.endpoint, label_json) for label_json in result[RESULTS]]

    def get_label(self, id_label):
        return Label(self.api_key, self.endpoint, self.get(LABEL_ENDPOINT+id_label))

    def upload_image(self, file_path, labels):
        raise NotImplementedError

    def get_image(self, id_image):
        raise NotImplementedError

    def remove_image(self, id_image):
        raise NotImplementedError


class Task(VizeRestClient):
    def __init__(self, api_key, endpoint, task_json):
        super(Task, self).__init__(api_key, endpoint)

        self.id = task_json[ID]
        self.name = task_json[NAME]
        self.frozen = task_json['frozen']
        self.type = task_json['type']
        self.production_version = task_json['production_version']

    def delete_task(self):
        super(Task, self).delete_task(self.id)

    def get_labels(self):
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
        raise NotImplementedError

    def remove_label(self, id_label):
        raise NotImplementedError


class Label(VizeRestClient):
    def __init__(self, api_key, endpoint, label_json):
        super(Label, self).__init__(api_key, endpoint)

        self.id = label_json[ID]
        self.name = label_json[NAME]

    def add_image(self, id_image):
        raise NotImplementedError


class Image(VizeRestClient):
    def __init__(self, api_key, endpoint, image_json):
        super(Image, self).__init__(api_key, endpoint)

        self.id = image_json[ID]

    def add_label(self, id_label):
        raise NotImplementedError

    def remove_label(self, id_label):
        raise NotImplementedError


if __name__ == '__main__':
    client = VizeRestClient('')
    #test = client.create_label('test label', '')
    #print(test)
    #tasks = client.get_all_tasks()
    #print(tasks)
    task = client.get_task('')
    #print(task.__dict__)
    #labels = client.get_all_labels()
    #print(labels)
    #label = client.get_label('')
    #print(label)
    #task_labels = task.get_labels()
    #print(task_labels)
    result = task.classify([{'_url': 'http://www.ximilar.com/examples/dubai.jpg'}, {'_file': 'normal.jpg'}])
    print(result)
