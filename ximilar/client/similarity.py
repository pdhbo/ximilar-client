from ximilar.client.constants import *
from ximilar.client import RestClient
from ximilar.client.recognition import Image, RecognitionClient

TYPE_ENDPOINT = "similarity/training/v2/type/"
TASK_ENDPOINT = "similarity/training/v2/task/"
GROUP_ENDPOINT = "similarity/training/v2/group/"
DESCRIPTOR_ENDPOINT = "similarity/training/v2/descriptor"


class CustomSimilarityClient(RecognitionClient):
    """
    Ximilar API Client for Custom Similarity.
    """

    def __init__(self, token, endpoint=ENDPOINT, workspace=DEFAULT_WORKSPACE, resource_name=CUSTOM_SIMILARITY):
        super(CustomSimilarityClient, self).__init__(
            token=token, endpoint=endpoint, workspace=workspace, max_image_size=512, resource_name=resource_name
        )
        self.PREDICT_ENDPOINT = DESCRIPTOR_ENDPOINT

    def create_group(self, name, description, sim_type):
        data = {NAME: name, DESCRIPTION: description, "type": sim_type}
        group_json = self.post(GROUP_ENDPOINT, data=data)
        if ID not in group_json:
            return None, {STATUS: "unexpected error"}
        return SimilarityGroup(self.token, self.endpoint, self.workspace, group_json), RESULT_OK

    def create_task(self, name, description=""):
        data = {NAME: name, DESCRIPTION: description}
        task_json = self.post(TASK_ENDPOINT, data=data)
        if ID not in task_json:
            return None, {STATUS: "unexpected error"}
        return SimilarityTask(self.token, self.endpoint, self.workspace, task_json), RESULT_OK

    def create_type(self, name, description=""):
        data = {NAME: name, DESCRIPTION: description}
        type_json = self.post(TYPE_ENDPOINT, data=data)
        if ID not in type_json:
            return None, {STATUS: "unexpected error"}
        return SimilarityType(self.token, self.endpoint, self.workspace, type_json), RESULT_OK

    def get_task(self, task_id):
        task_json = self.get(TASK_ENDPOINT + task_id)
        if ID not in task_json:
            return None, {STATUS: "SimilarityTask with this id not found!"}
        return SimilarityTask(self.token, self.endpoint, self.workspace, task_json), RESULT_OK

    def get_type(self, type_id):
        type_json = self.get(TYPE_ENDPOINT + type_id)
        if ID not in type_json:
            return None, {STATUS: "SimilarityType with this id not found!"}
        return SimilarityType(self.token, self.endpoint, self.workspace, type_json), RESULT_OK

    def get_group(self, group_id):
        group_json = self.get(GROUP_ENDPOINT + group_id)
        if ID not in group_json:
            return None, {STATUS: "SimilarityGroup with this id not found!"}
        return SimilarityGroup(self.token, self.endpoint, self.workspace, group_json), RESULT_OK

    def remove_group(self, group_id):
        return self.delete(GROUP_ENDPOINT + group_id)

    def remove_type(self, type_id):
        return self.delete(TYPE_ENDPOINT + type_id)

    def remove_task(self, task_id):
        return self.delete(TASK_ENDPOINT + task_id)

    def get_all_tasks(self):
        tasks, status = self.get_all_paginated_items(TASK_ENDPOINT)
        if not tasks and status[STATUS] == STATUS_ERROR:
            return None, status
        return [SimilarityTask(self.token, self.endpoint, self.workspace, t_json) for t_json in tasks], RESULT_OK

    def get_all_types(self):
        types, status = self.get_all_paginated_items(TYPE_ENDPOINT)
        if not types and status[STATUS] == STATUS_ERROR:
            return None, status
        return [SimilarityType(self.token, self.endpoint, self.workspace, t_json) for t_json in types], RESULT_OK

    def get_groups_url(self, page_url=None, search=None, test=None):
        url = (
            page_url.replace(self.endpoint, "").replace(self.endpoint.replace("https", "http"), "")
            if page_url
            else GROUP_ENDPOINT + "?page=1"
        )
        if page_url is None:
            url += "&" + search if search is not None else ""
        if test is not None:
            url += f"&test={'True' if test else 'False'}"

        return url

    def get_groups(self, page_url=None, search=None, test=None):
        url = self.get_groups_url(page_url, search, test)

        result = self.get(url)
        return (
            [SimilarityGroup(self.token, self.endpoint, self.workspace, group_json) for group_json in result[RESULTS]],
            result[NEXT],
            {"count": result["count"], STATUS: "ok"},
        )

    def get_all_groups(self, page_url=None, search=None, test=None):
        url = self.get_groups_url(page_url, search, test)

        groups, status = self.get_all_paginated_items(url)
        return (
            [SimilarityGroup(self.token, self.endpoint, self.workspace, group_json) for group_json in groups],
            RESULT_OK,
        )

    def get_all_groups_by_name(self, name, page_url=None, test=None):
        return self.get_all_groups(page_url, "search=" + name, test)

    def get_all_groups_by_type(self, sim_type, page_url=None, test=None):
        return self.get_all_groups(page_url, "type=" + sim_type, test)

    def get_groups_by_type(self, sim_type, page_url=None, test=None):
        return self.get_groups(page_url, "type=" + sim_type, test=test)

    def get_groups_by_type_name(self, type_name, page_url=None, test=None):
        return self.get_groups(page_url, "type__name=" + type_name, test=test)

    def descriptor(self, records, task_id, version=None):
        """
        Takes the images and calls the ximilar client for extracting visual descriptors.
        """
        # version is default set to None, so ximilar will determine which one to take
        data = self.construct_data(records=records, task_id=task_id, version=version)
        result = self.post(self.PREDICT_ENDPOINT, data=data)

        self.check_json_status(result)
        return result


