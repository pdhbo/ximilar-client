import os
from argparse import ArgumentParser

from ximilar.client import DetectionClient
from ximilar.client.constants import DEFAULT_WORKSPACE
from ximilar.client.detection import DetectionObject
from ximilar.client.recognition import Image

if __name__ == "__main__":
    parser = ArgumentParser(description="Get all images from a workspace and cut all their objects and create files")
    parser.add_argument("--api_prefix", type=str, help="API prefix", default="https://api.ximilar.com/")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--workspace_id", help="ID of workspace to upload the images into", default=DEFAULT_WORKSPACE)
    parser.add_argument("--label_id", help="directory to print the images to")
    parser.add_argument("--output_dir", help="directory to print the images to")
    parser.add_argument("--print_details", help="if true, info about each image is printed out", action="store_true")
    args = parser.parse_args()

    # client = RecognitionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)
    detection_client = DetectionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)

    image_dir = os.path.join(args.output_dir, "images")
    os.makedirs(image_dir, exist_ok=True)

    # getting all images of label (paginated result)
    images, next_page, status = detection_client.get_training_images()
    while next_page:
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
                detection_client.cv2_imwrite(image_record, object_file)
                if args.print_details:
                    print("creating file " + str(object_file))
                i += 1
