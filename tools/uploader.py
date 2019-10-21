import json
import os
import sys
from argparse import ArgumentParser

from ximilar.client import RecognitionClient
from ximilar.client.constants import FILE, DEFAULT_WORKSPACE, NORESIZE, LABELS, ID, NAME
from ximilar.client.recognition import Label


class LabelMock:
    def __init__(self, id):
        self.id = id


if __name__ == "__main__":
    parser = ArgumentParser(description="Image uploader into Ximilar App")
    parser.add_argument("--api_prefix", type=str, help="API prefix", default="https://api.ximilar.com/")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--workspace_id", help="ID of workspace to upload the images into", default=DEFAULT_WORKSPACE)
    parser.add_argument("--input_dir", help="directory with the images (recursively)")
    parser.add_argument("--no_resize", help="flag whether to preserve image size", action="store_true")
    parser.add_argument("--resize", type=int, default=1024, help="size of uploaded images, default: 1024")
    parser.add_argument("--print_details", help="if true, info about each image is printed out", action="store_true")
    parser.add_argument(
        "--extensions",
        help="list of file extensions to consider (ignore case)",
        type=list,
        default=[".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".gif"],
    )
    parser.add_argument("--labels_by_dir", help="label is created for each directory and assigned", action="store_true")
    parser.add_argument("--create_labels", help="create the labels by directory", action="store_true")
    parser.add_argument("--skip_nonempty", help="skip labels (dirs) that already have some images", action="store_true")
    parser.add_argument("--dryrun", help="if true, just print info", action="store_true")
    args = parser.parse_args()

    client = RecognitionClient(
        token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id, max_image_size=args.resize
    )

    if not os.path.isdir(args.input_dir):
        print("directory does not exist: " + args.input_dir, file=sys.stderr)
        exit(1)

    labels = {}
    if args.labels_by_dir and not args.create_labels:  # find the labels by search (don't create them)
        all_labels, _ = client.get_all_labels()
        labels = {l.name: l for l in all_labels}

    i = 1
    for root, subdirs, files in os.walk(args.input_dir):
        print("\n\nPROCESSING DIRECTORY: " + root + "\n")
        if args.labels_by_dir and args.create_labels:  # create labels for each directory
            for subdir in subdirs:
                if args.dryrun:
                    print(f"creating label: '{subdir}'")
                    labels[subdir] = LabelMock(str(i))
                    i += 1
                else:
                    labels[subdir], _ = client.create_label(subdir, "automatically created label for dir: " + subdir)

        files = filter(lambda x: os.path.splitext(x)[1].lower() in args.extensions, files)
        records = [{FILE: os.path.join(root, filename), NORESIZE: args.no_resize} for filename in files]
        if args.labels_by_dir:
            # find the label matching the directory name
            label_name = root.strip("./")
            if args.skip_nonempty and label_name in labels and labels[label_name].get_images_count() > 0:
                print("SKIPPING LABEL (DIR): " + root)
                records = []
            else:
                for rec in records:
                    if label_name not in labels:
                        print("ERROR FINDING LABEL: '" + label_name + "', skipping adding this label to: " + str(rec))
                    else:
                        rec[LABELS] = [labels[label_name].id]

        if args.dryrun:
            print(json.dumps(records, indent=2))
        else:
            results = client.parallel_records_processing(records, client.upload_images, output=True)

            for (images, status) in results:
                if status["status"] != "OK":
                    print("error status: " + str(status))
                if args.print_details:
                    for image in images:
                        print(image.img_path + " (" + str(image.img_width) + "px x " + str(image.img_height) + "px)")
