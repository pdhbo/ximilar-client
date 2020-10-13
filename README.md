# Ximilar API Python Client

![](logo.png)

This Python 3.X Client library is lightweight wrapper for `ximilar.com` and `vize.ai`. 

## Installation

PyPI (https://pypi.org/project/ximilar-client/):

    # we recommend to install ximilar-client to new virtualenv
    pip install ximilar-client

Manual installation with latest changes:

    1. Cloning the repo
    git clone https://gitlab.com/ximilar-public/ximilar-client.git
    2. Install it with pip to your virtualenv
    pip install -e ximilar-client


This will install also python-opencv, numpy, requests, tqdm and pytest library.

##  Usage

First you need to register via `app.ximilar.com` and obtain your `API TOKEN` for communication with ximilar rest endpoints. You can obtain the token from the [Ximilar App](https://app.ximilar.com/) at your profile page. 
After you obtain the token, the usage is quite straightforward. First, import this package and create specific rest client (reconition/vize, tagging, colors, search, ...).  In following example we will create client for `Ximilar Recognition Service` (vize.ai). For all other Ximilar Services as Tagging, Custom Object Detection you will need to contact `tech@ximilar.com` first, so they will provide you access to the service: 

```python
from ximilar.client import RecognitionClient, DetectionClient
from ximilar.client import DominantColorProductClient, DominantColorGenericClient
from ximilar.client import FashionTaggingClient, GenericTaggingClient

app_client = RecognitionClient(token="__API_TOKEN__")
detect_client = DetectionClient(token="__API_TOKEN__")
...
```

## Workspaces

With a new version of Ximilar App you are able to work also with workspaces. Workspaces are entities where all your task, labels and images live. Each user has by default workspace with name `Default` (it will be used if you do not specify workspace when working with Image, Label, Task). However you can specify id of workspace in the constructor.

```python
client = RecognitionClient(token="__API_TOKEN__", workspace='__UUID_OF_YOUR_WORKSPACE__')
client = DetectionClient(token="__API_TOKEN__", workspace='__UUID_OF_YOUR_WORKSPACE__')
```

## Ximilar Recognition
This client allows you to work with Ximilar Recognition Service. With this client you are able to create classification or tagging tasks based on latest trends in machine learning and neural networks.
After creating client object you can for example load your existing task and call train:

```python
task, status = client.get_task(task_id='__ID_TASK_')

# Every label in the task must have at least 20 images before training.
# The training can take up to several hours as we are trying to achieve really high quality
# solution. This endpoint will immediately return success if your task is in training queue.
task.train() 

# or you can list all your available tasks
tasks, status = client.get_all_tasks()

# or you can create new classification task
# each Task, Image, Label is identified by unique ID
task, status = client.create_task('__TASK_NAME__')
```

#### Task

Currently there are two types of task to create. User can select 'multi_class' (default) or 'multi_label'. See ximilar.docs for more info.

```python
# categorization/classification or multi class task means that image is assigned to exactly one label
# labels are exclusive which means image can contain only 'cat' or only 'dog'
classification_task, status = client.create_task('__TASK_NAME__')

# tagging or multi label task means that image can have one or more labels
# for example image can contain 'cat', 'dog' and 'animal' labels if there are on the picture
tagging_task, status = client.create_task('__TASK_NAME__', type='multi_label')

# removing task is possible through client object or task itself
client.remove_task(task.id)
task.remove()
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

Labels are connected to the task. Depends which task you are working with (Tagging/multi_label or Categorization/multi_class) you can create Tag or Category labels. Working with the labels are pretty simple:

```python
# getting existing label
existing_label, status = client.get_label('__ID_LABEL__')

# creating new label (CATEGORY, which is default) and attaching it to existing Categorization task (multi class)
label, status = client.create_label(name='__NEW_LABEL_NAME__')
task.add_label(label.id)

# creating new label (TAG) for Tagging task (multi label)
label, status = client.create_label(name='__NEW_LABEL_NAME__', label_type='tag')

# get all labels which are connected to the task
labels, status = task.get_labels()

for label in labels:
    print(label.id, label.name)

# get label with exact name which is also connected to specific task
label, status = task.get_label_by_name(name='__LABEL_NAME__')

# detaching (not deleting) existing label from existing task
task.detach_label(label.id)

# remove label (which also detach label from all tasks)
client.remove_label(label.id)

# detach image from label
label.detach_image(image.id)

# search labels which contains given substring in name
labels, status = client.get_labels_by_substring('__LABEL_NAME__')
```

#### Working with training images

Image is main entity in Ximilar system. Every image can have multiple labels (Recognition service) or multiple objects (Detection service).

```python
# getting all images of label (paginated result)
images, next_page, status = label.get_training_images()
while images:
    for image in images:
        print(str(image.id))

    if not next_page:
        break
    images, next_page, status = label.get_training_images(next_page)

# basic operations
image, status = client.get_image(image_id=image.id)
image.add_label(label.id)

# detach label from image
image.detach_label(label.id)

# deleting image 
client.remove_image(image.id)
```

Let's say you want to upload a training image and add several labels to this image:

```python
images, status = client.upload_images([{'_url': '__URL_PATH_TO_IMAGE__', 'labels': [label.id for label in labels], "meta_data": {"field": "key"}},
                                       {'_file': '__LOCAL_FILE_PATH__', 'labels': [label.id for label in labels]},
                                       {'_base64': '__BASE64_DATA__', 'labels': [label.id for label in labels]}])

# and maybe add another label to the first image
images[0].add_label("__SOME_LABEL_ID__")
```

Upload image without resizing it (for example Custom Object Detection requires high resolution images):

```python
images, status = client.upload_images([{'_url': '__URL_PATH_TO_IMAGE__', "noresize": True}])
```

Every image can have some meta data stored:

```python
image.add_meta_data({"__KEY_1__": "value", "__KEY_2__": {"THIS CAB BE":"COMPLEX"}})
image.clear_meta_data()
```

Every image can be marked with **test** flag (for evaluation on independent test dataset only):

```python
image.set_test(True)
```

Every image can be marked as real (default) or product. Product image should be images where is dominant one object on nice solid background. We can do more augmentations on these images.

```python
image.set_real(False) # will mark image as product
```

## Ximilar Flows

The client is able to get flow of the json or process images/records by the flow.

```python
from ximilar.client import FlowsClient

client = FlowsClient("__API_TOKEN__")

# get flow
flow, _ = client.get_flow("__FLOW_ID__")

# two way to call the flow on records
client.process_flow(flow.id, records)
flow.proces(records)
```


## Ximilar Object Detection

Ximilar Object Detection is service which will help you find exact location (Bounding Box/Object with four coordinates xmin, ymin, xmax, ymax).
In similar way as Ximilar Recognition, here we also have Tasks, Labels and Images. However one more entity called Object is present in Ximilar Object Detection.

First you need to create/get Detection Task:

```python
client = DetectionClient("__API_TOKEN__")
detection_task, status = client.create_task("__DETECTION_TASK_NAME__")
detection_task, status = client.get_task(task.id)
```

Second you need to create Detection Label and connect it to the task:

```python
detection_label, status = client.create_label("__DETECTION_LABEL_NAME__")
detection_label, status = client.get_label("__DETECTION_LABEL_ID__")

detection_task.add_label(detection_label.id)
```

Lastly you need to create Objects/Bounding box annotations of some type (Label) on the images:

```python
image, status = client.get_image("__IMAGE_ID__")
d_object, status = client.create_object("__DETECTION_LABEL_ID__", "__IMAGE_ID__", [xmin, ymin, xmax, ymax])
d_object, status = client.get_object(d_object.id)

# get all objects of image
d_objects, status = client.get_objects_of_image("__IMAGE_ID__")
```

Then you can create your task:

```python
detection_task.train()
```

Removing entities is same as in recognition client:

```python
client.remove_task("__DETECTION_TASK_ID__")
client.remove_label("__DETECTION_LABEL_ID__") # this will delete all objects which were created as this label
client.remove_object("__DETECTION_OBJECT_ID__")
client.remove_image("__IMAGE_ID__")

task.remove()
label.remove()

object1 = client.get_object("__DETECTION_OBJECT_ID__")
object1.remove()
image.remove()
```

Getting Detection Result:

```python
result = detection_task.detect([{"_url": "__URL_PATH_TO_IMAGE__"}])
```

Extracting object from image:

```python
image,  status = client.get_image("59f7240d-ca86-436b-b0cd-30f4b94705df")

object1, status = client.get_object("__DETECTION_OBJECT_ID__")
extracted_image_record = image.extract_object_data(object1.data)
```

## Speeding it up with Parallel Processing

If you are uploading/classifying thousands of images and really need to speed it up, then you can use method parallel_records_processing:

```python
# classifying images in Ximilar Custom Recognition service
result = client.parallel_records_processing([{"_url": image} for image in images], method=task.classify, output=True, max_workers=3)

# detection images in Ximilar Custom Object Detection
result = client.parallel_records_processing([{"_url": image} for image in images], method=task.detect, output=True, max_workers=3)

# uploading images
result = client.parallel_records_processing([{"_url": image, "labels": ["__LABEL_ID_1__"]} for image in images], method=client.upload_images, output=True)
```

This method works only for getting result for classification, tagging, detection, color extraction or uploading images (All methods which use json records as input).

## Ximilar Visual Search

Service for visual fashion search. For more information see docs.ximilar.com

```python
from ximilar.client.visual import VisualSearchClient

client = VisualSearchClient(token='__API_TOKEN__', collection_id='__COLLECTION_ID__')

# inserting image requires _id and product_id
client.insert([{"_id": "__IMAGE_ID__", "product_id": "__PRODUCT_ID__", "_url": "__URL_PATH_TO_IMAGE__"}])
result = client.detect([{"_url": "__URL_PATH_TO_IMAGE__"}])

# search in collection
result = client.search([{"_url": "__URL_PATH_TO_IMAGE__"}])
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

result = fashion_client.tags([{"_url": "__URL_PATH_TO_IMAGE__"}])
print(result['records'][0]['_tags'])

result = fashion_client.meta_tags([{"_url": "__URL_PATH_TO_IMAGE__"}])
print(result['records'][0]['_tags_meta_simple'])

```

## Ximilar Photo and Product similarity

These two services provides visual search (similarity search) for generic (stock) photos or products (e-commerce, fashion, ...).
When initializing client you need to specify both `token` and your `collection_id` that we created for you.

```python
from ximilar.client.search import SimilarityPhotosClient, SimilarityProductsClient

client = SimilarityPhotosClient(token='__API_TOKEN__', collection_id='__COLLECTION_ID__')
client = SimilarityProductsClient(token='__API_TOKEN__', collection_id='__COLLECTION_ID__')

# get random 7 items from database and return also _url if is present in item
result = client.random(count=7, fields_to_return=['_id', '_url'])

# search 10 most visually similar items for item in your index
result = client.search({'_id': '__ITEM_ID__'}, k=10)

# search 5 most visually similar items for external item (not in index) defined by _url field
result = client.search({'_url': '__URL_PATH_TO_IMAGE__'}, k=5)

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
result = client.get_records([{'_id': '__ITEM_ID__'}, {'_id': '__ITEM_ID__'}])

# insert item tot he index with your _id, and onr of _url | _base64, and other fields (meta-info) which you can 
# then use when applying filter in search or random menthods
result = client.insert([{'_id': '__ITEM_ID__', '_url': '__URL_PATH_TO_IMAGE__',
                         'meta-category-x': '__CATEGORY_OF_ITEM__',
                         'meta-info-y': '__ANOTHER_META_INFO__'}])

# delete item from id
result = client.remove([{'_id': '__ITEM_ID__'}])

# update item in index with all additional fields and meta-info
result = client.update([{'_id': '__ITEM_ID__', 'some-additional-field': '__VALUE__'}])
```

## Custom Similarity

This service let you train your custom image similarity model.

Creating entities is similar to recognition or detection service.

```python
from ximilar.client.similarity import CustomSimilarityClient
client = CustomSimilarityClient("__API__TOKEN__")
tasks, _ = client.get_all_tasks()

task, _ = client.create_task("__NAME__",  "__DESCRIPTION__")
type1, _ = client.create_type("__NAME__", "__DESCRIPTION__")
group, _ = client.create_group("__NAME__", "__DESCRIPTION__", type1.id)
```

Add/Remove types to/from task:

```python
task.add_type(type1.id)
task.remove_type(type1.id)
```

Add/Remove images to/from group:

```python
group.add_images(["__IMAGE_ID_1__"])
group.remove_images(["__IMAGE_ID_1__"])
group.refresh()
```

Add/Remove groups to/from group:

```python
group.add_groups(["__GROUP_ID_1__"])
group.remove_groups(["__GROUP_ID_1__"])
group.refresh()
```

Set unset group as test (test flag is for evaluation dataset):

```python
group.set_test(True) # or False if unsetting from eval dataset
group.refresh()
```

Searching groups with name:

```python
client.get_all_groups_by_name("__NAME__")
```

# Tools

In our `tools` folder you can find some useful scripts for:

* `uploader.py` for uploading all images from specific folder
* `data_saver.py` for saving entire recognition and detection workspace including images
* `data_wiper.py` for removing entire workspace and all your data in workspace
* `detection_cutter.py` cutting objects from images
