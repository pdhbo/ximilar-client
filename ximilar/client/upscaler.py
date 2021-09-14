import requests

from ximilar.client import RestClient
from ximilar.client.constants import *

RECORDS = "records"


class UpscaleClient(RestClient):
    def construct_data(self, records, **kwargs):
        if len(records) == 0:
            raise Exception("Please specify at least one record when using tags method.")

        data = {RECORDS: self.preprocess_records(records)}

        if kwargs:
            data.update(kwargs)

        return data

    def upscale(self, records, scale, **kwargs):
        """
        Call the upscaling endpoint
        :param records: [description]
        :param endpoint: [description]
        :return: json result data from the API
        """
        data = self.construct_data(records, **kwargs)
        result = self.post(f'/upscaler/{scale}x/upscale', data=data)
        return result