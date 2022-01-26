import base64
import json
import logging
import mimetypes
import email.encoders as encoder
import socket
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.core.mail.backends.smtp import EmailBackend

logger = logging.getLogger(__name__)


class GmailApiBackend(EmailBackend):
    def __init__(
            self,
            fail_silently=False,
            **kwargs
    ):
        super().__init__(fail_silently=fail_silently)

        self.connection = build('gmail', 'v1', cache_discovery=False, credentials=get_credentials())

    def send_messages(self, email_messages):
        new_conn_created = self.open()
        if not self.connection or new_conn_created is None:
            return 0
        num_sent = 0
        for email_message in email_messages:
            message = create_message(email_message)
            sent = self._send(message)
            if sent:
                num_sent += 1
        if new_conn_created:
            self.close()

        return num_sent

    def _send(self, email_message):
        try:
            self.connection.users().messages().send(userId='me', body=email_message).execute()
        except Exception as error:
            logger.error('Error sending email', error)
            if settings.EMAIL_BACKEND and settings.EMAIL_BACKEND == "mailer.backend.DbBackend":
                # If using "django-mailer" https://github.com/pinax/django-mailer, tt marks the related message as
                # deferred only for some exceptions, so we raise one of them to save the error on the db
                raise socket.error(error)
            else:
                raise
        return True


def get_credentials():
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(settings.GOOGLE_SERVICE_ACCOUNT), scopes=settings.GMAIL_SCOPES, subject=settings.EMAIL_FROM)
    return credentials


def create_message(email_message):
    if email_message.attachments:
        message = MIMEMultipart()
        msg = MIMEText(email_message.body, email_message.content_subtype)
        message.attach(msg)
    else:
        message = MIMEText(email_message.body, email_message.content_subtype)
    message['to'] = ','.join(map(str, email_message.to))
    message['from'] = email_message.from_email
    if email_message.reply_to:
        message['reply-to'] = ','.join(map(str, email_message.reply_to))
    if email_message.cc:
        message['cc'] = ','.join(map(str, email_message.cc))
    if email_message.bcc:
        message['bcc'] = ','.join(map(str, email_message.bcc))
    message['subject'] = str(email_message.subject)

    if email_message.attachments:
        for attachment in email_message.attachments:
            content_type, encoding = mimetypes.guess_type(attachment[0])
            if content_type is None or encoding is not None:
                content_type = 'application/octet-stream'
            main_type, sub_type = content_type.split('/', 1)
            if main_type == 'text':
                fp = open(attachment[1], 'rb')
                msg = MIMEText(fp.read(), _subtype=sub_type)
                fp.close()
            elif main_type == 'image':
                fp = open(attachment[1], 'rb')
                msg = MIMEImage(fp.read(), _subtype=sub_type)
                fp.close()
            elif main_type == 'audio':
                fp = open(attachment[1], 'rb')
                msg = MIMEAudio(fp.read(), _subtype=sub_type)
                fp.close()
            elif type(attachment[1]) is bytes:
                msg = MIMEBase(main_type, sub_type)
                msg.set_payload(attachment[1])
            else:
                fp = open(attachment[1], 'rb')
                msg = MIMEBase(main_type, sub_type)
                msg.set_payload(fp.read())
                fp.close()

            filename = attachment[0]

            msg.add_header('Content-Disposition', 'attachment', filename=filename)
            encoder.encode_base64(msg)
            message.attach(msg)

    b64_bytes = base64.urlsafe_b64encode(message.as_bytes())
    b64_string = b64_bytes.decode()
    return {'raw': b64_string}
