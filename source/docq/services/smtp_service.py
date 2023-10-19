"""SMTP Service === For sending verification emails to users."""
import base64
import hashlib
import logging as log
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import quote_plus

SENDER_EMAIL_KEY = "SMTP_LOGIN"
SMTP_PORT_KEY = "SMTP_PORT"
SMTP_PASSWORD_KEY = "SMTP_KEY"
SMTP_SERVER_KEY = "SMTP_SERVER"
SERVER_ADDRESS_KEY = "SERVER_ADDRESS"


def _get_email_template() -> str:
    directory = os.path.dirname(os.path.abspath(__file__))
    template = os.path.join(directory, "email-template.html")
    with open(template, "r") as f:
        return f.read()

def _send_email(
    sender_email: str,
    receiver_email: str,
    subject: str,
    message: str,
    smtp_server: str,
    smtp_port: int,
    username: str,
    password: str,
) -> None:
    """Send an email."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg.attach(MIMEText(message, "plain"))
        text = msg.as_string()
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
    except Exception as e:
        log.exception("SMTP send_verification_email error: %s", e)


def _generate_verification_url(user_id: int) -> str:
    """Generate a verification URL."""
    server_address = os.environ.get(SERVER_ADDRESS_KEY)
    timestamp = datetime.now().timestamp()
    stringparam = f"{user_id}::{timestamp}"
    hash_ = hashlib.sha256(stringparam.encode("utf-8")).hexdigest()
    query_param = quote_plus(base64.b64encode(f"{user_id}::{timestamp}::{hash_}".encode("utf-8")))
    return f"{server_address}/verify?token={query_param}"


def send_verification_email(reciever_email: str, name: str, user_id: int) -> None:
    """Send verification email."""
    sender_email = os.environ.get(SENDER_EMAIL_KEY)
    smtp_port = os.environ.get(SMTP_PORT_KEY)
    smtp_password = os.environ.get(SMTP_PASSWORD_KEY)
    smtp_server = os.environ.get(SMTP_SERVER_KEY)

    subject = "Docq.AI Sign-up - Email Verification"
    message = _get_email_template()
    message = message.replace("{{ doubleoptin }}", _generate_verification_url(user_id))
    _send_email(
        sender_email=sender_email,
        receiver_email=reciever_email,
        subject=subject,
        message=message,
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        username=sender_email,
        password=smtp_password,
    )
