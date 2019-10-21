from argparse import ArgumentParser

from ximilar.client import DetectionClient
from ximilar.client.constants import DEFAULT_WORKSPACE
from ximilar.client.detection import DetectionObject, DetectionTask
from ximilar.client.recognition import Image

det_label_map = {
    "57031f04-e6b2-4284-b9c1-4463d8ab5090": "0189a2ee-16b5-4f80-8be8-020707f406c4",  # Twirl2 Kopi
    "f830f47f-148d-42ac-835b-de01aaf1c7c8": "d9b23b56-666d-47b5-9134-2dd4a499b9bd",  # Twirl Bites
    "b62d73e3-31c6-441f-bee5-e2cac52e4c3a": "94812da6-0ec2-4e49-a813-23a08c3bd773",  # Wispa
    "9e21dbeb-ff5c-452e-b6e1-bccf2057a9c9": "6524ce52-c73e-4cdd-a977-0359cfc944ed",  # Wispa Gold
}

negative_label = "5fce6f24-f97d-4f81-ab7a-18df9ad90a31"
det_task_id = "632103ed-15c9-4ee3-b7e2-201ee46bd388"

if __name__ == "__main__":
    parser = ArgumentParser(description="Add tags to images according to their detections.")
    parser.add_argument("--api_prefix", type=str, help="API prefix", default="https://api.ximilar.com/")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--workspace_id", help="ID of workspace to upload the images into", default=DEFAULT_WORKSPACE)
    parser.add_argument("--print_details", help="if used, info about each image is printed out", action="store_true")
    parser.add_argument("--max_number", help="if >0, then only this number of images is processed", default=0, type=int)
    parser.add_argument("--verified", help="use just verified images and store to negative labels", action="store_true")

    args = parser.parse_args()

    detection_client = DetectionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)
    detection_task: DetectionTask = None
    if args.verified:
        detection_task, _ = detection_client.get_task(det_task_id)
    # det_label_object = {det: recognition_client.get_label(label) for det, label in det_label_map.items()}

    # getting all images of label (paginated result)
    i = 0
    for image in detection_client.training_images_iter(verification=1 if args.verified else None):
        if args.print_details:
            print(f"processing image {image.id}")
        image: Image
        objects, _ = detection_client.get_objects_of_image(image.id)
        if args.verified and len(objects) == 0:
            # the image has no object detected
            image.add_label(negative_label)
            detection_task.add_negative_image(image.id)
            if args.print_details:
                print(f"\t... setting NEGATIVE label: {negative_label} and adding to task {det_task_id} as negative")

        obj: DetectionObject
        for obj in objects:
            if obj.detection_label["id"] not in det_label_map:
                print("\t... skipping object which is not in the list: " + obj.detection_label)
                continue
            image.add_label(det_label_map[obj.detection_label["id"]])
            if args.print_details:
                print(f"\t... setting recognition label: {det_label_map[obj.detection_label['id']]}")
            i += 1
        if args.max_number and i >= args.max_number:
            break
