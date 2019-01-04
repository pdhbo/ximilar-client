import pytest

from ximilar.client.recognition import RecognitionClient, Image, Label, Task


def get_client(request):
    token = request.config.getoption("--token")
    client = RecognitionClient(token)
    return client


def test_client_non_existing(request):
    """Tests an API call for non existing Token"""
    token = 'non-existing-token'
    client = RecognitionClient(token)
    response = client.get_all_tasks()

    assert response is None


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
    labels_before = client.get_all_labels()
    task = client.create_task('Test-Task-In-Vize-X-1')
    task1 = client.get_task(task.id)
    label = task.create_label('Test-Task-In-Vize-Label-X-1')
    labels1 = task1.get_labels()
    images0 = label.get_training_images()
    image = label.upload_image('ximilar.png')
    images1 = label.get_training_images()
    label.detach_image(image.id)
    images0_new = label.get_training_images()

    task.detach_label(label.id)
    client.delete_task(task.id)
    client.delete_label(label.id)
    client.delete_image(image.id)
    labels_after = client.get_all_labels()

    with pytest.raises(Exception):
        client.get_task(task.id)

    with pytest.raises(Exception):
        client.get_label(label.id)

    with pytest.raises(Exception):
        client.get_image(image.id)

    # check creating of Task, Label and Image
    assert isinstance(task, Task)
    assert isinstance(label, Label)
    assert isinstance(image, Image)

    # check the get endpoints
    assert task.id == task1.id
    assert label.id == labels1[0].id

    # check the creating of label and image
    assert len(labels_before) == len(labels_after)
    assert len(labels1) == 1
    assert len(images0[0]) == 0
    assert len(images1[0]) == 1
    assert len(images0_new[0]) == 0


def test_classify(request):
    """Tests an API call for one of our label"""
    client = get_client(request)
    tasks = client.get_all_tasks()
    task = tasks[0]

    result = task.classify([{"_file": "ximilar.png"}])
    assert isinstance(result, dict)


