import os
import sys
import json
from tqdm import tqdm
from argparse import ArgumentParser
import concurrent.futures

from ximilar.client import RecognitionClient, DetectionClient
from ximilar.client.constants import FILE, DEFAULT_WORKSPACE, NORESIZE, OBJECTS
from ximilar.client.recognition import Image, Label
from ximilar.client.utils.json_data import read_json_file_list, JSONWriter

if __name__ == "__main__":
    parser = ArgumentParser(description="Save all images from a workspace and their metadata to json")
    parser.add_argument("--folder", default="folder to images and annotations")
    parser.add_argument("--api_prefix", type=str, help="API prefix", default="https://api.ximilar.com/")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--workspace_id", help="ID of workspace to upload the images into", default=DEFAULT_WORKSPACE)
    parser.add_argument("--task_id", help="if used, just images from this label are listed", default=None)
    args = parser.parse_args()

    client = RecognitionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)

    # create store directories
    os.makedirs(os.path.join(args.folder, args.task_id), exist_ok=True)
    os.makedirs(os.path.join(args.folder, args.task_id, "images"), exist_ok=True)

    # get recognition entities
    task, status = client.get_task(args.task_id)
    labels, status = task.get_labels()
    labels_ids = [str(label.id) for label in labels]

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    # iterate through the labels
    with JSONWriter(os.path.join(args.folder, args.task_id, "task.json")) as writer:
        writer.write({"id": task.id, "name": task.name, "type": task.type, "description": task.description})

    futures = {}
    print("Loading all data of task...")
    with JSONWriter(os.path.join(args.folder, args.task_id, "labels.json")) as writer:
        for label in labels:
            image_iter = label.training_images_iter()
            writer.write({"id": label.id, "name": label.name, "type": label.type, "negative": label.negative_for_task})

            # save images
            with tqdm(total=len([i for i in label.training_images_iter()])) as pbar:
                for image in image_iter:
                    image: Image
                    if image.id not in futures:
                        img_labels, _ = image.get_labels()
                        futures[image.id] = {
                            "future": executor.submit(
                                image.download, os.path.join(args.folder, args.task_id, "images")
                            ),
                            "labels": img_labels,
                        }
                    pbar.update(1)

    print("Downloading ....")
    with JSONWriter(os.path.join(args.folder, args.task_id, "images.json")) as writer:
        with tqdm(total=len(futures)) as pbar:
            for image_id, future in futures.items():
                result = future["future"].result()

                img_labels = future["labels"]
                img_labels = [img_label.id for img_label in img_labels if img_label.id in labels_ids]

                writer.write({"_file": result, "labels": img_labels})
                pbar.update(1)
    print("Finished!")
