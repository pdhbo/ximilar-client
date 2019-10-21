import json
from argparse import ArgumentParser

from ximilar.client import RecognitionClient
from ximilar.client.constants import DEFAULT_WORKSPACE
from ximilar.client.recognition import Image


def read_json_array(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        array = json.load(f)
        for rec in array:
            yield rec


if __name__ == "__main__":
    parser = ArgumentParser(description="Takes JSON with image metadata and sets labels to images accordingly")
    parser.add_argument("--api_prefix", type=str, help="API prefix", default="https://api.ximilar.com/")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--workspace_id", help="ID of workspace to upload the images into", default=DEFAULT_WORKSPACE)
    parser.add_argument("--print_details", help="if true, info about each image is printed out", action="store_true")
    parser.add_argument("--json_file", help="file with JSON metadata as produced by data_saver.py", required=True)
    args = parser.parse_args()

    client = RecognitionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)

    for record in read_json_array(args.json_file):
        image: Image
        image, _ = client.get_image(record["image"])
        if "labels" in record:
            for label_id in record["labels"]:
                result = image.add_label(label_id)
                print("processed: " + str(result))
