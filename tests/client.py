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
    label1 = task.get_labels(task.id)
    #image = label.upload_image()

    #client.remove_task(task.id)
    #task.remove_label(label1.id)
    #client.delete_task(label1.id)
    #client.remove_image(image.id)

    assert isinstance(task, Task)
    assert isinstance(label, Label)
    #assert isinstance(image, Image)
    assert task.id == task1.id
    assert label == label1.id
    assert len(labels0) == 0


def test_classify_v1(request):
    """Tests an API call for all labels"""
    pass


def test_classify_v2(request):
    """Tests an API call for all labels"""
    pass
