from ximilar.client.constants import _ID, K_COUNT, FIELDS_TO_RETURN, ENDPOINT, VISUAL_SEARCH, RECORDS, FILTER
from ximilar.client.search import SimilarityPhotosClient

VISUAL_SEARCH_V2 = "similarity/fashion/v2/"

SEARCH_PRODUCT = "visualTagsKNN"
INSERT_PRODUCT = "insert"
DELETE_PRODUCT = "insert"

ALL_IDS = "allIDs"
PING = "ping"


class FashionSearchClient(SimilarityPhotosClient):
    def __init__(self, token, collection_id=None, endpoint=ENDPOINT + VISUAL_SEARCH_V2, resource_name=VISUAL_SEARCH):
        super().__init__(token=token, collection_id=collection_id, endpoint=endpoint, resource_name=resource_name)
        self.PREDICT_ENDPOINT = SEARCH_PRODUCT

    def get_categories(self):
        """
        Return available top categories for products.
        """
        result = self.get(TOP_CATEGORIES)
        return result

    def descriptor(self, records, custom_flow=None, **kwargs):
        data = self.construct_data(records=records, custom_flow=custom_flow, **kwargs)
        return self.post("descriptor", data=data)

    def detect(self, records, custom_flow=None):
        """
        Detects Objects and Tags without searching items.
        :param records: list of dictionaries with _url|_file|_base64
        :return: json response
        """
        records = self.preprocess_records(records)
        data = self.fill_data({RECORDS: records}, custom_flow)
        return self.post(DETECT_PRODUCT, data=data)

    def insert(self, records, custom_flow=None):
        """
        Insert records into collection with all meta information.
        :param records: dictionary with your "_id" and with one of "_url", "_file" or "_base64" to extract descriptor.
        :param custom_flow: string ID of the flow that should be called during the insert (in extractor)
        :return: json response
        """
        data = self.fill_data({RECORDS: records}, custom_flow)
        return self.post(INSERT_PRODUCT, data=data)

    def random(self, filter=None, count=10, fields_to_return=[]):
        raise NotImplementedError("random operation does not work for Visual Search")

    def get_all_ids(self):
        """
        Returns an array with records with "_id" fields.
        :return: an array with records with "_id" fields.
        """
        return self.post(ALL_IDS, data={"something": "value"})

    def fill_data(self, data, custom_flow):
        if custom_flow is not None:
            data["custom_flow"] = custom_flow

        return data
