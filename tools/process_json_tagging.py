import json
from argparse import ArgumentParser

from ximilar.client import FashionTaggingClient, GenericTaggingClient
from ximilar.client.constants import DEFAULT_WORKSPACE, NORESIZE, LABELS, TEST_IMAGE, META_DATA
from json_data import read_json_file_iterator, JSONWriter


if __name__ == "__main__":
    parser = ArgumentParser(description="Image uploader from JSON records into Ximilar App")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--input_file", help="path to the json input file")
    parser.add_argument("--output_file", help="path to the json output file", default="output.json")
    parser.add_argument("--type", help="fashion or generic", default="fashion")
    args = parser.parse_args()

    if args.type.lower() == "fashion":
        client = FashionTaggingClient(token=args.auth_token)
    else:
        client = GenericTaggingClient(token=args.auth_token)

    records = []

    with JSONWriter(args.output_file) as writer:
        for rec in read_json_file_iterator(args.input_file):
            print("Processing record", rec)
            result = client.tags([rec])
            if "_status" in result["records"][0]:
                del result["records"][0]["_status"]

            writer.write(result["records"][0])
