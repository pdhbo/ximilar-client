from ximilar.client import RestClient
from ximilar.client.constants import *

REMOVEBG_ENDPOINT = "removebg/v2/removebg"


class RemoveBGClient(RestClient):
    def __init__(self, token, endpoint=ENDPOINT, resource_name=REMOVEBG):
        super(RemoveBGClient, self).__init__(token=token, endpoint=endpoint, resource_name=resource_name)
        self.PREDICT_ENDPOINT = REMOVEBG_ENDPOINT

    def construct_data(self, records=[]):
        if len(records) == 0:
            raise Exception("Please specify at least one record in detect method!")

        data = {RECORDS: self.preprocess_records(records)}
        return data

    def removebg(self, records):
        records = self.preprocess_records(records)
        return self.post(self.PREDICT_ENDPOINT, data={RECORDS: records})
