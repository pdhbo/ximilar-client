from argparse import ArgumentParser

from ximilar.client import SimilarityPhotosClient, SimilarityProductsClient
from ximilar.client.search import SimilarityFashionClient
from ximilar.client.utils.json_data import read_json_file_list


def clean_fields(index_images, fields):
    fields = fields.split(",")
    for img in index_images:
        for field in fields:
            if field in img:
                del img[field]
    return index_images


if __name__ == "__main__":
    parser = ArgumentParser(description="Insert all records in a given file into a similarity search collection")
    parser.add_argument("--api_prefix", help="API prefix", default="")
    parser.add_argument("--clean_fields", help="list of field (separated by comma) to remove from records", default="")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--collection_id", help="ID of collection to upload the image records into", required=True)
    parser.add_argument("--file_path", help="path to JSON file with image records", required=True)
    parser.add_argument("--type", help="product, generic or fashion similarity service", default="generic")
    parser.add_argument("--is_array", help="is the data JSON array or list of JSON records", default=False, type=bool)
    parser.add_argument("--batch_size", help="batch size for insert operation", default=10, type=int)
    parser.add_argument("--threads", help="# of threads to insert with", default=3, type=int)
    parser.add_argument("--skip", help="# of records from the file to be skipped", default=0, type=int)

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
    else:
        raise Exception("Please specify one of the similarity type (generic, product, visual)")

    index_images = read_json_file_list(args.file_path, is_array=args.is_array, skip=args.skip)
    if args.clean_fields:
        index_images = clean_fields(index_images, args.clean_fields)

    client.parallel_records_processing(index_images, client.insert, args.threads, args.batch_size, output=True)
