from mailchimp3 import MailChimp

from vize.api import VizeRestClient, Task, Image, Label


# MAILCHIMP INTEGRATION
MAILCHIMP_API_KEY = '50d3c6291b65e624c76c57bb597e7078-us18'
MAILCHIMP_SUBSCRIBE_LIST_ID = '1cf8f98eda'


client = MailChimp(MAILCHIMP_API_KEY)

client.lists.members.create(MAILCHIMP_SUBSCRIBE_LIST_ID, {
    'email_address': 'bejvisek@seznam.cz',
    'status': 'subscribed',
    'merge_fields': {
        'FNAME': 'David',
        'LNAME': 'Novak',
    },
})

# task = client.get_task(task_id='5136c465-2b3b-4ae5-b005-0205a2cea5f5')
#task.train()

