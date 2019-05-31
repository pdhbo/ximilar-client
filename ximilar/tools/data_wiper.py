import os
import sys
from argparse import ArgumentParser

from ximilar.client import RecognitionClient
from ximilar.client.constants import FILE, DEFAULT_WORKSPACE, NORESIZE
from ximilar.client.recognition import Image

if __name__ == "__main__":
    parser = ArgumentParser(description="Delete all images from a workspace")
    parser.add_argument("--api_prefix", type=str, help="API prefix", default="https://api.ximilar.com/")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--workspace_id", help="ID of workspace to upload the images into", default=DEFAULT_WORKSPACE)
    args = parser.parse_args()

    client = RecognitionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)

    images, next_page, status = client.get_training_images()
    while images:
        image: Image
        for image in images:
            print("removing image: " + str(image.id))
            image.remove()

        if not next_page:
            break
        images, next_page, status = client.get_training_images(next_page)
