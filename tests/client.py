import pytest

from vize.api.rest_client import VizeRestClient, Image, Label, Task


def get_client(request):
    token = request.config.getoption("--token")
    client = VizeRestClient(token)
    return client


def test_client_non_existing(request):
    """Tests an API call for non existing Token"""
    token = 'non-existing-token'
    client = VizeRestClient(token)
    response = client.get_all_tasks()

    assert isinstance(response, dict)
    assert response['detail'] == 'Invalid token.'


def test_client_existing(request):
    """Tests an API call for existing Token"""
    client = get_client(request)
    tasks = client.get_all_tasks()

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
    labels = client.get_all_labels()

    assert isinstance(labels, list)
    if len(labels):
        assert isinstance(labels[0], Label)
        assert hasattr(labels[0], 'id')
        assert hasattr(labels[0], 'name')


def test_client_create_task_label_image(request):
    """Tests an API call for creating task, label, image."""
    client = get_client(request)
    task = client.create_task('Test-Task-In-Vize-X-1')
    task1 = client.get_task(task.id)
    labels0 = task1.get_all_labels()
    label = task.create_label('Test-Task-In-Vize-Label-X-1')
    labels1 = task.get_labels()
    images0 = label.get_training_images()
    image = label.upload_image('ximilar.png')
    images1 = label.get_training_images()
    label.remove_image(image.id)
    images0_new = label.get_training_images()

    task.remove_label(label.id)
    client.delete_task(task.id)
    client.delete_label(label.id)
    client.remove_image(image.id)

    rtask = client.get_task(task.id)
    rlabel = client.get_label(label.id)
    rimage = client.get_image(image.id)

    # check creating of Task, Label and Image
    assert isinstance(task, Task)
    assert isinstance(label, Label)
    assert isinstance(image, Image)

    # check the get endpoints
    assert task.id == task1.id
    assert label.id == labels1[0].id

    # check the creating of label and image
    assert len(labels0) == 0
    assert len(labels1) == 1
    assert len(images0[0]) == 0
    assert len(images1[0]) == 1
    assert len(images0_new[0]) == 0

    # check that the removed task does not exists
    assert isinstance(rtask, dict)
    assert isinstance(rlabel, dict)
    assert isinstance(rimage, dict)


def test_classify_v1(request):
    """Tests an API call for all labels"""
    pass


def test_classify_v2(request):
    client = get_client(request)

