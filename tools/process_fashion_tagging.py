import traceback

import csv
from argparse import ArgumentParser
from tqdm import tqdm
from typing import List

from ximilar.client import FashionTaggingClient
from ximilar.client import RecognitionClient
from ximilar.client.constants import DEFAULT_WORKSPACE, RECORDS
from ximilar.client.recognition import IMAGE_ENDPOINT, Label


def find_label(labels_true: List[Label], label_id: str) -> bool:
    """
    :param labels_true: List of all labels that belongs to a test image.
    :param label_id: Index of a predicted.
    :return: Whether given label id is among ground truth labels.
    """
    label = next(filter(lambda l: l.id == label_id, labels_true), None)
    found = label is not None
    return found


def found_symbol(found: bool) -> str:
    """
    :param found: Whether the label was present in a ground truth list.
    :return: string representation of this boolean value
    """
    return "OK" if found else "X"


def categories_result(labels_true: List[Label], predicted: List, row: List[str], max_cat: int = 2) -> None:
    """
    Takes all labels assigned to an image and found outs if given (top) category is among them. Checks first two values,

    :param labels_true: List of all labels that belongs to a test image.
    :param predicted: Predicted (top) category
    :param row: list where the results will be added
    :param max_cat: how many (top) categories should we check
    """
    predicted.sort(reverse=True, key=lambda c: c["prob"])
    for i, pred in enumerate(predicted[0:max_cat]):
        found = find_label(labels_true, pred["id"])
        row.extend([pred["name"], pred["prob"], found_symbol(found)])

    # if there are no results, we need to put empty space there
    row.extend([""] * (3 * (2 - min(max_cat, len(predicted)))))


def process_workspace(
    recognition_client: RecognitionClient, fashion_tagging_client: FashionTaggingClient, output_file: str
) -> None:
    """
    Finds all testing images in given workspace, tags them and compare the result to labels assigned to given image.
    All is saved into a csv file.

    :param recognition_client:
    :param fashion_tagging_client:
    :param output_file:
    """
    max_labels = 30
    with open(output_file, "w", newline="") as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=",")

        # create CSV header
        header_probability = "prob"
        header_found = ""
        header_labels = ["top category 1", "top category 2", "category 1", "category 2", *(["label"] * max_labels)]
        header = ["image", "image id", "image URL"]
        for header_label in header_labels:
            header.extend([header_label, header_probability, header_found])
        csv_writer.writerow(header)

        page_size = 50
        page_url = f"{IMAGE_ENDPOINT}?test=true&page_size={page_size}"
        total_images = recognition_client.get_training_images(page_url=page_url)[2]["count"]

        with tqdm(total=total_images) as pbar:
            while page_url:
                # get one page with test images
                training_images_result = recognition_client.get_training_images(page_url=page_url)
                training_images = training_images_result[0]
                page_url = training_images_result[1]

                # prepare records for tagging and map for assigning Image object to urls
                records = [{"_url": img.img_path} for img in training_images]
                training_images = {img.img_path: img for img in training_images}

                # process all records as fast as possible, flatten the result to a list of records
                labels_response = fashion_tagging_client.parallel_records_processing(
                    records, fashion_tagging_client.tags, batch_size=10
                )
                labels_records = [item for sublist in labels_response for item in sublist[RECORDS]]

                # process one result (Image) at a time and write one line to CSV
                line_number = 2
                for labels_record in labels_records:
                    img = training_images[labels_record["_url"]]
                    try:
                        row = [f"=IMAGE(C{line_number})", img.id, img.img_path]

                        labels_true = img.get_labels()[0]
                        labels_pred = labels_record["_tags"]

                        # there is always same number of columns for top category and category
                        categories_result(labels_true, labels_pred.get("Top Category", []), row)
                        categories_result(labels_true, labels_pred.get("Category", []), row)

                        # number of other labels can vary
                        for key, labels in labels_pred.items():
                            if key in ["Top Category", "Category"]:
                                continue
                            labels.sort(reverse=True, key=lambda c: c["prob"])
                            for label in labels:
                                if "id" in label:
                                    found = find_label(labels_true, label["id"])
                                    row.extend([f"{key}: {label['name']}", label["prob"], found_symbol(found)])
                                else:
                                    row.extend([f"{key}: {label['name']}", label["prob"], ""])

                        row.extend([""] * (len(header) - len(row)))
                        csv_writer.writerow(row)
                        line_number += 1
                    except Exception:
                        print(f"Error for image id {img.id}")
                        traceback.print_exc()

                    # show progress
                    pbar.update()


if __name__ == "__main__":
    parser = ArgumentParser(description="Evaluate fashion tagging for all testing images in given workspace")
    parser.add_argument("--api_prefix", help="API prefix", default="https://api.ximilar.com/")
    parser.add_argument("--auth_token", help="user authorization token to be used for API authentication")
    parser.add_argument("--workspace_id", help="ID of workspace to take test images from", default=DEFAULT_WORKSPACE)
    parser.add_argument("--output_file", help="json output file [tagging_output.csv]", default="tagging_output.csv")
    args = parser.parse_args()

    fashion_tagging = FashionTaggingClient(token=args.auth_token)
    recognition = RecognitionClient(token=args.auth_token, endpoint=args.api_prefix, workspace=args.workspace_id)
    process_workspace(recognition, fashion_tagging, args.output_file)
