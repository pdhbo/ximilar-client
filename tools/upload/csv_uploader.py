import csv
from argparse import ArgumentParser
from typing import List

from ximilar.client import RecognitionClient
from ximilar.client.constants import DEFAULT_WORKSPACE, URL, TEST_IMAGE, NORESIZE, LABELS


class LabelMock:
    def __init__(self, id):
        self.id = id


class Processor:
    def __init__(self, client: RecognitionClient, no_resize: bool, create_labels: bool, test_image: bool, dryrun: bool):
        self.client = client
        self.no_resize = no_resize
        self.create_labels = create_labels
        self.test_image = test_image
        self.dryrun = dryrun
        self.mock_id = 0  # for creating label ids during dryrun

        # list of all available labels
        labels_all, _ = client.get_all_labels()
        self.labels_all = {l.name: l for l in labels_all}

    def run(self, file: str, labels: List[str], print_details: bool):
        labels_for_each = self._label_ids(labels)

        records = []
        with open(file, encoding="utf8", newline="") as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=",", quotechar='"')
            for image_line in csv_reader:
                if len(image_line) == 0:
                    continue

                labels_for_image = self._label_ids(image_line[1:])
                labels = [*labels_for_each, *labels_for_image]

                record = {URL: image_line[0], TEST_IMAGE: self.test_image, NORESIZE: self.no_resize}
                if len(labels) > 0:
                    record[LABELS] = labels

                records.append(record)

        if self.dryrun:
            print(records)
        else:
            results = client.parallel_records_processing(records, client.upload_images, output=True)
            for (images, status) in results:
                if status["status"] != "OK":
                    print("error status: " + str(status))
                if print_details:
                    for image in images:
                        print(image.img_path + " (" + str(image.img_width) + "px x " + str(image.img_height) + "px)")

    def _label_ids(self, labels: List[str]) -> List[str]:
        if not labels:
            return []

        ids = []
        for label in labels:
            if label not in self.labels_all:
                if self.create_labels:
                    if args.dryrun:
                        print(f"would create label: {label}")
                        self.labels_all[label] = LabelMock(f"mock{self.mock_id}")
                        self.mock_id += 1
                    else:
                        self.labels_all[label], _ = client.create_label(label, "automatically created label")
                        print(f"created label: {self.labels_all[label]}")
                else:
                    print(f"Unknown label {label}, skipping.")

            if label in self.labels_all:
                ids.append(self.labels_all[label].id)

        return ids


if __name__ == "__main__":
    parser = ArgumentParser(description="Image uploader from CSV records (NO HEADER) into Ximilar App")
    parser.add_argument("--api_prefix", type=str, help="API prefix", default="https://api.ximilar.com/")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--workspace_id", help="ID of workspace to upload the images into", default=DEFAULT_WORKSPACE)
    parser.add_argument(
        "--input_file", help="CSV file with records to be uploaded (first column URL, rest optional label names)"
    )
    parser.add_argument("--no_resize", help="flag whether to preserve image size", action="store_true")
    parser.add_argument("--test_image", help="mark the image as test", action="store_true")
    parser.add_argument("--resize", type=int, default=1024, help="size of uploaded images, default: 1024")
    parser.add_argument("--print_details", help="if true, info about each image is printed out", action="store_true")
    parser.add_argument("--label", help="list of labels which will be added to all images", nargs="+")
    parser.add_argument("--create_labels", help="create labels, if they don't exist", action="store_true")
    parser.add_argument("--dryrun", help="if true, just print info", action="store_true")
    args = parser.parse_args()

    client = RecognitionClient(
        token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id, max_image_size=args.resize
    )

    processor = Processor(client, args.no_resize, args.create_labels, args.test_image, args.dryrun)
    processor.run(args.input_file, args.label, args.print_details)
