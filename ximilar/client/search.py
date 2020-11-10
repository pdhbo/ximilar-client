from ximilar.client import RestClient
from ximilar.client.constants import (
    RECORDS,
    ENDPOINT,
    FIELDS_TO_RETURN,
    _ID,
    FILTER,
    COUNT,
    K_COUNT,
    QUERY_RECORD,
    COLLECTION,
    COLLECTION_ID,
    PHOTO_SIMILARITY,
    PRODUCT_SIMILARITY,
    FASHION_SIMILARITY,
)

SIMILARITY_PHOTOS = "similarity/photos/v2/"
SIMILARITY_PRODUCTS = "similarity/products/v2/"
SIMILARITY_FASHION = "similarity/fashion/v2/"
SMART_SEARCH = "smart/v2/product/"

SEARCH_OBJ_ENDPOINT = "search_by_object"
SEARCH = "search"
DETECT = "detect"
INSERT = "insert"
DELETE = "delete"
GET = "get"
UPDATE = "update"
RANDOM = "random"
KNN_VISUAL = "visualKNN"
PING = "ping"
RANK_RECORDS = "visualRankRecords"


class SimilarityPhotosClient(RestClient):
    def __init__(
        self, token, collection_id=None, endpoint=ENDPOINT + SIMILARITY_PHOTOS, resource_name=PHOTO_SIMILARITY
    ):
        super(SimilarityPhotosClient, self).__init__(
            token=token, endpoint=endpoint, max_image_size=512, resource_name=resource_name
        )
        self.headers[COLLECTION_ID] = collection_id
        self.PREDICT_ENDPOINT = KNN_VISUAL

    def construct_data(self, query_record=None, filter=None, k=5, fields_to_return=[_ID]):
        if query_record is None:
            raise Exception("Please specify record when using search method.")

        data = {
            QUERY_RECORD: self.preprocess_records([query_record])[0],
            K_COUNT: k,
            FIELDS_TO_RETURN: fields_to_return,
        }
        if filter:
            data[FILTER] = filter
        return data

    def allRecords(self, size=1000, page=1, fields_to_return=[_ID]):
        if size > 0:
            result = self.post("allRecords?size=%s&page=%s" % (size, page), data={FIELDS_TO_RETURN: fields_to_return})
        else:
            result = self.post("allRecords", data={FIELDS_TO_RETURN: fields_to_return})
        return result

    def get_all_ids(self):
        """
        Returns an array with records with "_id" fields.
        :return: {"answer_records": [an array with records with "_id" fields], "answer_count": "# of records"}
        """
        return self.allRecords(size=0, fields_to_return=[_ID])

    def search(self, query_record, filter=None, k=5, fields_to_return=[_ID]):
        """
        Calls visual knn
        :param query_record: dictionary with field '_id' (from your collection) or '_url' or "_base64' data
        :param k: how many similar items to return
        :param fields_to_return: fields to return in every record
        :param filter: how to filter picked items (mongodb syntax)
        :return: json response
        """
        data = self.construct_data(query_record, filter=filter, k=k, fields_to_return=fields_to_return)
        return self.post(self.PREDICT_ENDPOINT, data=data)

    def search_and_rank(self, query_record, records, fields_to_return=[_ID]):
        """
        Ranks the records agains query
        :param query_record: dictionary with field '_id' (from your collection) or '_url' or "_base64' data
        :param k: how many similar items to return
        :param fields_to_return: fields to return in every record
        :param filter: how to filter picked items (mongodb syntax)
        :return: json response
        """
        data = self.construct_data(query_record, fields_to_return=fields_to_return)
        data[RECORDS] = self.preprocess_records(records)
        del data[K_COUNT]
        return self.post(RANK_RECORDS, data=data)

    def random(self, filter=None, count=10, fields_to_return=[_ID]):
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

    def remove(self, records):
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
        records = self.preprocess_records(records)
        data = {RECORDS: records}
        return self.post(INSERT, data=data)

    def get_records(self, records, fields_to_return=[_ID]):
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
    def __init__(
        self, token, collection_id=None, endpoint=ENDPOINT + SIMILARITY_PRODUCTS, resource_name=PRODUCT_SIMILARITY
    ):
        super(SimilarityProductsClient, self).__init__(
            token=token, collection_id=collection_id, endpoint=endpoint, resource_name=resource_name
        )


class SimilarityFashionClient(SimilarityPhotosClient):
    def __init__(
        self, token, collection_id=None, endpoint=ENDPOINT + SIMILARITY_FASHION, resource_name=FASHION_SIMILARITY,
    ):
        super(SimilarityFashionClient, self).__init__(
            token=token, collection_id=collection_id, endpoint=endpoint, resource_name=resource_name
        )

    def insert(self, records, custom_flow=None):
        """
        Insert records into collection with all meta information.
        :param custom_flow: string ID of the flow that should be called during the insert (in extractor)
        :param records: dictionary with your "_id" and with one of "_url", "_file" or "_base64" to extract descriptor.
        :return: json response
        """
        records = self.preprocess_records(records)
        data = {RECORDS: self.fill_data(records, custom_flow)}
        return self.post(INSERT, data=data)

    def fill_data(self, records, custom_flow):
        if custom_flow is not None:
            for r in records:
                r["custom_flow"] = custom_flow
        return records
