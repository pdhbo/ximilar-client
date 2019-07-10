import os
import sys
import json
from argparse import ArgumentParser

from ximilar.client import RecognitionClient, DetectionClient
from ximilar.client.constants import FILE, DEFAULT_WORKSPACE, NORESIZE, OBJECTS
from ximilar.client.recognition import Image


if __name__ == "__main__":
    parser = ArgumentParser(description="Save all images from a workspace and their metadata to json")
    parser.add_argument("--folder", default="folder to images and annotations")
    parser.add_argument("--api_prefix", type=str, help="API prefix", default="https://api.ximilar.com/")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--workspace_id", help="ID of workspace to upload the images into", default=DEFAULT_WORKSPACE)
    args = parser.parse_args()

    client_r = RecognitionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)
    client_d = DetectionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)

    rec_json, det_json, img_json, obj_json = [], [], [], []

    # create store directories
    os.makedirs(args.folder, exist_ok=True)
    os.makedirs(args.folder + "/image/", exist_ok=True)

    # get recognition entities
    tasks, status = client_r.get_all_tasks()
    labels, status = client_r.get_all_labels()

    for task in tasks:
        rec_json.append(task.to_json())

    for label in labels:
        rec_json.append(label.to_json())

    with open(args.folder + "/recognition.json", "w") as outfile:
        json.dump(rec_json, outfile, indent=2)

    # get detection entities
    tasks, status = client_d.get_all_tasks()
    labels, status = client_d.get_all_labels()

    for task in tasks:
        det_json.append(task.to_json())

    for label in labels:
        det_json.append(label.to_json())

    with open(args.folder + "/detection.json", "w") as outfile:
        json.dump(det_json, outfile, indent=2)

    # save images with bounding boxes/objects
    images, next_page, status = client_r.get_training_images()
    while images:
        image: Image
        for image in images:
            print("saving image: " + str(image.id))
            image.download(destination=args.folder + "/image/")
            tmp_json = image.to_json()
            objects, status = client_d.get_objects_of_image(image.id)
            tmp_json[OBJECTS] = [object1.to_json() for object1 in objects]
            img_json.append(tmp_json)

        if not next_page:
            break

        images, next_page, status = client_r.get_training_images(next_page)

    with open(args.folder + "/images.json", "w") as outfile:
        json.dump(img_json, outfile, indent=2)
