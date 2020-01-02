import os
import sys
import json
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
    parser.add_argument("--folder", default="folder to images and annotations")
    parser.add_argument("--api_prefix", type=str, help="API prefix", default="https://api.ximilar.com/")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--workspace_id", help="ID of workspace to upload the images into", default=DEFAULT_WORKSPACE)
    parser.add_argument("--task_id", help="if used, just images from this label are listed", default=None)
    args = parser.parse_args()

    client = RecognitionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)
    client.max_image_size = 0

    tasks = read_json_file_list(os.path.join(args.folder, "task.json"))
    task, _ = client.create_task(tasks[0]["id"], task_type=tasks[0]["type"])
    labels, negative = [], None

    if task.type == "multi_label":
        negative, _ = task.get_negative_label()

    labels_to_create = read_json_file_list(os.path.join(args.folder, "labels.json"))
    for label_create in labels_to_create:
        if label_create["negative"] is not None:
            continue
        else:
            label, _ = client.create_label(label_create["id"], label_type=label_create["type"])
            labels.append(label)
            task.add_label(label.id)

    records = read_json_file_list(os.path.join(args.folder, "images.json"))

    for i in range(len(records)):
        records[i]["labels"] = [get_label_id(labels, rlabel, negative) for rlabel in records[i]["labels"]]

    client.parallel_records_processing(records, client.upload_images, max_workers=5, output=True)