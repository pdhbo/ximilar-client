from ximilar.client import RestClient
from ximilar.client.constants import RECORDS

SIMILARITY_PHOTOS = '/similarity/photos/v2/'
SIMILARITY_PHOTOS = '/similarity/products/v2/'

SMART_INSERT_ENDPOINT = '/smart/v2/product/insert'
SMART_SEARCH_ENDPOINT = '/smart/v2/product/search'
SMART_DETECT_ENDPOINT = '/smart/v2/product/detect'
SMART_SEARCH_OBJ_ENDPOINT = '/smart/v2/product/search_by_object'


class Similarity(RestClient):
    def insert(self):
        raise NotImplementedError

    def search(self, records, collection):
        raise NotImplementedError

    def delete(self, records, collection):
        raise NotImplementedError

    def random(self, records, collection):
        raise NotImplementedError

    def get(self):
        raise NotImplementedError


class SmartSearchClient(RestClient):
    def __init__(self, token):
        super(SmartSearchClient, self).__init__(token)
        self.max_size = 1000

    def insert(self):
        raise NotImplementedError

    def search(self, records, collection):
        raise NotImplementedError

    def detect(self, records):
        records = self.preprocess_records(records)
        return self.post(SMART_DETECT_ENDPOINT, data={RECORDS: records})

    def search_by_object(self, records, collection):
        raise NotImplementedError