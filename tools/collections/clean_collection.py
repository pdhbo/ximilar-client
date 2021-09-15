from argparse import ArgumentParser

from ximilar.client import (
    SimilarityPhotosClient,
    SimilarityProductsClient,
    SimilarityFashionClient,
    SimilarityCustomClient,
)

if __name__ == "__main__":
    parser = ArgumentParser(description="Train all non trained tasks of workspace")
    parser.add_argument("--api_prefix", type=str, help="API prefix", default="https://api.ximilar.com/")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--collection_id", help="ID of collection to upload the images into", default="")
    parser.add_argument("--type", help="product or generic", default="generic")

    args = parser.parse_args()

    if args.type == "generic":
        client = SimilarityPhotosClient(
            token=args.auth_token, endpoint=args.api_prefix, collection_id=args.collection_id
        )
    elif args.type == "product":
        client = SimilarityProductsClient(
            token=args.auth_token, endpoint=args.api_prefix, collection_id=args.collection_id
        )
    elif args.type == "visual":
        client = SimilarityFashionClient(
            token=args.auth_token, endpoint=args.api_prefix, collection_id=args.collection_id
        )
    elif args.type == "custom":
        client = SimilarityCustomClient(token=args.auth_token, collection_id=args.collection_id)
    else:
        raise Exception("Please specify one of the similarity type (generic, product, visual)")

    page, records = 1, []
    while True:
        result = client.allRecords(page=page)
        records += result["answer_records"]
        page += 1
        if "next" not in result:
            break

    client.parallel_records_processing(records, client.remove, batch_size=10, output=True)
