import os
from argparse import ArgumentParser

from ximilar.client import RecognitionClient, DetectionClient
from ximilar.client.constants import (
    DETECTION,
    LABELS,
    ID,
    TASK_TYPE,
    LABEL_TYPE,
    DESCRIPTION,
    DEFAULT_WORKSPACE,
    OBJECTS,
    MULTI_LABEL,
    COLOR,
    DETECTION_LABEL,
    NAME,
    TASK_NAME,
    NORESIZE,
)
from ximilar.client.utils.json_data import read_json_file_list


def upload_recognition(task_json, args):
    client = RecognitionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)
    client.max_image_size = 0

    task, _ = client.create_task(
        f"{task_json[0][TASK_NAME]} ({task_json[0][ID]})",
        task_type=task_json[0][TASK_TYPE],
        description=task_json[0][DESCRIPTION],
    )
    labels, negative = {}, None

    if task.type == MULTI_LABEL:
        negative, _ = task.get_negative_label()

    labels_to_create = read_json_file_list(os.path.join(args.folder, "labels.json"))
    for label_create in labels_to_create:
        if label_create["negative"] is not None:
            continue
        else:
            label, _ = client.create_label(
                f"{label_create[NAME]} ({label_create[ID]})",
                description=label_create[DESCRIPTION],
                label_type=label_create[LABEL_TYPE],
            )
            labels[label_create[ID]] = label
            task.add_label(label.id)

    records = read_json_file_list(os.path.join(args.folder, "images.json"))

    for i in range(len(records)):
        records[i][NORESIZE] = True
        records[i][LABELS] = [(labels[rlabel].id if rlabel in labels else negative.id) for rlabel in records[i][LABELS]]

    client.parallel_records_processing(records, client.upload_images, max_workers=5, output=True)


def upload_detection(task_json, args):
    client = DetectionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)
    client.max_image_size = 0

    task, _ = client.create_task(
        f"{task_json[0][TASK_NAME]} ({task_json[0][ID]})", description=task_json[0][DESCRIPTION]
    )

    labels = {}
    labels_to_create = read_json_file_list(os.path.join(args.folder, "labels.json"))
    for label_create in labels_to_create:
        label, _ = client.create_label(
            f"{label_create[NAME]} ({label_create[ID]})",
            description=label_create[DESCRIPTION],
            color=label_create[COLOR],
        )
        labels[label_create[ID]] = label
        task.add_label(label.id)

    records = read_json_file_list(os.path.join(args.folder, "images.json"))

    for i in range(len(records)):
        records[i][NORESIZE] = True
        for j in range(len(records[i][OBJECTS])):
            old_id = records[i][OBJECTS][j][DETECTION_LABEL]
            records[i][OBJECTS][j][DETECTION_LABEL] = labels[old_id].id

    client.parallel_records_processing(records, client.upload_images, max_workers=5, output=True)


if __name__ == "__main__":
    parser = ArgumentParser(description="Save all images from a workspace and their metadata to json")
    parser.add_argument("--folder", default="folder to images and annotations")
    parser.add_argument("--api_prefix", type=str, help="API prefix", default="https://api.ximilar.com/")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--workspace_id", help="ID of workspace to upload the images into", default=DEFAULT_WORKSPACE)
    parser.add_argument("--task_id", help="if used, just images from this label are listed", default=None)
    args = parser.parse_args()

    task_json = read_json_file_list(os.path.join(args.folder, "task.json"))
    if task_json[0][TASK_TYPE] == DETECTION:
        upload_detection(task_json, args)
    else:
        upload_recognition(task_json, args)
