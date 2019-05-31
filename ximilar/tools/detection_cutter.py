import cv2
import os
from argparse import ArgumentParser

from ximilar.client import DetectionClient
from ximilar.client.constants import DEFAULT_WORKSPACE, IMG_DATA
from ximilar.client.detection import DetectionObject
from ximilar.client.recognition import Image


def resize(image_data, rect_size):
    (origH, origW) = image_data.shape[:2]

    # set the new width and height and then determine the ratio in change for both the width and height
    WHITE = [255, 255, 255]
    if origW >= origH:
        rW = rH = origW / float(rect_size)
    else:
        rW = rH = origH / float(rect_size)

    print(f"origH {origH}, origW {origW}, rW{rW}, rect_size {rect_size}")
    # resize the image
    resized_image = cv2.resize(image_data, (int(origW / rW), int(origH / rH))) if rW >= 1.0 else image_data

    # add white pixels to achieve 320 x 320
    resized_image = cv2.copyMakeBorder(
        resized_image,
        0,
        rect_size - resized_image.shape[:2][0],
        0,
        rect_size - resized_image.shape[:2][1],
        cv2.BORDER_CONSTANT,
        value=WHITE,
    )
    return resized_image


if __name__ == "__main__":
    parser = ArgumentParser(description="Get all images from a workspace and cut all their objects and create files")
    parser.add_argument("--api_prefix", type=str, help="API prefix", default="https://api.ximilar.com/")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--workspace_id", help="ID of workspace to upload the images into", default=DEFAULT_WORKSPACE)
    parser.add_argument("--label_id", help="directory to print the images to")
    parser.add_argument("--output_dir", help="directory to print the images to")
    parser.add_argument("--resize", help="if not 0 or negative, the image is resized and filled with white", type=int)
    parser.add_argument("--print_details", help="if true, info about each image is printed out", action="store_true")

    args = parser.parse_args()

    # client = RecognitionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)
    detection_client = DetectionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)

    image_dir = os.path.join(args.output_dir, "images")
    os.makedirs(image_dir, exist_ok=True)

    # getting all images of label (paginated result)
    images, next_page, status = detection_client.get_training_images()
    while images:
        image: Image
        for image in images:
            objects, status = detection_client.get_objects_of_image(image.id)
            obj: DetectionObject
            i = 1
            for obj in objects:
                image_record = image.extract_object_data(obj.get_bbox(), image_dir)
                object_file = os.path.join(
                    args.output_dir, str(image.id) + "_" + obj.detection_label["name"] + "_" + str(i) + ".jpg"
                )
                if args.resize > 0:
                    image_record[IMG_DATA] = resize(image_record[IMG_DATA], args.resize)
                detection_client.cv2_imwrite(image_record, object_file)
                if args.print_details:
                    print("creating file " + str(object_file))
                i += 1

        if not next_page:
            break
        images, next_page, status = detection_client.get_training_images(next_page)
