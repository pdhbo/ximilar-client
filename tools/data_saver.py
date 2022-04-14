import os
import sys
import json
from argparse import ArgumentParser
from tqdm import tqdm

from ximilar.client import RecognitionClient, DetectionClient
from ximilar.client.constants import FILE, DEFAULT_WORKSPACE, NORESIZE, OBJECTS
from ximilar.client.recognition import Image, Label

if __name__ == "__main__":
    parser = ArgumentParser(description="Save all images from a workspace, label and their metadata to json")
    parser.add_argument("--folder", default="folder", help="default folder")
    parser.add_argument("--api_prefix", type=str, help="API prefix", default="https://api.ximilar.com/")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--workspace_id", help="ID of workspace to upload the images into", default=DEFAULT_WORKSPACE)
    parser.add_argument("--label_id", help="if used, just images from this label are listed", default=None)
    parser.add_argument("--download_images", help="if false, just the JSON is created", action="store_true")
    args = parser.parse_args()

    client_r = RecognitionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)
    client_d = DetectionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)

    rec_json, det_json, img_json = [], [], []

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

    print("Created recognition.json")

    # get detection entities
    det_tasks, status = client_d.get_all_tasks()
    det_labels, status = client_d.get_all_labels()

    if det_tasks is not None:
        for task in det_tasks:
            det_json.append(task.to_json())

        for label in det_labels:
            det_json.append(label.to_json())

        with open(args.folder + "/detection.json", "w") as outfile:
            json.dump(det_json, outfile, indent=2)

    print("Created detection.json")

    # if we should take just one label
    if args.label_id:
        label, _ = client_r.get_label(args.label_id)
        image_iter = label.training_images_iter()
    else:
        image_iter = client_r.training_images_iter()

    # save images with bounding boxes/objects
    image: Image

    data = {}
    if os.path.exists(args.folder + "/images.json"):
        with open(args.folder + "/images.json") as outfile:
            data = json.load(outfile)
            data = {item["image"]: item for item in data}

    print("Creating images.json ...")
    k = 0
    with tqdm(total=0) as pbar:
        for image in image_iter:
            # print("Processing image: " + str(image.id))

            if args.download_images:
                image.download(destination=args.folder + "/image/")

            if image.id in data:
                img_json.append(data[image.id])
                pbar.update(1)
                continue

            tmp_json = image.to_json()
            objects, status = client_d.get_objects_of_image(image.id)
            if objects is not None and len(objects):
                tmp_json[OBJECTS] = [object1.to_json() for object1 in objects]
            img_json.append(tmp_json)

            k += 1
            if k == 1000:
                with open(args.folder + "/images.json", "w") as outfile:
                    json.dump(img_json, outfile, indent=2)
                k = 0
            pbar.update(1)

    with open(args.folder + "/images.json", "w") as outfile:
        json.dump(img_json, outfile, indent=2)
