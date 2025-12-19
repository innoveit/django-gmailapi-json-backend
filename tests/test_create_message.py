import base64
from email import policy
from email.parser import BytesParser

from django.core.mail import EmailMultiAlternatives

from gmailapi_backend.service import create_message


def _parse_raw_payload(raw: str):
    raw_bytes = base64.urlsafe_b64decode(raw.encode("utf-8"))
    return BytesParser(policy=policy.default).parsebytes(raw_bytes)


def test_create_message_preserves_multipart_alternative():
    email = EmailMultiAlternatives(
        subject="Subject",
        body="Plain body",
        from_email="from@example.com",
        to=["to@example.com"],
    )
    email.attach_alternative("<p>HTML body</p>", "text/html")

    payload = create_message(email)
    msg = _parse_raw_payload(payload["raw"])

    assert msg.get_content_type() == "multipart/alternative"

    parts = [p for p in msg.walk() if p.get_content_maintype() != "multipart"]
    content_types = {p.get_content_type() for p in parts}
    assert "text/plain" in content_types
    assert "text/html" in content_types

    plain = next(p for p in parts if p.get_content_type() == "text/plain")
    html = next(p for p in parts if p.get_content_type() == "text/html")
    assert "Plain body" in plain.get_content()
    assert "<p>HTML body</p>" in html.get_content()


def test_create_message_with_attachment_and_alternative():
    email = EmailMultiAlternatives(
        subject="Subject",
        body="Plain body",
        from_email="from@example.com",
        to=["to@example.com"],
    )
    email.attach_alternative("<p>HTML body</p>", "text/html")
    email.attach("hello.txt", "HELLO", "text/plain")

    payload = create_message(email)
    msg = _parse_raw_payload(payload["raw"])

    # With attachments, Django builds multipart/mixed with a multipart/alternative subpart.
    assert msg.get_content_type() == "multipart/mixed"

    parts = [p for p in msg.walk() if p.get_content_maintype() != "multipart"]
    attachment = next(p for p in parts if p.get_filename() == "hello.txt")
    assert attachment.get_content_disposition() == "attachment"
    assert "HELLO" in attachment.get_content()


def test_create_message_includes_bcc_header_for_gmail_api_delivery():
    email = EmailMultiAlternatives(
        subject="Subject",
        body="Plain body",
        from_email="from@example.com",
        to=["to@example.com"],
        bcc=["bcc1@example.com", "bcc2@example.com"],
    )
    payload = create_message(email)
    msg = _parse_raw_payload(payload["raw"])

    assert "Bcc" in msg
    assert "bcc1@example.com" in msg["Bcc"]
    assert "bcc2@example.com" in msg["Bcc"]


