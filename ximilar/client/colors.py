import json

from ximilar.client import RestClient
from ximilar.client.constants import *

DOMINANT_COLOR_GENERIC_ENDPOINT = "dom_colors/generic/v2/dominantcolor"
DOMINANT_COLOR_PRODUCT_ENDPOINT = "dom_colors/product/v2/dominantcolor"


class DominantColorClient(RestClient):
    def construct_data(self, records=[]):
        if len(records) == 0:
            raise Exception("Please specify at least one record in detect method!")

        data = {RECORDS: self.preprocess_records(records)}
        return data

    def dominantcolor(self, records, endpoint):
        records = self.preprocess_records(records)
        return self.post(endpoint, data={RECORDS: records})


class DominantColorGenericClient(DominantColorClient):
    def __init__(self, token, endpoint=ENDPOINT, resource_name=DOMINANT_COLORS_PRODUCT):
        super().__init__(token=token, endpoint=endpoint, resource_name=resource_name)
        self.PREDICT_ENDPOINT = DOMINANT_COLOR_GENERIC_ENDPOINT

    def dominantcolor(self, records):
        return super().dominantcolor(records, DOMINANT_COLOR_GENERIC_ENDPOINT)


class DominantColorProductClient(DominantColorClient):
    def __init__(self, token, endpoint=ENDPOINT, resource_name=DOMINANT_COLORS_GENERIC):
        super().__init__(token=token, endpoint=endpoint, resource_name=resource_name)
        self.PREDICT_ENDPOINT = DOMINANT_COLOR_PRODUCT_ENDPOINT

    def dominantcolor(self, records):
        return super().dominantcolor(records, DOMINANT_COLOR_PRODUCT_ENDPOINT)
