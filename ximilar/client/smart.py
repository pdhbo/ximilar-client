from ximilar.client.constants import (
    _ID,
    K_COUNT,
    FIELDS_TO_RETURN,
    ENDPOINT,
    SMART_PRODUCT_SEARCH,
    RECORDS,
    COLLECTION,
    FILTER,
)
from ximilar.client.search import SimilarityPhotosClient

SMART_SEARCH = "smart/v2/"

SEARCH_OBJ_ENDPOINT = "product/search_by_object"
SEARCH_PRODUCT = "product/search"
DETECT_PRODUCT = "product/detect"
INSERT_PRODUCT = "product/insert"
ALL_IDS = "allIDs"
PING = "ping"


class SmartSearchClient(SimilarityPhotosClient):
    def __init__(
        self,
        token,
        collection=None,
        collection_id=None,
        endpoint=ENDPOINT + SMART_SEARCH,
        resource_name=SMART_PRODUCT_SEARCH,
    ):
        super(SmartSearchClient, self).__init__(
            token=token,
            collection=collection,
            collection_id=collection_id,
            endpoint=endpoint,
            resource_name=resource_name,
        )

    def search(self, records, filter=None, count=5, fields_to_return=[_ID]):
        """
        Detects Objects and Tags and find for the largest object most visually similar items in your collection.
        :param records: array with one record (dictionary) with '_url' or "_base64' data
        :param count: how many similar items to return
        :param fields_to_return: fields to return in every record
        :param filter: how to filter picked items (mongodb syntax)
        :return:
        """
        data = {RECORDS: self.preprocess_records(records), K_COUNT: count, FIELDS_TO_RETURN: fields_to_return}
        if filter:
            data[FILTER] = filter

        return self.post(SEARCH_PRODUCT, data=data)

    def detect(self, records):
        """
        Detects Objects and Tags without searching items.
        :param records: list of dictionaries with _url|_file|_base64
        :return: json response
        """
        records = self.preprocess_records(records)
        return self.post(DETECT_PRODUCT, data={RECORDS: records})

    def search_by_object(self, records, filter=None, count=5, fields_to_return=[_ID]):
        """
        Detects Objects and Tags without searching items.
        :param records: list of dictionaries with _url|_file|_base64
        :return: json response
        """
        data = {RECORDS: self.preprocess_records(records), K_COUNT: count, FIELDS_TO_RETURN: fields_to_return}
        if filter:
            data[FILTER] = filter
        return self.post(SEARCH_OBJ_ENDPOINT, data={RECORDS: records, COLLECTION: self.headers[COLLECTION]})

    def insert(self, records):
        """
        Insert records into collection with all meta information.
        :param records: dictionary with your "_id" and with one of "_url", "_file" or "_base64" to extract descriptor.
        :return: json response
        """
        data = {RECORDS: records}
        return self.post(INSERT_PRODUCT, data=data)

    def random(self, filter=None, count=10, fields_to_return=[]):
        raise NotImplementedError("random operation does not work for Smart Search")

    def get_all_ids(self):
        """
        Returns an array with records with "_id" fields.
        :return: an array with records with "_id" fields.
        """
        return self.post(ALL_IDS, data={"something": "value"})
