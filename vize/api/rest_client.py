import requests
import json
import base64
import cv2

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
        self.cache = {}
        self.endpoint = endpoint
        self.max_size = 600
        self.headers = {'Content-Type': 'application/json',
                        'Authorization': 'Token ' + self.token}

    def invalidate(self):
        self.cache = {}

    def get(self, api_endpoint, data=None):
        """
        Call the http GET request with data.
        :param api_endpoint: endpoint path
        :param data: optional data
        :return: json response
        """
        result = requests.get(self.endpoint+api_endpoint, headers=self.headers, data=data)
        return result.json()

    def post(self, api_endpoint, data=None, files=None):
        """
        Call the http POST request with data.
        :param api_endpoint: endpoint path
        :param data: optional data
        :param files: optional files to upload
        :return: json response
        """
        self.invalidate()
        if data:
            data = json.dumps(data)

        headers = self.headers if not files else {'Authorization': 'Token ' + self.token}
        result = requests.post(self.endpoint+api_endpoint, headers=headers, data=data, files=files)
        print(result)
        return result.json()

    def delete(self, api_endpoint, data=None):
        """
        Call the http DELETE request with data.
        :param api_endpoint: endpoint path
        :param data: optional data
        :return: response
        """
        self.invalidate()
        return requests.delete(self.endpoint+api_endpoint, headers=self.headers, data=data)

    def resize_image_data(self, image_data, aspect_ratio=False):
        """
        Resize image data that are no bigger than max_size.
        :param image_data: cv2/np ndarray
        :return: cv2/np ndarray
        """
        height, width, _ = image_data.shape
        if height > self.max_size and width > self.max_size and not aspect_ratio:
            image_data = cv2.resize(image_data, (self.max_size, self.max_size))
        if height > self.max_size and width > self.max_size and aspect_ratio:
            image_data = cv2.resize(image_data, self.get_aspect_ratio_dim(image_data, self.max_size))
        return image_data

    def get_aspect_ratio_dim(self, image, img_size):
        if image.shape[0] > image.shape[1]:
            r = float(img_size) / image.shape[1]
            dim = (img_size, int(image.shape[0] * r))
        else:
            r = float(img_size) / image.shape[0]
            dim = (int(image.shape[1] * r), img_size)
        return dim

    def load_base64_file(self, path):
        """
        Load file from disk to base64.
        :param path: local path to the image
        :return: base64 encoded string
        """
        image = cv2.imread(str(path))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = self.resize_image_data(image)
        image = self.cv2img_to_base64(image)
        return image

    def cv2img_to_base64(self, image):
        """
        Load raw numpy/cv2 data of image to base64. The input image to this method should have RGB order.
        The vize accepts base64 data to have BGR order that is why we convert it here.
        The image_data was loaded in similar way:
            image = cv2.imread(str(path))
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        :param image_data: numpy/cv2 data with RGB order
        :return: base64 encoded string
        """
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        image = self.resize_image_data(image)
        retval, buffer = cv2.imencode('.jpg', image)
        jpg_as_text = base64.b64encode(buffer).decode('utf-8')
        return jpg_as_text


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
            msg = task_json['detail'] if 'detail' in task_json else ''
            raise Exception("Error creating task" + " '" + name + "':" + msg)
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

    def get_all_labels(self, suffix=''):
        """
        Get all labels of the user(user is specified by api key).
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

        return labels

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

    def get_labels(self):
        """
        Get labels of this task.
        :return: list of Labels
        """
        if 'labels' in self.cache:
            return self.cache['labels']
        else:
            labels = self.get_all_labels(suffix='?task=' + self.id)
            self.cache['labels'] = labels
            return self.cache['labels']

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
        for i in range(len(records)):
            if '_file' in records[i] and '_base64' not in records[i] and '_img_data' not in records[i]:
                records[i]['_base64'] = self.load_base64_file(records[i]['_file'])
            elif '_img_data' in records[i]:
                records[i]['_base64'] = self.cv2img_to_base64(records[i]['_img_data'])

            # finally we need to delete the image data and just send url or base64
            if '_img_data' in records[i]:
                del records[i]['_img_data']

        # version is default set to None, so vize will determine which one to take
        data = {'records': records, 'task_id': self.id, 'version': version}
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
            images_m, next_page = label_b.get_training_images(page_url=next_page)
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
        return [Image(self.token, self.endpoint, image_json) for image_json in result[RESULTS]], result['next']

    def upload_image(self, file_path=None, base64=None):
        """
        Upload image to the vize.ai and adding label to this image.
        :param file_path: local path to the file
        :return: None
        """
        return super(Label, self).upload_image(file_path=file_path, base64=base64, label_ids=[self.id])

    def remove_image(self, image_id):
        """
        Remove/Detach label from the image.
        :param label_id: id of label
        :return: result
        """
        return self.post(IMAGE_ENDPOINT + image_id + '/remove-label/', data={'label_id': self.id})

    def delete_label(self):
        """
        Delete the image from vize.
        :return: None
        """
        super(Label, self).delete_label(self.id)


class Image(VizeRestClient):
    def __init__(self, token, endpoint, image_json):
        super(Image, self).__init__(token, endpoint)

        self.id = image_json[ID]
        self.thumb_img_path = image_json['thumb_img_path']

    def __str__(self):
        return self.thumb_img_path

    def delete_image(self):
        """
        Delete the image from vize.
        :return: None
        """
        super(Image, self).delete_image(self.id)

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
