from ximilar.client import RestClient
from ximilar.client.constants import *

FASHION_TAGGING_ENDPOINT = "tagging/fashion/v2/tags"
GENERIC_TAGGING_ENDPOINT = "tagging/generic/v2/tags"


class TaggingClient(RestClient):
    def construct_data(self, records=[]):
        if len(records) == 0:
            raise Exception("Please specify at least on record when using tags method.")

        data = {RECORDS: self.preprocess_records(records)}
        return data

    def tags(self, records, endpoint):
        data = self.construct_data(records=records)
        return self.post(endpoint, data=data)


class FashionTaggingClient(TaggingClient):
    def __init__(self, token, endpoint=ENDPOINT, resource_name=FASHION_TAGGING):
        super(FashionTaggingClient, self).__init__(token=token, endpoint=endpoint, resource_name=resource_name)
        self.PREDICT_ENDPOINT = FASHION_TAGGING_ENDPOINT

    def tags(self, records):
        return super().tags(records, self.PREDICT_ENDPOINT)


class GenericTaggingClient(TaggingClient):
    def __init__(self, token, endpoint=ENDPOINT, resource_name=GENERIC_TAGGING):
        super(GenericTaggingClient, self).__init__(token=token, endpoint=endpoint, resource_name=resource_name)
        self.PREDICT_ENDPOINT = GENERIC_TAGGING_ENDPOINT

    def tags(self, records):
        return super().tags(records, self.PREDICT_ENDPOINT)
