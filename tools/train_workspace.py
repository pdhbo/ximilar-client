from argparse import ArgumentParser

from ximilar.client import RecognitionClient
from ximilar.client.constants import DEFAULT_WORKSPACE
from ximilar.client.recognition import Image

if __name__ == "__main__":
    parser = ArgumentParser(description="Train all non trained tasks of workspace")
    parser.add_argument("--api_prefix", type=str, help="API prefix", default="https://api.ximilar.com/")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--workspace_id", help="ID of workspace to upload the images into", default=DEFAULT_WORKSPACE)
    parser.add_argument(
        "--train_all", help="Train all tasks (even if they are trained)", default=False, action="store_true"
    )
    args = parser.parse_args()

    client = RecognitionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)
    tasks, status = client.get_all_tasks()

    for task in tasks:
        if args.train_all or not (task.last_train_status == "TRAINED" or task.last_train_status == "IN_TRAINING"):
            result = task.train()
            print("TRAINING", task.name, task.id, result)
