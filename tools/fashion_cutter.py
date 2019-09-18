import sys

import cv2
import os
from argparse import ArgumentParser

from ximilar.client import DetectionClient, RecognitionClient
from ximilar.client.constants import DEFAULT_WORKSPACE, IMG_DATA, LABELS, META_DATA, NORESIZE
from ximilar.client.detection import DetectionObject
from ximilar.client.recognition import Image


# python ~/ximilar-recognition/ximilar-client/tools/fashion_cutter.py --auth_token <token> --workspace_id 041049f9-f564-456b-8c73-dbb77181d700 --output_dir . --resize 512 --object_resize 448 --min_size 256 --print_details --out_workspace d64fd027-b76c-4cbe-b292-c0f7a47781c9 --max_per_label 1000 --label_to_add 251748fe-e772-46ef-bf21-a0e65fcbe6cc


def resize(image_data, rect_size, object_resize):
    (origH, origW) = image_data.shape[:2]

    # set the new width and height and then determine the ratio in change for both the width and height
    WHITE = [255, 255, 255]
    if not object_resize:
        object_resize = rect_size
    if origW >= origH:
        rW = rH = origW / float(object_resize)
    else:
        rW = rH = origH / float(object_resize)

    # print(f"origH {origH}, origW {origW}, rW{rW}, rect_size {rect_size}")
    # resize the image
    resized_image = cv2.resize(image_data, (int(origW / rW), int(origH / rH))) if rW >= 1.0 else image_data

    # add white pixels to achieve the required size
    white_top = int((rect_size - resized_image.shape[:2][0]) / 2)
    white_left = int((rect_size - resized_image.shape[:2][1]) / 2)
    resized_image = cv2.copyMakeBorder(
        resized_image,
        white_top,
        rect_size - resized_image.shape[:2][0] - white_top,
        white_left,
        rect_size - resized_image.shape[:2][1] - white_left,
        cv2.BORDER_CONSTANT,
        value=WHITE,
    )
    return resized_image


def get_file_name(output_dir, obj, image):
    output_dir = os.path.join(output_dir, obj.detection_label["name"])
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return os.path.join(output_dir, str(image.id) + "_" + obj.id + ".jpg")


rec_labels_to_skip = [
    "509d0922-f323-4ab1-a435-9df13f4ba8b1",
    "1f6d7c6d-14a9-4514-ad1c-3488d855e4f4",
    "7f792acb-877f-4c86-a62c-c9604eee045e",
]

if __name__ == "__main__":
    parser = ArgumentParser(description="Get all images from a workspace and cut all their objects and create files")
    parser.add_argument("--api_prefix", type=str, help="API prefix", default="https://api.ximilar.com/")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--workspace_id", help="ID of workspace to upload the images into", default=DEFAULT_WORKSPACE)
    parser.add_argument("--label_id", help="id of detection label to be considered (None = all labels)")
    parser.add_argument("--output_dir", help="directory to print the images to", required=True)
    parser.add_argument("--resize", help="if positive, the image is resized and filled with white", type=int, default=0)
    parser.add_argument(
        "--object_resize", help="if positive, the object is resized before filling with white", type=int, default=0
    )
    parser.add_argument("--min_size", help="if positive, min object width AND height is checked", type=int, default=0)
    parser.add_argument("--print_details", help="if used, info about each image is printed out", action="store_true")
    parser.add_argument("--out_workspace", help="if used then output is uploaded to this WS")
    parser.add_argument("--max_per_label", help="max objects in each cat. to upload", default=sys.maxsize, type=int)
    parser.add_argument("--label_to_add", help="label to be added to all uploaded images")

    args = parser.parse_args()

    # client = RecognitionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)
    detection_client = DetectionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)

    output_client = None
    output_ws_labels = {}
    if args.out_workspace:
        output_client = RecognitionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.out_workspace)
        # map (cache) of labels to be added to images in the output workspace

    counts_per_label = {}

    image_dir = os.path.join(args.output_dir, "images_tmp")
    os.makedirs(image_dir, exist_ok=True)

    # getting all images of label (paginated result)
    images, next_page, status = detection_client.get_training_images()
    while images:
        image: Image
        for image in images:
            if args.print_details:
                print(f"processing image {image.id}: {str(image.get_meta_data())}")
            if ("is_product" in image.get_meta_data() and image.get_meta_data()["is_product"] == 1) or (
                "verified" in image.get_meta_data() and image.get_meta_data()["verified"] == 0
            ):
                if args.print_details:
                    print("\t... skipping due to metadata")
                continue
            objects, status = detection_client.get_objects_of_image(image.id)
            obj: DetectionObject
            i = 1
            for obj in objects:
                if args.label_id and obj.detection_label["id"] != args.label_id:
                    if args.print_details:
                        print("\t... skipping object due to different label ID: " + str(obj.detection_label))
                    continue

                if any([label_id in obj.recognition_labels for label_id in rec_labels_to_skip]):
                    if args.print_details:
                        print("\t... skipping object due to recognition_label: " + str(obj.recognition_labels))
                    continue

                bbox = obj.get_bbox()
                if args.min_size > 0 and (bbox[2] - bbox[0] < args.min_size or bbox[3] - bbox[1] < args.min_size):
                    if args.print_details:
                        print("\t... skipping object due to size: " + str(bbox))
                    continue

                # check the number of images of this type that were already uploaded
                if obj.detection_label["id"] not in counts_per_label:
                    counts_per_label[obj.detection_label["id"]] = 0
                if counts_per_label[obj.detection_label["id"]] >= args.max_per_label:
                    if args.print_details:
                        print("\t... skipping: max number already uploaded for: " + str(obj.detection_label["name"]))
                    continue
                counts_per_label[obj.detection_label["id"]] += 1

                image_record = image.extract_object_data(obj.get_bbox(), image_dir)
                if args.resize > 0:
                    image_record[IMG_DATA] = resize(image_record[IMG_DATA], args.resize, args.object_resize)

                object_file = get_file_name(args.output_dir, obj, image)
                detection_client.cv2_imwrite(image_record, object_file)
                if args.print_details:
                    print("creating file " + str(object_file))

                if output_client:
                    image_record[NORESIZE] = True
                    # check if there is info about "product_id" in the object
                    image_record[META_DATA] = {
                        "from_detection": 1,
                        "is_product": 0,
                        "source_workspace": args.workspace_id,
                        "source_image": image.id,
                        "sqlite_id": image.get_meta_data()["id"],
                    }
                    if "id_product" in obj.get_meta_data() and obj.get_meta_data()["id_product"]:
                        image_record[META_DATA]["id_product"] = obj.get_meta_data()["id_product"]
                    # find label in the target output workspace
                    if obj.detection_label["name"] not in output_ws_labels:
                        output_labels, status = output_client.get_labels_by_substring(obj.detection_label["name"])
                        if not output_labels:
                            print(f"ERROR finding label '{obj.detection_label['name']}' in target WS: {str(status)}")
                            continue
                        output_ws_labels[obj.detection_label["name"]] = output_labels[0].id
                    image_record[LABELS] = [output_ws_labels[obj.detection_label["name"]]]
                    if args.label_to_add:
                        image_record[LABELS].append(args.label_to_add)

                    results = output_client.upload_images([image_record])
                    # results = output_client.parallel_records_processing(records, client.upload_images, output=True)

                i += 1

        if not next_page:
            break
        print(f"loading next page")
        images, next_page, status = detection_client.get_training_images(next_page)
        # images = None
