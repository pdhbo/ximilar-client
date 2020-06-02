import json

from ximilar.client import RestClient
from ximilar.client.constants import *

DOMINANT_COLOR_GENERIC_ENDPOINT = "dom_colors/generic/v2/dominantcolor"
DOMINANT_COLOR_PRODUCT_ENDPOINT = "dom_colors/product/v2/dominantcolor"


class DominantColorClient(RestClient):
    def dominantcolor(self, records, endpoint):
        records = self.preprocess_records(records)
        return self.post(endpoint, data={RECORDS: records})


class DominantColorGenericClient(DominantColorClient):
    def __init__(self, token, endpoint=ENDPOINT, resource_name=DOMINANT_COLORS_PRODUCT):
        super(DominantColorGenericClient, self).__init__(token=token, endpoint=endpoint, resource_name=resource_name)

    def dominantcolor(self, records):
        return super().dominantcolor(records, DOMINANT_COLOR_GENERIC_ENDPOINT)


class DominantColorProductClient(DominantColorClient):
    def __init__(self, token, endpoint=ENDPOINT, resource_name=DOMINANT_COLORS_GENERIC):
        super(DominantColorProductClient, self).__init__(token=token, endpoint=endpoint, resource_name=resource_name)

    def dominantcolor(self, records):
        return super().dominantcolor(records, DOMINANT_COLOR_PRODUCT_ENDPOINT)
