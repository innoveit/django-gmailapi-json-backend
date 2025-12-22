import base64
import json
import logging
import socket

from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend

logger = logging.getLogger(__name__)


class GmailApiBackend(EmailBackend):
    def __init__(
            self,
            fail_silently=False,
            google_service_account=None,
            gmail_scopes=None,
            gmail_user=None,
            **kwargs
    ):
        super().__init__(fail_silently=fail_silently)
        
        self.google_service_account = settings.GOOGLE_SERVICE_ACCOUNT if google_service_account is None else google_service_account
        self.gmail_scopes = gmail_scopes if gmail_scopes else (settings.GMAIL_SCOPES if settings.GMAIL_SCOPES else 'https://www.googleapis.com/auth/gmail.send')
        self.gmail_user = settings.GMAIL_USER if gmail_user is None else gmail_user
        self.connection = None
        self.open()

    def open(self):
        if self.connection: return False
        try:
            # Lazy imports so library users can import this module (and unit-test create_message)
            # without needing Google client dependencies unless actually opening a Gmail connection.
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            credentials = service_account.Credentials.from_service_account_info(json.loads(
                self.google_service_account), scopes=self.gmail_scopes, subject=self.gmail_user)
            self.connection = build('gmail', 'v1', cache_discovery=False, credentials=credentials)
            return True
        except:
            if not self.fail_silently:
                raise
    
    def close(self):
        if self.connection is None: return
        try:
            self.connection.close()
            self.connection = None
        except:
            self.connection = None
            if self.fail_silently:
                return
            raise

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

        return num_sent

    def _send(self, email_message):
        try:
            self.connection.users().messages().send(userId=self.gmail_user, body=email_message).execute()
        except Exception as error:
            logger.error('Error sending email', error)
            if settings.EMAIL_BACKEND and settings.EMAIL_BACKEND == "mailer.backend.DbBackend":
                # If using "django-mailer" https://github.com/pinax/django-mailer, tt marks the related message as
                # deferred only for some exceptions, so we raise one of them to save the error on the db
                raise socket.error(error)
            else:
                if not self.fail_silently:
                    raise
                return False
        return True


def create_message(email_message):
    # Let Django build the RFC822/MIME message. This preserves multipart/alternative
    # (EmailMultiAlternatives), correct headers encoding, and attachment handling.
    message = email_message.message()
    # Django's SMTP backend uses the envelope to deliver BCC recipients without adding a header.
    # Gmail API doesn't have an envelope; recipients must be present in the raw message headers.
    if getattr(email_message, "bcc", None) and "Bcc" not in message:
        message["Bcc"] = ",".join(map(str, email_message.bcc))

    b64_bytes = base64.urlsafe_b64encode(message.as_bytes())
    b64_string = b64_bytes.decode()
    return {'raw': b64_string}
