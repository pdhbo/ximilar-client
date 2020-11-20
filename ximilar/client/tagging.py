import requests

from ximilar.client import RestClient
from ximilar.client.constants import *

FASHION_TAGGING_ENDPOINT = "tagging/fashion/v2/tags"
META_FASHION_TAGGING_ENDPOINT = "tagging/fashion/v2/meta"
GENERIC_TAGGING_ENDPOINT = "tagging/generic/v2/tags"
HOME_DECOR_TAGGING_ENDPOINT = "tagging/homedecor/v2/tags"
DETECT_FASHION_TAGGING_ENDPOINT = "tagging/fashion/v2/detect_tags"
DETECT_FASHION_ENDPOINT = "tagging/fashion/v2/detect"


class TaggingClient(RestClient):
    def construct_data(self, records, aggregate_labels=None, profile=None, **kwargs):
        if len(records) == 0:
            raise Exception("Please specify at least on record when using tags method.")

        data = {RECORDS: self.preprocess_records(records)}

        if aggregate_labels:
            data["aggregate_labels"] = True

        if profile:
            data["profile"] = profile

        if kwargs:
            data.update(kwargs)

        return data

    def tags(self, records, endpoint, aggregate_labels=False, profile=None, **kwargs):
        """
        Call the tagging endpoint
        :param records: [description]
        :param endpoint: [description]
        :param aggregate_labels: [description], defaults to False
        :param profile: [description], defaults to None
        :return: json result data from the API
        """
        data = self.construct_data(records, aggregate_labels=aggregate_labels, profile=profile, **kwargs)
        result = self.post(endpoint, data=data)
        # todo: self.check_json_status(result)
        return result


class FashionTaggingClient(TaggingClient):
    def __init__(self, token, endpoint=ENDPOINT, resource_name=FASHION_TAGGING):
        super(FashionTaggingClient, self).__init__(token=token, endpoint=endpoint, resource_name=resource_name)
        self.PREDICT_ENDPOINT = FASHION_TAGGING_ENDPOINT

    def change_predict_endpoint(self, new_endpoint):
        self.PREDICT_ENDPOINT = new_endpoint

    def tags(self, records, aggregate_labels=False, profile=None):
        return super().tags(records, self.PREDICT_ENDPOINT, aggregate_labels=aggregate_labels, profile=profile)

    def meta_tags(self, records, profile=None, **kwargs):
        return super().tags(records, META_FASHION_TAGGING_ENDPOINT, profile=profile, **kwargs)

    def detect(self, records, profile=None, **kwargs):
        return super().tags(records, DETECT_FASHION_ENDPOINT, profile=profile, **kwargs)

    def detect_tags(self, records, profile=None, **kwargs):
        return super().tags(records, DETECT_FASHION_TAGGING_ENDPOINT, profile=profile, **kwargs)

    def get_top_categories(self):
        result = requests.get(self.urljoin(self.endpoint, "tagging/fashion/v2/top_categories"))
        return result.json()["labels"]

    def get_categories(self):
        result = requests.get(self.urljoin(self.endpoint, "tagging/fashion/v2/categories"))
        return result.json()["labels"]


class HomeDecorTaggingClient(TaggingClient):
    def __init__(self, token, endpoint=ENDPOINT, resource_name=HOME_DECOR_TAGGING):
        super(HomeDecorTaggingClient, self).__init__(token=token, endpoint=endpoint, resource_name=resource_name)
        self.PREDICT_ENDPOINT = HOME_DECOR_TAGGING_ENDPOINT

    def change_predict_endpoint(self, new_endpoint):
        self.PREDICT_ENDPOINT = new_endpoint

    def tags(self, records, aggregate_labels=False, profile=None):
        return super().tags(records, self.PREDICT_ENDPOINT, aggregate_labels=aggregate_labels, profile=profile)


class GenericTaggingClient(TaggingClient):
    def __init__(self, token, endpoint=ENDPOINT, resource_name=GENERIC_TAGGING):
        super(GenericTaggingClient, self).__init__(token=token, endpoint=endpoint, resource_name=resource_name)
        self.PREDICT_ENDPOINT = GENERIC_TAGGING_ENDPOINT

    def tags(self, records):
        return super().tags(records, self.PREDICT_ENDPOINT)
