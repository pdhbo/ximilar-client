import json
from argparse import ArgumentParser
from typing import Union

from ximilar.client import FashionTaggingClient, GenericTaggingClient
from ximilar.client.constants import DEFAULT_WORKSPACE, NORESIZE, LABELS, TEST_IMAGE, META_DATA
from ximilar.client.utils.json_data import read_json_file_iterator, JSONWriter


def process_batch(tagging_client, record_batch, output_writer):
    records = tagging_client.tags(record_batch)["records"]
    for r in records:
        if "_status" in r:
            del r["_status"]
        output_writer.write(r)


if __name__ == "__main__":
    parser = ArgumentParser(description="Image uploader from JSON records into Ximilar App")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--input_file", help="path to the json input file")
    parser.add_argument("--output_file", help="path to the json output file", default="output.json")
    parser.add_argument("--type", help="fashion or generic", default="fashion")
    parser.add_argument("--batch_size", help="size of batch in which to process the data", default=10, type=int)
    args = parser.parse_args()

    client: Union[FashionTaggingClient, GenericTaggingClient]
    if args.type.lower() == "fashion":
        client = FashionTaggingClient(token=args.auth_token)
    else:
        client = GenericTaggingClient(token=args.auth_token)

    with JSONWriter(args.output_file) as writer:
        batch = []
        for index, rec in enumerate(read_json_file_iterator(args.input_file)):
            print("Reading record ", index, rec)
            batch.append(rec)
            if len(batch) < args.batch_size:
                continue

            process_batch(client, batch, writer)
            batch = []
        process_batch(client, batch, writer)