class SimilarityTask(CustomSimilarityClient):
    def __init__(self, token, endpoint, workspace, task_json):
        super(SimilarityTask, self).__init__(token, endpoint=endpoint, workspace=workspace, resource_name=None)

        self.id = task_json["id"]
        self.name = task_json["name"]

    def __str__(self):
        return self.name + ":" + self.id

    def add_type(self, type_id):
        return self.post(TASK_ENDPOINT + self.id + "/add-type/", data={TYPE_ID: type_id})

    def remove_type(self, type_id):
        return self.post(TASK_ENDPOINT + self.id + "/remove-type/", data={TYPE_ID: type_id})

    def train(self):
        pass

    def descriptor(self, json_records):
        return self.descriptor(json_records, self.id)

    def remove(self):
        self.remove_task(self.id)


class SimilarityType(CustomSimilarityClient):
    def __init__(self, token, endpoint, workspace, type_json):
        super(SimilarityType, self).__init__(token, endpoint=endpoint, workspace=workspace, resource_name=None)

        self.id = type_json["id"]
        self.name = type_json["name"]

    def __str__(self):
        return self.name + ":" + self.id

    def remove(self):
        self.remove_type(self.id)


class SimilarityGroup(CustomSimilarityClient):
    def __init__(self, token, endpoint, workspace, group_json):
        super(SimilarityGroup, self).__init__(token, endpoint=endpoint, workspace=workspace, resource_name=None)

        self.id = group_json["id"]
        self.name = group_json["name"] if "name" in group_json else None

        self.groups = None
        if "groups" in group_json:
            self.groups = [SimilarityGroup(token, endpoint, workspace, group) for group in group_json["groups"]]

        self.images = None
        if "images" in group_json:
            self.images = [Image(token, endpoint, image) for image in group_json["images"]]

        self.test_group = group_json["test_group"] if "test_group" in group_json else None
        if isinstance(group_json["type"], str):
            self.type = group_json["type"]
        elif isinstance(group_json["type"], dict):
            self.type = SimilarityType(token, endpoint, workspace, group_json["type"])

        self.type = group_json["type"] if "type" in group_json else None

    def __str__(self):
        return self.name + ":" + self.id

    def refresh(self, force):
        if force or self.images is None or self.groups is None:
            group, _ = self.get_group(self.id)

            self.name = group.name
            self.groups = group.groups
            self.images = group.images
            self.type = group.type
            self.test_group = group.test_group

    def get_images(self):
        self.refresh(False)
        return self.images

    def get_groups(self):
        self.refresh(False)
        return self.groups

    def add_images(self, images, refresh=False):
        result = self.post(GROUP_ENDPOINT + self.id + "/add-images/", data={"images": images})
        self.refresh(refresh)
        return result

    def remove_images(self, images, refresh=False):
        result = self.post(GROUP_ENDPOINT + self.id + "/remove-images/", data={"images": images})
        self.refresh(refresh)
        return result

    def add_groups(self, groups, refresh=False):
        result = self.post(GROUP_ENDPOINT + self.id + "/add-groups/", data={"groups": groups})
        self.refresh(refresh)
        return result

    def remove_groups(self, groups, refresh=False):
        result = self.post(GROUP_ENDPOINT + self.id + "/remove-groups/", data={"groups": groups})
        self.refresh(refresh)
        return result

    def set_test(self, test, refresh=False):
        field = "mark-test" if test else "unmark-test"
        result = self.post(GROUP_ENDPOINT + "update", data={"groups": [self.id], field: True})
        self.refresh(refresh)
        return result

    def remove(self):
        self.remove_group(self.id)


class SimilarityRunLogClient(RestClient):
    BASE_ENDPOINT = "/similarity/v2/run-log/"

    def __init__(self, token, endpoint=ENDPOINT):
        self.workspace = None
        super(SimilarityRunLogClient, self).__init__(token=token, endpoint=endpoint, resource_name=None)

    def create_log(self, collection, data):
        return self.post(self.BASE_ENDPOINT, {"collection": collection, "data": data})

    def get_log(self, log_id):
        return self.get(self.BASE_ENDPOINT + log_id)

    def delete_log(self, log_id):
        return self.delete(self.BASE_ENDPOINT + log_id)

    def update_log(self, log_id, data):
        return self.put(self.BASE_ENDPOINT + log_id, {"data": data})
