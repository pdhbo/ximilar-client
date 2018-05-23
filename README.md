# VIZE.AI API Python Client

This Python Client library is simple wrapper for vize.ai.

You can use this library to enhance your application with vize.ai.

## Installation

    pip install git@gitlab.com:ximilar-public/ximilar-vize-api.git

This will install also python-opencv, requests and pprint library.

##  Usage

First you need to obtain your api token for communication with vize rest endpoints. You can obtain the token from the vize.ai administration page. After you obtain the token the usage is quite straightforward. First import this package and create the rest client.

```python
from vize.api.rest_client import VizeRestClient
    
client = VizeRestClient(token='your-api-token')
```

After creating client object you can for example load your existing task:

```python
task = client.get_task(task_id='your-identification-of-task')
```

#### Classify

Suppose you want to use the task to predict the result on your image. Always try to send us image bigger than 200px and lower than 600px for speed and performance:

```python
result_v1 = task.classify_v1({'_url': 'www.example.com/1.jpg'})
result_v2 = task.classify_v2([{'_url': 'www.example.com/1.jpg'}])
```

The result is in json/dictionary format and you can access it like this(depends on which version of classify you use):

```python
best_label_v1 = result_v1['best_label']
best_label_v2 = result_v2['records'][0]['best_label']
```

There is an option to send also file from your local storage. Internally it will convert and send base64 image representation.

```python
result_v1 = task.classify_v2([{'_file': 'c:/test.jpg'}])
```

#### Working with Task

To list all tasks you can use this:

```python
tasks = client.get_all_tasks()
```

Creating new task:

```python
task = client.create_new_task()
```

Delete existing task:
 
 ```python
client.delete_task('task_id')
```

#### Working with Labels

To create new label and add this label to task:

```python
label = client.create_label()
task = task.add_label(label)
```

To get all labels of given task use:

```python
labels = task.get_labels()

for label in labels:
    print(label.id, label.name)
```

To get list of all images of label use:

```python
images = label.get_all_images()
```

#### Working with images

Uploading image is quite straightforward with combination of existing labels:

```python
image = client.upload_image({'_url': 'www.example.com/1.jpg'}, labels=labels)
```

Deleting image:

```python
client.remove_image(image)
```

#### Start training of Task

```python
training = task.start_training()
```
