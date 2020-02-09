from ximilar.client import RestClient
from ximilar.client.constants import (
    RECORDS,
    ENDPOINT,
    FIELDS_TO_RETURN,
    _ID,
    FILTER,
    COUNT,
    ID,
    NAME,
    DESCRIPTION,
    WORKSPACE,
    TOP_NODE,
    K_COUNT,
    QUERY_RECORD,
    COLLECTION,
    COLLECTION_ID,
    PHOTO_SIMILARITY,
    PRODUCT_SIMILARITY,
    RESULT_OK
)

SIMILARITY_PHOTOS = "similarity/photos/v2/"
SIMILARITY_PRODUCTS = "similarity/products/v2/"
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


class FlowsClient(RestClient):
    def __init__(
        self,
        token,
        endpoint=ENDPOINT,
        resource_name=PHOTO_SIMILARITY,
        max_image_size=512
    ):
        super(FlowsClient, self).__init__(
            token=token, endpoint=endpoint, max_image_size=max_image_size, resource_name=resource_name
        )

        self.PREDICT_ENDPOINT = "/flows/v2/process"

    def construct_data(self, flow_id=None, records=None):
        if flow_id is None or records is None or len(records) == 0:
            raise Exception("Please specify flow_id and records!")

        return {"flow_id": flow_id, RECORDS: self.preprocess_records(records)}

    def get_flow(self, flow_id):
        flow_json = self.get("/flows/v2/flow/" + flow_id)
        return Flow(self.token, self.endpoint, flow_json, max_image_size=self.max_image_size), RESULT_OK


class Flow(FlowsClient):
    """
    Flow entity from /flows/v2/flow endpoint.
    """
    def __init__(self, token, endpoint, flow_json, max_image_size=512):
        super(Flow, self).__init__(token, endpoint=endpoint, max_image_size=max_image_size, resource_name="")

        self.id = flow_json[ID]
        self.name = flow_json[NAME]
        self.description = flow_json[DESCRIPTION]
        self.workspace = flow_json[WORKSPACE]
        self.top_node = flow_json[TOP_NODE]

    def to_json(self):
        """
        Returns flow in json format.
        """
        return self.get("/flows/v2/flow/" + str(self.id) + "/json")

    def process(self, flow_id, records):
        """
        Call processing of the flow.
        """
        data = self.construct_data(flow_id=flow_id, records=records)
        return self.post("/flows/v2/process", data=data)