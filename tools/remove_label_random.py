import json
from argparse import ArgumentParser
import random
from ximilar.client import RecognitionClient
from ximilar.client.constants import DEFAULT_WORKSPACE
from ximilar.client.recognition import Image


if __name__ == "__main__":
    parser = ArgumentParser(description="Takes JSON with image metadata and sets labels to images accordingly")
    parser.add_argument("--api_prefix", type=str, help="API prefix", default="https://api.ximilar.com/")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--workspace_id", help="ID of workspace to upload the images into", default=DEFAULT_WORKSPACE)
    parser.add_argument("--label_id", help="if used, just images from this label are listed", default=None)
    parser.add_argument("--remove_probability", help="probability to remove label [0,1]", type=float)
    parser.add_argument("--dryrun", help="the script just writes out what it would do", type=bool, default=False)
    args = parser.parse_args()

    client = RecognitionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)

    label, _ = client.get_label(args.label_id)
    image_iter = label.training_images_iter()

    im_counter = 0
    removed_counter = 0
    image_to_remove = []
    image: Image
    for image in image_iter:
        im_counter += 1
        if random.uniform(0.0, 1.0) < args.remove_probability:
            print("removing label from image: " + str(image.id))
            removed_counter += 1
            image_to_remove.append(image)
        else:
            print("leaving : " + str(image.id))

    if not args.dryrun:
        print("ACTUALLY REMOVING THE LABEL")
        for image in image_to_remove:
            image.detach_label(args.label_id)

    print(f"removed {removed_counter} out of {im_counter}, probability: {float(removed_counter)/float(im_counter)}")
