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

    def tags(self, records, endpoint, aggregate_labels=False):
        data = self.construct_data(records=records)

        if aggregate_labels:
            data["aggregate_labels"] = True

        result = self.post(endpoint, data=data)
        self.check_json_status(result)
        return result


class FashionTaggingClient(TaggingClient):
    def __init__(self, token, endpoint=ENDPOINT, resource_name=FASHION_TAGGING):
        super(FashionTaggingClient, self).__init__(token=token, endpoint=endpoint, resource_name=resource_name)
        self.PREDICT_ENDPOINT = FASHION_TAGGING_ENDPOINT

    def tags(self, records, aggregate_labels=False, predict_endpoint=None):
        # todo: remove this if, just for dev
        if predict_endpoint:
            return super().tags(records, predict_endpoint, aggregate_labels=aggregate_labels)
        return super().tags(records, self.PREDICT_ENDPOINT, aggregate_labels=aggregate_labels)


class GenericTaggingClient(TaggingClient):
    def __init__(self, token, endpoint=ENDPOINT, resource_name=GENERIC_TAGGING):
        super(GenericTaggingClient, self).__init__(token=token, endpoint=endpoint, resource_name=resource_name)
        self.PREDICT_ENDPOINT = GENERIC_TAGGING_ENDPOINT

    def tags(self, records):
        return super().tags(records, self.PREDICT_ENDPOINT)
