import requests
import json
import base64
import cv2
import os
import numpy as np
import concurrent.futures
from tqdm import tqdm

from ximilar.client.constants import *


CONFIG_ENDPOINT = "account/v2/config/"


class RestClient(object):
    """
    Parent class that implements HTTP GET, POST, DELETE methods with requests lib and loading images to base64.

    All objects contains TOKEN and ENDPOINT information.
    """

    def __init__(self, token, endpoint=ENDPOINT, resource_name=""):
        self.token = token
        self.cache = {}
        self.endpoint = endpoint
        self.max_size = 600
        self.headers = {"Content-Type": "application/json", "Authorization": "Token " + self.token}
        self.check_resource(resource_name)

    def invalidate(self):
        self.cache = {}

    def get(self, api_endpoint, data=None, params=None):
        """
        Call the http GET request with data.
        :param api_endpoint: endpoint path
        :param data: optional data
        :param params: optional dictionary of URL params
        :return: json response
        """
        result = requests.get(self.endpoint + api_endpoint, params=params, headers=self.headers, data=data, timeout=30)
        return result.json()

    def post(self, api_endpoint, data=None, files=None, params=None):
        """
        Call the http POST request with data.

        :param api_endpoint: endpoint path
        :param data: optional data
        :param files: optional files to upload
        :param params: optional dictionary of URL params
        :return: json response
        """
        self.invalidate()

        if data is not None and files is not None:
            raise Exception("Unable to send data along with files with python requests library!")

        if data is not None:
            data = json.dumps(data)

        result = requests.post(
            self.endpoint + api_endpoint, params=params, headers=self.headers, data=data, files=files, timeout=30
        )

        try:
            json_result = result.json()
            return json_result
        except ValueError as e:
            return None

    def delete(self, api_endpoint, data=None, params=None):
        """
        Call the http DELETE request with data.
        :param api_endpoint: endpoint path
        :param data: optional data
        :param params: optional dictionary of URL params
        :return: response
        """
        self.invalidate()

        result = requests.delete(
            self.endpoint + api_endpoint, params=params, headers=self.headers, data=data, timeout=30
        )

        if result.status_code == HTTP_NO_COTENT_204:
            return result

        return result.json()

    def check_resource(self, resource_name):
        """
        Checks if the user has access (resource) to the service.
        :param resource_name: name of the service
        :return: True if user has access otherwise False
        """
        result = self.post("authorization/v2/authorize", data={"service_name": resource_name})

        if result and USER_ID in result:
            return True

        raise Exception("User has no access for service: " + resource_name + ". Please contact tech@ximilar.com!")

    def get_all_paginated_items(self, url):
        """
        Getting all paginated items from specific endpoint url
        :param url: url path which will be queried
        :return: items
        """
        items = []

        while True:
            result = self.get(url)
            if RESULTS in result:
                for item in result[RESULTS]:
                    items.append(item)

                if result[NEXT] is None:
                    break
            else:
                if DETAIL in result:
                    return None, {DETAIL: result[DETAIL], STATUS: STATUS_ERROR}
                else:
                    return None, RESULT_ERROR

            # we need to replace the full url just with the end, because endpoint
            # is automatically adde during the request
            url = result[NEXT].replace(self.endpoint, "")\
                .replace(self.endpoint.replace("https", "http"), "")\
                .replace("http://localhost/api/", "")

        return items, RESULT_OK

    def resize_image_data(self, image_data, aspect_ratio=False, resize=True):
        """
        Resize image data that are no bigger than max_size.
        :param image_data: cv2/np ndarray
        :return: cv2/np ndarray
        """
        # do not resize image if set to 0
        if resize == False or self.max_size == 0:
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

    def load_base64_file(self, path, resize=True):
        """
        Load file from disk to base64.
        :param path: local path to the image
        :return: base64 encoded string
        """
        image = cv2.imread(str(path))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = self.resize_image_data(image, resize=resize)
        image = self.cv2img_to_base64(image, resize=resize)
        return image

    def cv2img_to_base64(self, image, resize=True):
        """
        Load raw numpy/cv2 data of image to base64. The input image to this method should have RGB order.
        The ximilar accepts base64 data to have BGR order that is why we convert it here.
        The image_data was loaded in similar way:
            image = cv2.imread(str(path))
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        :param image_data: numpy/cv2 data with RGB order
        :param resize: if we want to resize image
        :return: base64 encoded string
        """
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        image = self.resize_image_data(image, resize=resize)
        retval, buffer = cv2.imencode(".jpg", image)
        jpg_as_text = base64.b64encode(buffer).decode("utf-8")
        return jpg_as_text

    def load_url_image(self, path, resize=True):
        """
        Load url file to base64 WITHOUT resizing (it is used in upload image for recognition).
        :param path: url path
        :param resize: if we want to resize image
        :return: base64 encoded string
        """
        r = requests.get(str(path), headers={"Accept": "*/*", "User-Agent": "request"})
        img_bin = r.content
        image = np.asarray(bytearray(img_bin), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = self.cv2img_to_base64(image, resize=resize)
        return image

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

    def custom_endpoint_processing(self, records, endpoint):
        """
        Records processing for your custom endpoint.
        :param records: list of dictionaries with _url, _file, _base64
        :param endpoint: endpoint to add to api.ximilar.com/
        :return: result from endpoint
        """
        records = self.preprocess_records(records)
        return self.post(endpoint, data={RECORDS: records})

    def get_config(self, config_type, version=None):
        """
        Get configuration json from account/v2/config endpoint
        :param config_type: name of the configuration
        :param version: number of config version (optional
        :return: json response
        """
        version = "?version=" + str(version) if version else ""
        return self.get(CONFIG_ENDPOINT + config_type + version)

    def download_image(self, url, destination=""):
        """
        Download image from url to the destination
        :param url: url to the image
        :param destination: where the image will be stored
        :return: None
        """
        f_name = url.split("/")[-1]
        f_dest = destination + f_name

        if os.path.isfile(f_dest):
            return f_dest

        page = requests.get(url)
        with open(f_dest, "wb") as f:
            f.write(page.content)
        return f_dest

    def parallel_records_processing(self, records, method, max_workers=3, batch_size=1, output=False):
        """
        Process method which uses records in parallel way. This works for methods:

        RecogntionClient.upload_image
        RecognitionClient.classify
        FashionTaggingClient.tags
        GenericTaggingClient.tags
        DominantColorClient.dominantcolor

        :param records: list of dictionaries with _url, _file, _base64 and other metadata
                        [{'_file': '__IMG_PATH__', 'id': '__MY_IMAGE_ID__'}, ... ]
        :param method: method to call
        :param max_workers: how many threads will we spawn for work (recommended is 3)
        :param batch_size: how many images are we sending in batch
        :param output: output to stdout with progressbar / tqdm
        :return: list of results from every method
        """
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        futures = [
            {"future": executor.submit(method, records_to_proc), "size": len(records_to_proc)}
            for records_to_proc in self.batch(records, n=batch_size)
        ]

        results = []
        if output:
            with tqdm(total=len(records)) as pbar:
                for future in futures:
                    result = future["future"].result()
                    results.append(result)
                    pbar.update(future["size"])
        else:
            results = [future["future"].result() for future in futures]
        return results

    def batch(self, iterable, n=1):
        """
        Divides list to batches of size n.
        """
        l = len(iterable)
        for ndx in range(0, l, n):
            yield iterable[ndx : min(ndx + n, l)]
