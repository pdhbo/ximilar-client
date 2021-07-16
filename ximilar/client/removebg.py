from ximilar.client import RestClient
from ximilar.client.constants import *

REMOVEBG_ENDPOINT_PRECISE = "removebg/precise/removebg"
REMOVEBG_ENDPOINT_FAST = "removebg/fast/removebg"


class RemoveBGClient(RestClient):
    def __init__(self, token, endpoint=ENDPOINT, resource_name=REMOVEBG):
        super(RemoveBGClient, self).__init__(token=token, endpoint=endpoint, resource_name=resource_name)
        self.PREDICT_ENDPOINT = REMOVEBG_ENDPOINT_PRECISE

    def construct_data(self, records=[]):
        if len(records) == 0:
            raise Exception("Please specify at least one record in detect method!")

        data = {RECORDS: self.preprocess_records(records)}
        return data

    def removebg_precise(self, records):
        records = self.preprocess_records(records)
        return self.post(self.PREDICT_ENDPOINT, data={RECORDS: records})

    def removebg_fast(self, records):
        records = self.preprocess_records(records)
        return self.post(REMOVEBG_ENDPOINT_FAST, data={RECORDS: records})
