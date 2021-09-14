import requests

from ximilar.client import RestClient
from ximilar.client.constants import *

FASHION_TAGGING_ENDPOINT = "tagging/fashion/v2/tags"
META_FASHION_TAGGING_ENDPOINT = "tagging/fashion/v2/meta"
RECORDS = "records"


class UpscaleClient(RestClient):
    def construct_data(self, records, **kwargs):
        if len(records) == 0:
            raise Exception("Please specify at least one record when using tags method.")

        data = {RECORDS: self.preprocess_records(records)}

        if kwargs:
            data.update(kwargs)

        return data

    def upscale(self, records, endpoint, **kwargs):
        """
        Call the upscaling endpoint
        :param records: [description]
        :param endpoint: [description]
        :return: json result data from the API
        """
        data = self.construct_data(records, **kwargs)
        result = self.post(endpoint, data=data)
        return result