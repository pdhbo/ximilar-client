import concurrent.futures
import os
import sys
from argparse import ArgumentParser
from enum import Enum

from tqdm import tqdm

from ximilar.client import RecognitionClient, DetectionClient
from ximilar.client.constants import (
    DETECTION,
    LABELS,
    ID,
    TASK_TYPE,
    LABEL_TYPE,
    DESCRIPTION,
    DEFAULT_WORKSPACE,
    COLOR,
    TASK_NAME,
    NAME,
    OUTPUT_NAME,
    OBJECTS,
    FILE,
    IMAGE,
    DETECTION_LABEL,
)
from ximilar.client.recognition import Image
from ximilar.client.utils.json_data import JSONWriter


class TaskType(Enum):
    RECOGNITION = 0
    DETECTION = 1


def save(task, task_type, args):
    # create store directories
    os.makedirs(os.path.join(args.folder, args.task_id), exist_ok=True)
    os.makedirs(os.path.join(args.folder, args.task_id, "images"), exist_ok=True)

    # write task info
    with JSONWriter(os.path.join(args.folder, args.task_id, "task.json")) as writer:
        writer.write(
            {
                ID: task.id,
                TASK_NAME: task.name,
                TASK_TYPE: task.type if task_type == TaskType.RECOGNITION else DETECTION,
                DESCRIPTION: task.description,
            }
        )

    # get recognition entities
    labels, status = task.get_labels() if task_type == TaskType.RECOGNITION else task.get_all_labels()
    labels_ids = [str(label.id) for label in labels]
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    futures = {}
    print("Loading all data of task and saving images...")
    with JSONWriter(os.path.join(args.folder, args.task_id, "labels.json")) as writer:
        for label in labels:
            image_iter = label.training_images_iter()

            base = {ID: label.id, NAME: label.name, OUTPUT_NAME: label.output_name}
            if task_type == TaskType.RECOGNITION:
                writer.write(
                    {
                        **base,
                        DESCRIPTION: label.description,
                        LABEL_TYPE: label.type,
                        "negative": label.negative_for_task,
                    }
                )
            else:
                writer.write({**base, DESCRIPTION: label.description, COLOR: label.color})

            # save images
            with tqdm(total=len([i for i in label.training_images_iter()])) as pbar:
                for image in image_iter:
                    image: Image
                    if image.id not in futures:
                        future = executor.submit(image.download, os.path.join(args.folder, args.task_id, "images"))

                        if task_type == TaskType.RECOGNITION:
                            img_labels, _ = image.get_labels()
                            futures[image.id] = {"future": future, LABELS: img_labels}
                        else:
                            objects, _ = task.get_objects_of_image(image.id)
                            futures[image.id] = {"future": future, OBJECTS: objects}

                    pbar.update(1)

    print("Saving image details ....")
    with JSONWriter(os.path.join(args.folder, args.task_id, "images.json")) as writer:
        with tqdm(total=len(futures)) as pbar:
            for image_id, future in futures.items():
                result = future["future"].result()

                if task_type == TaskType.RECOGNITION:
                    img_labels = future[LABELS]
                    img_labels = [img_label.id for img_label in img_labels if img_label.id in labels_ids]
                    writer.write({FILE: result, LABELS: img_labels})
                else:
                    objects = list(map(lambda o: o.to_json(), future[OBJECTS]))
                    for obj in objects:
                        obj[DETECTION_LABEL] = obj[DETECTION_LABEL][ID]
                        del obj[IMAGE]
                        del obj[LABELS]  # TODO not used yet
                    writer.write({FILE: result, OBJECTS: objects})

                pbar.update(1)

    print("Finished!")


if __name__ == "__main__":
    parser = ArgumentParser(description="Save all images from a workspace and their metadata to json")
    parser.add_argument("--folder", default="folder to images and annotations")
    parser.add_argument("--api_prefix", type=str, help="API prefix", default="https://api.ximilar.com/")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--workspace_id", help="ID of workspace to download the images from", default=DEFAULT_WORKSPACE)
    parser.add_argument("--task_id", help="only images from this task are listed", default=None)
    args = parser.parse_args()

    # Try to find the task among recognition tasks and save it if found.
    client = RecognitionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)
    task, _ = client.get_task(args.task_id)
    if task:
        save(task, TaskType.RECOGNITION, args)
        sys.exit()

    # Try to find the task among detection tasks and save it if found.
    client = DetectionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)
    task, _ = client.get_task(args.task_id)
    if task:
        save(task, TaskType.DETECTION, args)
        sys.exit()

    # Id not found.
    print("Task dos not exists.")
