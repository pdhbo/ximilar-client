import os
import sys
from argparse import ArgumentParser

from ximilar.client import RecognitionClient
from ximilar.client.constants import FILE, DEFAULT_WORKSPACE, NORESIZE


if __name__ == "__main__":
    parser = ArgumentParser(description="Image uploader into Ximilar App")
    parser.add_argument("--api_prefix", type=str, help="API prefix", default="https://api.ximilar.com/")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--workspace_id", help="ID of workspace to upload the images into", default=DEFAULT_WORKSPACE)
    parser.add_argument("--input_dir", help="directory with the images (recursively)")
    parser.add_argument("--no_resize", help="flag whether to preserve image size", action="store_true")
    parser.add_argument("--print_details", help="if true, info about each image is printed out", action="store_true")
    parser.add_argument(
        "--extensions",
        help="list of file extensions to consider (ignore case)",
        type=list,
        default=[".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".gif"],
    )
    args = parser.parse_args()

    client = RecognitionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)

    if not os.path.isdir(args.input_dir):
        print("directory does not exist: " + args.input_dir, file=sys.stderr)
        exit(1)

    for root, subdirs, files in os.walk(args.input_dir):
        files = filter(lambda x: os.path.splitext(x)[1].lower() in args.extensions, files)
        records = [{FILE: os.path.join(root, filename), NORESIZE: args.no_resize} for filename in files]
        results = client.parallel_records_processing(records, client.upload_images, output=True)

        for (images, status) in results:
            if status["status"] != "OK":
                print("error status: " + str(status))
            if args.print_details:
                for image in images:
                    print(image.img_path + " (" + str(image.img_width) + "px x " + str(image.img_height) + "px)")
