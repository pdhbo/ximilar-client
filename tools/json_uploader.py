import json
from argparse import ArgumentParser

from ximilar.client import RecognitionClient
from ximilar.client.constants import DEFAULT_WORKSPACE, NORESIZE, LABELS, TEST_IMAGE, META_DATA
from ximilar.client.utils.json_data import read_json_file_iterator


class LabelMock:
    def __init__(self, id):
        self.id = id


if __name__ == "__main__":
    parser = ArgumentParser(description="Image uploader from JSON records into Ximilar App")
    parser.add_argument("--api_prefix", type=str, help="API prefix", default="https://api.ximilar.com/")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--workspace_id", help="ID of workspace to upload the images into", default=DEFAULT_WORKSPACE)
    parser.add_argument("--input_file", help="JSON file with records to be uploaded")
    parser.add_argument("--no_resize", help="flag whether to preserve image size", action="store_true")
    parser.add_argument("--test_image", help="mark the image as test", action="store_true")
    parser.add_argument("--resize", type=int, default=1024, help="size of uploaded images, default: 1024")
    parser.add_argument("--print_details", help="if true, info about each image is printed out", action="store_true")
    parser.add_argument("--label_fields", help="list of JSON fields to take label names from", nargs="+")
    parser.add_argument("--create_labels", help="create labels from the fields, if don't exist", action="store_true")
    parser.add_argument("--one_image_per_label", help="upload images with more labels more times", action="store_true")
    parser.add_argument("--dryrun", help="if true, just print info", action="store_true")
    args = parser.parse_args()

    client = RecognitionClient(
        token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id, max_image_size=args.resize
    )

    labels = {}
    if len(args.label_fields) > 0:  # find the labels by search (don't create them)
        all_labels, _ = client.get_all_labels()
        labels = {l.name: l for l in all_labels}

    records = []
    for rec in read_json_file_iterator(args.input_file):
        rec_labels = []
        for f in args.label_fields:
            if f not in rec or not rec[f] or len(rec[f]) == 0:
                continue
            # if labels should be added, try to find them in the labels
            if rec[f] not in labels and args.create_labels:
                if args.dryrun:
                    print("would create label: " + str(rec[f]))
                else:
                    labels[rec[f]], _ = client.create_label(rec[f], "automatically created label")
                    print("created label: " + str(labels[rec[f]]))
            if rec[f] in labels:
                rec_labels.append(labels[rec[f]].id)

        rec[META_DATA] = rec.copy()
        rec[TEST_IMAGE] = args.test_image
        rec[NORESIZE] = args.no_resize
        if args.one_image_per_label and len(rec_labels) > 1:
            for lab in rec_labels:
                new_rec = rec.copy()
                new_rec[LABELS] = [lab]
                records.append(new_rec)
        else:
            rec[LABELS] = rec_labels
            records.append(rec)

    if args.dryrun:
        print(json.dumps(records, indent=2))
    else:
        results = client.parallel_records_processing(records, client.upload_images, max_workers=5, output=True)

        for (images, status) in results:
            if status["status"] != "OK":
                print("error status: " + str(status))
            if args.print_details:
                for image in images:
                    print(image.img_path + " (" + str(image.img_width) + "px x " + str(image.img_height) + "px)")
