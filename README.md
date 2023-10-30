# django-gmailapi-json-backend
[![PyPI version](https://badge.fury.io/py/django-gmailapi-json-backend.svg)](https://badge.fury.io/py/django-gmailapi-json-backend)
[![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/release/python-390)
[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-310)


Email backend for Django which sends email via the Gmail API through a JSON credential

The simple SMTP protocol is disabled by default for Gmail users, since this is included in the Less Secure Apps (LSA) category.
This package implements the Gmail API directly with a JSON Google service account as a Django email backend and can be used with 'django-mailer'.

## Requirements
Python 3.9+

## Installation
The package is available through pip. To easily install or upgrade it, do
```
pip install --upgrade django-gmailapi-json-backend
```

## Configuration
In your `settings.py`:
1. Add the module into the INSTALLED_APPS
    ```py
    INSTALLED_APPS = [
        ...
        'gmailapi_backend',
        ...
    ]
    ```
2. Set the email backend
    ```py
   EMAIL_FROM = 'Company<your-email@domain.com>'
   GMAIL_USER = 'your-email@domain.com'
   EMAIL_BACKEND = "gmailapi_backend.service.GmailApiBackend"
   GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']
   GOOGLE_SERVICE_ACCOUNT = '{
         "type": "service_account",
         "project_id": "your-project",
         "private_key_id": 
         ...
   }'
    ```
   If you use *django-mailer* as email backend you can send through gmail API as follow:
    ```py
   EMAIL_BACKEND = "mailer.backend.DbBackend"
   MAILER_EMAIL_BACKEND = "gmailapi_backend.service.GmailApiBackend"
    ```

## How to create the Google service account 
1. Create a project on the developer console at https://console.cloud.google.com (it must be a Google Workspace account, not a simple gmail account)
2. Enable the gmail api from the library menu
3. On API and services > Credentials, create a new service account as a JSON you should use for GOOGLE_SERVICE_ACCOUNT
4. Copy your *client id* from the menu IAM and administration > service account. Click on the service you have just created, find the unique id and copy it.
5. Move to the administrator console at https://admin.google.com/ and choose your user (i.e. EMAIL_FROM)
6. Go to Security > Data access and control > API controls > Delegation at domain level and add a new one with your *client id* and the services you need like *https://www.googleapis.com/auth/gmail.send* to send email through API.


## Usage
Use the native `EmailMessage` class in Django. Just a sample:
```py
message = render_to_string('email/ordine_pagato.html', {
  'ordine': ordine,
})
mail_subject = _('This is just a sample')
email = EmailMessage(
  mail_subject, message, settings.EMAIL_FROM, to=['recipient@domain.com']
)
email.content_subtype = "html"
email.attach(sample_file.file.name, sample_file.file.read(), 'application/pdf')
email.send()
```
