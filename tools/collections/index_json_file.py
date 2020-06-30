from argparse import ArgumentParser

from ximilar.client import SimilarityPhotosClient, SimilarityProductsClient
from ximilar.client.utils.json_data import read_json_file_list


def clean_fields(index_images, fields):
    fields = fields.split(",")
    for img in index_images:
        for field in fields:
            if field in img:
                del img[field]
    return index_images


if __name__ == "__main__":
    parser = ArgumentParser(description="Train all non trained tasks of workspace")
    parser.add_argument("--api_prefix", help="API prefix", default="")
    parser.add_argument("--clean_fields", help="list of field (separated by comma) to remove from records", default="")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--collection_id", help="ID of collection to upload the images into", required=True)
    parser.add_argument("--path", help="path to the json file", required=True)
    parser.add_argument("--type", help="product or generic or visual", default="generic")
    parser.add_argument("--is_array", help="true just in case the data is JSON array", default=False, type=bool)

    args = parser.parse_args()

    kwargs = {}
    if args.api_prefix:
        kwargs["endpoint"] = args.api_prefix

    if args.type == "generic":
        client = SimilarityPhotosClient(token=args.auth_token, collection_id=args.collection_id, **kwargs)
    elif args.type == "product":
        client = SimilarityProductsClient(token=args.auth_token, collection_id=args.collection_id, **kwargs)
    elif args.type == "visual":
        client = SimilarityProductsClient(token=args.auth_token, collection_id=args.collection_id, **kwargs)
    else:
        raise Exception("Please specify one of the similarity type (generic, product, visual)")

    index_images = read_json_file_list(args.path, is_array=args.is_array)
    if args.clean_fields:
        index_images = clean_fields(index_images, args.clean_fields)

    client.parallel_records_processing(index_images, client.insert, batch_size=10, output=True)
