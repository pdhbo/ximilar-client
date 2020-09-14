from ximilar.client import RestClient
from ximilar.client.constants import *
from ximilar.client.recognition import  Image, RecognitionClient

TYPE_ENDPOINT = "similarity/training/v2/type/"
TASK_ENDPOINT = "similarity/training/v2/task/"
GROUP_ENDPOINT = "similarity/training/v2/group/"


class CustomSimilarityClient(RestClient):
    """
    Ximilar API Client for Custom Similarity.
    """
    def __init__(self, token, endpoint=ENDPOINT, resource_name=CUSTOM_SIMILARITY):
        super(CustomSimilarityClient, self).__init__(token=token, endpoint=endpoint, max_image_size=512, resource_name=resource_name)

    def create_group(self, name, description, sim_type):
        data = {NAME: name, DESCRIPTION: description, "type": sim_type}
        group_json = self.post(GROUP_ENDPOINT, data=data)
        if ID not in group_json:
            return None, {STATUS: "unexpected error"}
        return SimilarityGroup(self.token, self.endpoint, group_json), RESULT_OK

    def create_task(self, name, description):
        data = {NAME: name, DESCRIPTION: description}
        task_json = self.post(TASK_ENDPOINT, data=data)
        if ID not in task_json:
            return None, {STATUS: "unexpected error"}
        return SimilarityTask(self.token, self.endpoint, task_json), RESULT_OK

    def create_type(self, name, description):
        data = {NAME: name, DESCRIPTION: description}
        type_json = self.post(TYPE_ENDPOINT, data=data)
        if ID not in type_json:
            return None, {STATUS: "unexpected error"}
        return SimilarityType(self.token, self.endpoint, type_json), RESULT_OK

    def get_task(self, task_id):
        task_json = self.get(TASK_ENDPOINT + task_id)
        if ID not in task_json:
            return None, {STATUS: "SimilarityTask with this id not found!"}
        return SimilarityTask(self.token, self.endpoint, task_json), RESULT_OK

    def get_type(self, type_id):
        type_json = self.get(TYPE_ENDPOINT + type_id)
        if ID not in type_json:
            return None, {STATUS: "SimilarityType with this id not found!"}
        return SimilarityType(self.token, self.endpoint, type_json), RESULT_OK

    def get_group(self, group_id):
        group_json = self.get(GROUP_ENDPOINT + group_id)
        if ID not in group_json:
            return None, {STATUS: "SimilarityGroup with this id not found!"}
        return SimilarityGroup(self.token, self.endpoint, group_json), RESULT_OK

    def remove_group(self, group_id):
        return self.delete(GROUP_ENDPOINT + group_id)

    def remove_type(self, type_id):
        return self.delete(TYPE_ENDPOINT + type_id)

    def remove_task(self, task_id):
        return self.delete(TASK_ENDPOINT + task_id)

    def get_groups_by_name(self, name):
        result = self.get(GROUP_ENDPOINT + "?search=" + name)
        if "results" not in result:
            return result
        return [SimilarityGroup(self.token, self.endpoint, group_json) for group_json in result["results"]], RESULT_OK

    def get_groups_by_type(self, sim_type):
        result = self.get(GROUP_ENDPOINT + "?type=" + sim_type)
        if "results" not in result:
            return result
        return [SimilarityGroup(self.token, self.endpoint, group_json) for group_json in result["results"]], RESULT_OK

    def get_groups_by_type_name(self, type_name):
        result = self.get(GROUP_ENDPOINT + "?type__name=" + type_name)
        if "results" not in result:
            return result
        return [SimilarityGroup(self.token, self.endpoint, group_json) for group_json in result["results"]], RESULT_OK

    def predict(self, json_records, task_id):
        pass


class SimilarityTask(CustomSimilarityClient):
    def __init__(self, token, endpoint, task_json):
        super(SimilarityTask, self).__init__(token, endpoint)

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

    def predict(self, json_records):
        pass

    def remove(self):
        self.remove_task(self.id)


class SimilarityType(CustomSimilarityClient):
    def __init__(self, token, endpoint, type_json):
        super(SimilarityType, self).__init__(token, endpoint)

        self.id = type_json["id"]
        self.name = type_json["name"]

    def __str__(self):
        return self.name + ":" + self.id

    def remove(self):
        self.remove_type(self.id)


class SimilarityGroup(CustomSimilarityClient):
    def __init__(self, token, endpoint, group_json):
        super(SimilarityGroup, self).__init__(token, endpoint)

        self.id = group_json["id"]
        self.name = group_json["name"] if "name" in group_json else None

        if "groups" in group_json:
            self.groups = [SimilarityGroup(token, endpoint, group) for group in group_json["groups"]]
        else:
            self.groups = []

        if "images" in group_json:
            self.images = [Image(token, endpoint, image) for image in group_json["images"]]
        else:
            self.images = []

        if isinstance(group_json["type"], str):
            self.type = group_json["type"]
        elif isinstance(group_json["type"], dict):
            self.type = SimilarityType(token, endpoint, group_json["type"])

        self.type = group_json["type"] if "type" in group_json else None

    def __str__(self):
        return self.name + ":" + self.id

    def refresh(self):
        group, _ = self.get_group(self.id)

        self.name = group.name
        self.groups = group.groups
        self.images = group.images
        self.type = group.type

    def get_images(self, images):
        return self.images

    def get_groups(self, groups):
        return self.groups

    def add_images(self, images):
        result = self.post(GROUP_ENDPOINT + self.id + "/add-images/", data={"images": images})
        self.refresh()
        return result

    def remove_images(self, images):
        result = self.post(GROUP_ENDPOINT + self.id + "/remove-images/", data={"images": images})
        self.refresh()
        return result

    def add_groups(self, groups):
        result = self.post(GROUP_ENDPOINT + self.id + "/add-groups/", data={"groups": groups})
        self.refresh()
        return result

    def remove_groups(self, groups):
        result = self.post(GROUP_ENDPOINT + self.id + "/remove-groups/", data={"groups": groups})
        self.refresh()
        return result

    def remove(self):
        self.remove_group(self.id)


if __name__ == "__main__":
    client = CustomSimilarityClient("")
    t1, status = client.get_groups_by_type_name("TEST MICHAL 2")
    print(t1)