from ximilar.client import RestClient
from ximilar.client.constants import RECORDS

DOMINANT_COLOR_GENERIC_ENDPOINT = 'generic_photos/v2/dominantcolor'
DOMINANT_COLOR_PRODUCT_ENDPOINT = 'product_photos/v2/dominantcolor'


class DominantColorClient(RestClient):
    def dominantcolor(self, records, endpoint):
        records = self.preprocess_records(records)
        return self.post(endpoint, data={RECORDS: records})


class DominantColorGenericClient(DominantColorClient):
    def dominantcolor(self, records):
        return super().dominantcolor(records, DOMINANT_COLOR_GENERIC_ENDPOINT)


class DominantColorProductClient(DominantColorClient):
    def dominantcolor(self, records):
        return super().dominantcolor(records, DOMINANT_COLOR_PRODUCT_ENDPOINT)

