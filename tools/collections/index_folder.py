import os
from argparse import ArgumentParser

from ximilar.client import SimilarityPhotosClient, SimilarityProductsClient
from ximilar.client.constants import DEFAULT_WORKSPACE
from ximilar.client.recognition import Image

if __name__ == "__main__":
    parser = ArgumentParser(description="Train all non trained tasks of workspace")
    parser.add_argument("--api_prefix", type=str, help="API prefix", default="https://api.ximilar.com/")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--collection_id", help="ID of collection to upload the images into", default="")
    parser.add_argument("--folder", help="path to the folder", default="")
    parser.add_argument("--type", help="product or generic", default="generic")

    args = parser.parse_args()

    if args.type == "generic":
        client = SimilarityPhotosClient(token=args.auth_token, endpoint=args.api_prefix, collection_id=args.collection_id)
    else:
        client = SimilarityProductsClient(token=args.auth_token, endpoint=args.api_prefix, collection_id=args.collection_id)

    index_images = []
    for image in os.listdir(args.folder):
        index_images.append({"_file": os.path.join(args.folder, image)})

    client.parallel_records_processing(index_images, client.insert, batch_size=2, output=True)