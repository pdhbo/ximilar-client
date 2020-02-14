from ximilar.client import RestClient
from ximilar.client.constants import *


class FlowsClient(RestClient):
    def __init__(self, token, endpoint=ENDPOINT, resource_name="flows", max_image_size=512):
        super(FlowsClient, self).__init__(
            token=token, endpoint=endpoint, max_image_size=max_image_size, resource_name=resource_name
        )

        self.PREDICT_ENDPOINT = "/flows/v2/process"

    def construct_data(self, flow=None, records=None):
        if flow is None or records is None or len(records) == 0:
            raise Exception("Please specify flow and records!")

        return {"flow": flow, RECORDS: self.preprocess_records(records)}

    def get_flow(self, flow_id):
        flow_json = self.get("/flows/v2/flow/" + flow_id)
        if DETAIL in flow_json:
            return None, RESULT_ERROR
        return Flow(self.token, self.endpoint, flow_json, max_image_size=self.max_image_size), RESULT_OK

    def process_flow(self, flow, records):
        data = self.construct_data(flow=flow, records=records)
        return self.post(self.PREDICT_ENDPOINT, data=data)

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
        self.valid = flow_json[VALID]
        self.image_size = 512

    def to_json(self):
        """
        Returns flow in json format.
        """
        return self.get("/flows/v2/flow/" + str(self.id) + "/json")

    def process(self, records):
        """
        Call processing of the flow.
        """
        return self.process_flow(self.id, records)
