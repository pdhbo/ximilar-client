# ----------------- PLEASE READ -------------------
# RUN THIS as pytest client.py --token __TOKEN_ID__
# This test scenario suggest that you already:
#     1. Have two Workspaces (Default, Other/Test)
#     2. In your Default workspace you have on Tagging and one Categorization task trained
#     3. Also that you have resources to almost all services
#     4. In your Default workspace some images are present

import pytest

from ximilar.client.constants import *
from ximilar.client.recognition import RecognitionClient, Image, Label, Task
from ximilar.client.detection import DetectionClient, DetectionObject, DetectionLabel, DetectionTask
from ximilar.client.tagging import FashionTaggingClient, GenericTaggingClient

TASK_NAME = "Test-Task-In-Vize-X-1"
LABEL_NAME = "Test-Task-In-Vize-Label-X-1"
TEST_IMG_URL = "https://vize.ai/examples/screw/05.jpg"
TEST_IMG_BIG = "big_image.jpg"
TEST_IMG_SMALL = "ximilar.png"


def get_recognition_client(request) -> RecognitionClient:
    token = request.config.getoption("--token")
    client = RecognitionClient(token)
    return client


def get_detection_client(request):
    token = request.config.getoption("--token")
    client = DetectionClient(token)
    return client


def test_01_client_non_existing(request):
    """
    Tests an API call for non existing Token
    """
    with pytest.raises(Exception) as e:
        token = "non-existing-token"
        client = RecognitionClient(token)

    assert "tech@ximilar.com" in str(e.value)


def test_02_client_existing(request):
    """
    Tests an API call for existing Token
    """
    client = get_recognition_client(request)
    tasks, status = client.get_all_tasks()

    assert isinstance(tasks, list)
    if len(tasks):
        assert isinstance(tasks[0], Task)
        assert hasattr(tasks[0], ID)
        assert hasattr(tasks[0], NAME)
        assert hasattr(tasks[0], TYPE)
        assert hasattr(tasks[0], "production_version")


def test_03_client_all_labels(request):
    """
    Tests an API call for all labels
    """
    client = get_recognition_client(request)
    labels, status = client.get_all_labels()

    assert isinstance(labels, list)
    if len(labels):
        assert isinstance(labels[0], Label)
        assert hasattr(labels[0], ID)
        assert hasattr(labels[0], NAME)


def test_04_client_create_task_label_image(request):
    """
    Tests an API call for creating task, label, image.
    """
    # Query to test
    client = get_recognition_client(request)
    labels_before, status = client.get_all_labels()

    # LETS create some task, label and image
    task, status = client.create_task(TASK_NAME)
    label, status = task.create_label(LABEL_NAME)
    images0, n_page, status = label.get_training_images()
    label_count1 = label.images_count
    images, status = label.upload_images([{FILE: TEST_IMG_SMALL}])
    added_labels, status = images[0].get_labels()
    cached_labels, status = images[0].get_labels()

    label_count2 = label.get_images_count()

    # Query after creating
    task1, status = client.get_task(task.id)
    labels1, status = task1.get_labels()
    images1, n_page, status = label.get_training_images()
    label.detach_image(images[0].id)
    tasksX, status = client.get_tasks_by_name(TASK_NAME)
    labelsX, status = client.get_labels_by_substring(LABEL_NAME)

    # then delete everything
    client.remove_image(images[0].id)
    task.detach_label(label.id)

    for task_to_delete in tasksX:
        task_to_delete.remove()
    for label_to_delete in labelsX:
        label_to_delete.remove()

    # query after deleting
    tasks, status = client.get_tasks_by_name(TASK_NAME)
    labels, status = client.get_labels_by_substring(LABEL_NAME)
    labels_after, status = client.get_all_labels()
    no_task, no_task_status = client.get_task(task.id)
    no_image, no_image_status = client.get_label(label.id)
    no_label, no_label_status = client.get_label(label.id)

    # check the label had connected images
    assert len(added_labels) == 1
    assert len(cached_labels) == 1
    assert label_count1 == 0
    assert label_count2 == 1

    # and check it
    assert labels is None
    assert tasks is None
    assert no_task is None
    assert no_image is None
    assert no_label is None

    # check creating of Task, Label and Image
    assert isinstance(task, Task)
    assert isinstance(label, Label)
    assert isinstance(images[0], Image)

    # check the get endpoints
    assert task.id == tasksX[0].id
    assert label.id == labelsX[0].id

    # check the creating of label and image
    assert len(labels_before) == len(labels_after)
    assert len(labelsX) == 1
    assert len(images0) == 0
    assert len(images1) == 1


def test_05_paginated_methods_recognition_1(request):
    """
    Test creating labels and getting all labels(which works with pagination.
    """
    client = get_recognition_client(request)
    labels_old, status = client.get_all_labels()

    labels = []
    for i in range(10):
        label, status = client.create_label(LABEL_NAME)
        labels.append(label)

    all_labels, status = client.get_all_labels()

    for label in labels:
        label.remove()

    assert len(all_labels) == len(labels_old) + len(labels)


def test_06_upload_image_url_file_big(request):
    """
    Test uploading images with resize and no resize
    """
    client = get_recognition_client(request)
    images1, status = client.upload_images([{URL: TEST_IMG_URL, "noresize": True}])
    images2, status = client.upload_images([{URL: TEST_IMG_URL}])
    images3 = client.parallel_records_processing([{FILE: TEST_IMG_BIG, "noresize": True}], client.upload_images)

    images1[0].remove()
    images2[0].remove()
    images3[0][0][0].remove()

    assert images2[0].img_height == client.max_image_size
    assert images2[0].img_height == client.max_image_size
    assert images1[0].img_height > images2[0].img_height
    assert images3[0][0][0].img_height == images1[0].img_height
    assert 0 == 0


