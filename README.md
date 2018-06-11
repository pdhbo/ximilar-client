# VIZE.AI API Python Client

This Python 3.X Client library is simple wrapper for vize.ai.

You can use this library to enhance your application with vize.ai.

## Installation

Manual installation:

    1. Cloning the repo
    clone git@gitlab.com:ximilar-public/ximilar-vize-api.git
    2. Install it with pip to your virtualenv
    pip install -e ximilar-vize-api


This will install also python-opencv, requests library.

##  Usage

First you need to obtain your api token for communication with vize rest endpoints. You can obtain the token from the vize.ai administration page. After you obtain the token the usage is quite straightforward. First import this package and create the rest client.

```python
from vize.api import VizeRestClient, Task, Image, Label
    
client = VizeRestClient(token='your-api-token')
```

After creating client object you can for example load your existing task:

```python
task = client.get_task(task_id='identification-of-your-task')
```


## Train the task

If your task is not trained yet, you can call the api to force it:

```python
task.train()
```

#### Classify

Suppose you want to use the task to predict the result on your images. Always try to send us image bigger than 200px and lower than 600px for quality and speed:

```python
result = task.classify([{'_url': 'www.example.com/1.jpg'}])
```

The result is in json/dictionary format and you can access it like this:

```python
best_label = result['records'][0]['best_label']
```

There is an option to send also file from your local storage. Internally it will convert and send base64 image representation.

```python
result = task.classify([{'_file': 'c:/test.jpg'}])
```

#### Working with Task

To list all tasks you can use this:

```python
tasks = client.get_all_tasks()
```

Creating new task:

```python
task = client.create_task()
```

Delete existing task (two ways):
 
 ```python
task.delete_task()
client.delete_task('task_id')
```

#### Working with Labels

To create new label and add this label to task:

```python
label = client.create_label(name='New-Label')
task = task.add_label(label.id)
```

To get all labels of given task use:

```python
labels = task.get_labels()

for label in labels:
    print(label.id, label.name)
```

To detach label from task:

```python
task.remove_label(label.id)
```

To remove label from database(and all tasks):

```python
client.remove_label(label.id)
```


#### Working with training images

To get list of all images of label use:

```python
images = label.get_all_images()
for image in images:
    print(str(image.id))
```

Let's say you want to upload a training image and add several labels to this image.
It's quite straightforward if you have objects of these labels:

```python
image = client.upload_image({'_url': 'www.example.com/1.jpg'}, labels=labels)
```

You can get image by id and add/remove labels also after uploading image.

```python
image = client.get_image(image_id=image.id)
image.add_label(label.id)
image.remove_label(label.id)
```

Deleting image:

```python
client.remove_image(image.id)
```

#### Start training of Task

```python
training = task.start_training()
```
