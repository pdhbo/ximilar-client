from ximilar.client import RestClient
from ximilar.client.constants import *

FASHION_TAGGING_ENDPOINT = "tagging/fashion/v2/tags"
GENERIC_TAGGING_ENDPOINT = "tagging/generic/v2/tags"


class TaggingClient(RestClient):
    def tags(self, records, endpoint):
        records = self.preprocess_records(records)
        return self.post(endpoint, data={RECORDS: records})


class FashionTaggingClient(TaggingClient):
    def __init__(self, token, endpoint=ENDPOINT, resource_name=FASHION_TAGGING):
        super(FashionTaggingClient, self).__init__(token=token, endpoint=endpoint, resource_name=resource_name)

    def tags(self, records):
        return super().tags(records, FASHION_TAGGING_ENDPOINT)


class GenericTaggingClient(TaggingClient):
    def __init__(self, token, endpoint=ENDPOINT, resource_name=GENERIC_TAGGING):
        super(GenericTaggingClient, self).__init__(token=token, endpoint=endpoint, resource_name=resource_name)

    def tags(self, records):
        return super().tags(records, GENERIC_TAGGING_ENDPOINT)
