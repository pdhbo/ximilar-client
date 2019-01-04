# Ximilar API Python Client

This Python 3.X Client library is lightweight wrapper for `ximilar.com` and `vize.ai`. 

## Installation

Manual installation:

    1. Cloning the repo
    clone git@gitlab.com:ximilar-public/ximilar-vize-api.git
    2. Install it with pip to your virtualenv
    pip install -e ximilar-vize-api


This will install also python-opencv, requests and pytest library.

##  Usage

First you need to obtain your `API TOKEN` for communication with ximilar rest endpoints. You can obtain the token from the [Ximilar App](https://app.ximilar.com/) page. 
After you obtain the token, the usage is quite straightforward. First, import this package and create specific rest client (reconition/vize, tagging, colors, search, ...).  In following example we will create client for `Ximilar Recognition Service` (vize.ai): 

```python
from ximilar.client import VizeRestClient
from ximilar.client import DominantColorProductClient, DominantColorGenericClient
from ximilar.client import FashionTaggingClient, GenericTaggingClient

app_client = VizeRestClient(token="__API_TOKEN__")
fashion_client = FashionTaggingClient(token="__API_TOKEN__")
...
```


## Ximilar Recognition
This client allows you to work with Ximilar Recognition Service. With this client you are able to create classification tasks/models based on latest trends in machine learning and neural networks.
After creating client object you can for example load your existing task and call train:

```python
task = client.get_task(task_id='__ID_TASK_')

# Every label in the task must have at least 20 images before training.
# The training can take up to several hours so this endpoint will 
# immediately return success if your task is in training queue.
task.train() 

# or you can list all your available tasks
tasks = client.get_all_tasks()

# or you can create new task and immediatelly delete it
# each Task, Image, Label is identified by unique ID
task = client.create_task('__TASK_NAME__')
client.delete_task(task.id)
```

#### Classify

Suppose you want to use the task to predict the result on your images. Please, always try to send image bigger than 200px and lower than 600px for quality and speed:

```python
# you can send image in _file, _url or _base64 format
# the _file format is intenally converted to _base64 as rgb image
result = task.classify([{'_url': '__URL_PATH_TO_IMG__'}, {'_file', '__LOCAL_FILE_PATH__'}, {'_base64': '__BASE64_DATA__'}])

# the result is in json/dictionary format and you can access it in following way:
best_label = result['records'][0]['best_label']
```

#### Labels

Working with the labels are pretty simple.

```python
# getting existing label
existing_label = client.get_label('__ID_LABEL__')

# creating new label and attaching it to existing task
label = client.create_label(name='__NEW_LABEL_NAME__')
task = task.add_label(label.id)

# get all labels of given task use
labels = task.get_labels()

for label in labels:
    print(label.id, label.name)

# detaching existing label from existing task
task.detach_label(label.id)

# remove label (which also detach label from task)
client.delete_label(label.id)

# detach image from label
label.detach_image(image.id)
```

#### Working with training images

```python
# getting all images of label (paginated result)
images, next_page = label.get_training_images()
while next_page:
    for image in images:
        print(str(image.id))

    next_page = label.get_training_images(next_page)

# basic operations
image = client.get_image(image_id=image.id)
image.add_label(label.id)

# detach label from image
image.detach_label(label.id)

# deleting image 
client.remove_image(image.id)
```

Let's say you want to upload a training image and add several labels to this image.
It's quite straightforward if you have objects of these labels:

```python
image = client.upload_image({'_url': '__SOME_URL__'}, label_ids=[label.id for label in labels])

# and maybe add another label
image.add_label(label_X.id)
```

## Ximilar Dominant Colors

You can select the service for extracting dominant colors by type of your image. If the image is from Product/Fashion domain, which means that product is tipically on some solid background then us `DominanColorProductClient`.

```python
from ximilar.client import DominantColorProductClient, DominantColorGenericClient

product_client = DominantColorProductClient(token="__API_TOKEN__")
generic_client = DominantColorGenericClient(token="__API_TOKEN__")

result = product_client.dominantcolor([{"_url": "__URL_PATH_TO_IMAGE__"}])
print(result['records'][0]['_dominant_colors'])
```

## Ximilar Generic and Fashion Tagging

Tagging contains two clients in similar way as DominanColors do.

```python
from ximilar.client import FashionTaggingClient, GenericTaggingClient

fashion_client = FashionTaggingClient(token="__API_TOKEN__")
generic_client = GenericTaggingClient(token="__API_TOKEN__")

result = generic_client.tags([{"_url": "__URL_PATH_TO_IMAGE__"}])
print(result['records'][0]['_tags'])
```