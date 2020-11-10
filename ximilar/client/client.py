import requests
import json
import base64
import cv2
import os
import re
import numpy as np
import concurrent.futures
import urllib.parse

from tqdm import tqdm

from ximilar.client.constants import *
from ximilar.client.exceptions import XimilarClientException
from ximilar.client.utils.decorators import retry_when

CONFIG_ENDPOINT = "account/v2/config/"
BASE64_HEADER_PATTERN = re.compile(r"^data:image/(\w+);base64,")


class RestClient(object):
    """
    Parent class that implements HTTP GET, POST, DELETE methods with requests lib and loading images to base64.

    All objects contains TOKEN and ENDPOINT information.
    """

    def __init__(self, token, endpoint=ENDPOINT, max_image_size=600, resource_name="", request_timeout=90):
        self.token = token
        self.cache = {}
        self.endpoint = endpoint
        self.max_image_size = max_image_size
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": self.get_token_header(self.token),
            "User-Agent": "Ximilar Client/Python",
        }
        self.check_resource(resource_name)
        self.request_timeout = request_timeout

    def add_workspace(self, data, url=None):
        """
        Add workspace uuid to the data.
        :param data: dictionary/json data which will be send to endpoint
        :return: modified json data with workspace
        """
        if self.workspace != DEFAULT_WORKSPACE:
            if data is None:
                data = {}

            # if workspace is already in url then do not create the param
            if url is not None and self.workspace not in url:
                data[WORKSPACE] = self.workspace
            elif url is None:
                data[WORKSPACE] = self.workspace
        return data

    def get_token_header(self, token):
        if len(token) < 70:
            return "Token " + token
        return "JWT " + token

    def invalidate(self):
        self.cache = {}

    def _type(self):
        """
        Returns the Class name of the object.
        For example RecogntionClient._type() => "RecognitionClient"
                    Image._type() => "Image"
        """
        return self.__class__.__name__

    @staticmethod
    def urljoin(*args):
        """
        Joins given arguments into an url. Trailing and leading slashes are
        stripped for each argument.
        """

        url = "/".join(map(lambda x: str(x).rstrip("/").lstrip("/"), args))
        return url

    @retry_when(ConnectionError)
    def get(self, api_endpoint, data=None, params=None):
        """
        Call the http GET request with data.
        :param api_endpoint: endpoint path
        :param data: optional data
        :param params: optional dictionary of URL params
        :return: json response
        """
        result = requests.get(
            self.urljoin(self.endpoint, api_endpoint),
            params=params,
            headers=self.headers,
            data=data,
            timeout=self.request_timeout,
        )
        return result.json()

    @retry_when(ConnectionError)
    def post(self, api_endpoint, data=None, files=None, params=None, method=requests.post, headers=None):
        """
        Call the http POST request with data.

        :param api_endpoint: endpoint path
        :param data: optional data
        :param files: optional files to upload
        :param params: optional dictionary of URL params
        :param method: POST or PUT method of request
        :return: json response
        """
        self.invalidate()
        if data is not None and files is not None:
            raise Exception("Unable to send data along with files with python requests library!")

        if data is not None:
            data = json.dumps(data)

        result = method(
            self.urljoin(self.endpoint, api_endpoint),
            params=params,
            headers=self.headers if headers is None else headers,
            data=data,
            files=files,
            timeout=self.request_timeout,
        )
        # todo: check JSON RESULT CODES -> raise XimilarClientException
        # todo: check HTTP STATUS CODES -> raise XimilarClientException
        try:
            json_result = result.json()
            return json_result
        except ValueError as e:
            return None

    @retry_when(ConnectionError)
    def put(self, api_endpoint, data=None, files=None, params=None):
        """
        Call the http PUT request with data
        """
        return self.post(api_endpoint, data=data, files=files, params=params, method=requests.put)

    @retry_when(ConnectionError)
    def delete(self, api_endpoint, data=None, params=None):
        """
        Call the http DELETE request with data.
        :param api_endpoint: endpoint path
        :param data: optional data
        :param params: optional dictionary of URL params
        :return: response
        """
        self.invalidate()

        url = urllib.parse.urljoin(self.endpoint, api_endpoint)
        result = requests.delete(url, params=params, headers=self.headers, data=data, timeout=self.request_timeout)

        if result.status_code == HTTP_NO_CONTENT_204:
            return result

        return result.json()

    def check_resource(self, resource_name):
        """
        Checks if the user has access (resource) to the service.
        :param resource_name: name of the service
        :return: True if user has access otherwise False
        """
        # we don't want to check resource for entities like Image, Task, Object, DetectionLabel, ...
        if "localhost" in self.endpoint or "Client" not in self._type() or not self.token or not resource_name:
            return True

        # we need to authorize it with FIXED Endpoint https://api.ximilar.com/authorization/v2/authorize
        # as the self.endpoint can be different size
        result = requests.post(
            ENDPOINT + "authorization/v2/authorize",
            data=json.dumps({"service": resource_name}),
            headers=self.headers,
            timeout=10,
        )

        try:
            result = result.json()
        except:
            result = None

        if result and USER_ID in result:
            return True

        if "detail" in result:
            raise Exception(result["detail"] + " " + resource_name + ". Please contact tech@ximilar.com!")
        raise Exception("User has no access for service: " + resource_name + ". Please contact tech@ximilar.com!")

    def get_user_details(self):
        """
        Get Basic information of actual user.
        :return: json response if success
        """
        return self.get("account/v2/user/")

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
            url = (
                result[NEXT]
                .replace(self.endpoint, "")
                .replace(self.endpoint.replace("https", "http"), "")
                .replace("http://localhost/api/", "")
            )

        return items, RESULT_OK

    def add_header(self, header):
        """ Add header to the every request """
        self.headers.update(header)

    def check_json_status(self, result):
        """
        Check status code in json result, if not 200 then raises exception!
        :param result: json dictionary
        :raises XimilarClientException: returned status code from endpoint, text
        :raises XimilarClientException: 500, text
        """
        if result is not None and "status" in result:
            if "code" in result["status"] and result["status"]["code"] != 200:
                if result["status"]["text"]:
                    raise XimilarClientException(result["status"]["code"], result["status"]["text"])
                raise XimilarClientException(500, "Unexpected error when getting result from endpoint!")

    def resize_image_data(self, image_data, aspect_ratio=True, resize=True):
        """
        Resize image data that are no bigger than max_size.
        :param image_data: cv2/np ndarray
        :return: cv2/np ndarray
        """
        # do not resize image if set to 0
        if not resize or self.max_image_size == 0:
            return image_data

        height, width, _ = image_data.shape
        if height > self.max_image_size and width > self.max_image_size and not aspect_ratio:
            image_data = cv2.resize(image_data, (self.max_image_size, self.max_image_size))
        if height > self.max_image_size and width > self.max_image_size and aspect_ratio:
            image_data = cv2.resize(image_data, self.get_aspect_ratio_dim(image_data, self.max_image_size))
        return image_data

    def get_aspect_ratio_dim(self, image, img_size):
        if image.shape[0] > image.shape[1]:
            r = float(img_size) / image.shape[1]
            dim = (img_size, int(image.shape[0] * r))
        else:
            r = float(img_size) / image.shape[0]
            dim = (int(image.shape[1] * r), img_size)
        return dim

    def cv2_imread(self, path):
        image = cv2.imread(str(path))
        return image

    def cv2_imwrite(self, image_record, path):
        """
        Writes image data into given file
        :param image_record: dictionary with image data and color space
        :param path: file to store the image to
        :return: true if everything was fine
        """
        image = image_record[IMG_DATA]
        image_space = image_record[COLOR_SPACE] if COLOR_SPACE in image_record else "RGB"
        image = self._convert_image_to_bgr(image, image_space)

        cv2.imwrite(path, image)
        return True

    def load_base64_file(self, path, resize=True):
        """
        Load file from disk to base64.
        :param path: local path to the image
        :return: base64 encoded string
        """
        # if the image is quite small then just convert it to base64
        if (not resize) or os.stat(path).st_size / (1024 * 1024) < 0.1:
            with open(path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            return encoded_string

        # otherwise convert it to cv2 matrix, then encode it  and then to base64
        image = self.cv2_imread(path)
        image = self.cv2img_to_base64(image, image_space="BGR", resize=resize)
        return image

    def cv2img_to_base64(self, image, image_space="RGB", resize=True):
        """
        Load raw numpy/cv2 data of image to base64. The input image to this method should have RGB order.
        The ximilar accepts base64 data to have BGR order that is why we convert it here.
        The image_data was loaded in similar way:
            image = cv2.imread(str(path))
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        :param image: numpy/cv2 data with RGB order
        :param image_space: from which color space we are converting (default RGB)
        :param resize: if we want to resize image
        :return: base64 encoded string
        """
        image = self._convert_image_to_bgr(image, image_space)
        image = self.resize_image_data(image, resize=resize)
        retval, buffer = cv2.imencode(".jpg", image, params=[cv2.IMWRITE_JPEG_QUALITY, 96])
        jpg_as_text = "data:image/jpeg;base64," + base64.b64encode(buffer).decode("utf-8")
        return jpg_as_text

    def base64_to_cv2img(self, base64image):
        """
        Convert base64 data to image in BGR format.
        :param base64image: base64 image encoded
        :return: opencv2/numpy image
        """
        try:
            header = BASE64_HEADER_PATTERN.match(base64image)
            if header:
                base64data = BASE64_HEADER_PATTERN.sub("", base64image)
                base64image = base64data

            img_array = base64.b64decode(base64image)

            image = np.frombuffer(img_array, dtype=np.uint8)
            image = cv2.imdecode(image, 1)
            if image.shape[2] != 3:
                raise Exception("Image has not shape (height, width, 3)")
            return image
        except Exception as e:
            raise Exception("Unable to read base64:" + str(e))

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
        # (shallow) copy the records in order not to modify the incoming dictionaries
        records = [rec.copy() for rec in records]
        for i in range(len(records)):
            if (
                FILE not in records[i]
                and BASE64 not in records[i]
                and URL not in records[i]
                and IMG_DATA not in records[i]
                and "_id" not in records[i]
            ):
                raise Exception("Please specify one of '_file', '_base64', '_url', '_img_data' field in record")

            noresize = NORESIZE in records[i] and records[i][NORESIZE]

            if FILE in records[i] and BASE64 not in records[i] and IMG_DATA not in records[i]:
                records[i][BASE64] = self.load_base64_file(records[i][FILE], resize=not noresize)
            elif BASE64 in records[i] and (noresize or self.max_image_size == 0):
                # if we have base64 and we do not want to resize it at all
                pass
            elif BASE64 in records[i]:
                # if we have base64 and we need to resize it
                image = self.base64_to_cv2img(records[i][BASE64])
                records[i][BASE64] = self.cv2img_to_base64(image, image_space="BGR", resize=not noresize)
            elif IMG_DATA in records[i]:
                records[i][BASE64] = self.cv2img_to_base64(
                    records[i][IMG_DATA],
                    image_space=records[i][COLOR_SPACE] if COLOR_SPACE in records[i] else "RGB",
                    resize=not noresize,
                )

            # finally we need to delete the image data and just send url or base64
            if IMG_DATA in records[i]:
                del records[i][IMG_DATA]

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

    @staticmethod
    def download_image(url, destination="", name=None):
        """
        Download image from url to the destination
        :param url: url to the image
        :param destination: where the image will be stored
        :return: None
        """
        f_name = url.split("/")[-1] if name is None else name
        f_dest = os.path.join(destination, f_name)
        f_dest += ".jpg" if "." not in f_name else ""

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
            status = {"answer_records": 0, "records": 0, "error": 0, "skipped_records": 0}
            with tqdm(total=len(records)) as pbar:
                for future in futures:
                    result = future["future"].result()
                    self.update_status(status, result)
                    results.append(result)
                    pbar.update(future["size"])
            print(status)
        else:
            results = [future["future"].result() for future in futures]
        return results

    def update_status(self, status, result):
        if "status" in result:
            if isinstance(result["status"], int):
                if result["status"] >= 300:
                    status["error"] += 1
            if isinstance(result["status"], dict):
                if "code" in result["status"]:
                    if result["status"]["code"] >= 300:
                        status["error"] += 1
        if "records" in result:
            status["records"] += len(result["records"])
        if "skipped_records" in result:
            status["skipped_records"] += len(result["skipped_records"])
        if "answer_records" in result:
            status["answer_records"] += len(result["answer_records"])

    def batch(self, iterable, n=1):
        """
        Divides list to batches of size n.
        """
        l = len(iterable)
        for ndx in range(0, l, n):
            yield iterable[ndx : min(ndx + n, l)]

    @staticmethod
    def _convert_image_to_bgr(image, image_space="RGB"):
        """
        Converts given image from given record to BGR
        :param image: image data
        :param image_space: string saying the image space
        :return: image data in BGR
        """
        if image_space == "BGR":
            return image
        if image_space == "RGB":
            return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        elif image_space == "HSV":
            return cv2.cvtColor(image, cv2.COLOR_HSV2BGR)
        elif image_space == "LUV":
            return cv2.cvtColor(image, cv2.COLOR_LUV2BGR)
        raise ValueError("unknown image space: " + image_space)
