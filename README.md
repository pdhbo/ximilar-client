# Ximilar API Python Client

This Python 3.X Client library is lightweight wrapper for `ximilar.com` and `vize.ai`. 

## Installation

PyPI:

    # we recommend to install ximilar-client to new virtualenv
    pip install ximilar-client

Manual installation:

    1. Cloning the repo
    git clone https://gitlab.com/ximilar-public/ximilar-client.git
    2. Install it with pip to your virtualenv
    pip install -e ximilar-client


This will install also python-opencv, requests and pytest library.

##  Usage

First you need to obtain your `API TOKEN` for communication with ximilar rest endpoints. You can obtain the token from the [Ximilar App](https://app.ximilar.com/) page. 
After you obtain the token, the usage is quite straightforward. First, import this package and create specific rest client (reconition/vize, tagging, colors, search, ...).  In following example we will create client for `Ximilar Recognition Service` (vize.ai): 

```python
from ximilar.client import RecognitionClient
from ximilar.client import DominantColorProductClient, DominantColorGenericClient
from ximilar.client import FashionTaggingClient, GenericTaggingClient

app_client = RecognitionClient(token="__API_TOKEN__")
fashion_client = FashionTaggingClient(token="__API_TOKEN__")
...
```


## Ximilar Recognition
This client allows you to work with Ximilar Recognition Service. With this client you are able to create classification tasks/models based on latest trends in machine learning and neural networks.
After creating client object you can for example load your existing task and call train:

```python
task, status = client.get_task(task_id='__ID_TASK_')

# Every label in the task must have at least 20 images before training.
# The training can take up to several hours so this endpoint will 
# immediately return success if your task is in training queue.
task.train() 

# or you can list all your available tasks
tasks, status = client.get_all_tasks()

# or you can create new classification task and immediatelly delete it
# each Task, Image, Label is identified by unique ID
task, status = client.create_task('__TASK_NAME__')
client.delete_task(task.id) 
```

With a new version of Recognition App you are able to work also with workspaces. Workspaces are entities where all your task, labels and images live. Each user has by default workspace with name `Default` (it will be used if you do not specify workspace when working with Image, Label, Task)..

```python
client = RecognitionClient(token="__API_TOKEN__", workspace='__UUID_OF_YOUR_WORKSPACE__')
```

#### Task

Currently there are two types of task to create. User can select 'multi_class' (default) or 'multi_label'.

```python
# categorization/classification or multi class task means that image is assigned to exactly one label
# labels are exclusive which means image can contain only 'cat' or only 'dog'
classification_task, status = client.create_task('__TASK_NAME__')

# tagging or multi label task means that image can have one or more labels
# for example image can contain 'cat', 'dog' and 'animal' labels if there are on the picture
tagging_task, status = client.create_task('__TASK_NAME__', type='multi_label')
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
existing_label, status = client.get_label('__ID_LABEL__')

# creating new label (CATEGORY) and attaching it to existing Categorization task (multi class)
label, status = client.create_label(name='__NEW_LABEL_NAME__')
task.add_label(label.id)

# creating new label (TAG) for Tagging task (multi label)
label, status = client.create_label(name='__NEW_LABEL_NAME__', label_type='tag')

# get all labels of given task use
labels, status = task.get_labels()

for label in labels:
    print(label.id, label.name)

# get label with name which is mapped to task
label, status = task.get_label_by_name(name='__LABEL_NAME__')

# detaching existing label from existing task
task.detach_label(label.id)

# remove label (which also detach label from task)
client.delete_label(label.id)

# detach image from label
label.detach_image(image.id)

# search labels which contains given substring in name
labels, status = client.get_labels_by_substring('__LABEL_NAME__')
```

#### Working with training images

```python
# getting all images of label (paginated result)
images, next_page, status = label.get_training_images()
while next_page:
    for image in images:
        print(str(image.id))

    images, next_page, status = label.get_training_images(next_page)

# basic operations
image, status = client.get_image(image_id=image.id)
image.add_label(label.id)

# detach label from image
image.detach_label(label.id)

# deleting image 
client.remove_image(image.id)
```

Let's say you want to upload a training image and add several labels to this image.
It's quite straightforward if you have objects of these labels:

```python
images, status = client.upload_images([{'_url': '__URL_PATH_TO_IMAGE__', 'labels': [label.id for label in labels]},
                                       {'_file': '__LOCAL_FILE_PATH__', 'labels': [label.id for label in labels]},
                                       {'_base64': '__BASE64_DATA__', 'labels': [label.id for label in labels]}])

# and maybe add another label to the first image
images[0].add_label(label_X.id)
```

#### Speeding it up with Parallel Processing

If you are uploading/classifying thousands of images and really need to speed it up, then you can use method parallel_records_processing in similar way:

```python
# classifying images
result = client.parallel_records_processing([{"_url": image} for image in images], method=task.classify, output=True, max_workers=3)

# uploading images
result = client.parallel_records_processing([{"_url": image, "labels": ["__LABEL_ID_1__"]} for image in images], method=client.upload_images, output=True)
```

This method works only for getting result for classification, tagging, detection, color or uploading images to Ximilar Recognition platform.

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

## Ximilar Photo and Product similarity

These two services provides visual search (similarity search) for generic (stock) photos or products (e-commerce, fashion, ...).
When initializing client you need to specify both `token` and your `collection` that we created for you.

```python
from ximilar.client.search import SimilarityPhotosClient, SimilarityProductsClient

client = SimilarityPhotosClient(token='__API_TOKEN__', collection='__COLLECTION_ID__')
client = SimilarityProductsClient(token='__API_TOKEN__', collection='__COLLECTION_ID__')

# get random 7 items from database and return also _url if is present in item
result = client.random(count=7, fields_to_return=['_id', '_url'])

# search 10 most visually similar items for item in your index
result = client.search({'_id': '__ITEM_ID__'}, count=10)

# search 5 most visually similar items for external item (not in index) defined by _url field
result = client.search({'_url': '__URL_PATH_TO_IMAGE__'}, count=5)

# search visually similar items, return also _url field if present in item and 
# search only for items defined by filter (mongodb syntax)
result = client.search({'_id': '__ITEM_ID__'}, fields_to_return=['_id', '_url'],
                       filter={
                            'meta-category-x': { '$in': ['__SOME_VALUE_1__', '__SOME_VALUE_2__']},
                            'some-field': '__SOME_VALUE__'
                       })
```

All crud operations:

```python
# get list of items from index
result = client.get([{'_id': '__ITEM_ID__'}, {'_id': '__ITEM_ID__'}])

# insert item tot he index with your _id, and onr of _url | _base64, and other fields (meta-info) which you can 
# then use when applying filter in search or random menthods
result = client.insert([{'_id': '__ITEM_ID__', '_url': '__URL_PATH_TO_IMAGE__',
                         'meta-category-x': '__CATEGORY_OF_ITEM__',
                         'meta-info-y': '__ANOTHER_META_INFO__'}])

# delete item from id
result = client.delete([{'_id': '__ITEM_ID__'}])

# update item in index with all additional fields and meta-info
result = client.update([{'_id': '__ITEM_ID__', 'some-additional-field': '__VALUE__'}])
```
