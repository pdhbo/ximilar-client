import json
from argparse import ArgumentParser

from ximilar.client import (
    SimilarityPhotosClient,
    SimilarityProductsClient,
    SimilarityCustomClient,
    SimilarityFashionClient,
    ImageMatchingSearchClient,
)
from ximilar.client.utils.json_data import read_json_file_list


def clean_fields(index_images, fields):
    fields = fields.split(",")
    for img in index_images:
        for field in fields:
            if field in img:
                del img[field]
    return index_images


if __name__ == "__main__":
    parser = ArgumentParser(description="Read all records from a similarity collection and print to a given file")
    parser.add_argument("--api_prefix", help="API prefix", default="")
    parser.add_argument("--fields_to_return", help="list of field (separated by comma) to return", default="")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--collection_id", help="ID of collection to upload the image records into", required=True)
    parser.add_argument("--batch_size", help="batch size for insert operation", default=1000, type=int)
    parser.add_argument("--limit", help="limit", type=int, required=False)
    parser.add_argument("--type", help="product, generic, fashion similarity or custom service", default="generic")
    parser.add_argument("--file_path", help="path to JSON file to print image records to", required=True)

    args = parser.parse_args()

    kwargs = {}
    if args.api_prefix:
        kwargs["endpoint"] = args.api_prefix

    if args.type == "generic":
        client = SimilarityPhotosClient(token=args.auth_token, collection_id=args.collection_id, **kwargs)
    elif args.type == "product":
        client = SimilarityProductsClient(token=args.auth_token, collection_id=args.collection_id, **kwargs)
    elif args.type == "fashion":
        client = SimilarityFashionClient(token=args.auth_token, collection_id=args.collection_id, **kwargs)
    elif args.type == "custom":
        client = SimilarityCustomClient(token=args.auth_token, collection_id=args.collection_id, **kwargs)
    elif args.type == "matching":
        client = ImageMatchingSearchClient(token=args.auth_token, collection_id=args.collection_id, **kwargs)
    else:
        raise Exception("Please specify one of the similarity type (generic, product, visual)")

    with open(args.file_path, "w") as f:
        fields_to_return = args.fields_to_return.split(",") if args.fields_to_return else []
        counter = 0
        for r in client.all_records_iter(fields_to_return, args.batch_size):
            json.dump(r, f)
            print("", file=f)
            counter += 1
            if args.limit and args.limit <= counter:
                break
