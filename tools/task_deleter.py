import os
import sys
import json
from tqdm import tqdm
from argparse import ArgumentParser
import concurrent.futures

from ximilar.client import RecognitionClient, DetectionClient
from ximilar.client.constants import FILE, DEFAULT_WORKSPACE, NORESIZE, OBJECTS
from ximilar.client.recognition import Image, Label

if __name__ == "__main__":
    parser = ArgumentParser(description="Save all images from a workspace and their metadata to json")
    parser.add_argument("--folder", default="folder to images and annotations")
    parser.add_argument("--api_prefix", type=str, help="API prefix", default="https://api.ximilar.com/")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--workspace_id", help="ID of workspace to upload the images into", default=DEFAULT_WORKSPACE)
    parser.add_argument("--task_id", help="if used, just images from this label are listed", default=None)
    args = parser.parse_args()

    client = RecognitionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)

    # get recognition entities
    task, status = client.get_task(args.task_id)
    labels, status = task.get_labels()

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    # iterate through the labels
    futures = []
    for label in labels:
        image_iter = label.training_images_iter()

        # save images with bounding boxes/objects
        image: Image
        for image in image_iter:
            futures.append(executor.submit(image.remove))
        label.remove()

    # remove
    with tqdm(total=len(futures)) as pbar:
        for future in futures:
            try:
                result = future.result(timeout=5)
            except Exception as e:
                print(str(e))
            pbar.update(1)

    task.remove()