def test_07_upload_image_url_file_small(request):
    """
    Test uploading images with resize and no resize
    """
    client = get_recognition_client(request)
    images1, status = client.upload_images([{FILE: TEST_IMG_SMALL, "noresize": True}])
    images2, status = client.upload_images([{FILE: TEST_IMG_SMALL}])

    images1[0].remove()
    images2[0].remove()

    assert images2[0].img_height == images1[0].img_height


def test_08_classify(request):
    """
    Tests an API call for one of our label
    """
    client = get_recognition_client(request)
    tasks, status = client.get_all_tasks()
    task = tasks[0]

    result = task.classify([{FILE: TEST_IMG_SMALL}])
    assert isinstance(result, dict)


def test_09_parallel_classify(request):
    """
    Test an parallel method for classification endpoint.
    """
    client = get_recognition_client(request)
    tasks, status = client.get_all_tasks()
    task = tasks[0]

    result = client.parallel_records_processing(
        [{FILE: TEST_IMG_SMALL} for i in range(3)], method=task.classify, output=False, max_workers=3
    )
    assert len(result) == 3 and RECORDS in result[0] and len(result[0][RECORDS]) == 1


def test_10_fashion_tagging(request):
    """
    Test fashion tagging system prediction.
    """
    client = FashionTaggingClient(request.config.getoption("--token"))
    result = client.tags([{FILE: TEST_IMG_SMALL}])

    assert RECORDS in result and len(result[RECORDS]) > 0
    assert "_tags" in result[RECORDS][0]


def test_11_parallel_fashion_processing(request):
    """
    Test parallel processing for fashion tagging prediction.
    """
    client = FashionTaggingClient(request.config.getoption("--token"))
    result3 = client.parallel_records_processing(
        [{FILE: TEST_IMG_SMALL} for i in range(3)], method=client.tags, output=False, max_workers=3
    )
    result1 = client.parallel_records_processing(
        [{FILE: TEST_IMG_SMALL} for i in range(3)], method=client.tags, output=False, max_workers=3, batch_size=3
    )

    assert len(result1) == 1 and RECORDS in result1[0] and len(result1[0][RECORDS]) == 3
    assert len(result3) == 3 and RECORDS in result3[0] and len(result3[0][RECORDS]) == 1


def test_12_generic_tagging(request):
    """
    Test generic tagging system for prediction.
    """
    client = GenericTaggingClient(request.config.getoption("--token"))
    result = client.tags([{FILE: TEST_IMG_SMALL}])

    assert RECORDS in result and len(result[RECORDS]) > 0
    assert "_tags" in result[RECORDS][0]


def test_13_detection_workflow(request):
    """
    This is simple workflow test for detection.
    """
    client = get_detection_client(request)

    # lets create task, labels, image
    task, status = client.create_task("Test-Detection-Task-API")
    label1, status = client.create_label("Test-Detection-Label-API-1")
    label2, status = client.create_label("Test-Detection-Label-API-2")
    images1, status = client.upload_images([{FILE: TEST_IMG_BIG, "noresize": True}])
    object1, status = client.create_object(label1.id, images1[0].id, [0, 0, 100, 100])

    # connect label to task
    task.add_label(label1.id)

    # get labels of task
    labels1, status = task.get_labels()

    # get all detection labels
    labels2, status = client.get_all_labels()
    objects, status = client.get_objects_of_image(images1[0].id)

    # remove everything
    task.remove()
    label1.remove()
    label2.remove()
    images1[0].remove()  # this should delete also object
    object1.remove()

    assert len(objects) == 1
    assert len(labels1) == 1
    assert len(labels1) != len(labels2)


def test_14_recognition_workspace(request):
    """
    This test will be skipped if you do not have at least 2 workspaces.
    Test of creating new task to different workspace.
    """
    client = get_recognition_client(request)
    result, status = client.get_workspaces()

    def_workspace, oth_workspace = None, None
    for workspace in result:
        if workspace.name == "Default":
            def_workspace = workspace
        else:
            oth_workspace = workspace

    if len(result) > 1:
        client1 = RecognitionClient(request.config.getoption("--token"), workspace=def_workspace.id)
        client2 = RecognitionClient(request.config.getoption("--token"), workspace=oth_workspace.id)

        tasks1, status = client1.get_all_tasks()
        clean_tasks2, status = client2.get_all_tasks()

        for task in clean_tasks2:
            task.remove()

        task2, status = client2.create_task("Other Workspace Task")
        tasks2_other_workspace, status = client2.get_all_tasks()
        client2.remove_task(task2.id)
        tasks2_other_workspace_after_remove, status = client2.get_all_tasks()

        assert len(tasks1) > 1
        assert len(tasks2_other_workspace) == 1
        assert len(tasks2_other_workspace_after_remove) == 0


def test_15_upload_image_different_workspace(request):
    """
    This test will be skipped if you do not have at least 2 workspaces.
    Test of uploading image to different workspace.
    """
    client = get_recognition_client(request)
    result, status = client.get_workspaces()

    if len(result) < 2:
        return

    def_workspace, oth_workspace = None, None
    for workspace in result:
        if workspace.name == "Default":
            def_workspace = workspace
        else:
            oth_workspace = workspace

    client1 = RecognitionClient(request.config.getoption("--token"), workspace=oth_workspace.id)
    images1, status = client1.upload_images([{FILE: TEST_IMG_BIG, "noresize": True}])
    images1[0].remove()

    assert len(images1) > 0
    assert images1[0].workspace == oth_workspace.id
    assert images1[0].img_height > client1.max_image_size
