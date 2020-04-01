import requests

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

    def change_predict_endpoint(self, new_endpoint):
        self.PREDICT_ENDPOINT = new_endpoint

    def tags(self, records, aggregate_labels=False):
        return super().tags(records, self.PREDICT_ENDPOINT, aggregate_labels=aggregate_labels)

    def get_top_categories(self):
        result = requests.get(self.urljoin(self.endpoint, "tagging/fashion/v2/top_categories"))
        return result.json()["labels"]

    def get_categories(self):
        result = requests.get(self.urljoin(self.endpoint, "tagging/fashion/v2/categories"))
        return result.json()["labels"]


class GenericTaggingClient(TaggingClient):
    def __init__(self, token, endpoint=ENDPOINT, resource_name=GENERIC_TAGGING):
        super(GenericTaggingClient, self).__init__(token=token, endpoint=endpoint, resource_name=resource_name)
        self.PREDICT_ENDPOINT = GENERIC_TAGGING_ENDPOINT

    def tags(self, records):
        return super().tags(records, self.PREDICT_ENDPOINT)
