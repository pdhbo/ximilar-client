import pytest

from ximilar.client.recognition import RecognitionClient, Image, Label, Task
from ximilar.client.tagging import FashionTaggingClient, GenericTaggingClient

TASK_NAME = 'Test-Task-In-Vize-X-1'
LABEL_NAME = 'Test-Task-In-Vize-Label-X-1'


def get_client(request):
    token = request.config.getoption("--token")
    client = RecognitionClient(token)
    return client


def test_client_non_existing(request):
    """Tests an API call for non existing Token"""
    token = 'non-existing-token'
    client = RecognitionClient(token)
    response, status = client.get_all_tasks()

    assert response is None
    assert status['status'] == 'Invalid token.'


def test_client_existing(request):
    """Tests an API call for existing Token"""
    client = get_client(request)
    tasks, status = client.get_all_tasks()

    assert isinstance(tasks, list)
    if len(tasks):
        assert isinstance(tasks[0], Task)
        assert hasattr(tasks[0], 'id')
        assert hasattr(tasks[0], 'name')
        assert hasattr(tasks[0], 'type')
        assert hasattr(tasks[0], 'production_version')


def test_client_all_labels(request):
    """Tests an API call for all labels"""
    client = get_client(request)
    labels, status = client.get_all_labels()

    assert isinstance(labels, list)
    if len(labels):
        assert isinstance(labels[0], Label)
        assert hasattr(labels[0], 'id')
        assert hasattr(labels[0], 'name')


def test_client_create_task_label_image(request):
    """Tests an API call for creating task, label, image."""
    # Query to test
    client = get_client(request)
    labels_before, status = client.get_all_labels()

    # LETS create some task, label and image
    task, status = client.create_task(TASK_NAME)
    label, status = task.create_label(LABEL_NAME)
    images0, n_page, status = label.get_training_images()
    images, status = label.upload_images([{"_file": "ximilar.png"}])

    # Query after creating
    task1, status = client.get_task(task.id)
    labels1, status = task1.get_labels()
    images1, n_page, status = label.get_training_images()
    label.detach_image(images[0].id)
    tasks, status = client.get_tasks_by_name(TASK_NAME)
    labels, status = client.get_labels_by_substring(LABEL_NAME)

    # then delete everything
    client.delete_image(images[0].id)
    task.detach_label(label.id)
    for task_to_delete in tasks:
        task_to_delete.delete_task()
    for label_to_delete in labels:
        label_to_delete.delete_label()

    # query after deleting
    tasks, status = client.get_tasks_by_name(TASK_NAME)
    labels, status = client.get_labels_by_substring(LABEL_NAME)
    labels_after, status = client.get_all_labels()
    no_task, no_task_status = client.get_task(task.id)
    no_image, no_image_status = client.get_label(label.id)
    no_label, no_label_status = client.get_label(label.id)

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
    assert task.id == task1.id
    assert label.id == labels1[0].id

    # check the creating of label and image
    assert len(labels_before) == len(labels_after)
    assert len(labels1) == 1
    assert len(images0) == 0
    assert len(images1) == 1


def test_classify(request):
    """Tests an API call for one of our label"""
    client = get_client(request)
    tasks, status = client.get_all_tasks()
    task = tasks[0]

    result = task.classify([{"_file": "ximilar.png"}])
    assert isinstance(result, dict)


def parallel_classify(request):
    client = get_client(request)
    tasks, status = client.get_all_tasks()
    task = tasks[0]

    result = client.parallel_records_processing([{"_file": "ximilar.png"} for i in range(3)], method=task.classify,
                                                 output=False, max_workers=3)
    assert len(result) == 1 and 'records' in result[0] and len(result[0]['records']) == 3


def test_fashion_tagging(request):
    client = FashionTaggingClient(request.config.getoption("--token"))
    result = client.tags([{"_file": "ximilar.png"}])

    assert 'records' in result and len(result['records']) > 0
    assert '_tags' in result['records'][0]


def test_parallel_fashion_processing(request):
    client = FashionTaggingClient(request.config.getoption("--token"))
    result3 = client.parallel_records_processing([{"_file": "ximilar.png"} for i in range(3)], method=client.tags,
                                                 output=False, max_workers=3)
    result1 = client.parallel_records_processing([{"_file": "ximilar.png"} for i in range(3)], method=client.tags,
                                                 output=False, max_workers=3, batch_size=3)

    assert len(result1) == 1 and 'records' in result1[0] and len(result1[0]['records']) == 3
    assert len(result3) == 3 and 'records' in result3[0] and len(result3[0]['records']) == 1


def test_generic_tagging(request):
    client = GenericTaggingClient(request.config.getoption("--token"))
    result = client.tags([{"_file": "ximilar.png"}])

    assert 'records' in result and len(result['records']) > 0
    assert '_tags' in result['records'][0]