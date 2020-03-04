import os
import sys
import json
import uuid
from tqdm import tqdm
from argparse import ArgumentParser
import concurrent.futures

from ximilar.client import RecognitionClient, DetectionClient
from ximilar.client.constants import FILE, DEFAULT_WORKSPACE, NORESIZE, OBJECTS, MULTI_LABEL, MULTI_CLASS, CATEGORY, TAG
from ximilar.client.recognition import Image, Label
from ximilar.client.utils.json_data import read_json_file_list, JSONWriter


def get_label_id(labels, id, negative):
    for label in labels:
        if id == label.name:
            return label.id
    return negative.id


if __name__ == "__main__":
    parser = ArgumentParser(description="Save all images from a workspace and their metadata to json")
    parser.add_argument("--folder", default="folder to categories and folders")
    parser.add_argument("--api_prefix", type=str, help="API prefix", default="https://api.ximilar.com/")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--workspace_id", help="ID of workspace to upload the images into", default=DEFAULT_WORKSPACE)
    args = parser.parse_args()

    client = RecognitionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)
    client.max_image_size = 0

    add_label, _ = client.create_label("Uploaded_LABEL_"+str(uuid.uuid4()), label_type="category")
    task, _ = client.create_task("Uploaded", task_type="multi_class")

    for label_create in os.listdir(args.folder):
        label, _ = client.create_label(label_create, label_type="category")
        task.add_label(label.id)

        records = []
        for file_path in os.listdir(os.path.join(args.folder, label_create)):
            records.append({"_file": os.path.join(args.folder, label_create, file_path), "labels":[label.id, add_label.id]})

        client.parallel_records_processing(records, client.upload_images, max_workers=5, output=True)
        print("uploaded", label_create)
