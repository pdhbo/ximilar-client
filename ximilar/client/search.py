from ximilar.client import RestClient
from ximilar.client.constants import RECORDS, ENDPOINT, FIELDS_TO_RETURN, _ID, FILTER, COUNT, K_COUNT, QUERY_RECORD, COLLECTION

SIMILARITY_PHOTOS = 'similarity/photos/v2/'
SIMILARITY_PRODUCTS = 'similarity/products/v2/'
SMART_SEARCH = 'smart/v2/product/'

SEARCH_OBJ_ENDPOINT = 'search_by_object'
SEARCH = 'search'
DETECT = 'detect'
INSERT = 'insert'
DELETE = 'delete'
GET = 'get'
UPDATE = 'update'
RANDOM = 'random'
KNN_VISUAL = 'visualKNN'
PING = 'ping'


class SimilarityPhotosClient(RestClient):
    def __init__(self, token,  collection, endpoint=ENDPOINT+SIMILARITY_PHOTOS):
        super(SimilarityPhotosClient, self).__init__(token=token, endpoint=endpoint)

        self.max_size = 1000
        self.headers[COLLECTION] = collection

    def search(self, record, filter=None, count=5, fields_to_return=[]):
        """
        Calls visual knn
        :param record: dictionary with field '_id' (from your collection) or '_url' or "_base64' data
        :param k: how many similar items to return
        :param fields_to_return: fields to return in every record
        :param filter: how to filter picked items (mongodb syntax)
        :return: json response
        """
        data = {QUERY_RECORD: record, K_COUNT: count, FIELDS_TO_RETURN: fields_to_return}
        if filter:
            data[FILTER] = filter

        return self.post(KNN_VISUAL, data=data)

    def random(self, filter=None, count=10, fields_to_return=[]):
        """
        Call random endpoint which returns random(X=count) records from your collection.
        :param filter: how to filter picked items (mongodb syntax)
        :param count: number of items to return
        :param fields_to_return: fields to return in every record
        :return: json response
        """
        data = {COUNT: count, FIELDS_TO_RETURN: fields_to_return}
        if filter:
            data[FILTER] = filter

        return self.post(RANDOM, data=data)

    def update(self, records):
        """
        Update records with meta-information, this will not update the descriptor(please do delete and insert instead).
        :param records: list of dictionaries with field '_id', '_url' or '_base64' with your meta-info
        :return: json response
        """
        data = {RECORDS: records}
        return self.post(UPDATE, data=data)

    def delete(self, records):
        """
        Delete records from your collection.
        :param records: list of dictionaries with '_id' field
        :return: json response
        """
        data = {RECORDS: records}
        return self.post(DELETE, data=data)

    def insert(self, records):
        """
        Insert records into collection with all meta information.
        :param records: dictionary with your "_id" and with one of "_url", "_file" or "_base64" to extract descriptor.
        :return: json response
        """
        data = {RECORDS: records}
        return self.post(INSERT, data=data)

    def get(self, records, fields_to_return=[_ID]):
        """
        Get the records from your collection.
        :param records: list of dictionaries with "_id" (identification of your records)
        :param fields_to_return: fields to return in every record
        :return: json response
        """
        data = {RECORDS: records, FIELDS_TO_RETURN: fields_to_return}
        return self.post(GET, data=data)

    def ping(self):
        return self.post(PING)


class SimilarityProductsClient(SimilarityPhotosClient):
    def __init__(self, token, collection, endpoint=ENDPOINT+SIMILARITY_PRODUCTS):
        super(SimilarityProductsClient, self).__init__(token=token, collection=collection, endpoint=endpoint)


class SmartSearchClient(SimilarityPhotosClient):
    def __init__(self, token, collection, endpoint=ENDPOINT+SMART_SEARCH):
        super(SmartSearchClient, self).__init__(token=token, collection=collection, endpoint=endpoint)

    def search(self, records):
        """
        Detects Objects and Tags and find for the largest object most visually similar items in your collection.
        :param records:
        :return:
        """
        records = self.preprocess_records(records)
        return self.post(SEARCH, data={RECORDS: records})

    def detect(self, records):
        """
        Detects Objects and Tags without searching items.
        :param records: list of dictionaries with _url|_file|_base64
        :return: json response
        """
        records = self.preprocess_records(records)
        return self.post(DETECT, data={RECORDS: records, COLLECTION: self.headers[COLLECTION]})

    def search_by_object(self, records, collection):
        raise NotImplementedError
