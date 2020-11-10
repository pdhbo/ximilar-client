from ximilar.client import RestClient
from ximilar.client.constants import *

FLOW_ENDPOINT = "/flows/v2/flow/"


class FlowsClient(RestClient):
    def __init__(self, token, endpoint=ENDPOINT, resource_name="flows", max_image_size=512):
        super(FlowsClient, self).__init__(
            token=token, endpoint=endpoint, max_image_size=max_image_size, resource_name=resource_name
        )

        self.PREDICT_ENDPOINT = "/flows/v2/process"

    def construct_data(self, flow=None, records=None, store_images=None):
        if flow is None or records is None or len(records) == 0:
            raise Exception("Please specify flow and records!")

        data = {"flow": flow, RECORDS: self.preprocess_records(records)}
        if store_images is not None:
            data[STORE_IMAGES] = store_images

        return data

    def get_all_flows(self):
        flows, status = self.get_all_paginated_items(FLOW_ENDPOINT)

        if not flows and status[STATUS] == STATUS_ERROR:
            return None, status

        return [Flow(self.token, self.endpoint, flow_json) for flow_json in flows], RESULT_OK

    def get_flow(self, flow_id):
        flow_json = self.get(FLOW_ENDPOINT + flow_id)

        if DETAIL in flow_json:
            return None, RESULT_ERROR

        return Flow(self.token, self.endpoint, flow_json, max_image_size=self.max_image_size), RESULT_OK

    def process_flow(self, flow, records, store_images=None):
        data = self.construct_data(flow=flow, records=records, store_images=store_images)
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

    def process(self, records, store_images=None):
        """
        Call processing of the flow.
        """
        return self.process_flow(self.id, records, store_images=store_images)
