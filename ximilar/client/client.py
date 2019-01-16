import requests
import json
import base64
import cv2

from ximilar.client.constants import FILE, BASE64, IMG_DATA


class RestClient(object):
    """
    Parent class that implements HTTP GET, POST, DELETE methods with requests lib and loading images to base64.

    All objects contains TOKEN and ENDPOINT information.
    """
    def __init__(self, token, endpoint='https://api.ximilar.com/'):
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
        # do not resize image if set to 0
        if self.max_size == 0:
            return image_data

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
        The ximilar accepts base64 data to have BGR order that is why we convert it here.
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

    def preprocess_records(self, records):
        """
        Preprocess all records (list of dictionaries with possible '_base64'|'_file'|'_url' fields
        before processing/upload to Ximilar Application.
        :param records: list of dictionaries
        :return: modified list of dictionaries
        """
        for i in range(len(records)):
            if FILE in records[i] and BASE64 not in records[i] and IMG_DATA not in records[i]:
                records[i][BASE64] = self.load_base64_file(records[i][FILE])
            elif IMG_DATA in records[i]:
                records[i][BASE64] = self.cv2img_to_base64(records[i][IMG_DATA])

            # finally we need to delete the image data and just send url or base64
            if IMG_DATA in records[i]:
                del records[i][IMG_DATA]

            if FILE in records[i]:
                del records[i][FILE]

        return records
