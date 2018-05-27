import requests


LABEL_ENDPOINT = 'v2/label/'
TASK_ENDPOINT = 'v2/task/'
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

    def post(self, api_endpoint, data=None):
        return requests.post(self.endpoint+api_endpoint, headers=self.headers, data=data).json()

    def delete(self, api_endpoint, data=None):
        return requests.delete(self.endpoint+api_endpoint, headers=self.headers, data=data).json()

    def upload_image(self, path, labels):
        pass

    def get_image(self, id_image):
        pass

    def remove_image(self, id_image):
        pass


class VizeRestClient(RestClient):
    def get_task(self, id_task):
        for task in self.get_all_tasks():
            if task.id == id_task:
                return task
        return None

    def get_all_tasks(self):
        result = self.get(TASK_ENDPOINT)
        return [Task(self.api_key, self.endpoint, task_json) for task_json in result[RESULTS]]

    def delete_task(self, id_task):
        self.delete(TASK_ENDPOINT+id_task+'/')

    def create_task(self, name):
        return self.post(TASK_ENDPOINT, data={NAME: name})

    def create_label(self, name, task_id):
        return self.post(LABEL_ENDPOINT, data={NAME: name, TASK: task_id})

    def get_all_labels(self):
        result = self.get(LABEL_ENDPOINT, data={TASK: None})
        return [Label(self.api_key, self.endpoint, label_json) for label_json in result[RESULTS]]

    def get_label(self, label_id):
        for label in self.get_all_labels():
            if label.id == label_id:
                return label
        return None


class Task(VizeRestClient):
    def __init__(self, api_key, endpoint, task_json):
        super(Task, self).__init__(api_key, endpoint)

        self.id = task_json[ID]
        self.name = task_json[NAME]
        self.label_counts = task_json['labelsCount']
        self.frozen = task_json['frozen']
        self.type = task_json['type']

    def delete_task(self):
        super(Task, self).delete_task(self.id)

    def get_labels(self):
        result = self.get(LABEL_ENDPOINT, data={TASK: self.id})
        return [Label(self.api_key, self.endpoint, label_json) for label_json in result[RESULTS]]


class Label(VizeRestClient):
    def __init__(self, api_key, endpoint, label_json):
        super(Label, self).__init__(api_key, endpoint)

        self.id = label_json[ID]
        self.name = label_json[NAME]


if __name__ == '__main__':
    client = VizeRestClient('')
    tasks = client.get_all_tasks()
    print(tasks[0].__dict__)
    print(len(tasks))
    print(tasks[0].get_labels())
    #task.delete_task()
    client.create_task('test to test', 'testing')
    #client.create_label('test to test', 'testing')