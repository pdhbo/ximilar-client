from ximilar.client.constants import _ID, K_COUNT, FIELDS_TO_RETURN, ENDPOINT, VISUAL_SEARCH, RECORDS, FILTER
from ximilar.client.search import SimilarityPhotosClient

VISUAL_SEARCH_V2 = "visual-search/v2/"

SEARCH_OBJ_ENDPOINT = "product/search_by_object"
SEARCH_PRODUCT = "product/search"
TOP_CATEGORIES = "product/top_categories"
DETECT_PRODUCT = "product/detect"
INSERT_PRODUCT = "product/insert"
ALL_IDS = "allIDs"
PING = "ping"


class VisualSearchClient(SimilarityPhotosClient):
    def __init__(self, token, collection_id=None, endpoint=ENDPOINT + VISUAL_SEARCH_V2, resource_name=VISUAL_SEARCH):
        super(VisualSearchClient, self).__init__(
            token=token, collection_id=collection_id, endpoint=endpoint, resource_name=resource_name
        )
        self.PREDICT_ENDPOINT = SEARCH_PRODUCT

    def construct_data(self, records=[], filter=None, k=5, fields_to_return=[_ID], custom_flow=None, **kwargs):
        if len(records) == 0:
            raise Exception("Please specify at least on record when using search method.")

        data = {RECORDS: self.preprocess_records(records), K_COUNT: k, FIELDS_TO_RETURN: fields_to_return}
        if filter:
            data[FILTER] = filter

        if kwargs:
            data.update(kwargs)

        data = self.fill_data(data, custom_flow)
        return data

    def get_categories(self):
        """
        Return available top categories for products.
        """
        result = self.get(TOP_CATEGORIES)
        return result

    def descriptor(self, records, custom_flow=None, **kwargs):
        data = self.construct_data(records=records, custom_flow=custom_flow, **kwargs)
        return self.post("descriptor", data=data)

    def search(self, records, filter=None, k=5, fields_to_return=[_ID], custom_flow=None):
        """
        Detects Objects and Tags and find for the largest object most visually similar items in your collection.
        :param records: array with one record (dictionary) with '_url' or "_base64' data
        :param k: how many similar items to return
        :param fields_to_return: fields to return in every record
        :param filter: how to filter picked items (mongodb syntax)
        :return:
        """
        data = self.construct_data(
            records=records, filter=filter, k=k, fields_to_return=fields_to_return, custom_flow=custom_flow
        )
        return self.post(self.PREDICT_ENDPOINT, data=data)

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
