import os
import sys
import json
from argparse import ArgumentParser
from tqdm import tqdm

from ximilar.client import RecognitionClient, DetectionClient
from ximilar.client.constants import FILE, DEFAULT_WORKSPACE, NORESIZE, OBJECTS
from ximilar.client.recognition import Image, Label

if __name__ == "__main__":
    parser = ArgumentParser(description="Upload all images from a workspace, label and their metadata to json")
    parser.add_argument("--folder", default="folder")
    parser.add_argument("--api_prefix", type=str, help="API prefix", default="https://api.ximilar.com/")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--workspace_id", help="ID of workspace to upload the images into", default=DEFAULT_WORKSPACE)
    parser.add_argument(
        "--old_workspace_id", help="ID of workspace to upload the images into", default=DEFAULT_WORKSPACE
    )
    parser.add_argument("--label_id", help="if used, just images from this label are listed", default=None)
    parser.add_argument("--download_images", help="if false, just the JSON is created", action="store_true")
    args = parser.parse_args()

    client_old = RecognitionClient(
        token=args.auth_token, endpoint=args.api_prefix, workspace=args.old_workspace_id, max_image_size=0
    )

    client_r = RecognitionClient(
        token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id, max_image_size=0
    )
    client_d = DetectionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)

    rec_json, det_json, img_json, obj_json = [], [], [], []  # type: ignore

    # create store directories
    # args.folder
    recognition, detection, images = None, None, None

    with open(os.path.join(args.folder, "recognition.json"), "r") as f:
        recognition = json.load(f)

    with open(os.path.join(args.folder, "detection.json"), "r") as f:
        detection = json.load(f)

    with open(os.path.join(args.folder, "images.json"), "r") as f:
        images = json.load(f)

    # create r labels
    recognition_r = {"LABELS": {}, "TASKS": {}}  # type: ignore
    for entity in recognition:
        if "label_id" in entity and entity["negative_for_task"] is None:
            print("LABEL", entity["name"])
            labels, _ = client_r.get_labels_by_substring(entity["name"])

            label = None
            if labels is not None:
                for label_1 in labels:
                    if label_1.description == entity["label_id"]:
                        label = label_1

            if label is None:
                label, _ = client_r.create_label(
                    entity["name"], entity["label_id"], entity["output_name"], entity["type"]
                )

            recognition_r["LABELS"][entity["label_id"]] = label
        elif "label_id" in entity and entity["negative_for_task"]:
            recognition_r["LABELS"][entity["label_id"]] = False

    # create r tasks
    for entity in recognition:
        if "task_id" in entity:
            print("TASK", entity["name"])
            task = None
            tasks, _ = client_r.get_tasks_by_name(entity["name"])
            if tasks is not None:
                for task_1 in tasks:
                    if task_1.description == entity["task_id"]:
                        task = task_1

            if task is None:
                task, _ = client_r.create_task(entity["name"], entity["task_id"], entity["type"])

            recognition_r["TASKS"][entity["task_id"]] = task

            for elabel in entity["labels"]:
                label = recognition_r["LABELS"][elabel]
                if label != False:
                    task.add_label(label.id)

    # create d labels
    detection_r = {"LABELS": {}, "TASKS": {}}  # type: ignore
    for entity in detection:
        if "label_id" in entity:
            print("LABEL", entity["name"])
            labels, _ = client_d.get_all_labels()

            label = None
            if labels is not None:
                for label_1 in labels:
                    if label_1.description == entity["label_id"]:
                        label = label_1

            if label is None:
                label, _ = client_d.create_label(
                    entity["name"], entity["label_id"]
                )  # , entity["description"]) #, ouput_name=entity["output_name"])
            detection_r["LABELS"][entity["label_id"]] = label

    # create d tasks
    for entity in detection:
        if "task_id" in entity:
            print("TASK", entity["name"])
            task = None
            tasks, _ = client_d.get_tasks_by_name(entity["name"])
            if tasks is not None:
                for task_1 in tasks:
                    if task_1.description == entity["task_id"]:
                        task = task_1

            if task is None:
                task, _ = client_d.create_task(entity["name"], entity["task_id"])

            detection_r["TASKS"][entity["task_id"]] = task

            for elabel in entity["labels"]:
                label = detection_r["LABELS"][elabel]
                task.add_label(label.id)

    with tqdm(total=len(images)) as pbar:
        for image in images:
            # print("IMAGE")
            if image["_file"] is not None:
                image_e, _ = client_r.upload_images([{"_file": image["_file"]}])
                image_e = image_e[0]
            else:
                image_1, _ = client_old.get_image(image["image"])
                if image_1 is None:
                    pbar.update(1)
                    continue
                image_e, status = client_r.upload_images(
                    [{"_url": image_1.img_path, "meta_data": {"id": image["image"]}}]
                )
                image_e = image_e[0]

            if "present" in status["status"]:
                print("SKIP IMAGE...", image_e.id, image["image"])
                pbar.update(1)
                continue

            for label in image["labels"]:
                # print("Adding label", label, recognition_r["LABELS"][label])
                if recognition_r["LABELS"][label]:
                    image_e.add_label(recognition_r["LABELS"][label].id)

            if "objects" in image:
                for object_1 in image["objects"]:
                    object_c, _ = client_d.create_object(
                        detection_r["LABELS"][object_1["detection_label"]["id"]].id, image_e.id, object_1["data"]
                    )

                    for label in object_1["labels"]:
                        object_c.add_recognition_label(recognition_r["LABELS"][label].id)
            pbar.update(1)
