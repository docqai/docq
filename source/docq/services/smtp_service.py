"""SMTP Service === For sending verification emails to users."""
import base64
import hashlib
import logging as log
import os
import smtplib
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import quote_plus

SENDER_EMAIL_KEY = "DOCQ_SMTP_LOGIN"
SMTP_PORT_KEY = "DOCQ_SMTP_PORT"
SMTP_PASSWORD_KEY = "DOCQ_SMTP_KEY"
SMTP_SERVER_KEY = "DOCQ_SMTP_SERVER"
SERVER_ADDRESS_KEY = "DOCQ_SERVER_ADDRESS"
SMTP_SENDER_EMAIL_KEY = "DOCQ_SMTP_FROM"

VERIFICATION_EMAIL_TEMPLATE = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office"><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"><meta http-equiv="X-UA-Compatible" content="IE=edge"><meta name="format-detection" content="telephone=no"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{{ subject }}</title><style type="text/css" emogrify="no">#outlook a { padding:0; } .ExternalClass { width:100%; } .ExternalClass, .ExternalClass p, .ExternalClass span, .ExternalClass font, .ExternalClass td, .ExternalClass div { line-height: 100%; } table td { border-collapse: collapse; mso-line-height-rule: exactly; } .editable.image { font-size: 0 !important; line-height: 0 !important; } .nl2go_preheader { display: none !important; mso-hide:all !important; mso-line-height-rule: exactly; visibility: hidden !important; line-height: 0px !important; font-size: 0px !important; } body { width:100% !important; -webkit-text-size-adjust:100%; -ms-text-size-adjust:100%; margin:0; padding:0; } img { outline:none; text-decoration:none; -ms-interpolation-mode: bicubic; } a img { border:none; } table { border-collapse:collapse; mso-table-lspace:0pt; mso-table-rspace:0pt; } th { font-weight: normal; text-align: left; } *[class="gmail-fix"] { display: none !important; } </style><style type="text/css" emogrify="no"> @media (max-width: 600px) { .gmx-killpill { content: ' \03D1';} } </style><style type="text/css" emogrify="no">@media (max-width: 600px) { .gmx-killpill { content: ' \03D1';} .r0-o { border-style: solid !important; margin: 0 auto 0 auto !important; width: 320px !important } .r1-c { box-sizing: border-box !important; text-align: center !important; valign: top !important; width: 100% !important } .r2-o { border-style: solid !important; margin: 0 auto 0 auto !important; width: 100% !important } .r3-i { background-color: #0c8f19 !important; padding-bottom: 20px !important; padding-left: 15px !important; padding-right: 15px !important; padding-top: 20px !important } .r4-c { box-sizing: border-box !important; display: block !important; valign: top !important; width: 100% !important } .r5-o { border-style: solid !important; width: 100% !important } .r6-i { padding-left: 0px !important; padding-right: 0px !important } .r7-i { padding-bottom: 0px !important; padding-left: 1px !important; padding-right: 0px !important; padding-top: 0px !important } .r8-c { box-sizing: border-box !important; text-align: left !important; valign: top !important; width: 100% !important } .r9-o { border-style: solid !important; margin: 0 auto 0 0 !important; width: 100% !important } .r10-i { padding-bottom: 0px !important; padding-top: 31px !important; text-align: left !important } .r11-i { background-color: #ececec !important; padding-bottom: 20px !important; padding-left: 10px !important; padding-right: 10px !important; padding-top: 20px !important } .r12-i { padding-bottom: 15px !important; padding-left: 8px !important; padding-right: 8px !important; padding-top: 15px !important; text-align: left !important } .r13-c { box-sizing: border-box !important; padding: 0 !important; text-align: center !important; valign: top !important; width: 100% !important } .r14-o { border-style: solid !important; margin: 0 auto 0 auto !important; margin-bottom: 15px !important; margin-top: 15px !important; width: 100% !important } .r15-i { padding: 0 !important; text-align: center !important } .r16-r { background-color: #0c8f19 !important; border-radius: 4px !important; border-width: 0px !important; box-sizing: border-box; height: initial !important; padding: 0 !important; padding-bottom: 12px !important; padding-left: 5px !important; padding-right: 5px !important; padding-top: 12px !important; text-align: center !important; width: 100% !important } .r17-c { box-sizing: border-box !important; text-align: center !important; width: 100% !important } .r18-c { box-sizing: border-box !important; width: 100% !important } .r19-i { font-size: 0px !important; padding-bottom: 15px !important; padding-left: 105px !important; padding-right: 105px !important; padding-top: 15px !important } .r20-c { box-sizing: border-box !important; width: 32px !important } .r21-o { border-style: solid !important; margin-right: 8px !important; width: 32px !important } .r22-i { padding-bottom: 5px !important; padding-top: 5px !important } .r23-o { border-style: solid !important; margin-right: 0px !important; width: 32px !important } body { -webkit-text-size-adjust: none } .nl2go-responsive-hide { display: none } .nl2go-body-table { min-width: unset !important } .mobshow { height: auto !important; overflow: visible !important; max-height: unset !important; visibility: visible !important; border: none !important } .resp-table { display: inline-table !important } .magic-resp { display: table-cell !important } } </style><!--[if !mso]><!--><style type="text/css" emogrify="no">@import url("https://fonts.googleapis.com/css2?family=Manrope"); </style><!--<![endif]--><style type="text/css">p, h1, h2, h3, h4, ol, ul { margin: 0; } a, a:link { color: #111119; text-decoration: underline } .nl2go-default-textstyle { color: #3b3f44; font-family: arial,helvetica,sans-serif; font-size: 18px; line-height: 1.5; word-break: break-word } .default-button { color: #ffffff; font-family: arial,helvetica,sans-serif; font-size: 16px; font-style: normal; font-weight: bold; line-height: 1.15; text-decoration: none; word-break: break-word } .default-heading1 { color: #1F2D3D; font-family: Manrope, Arial; font-size: 36px; word-break: break-word } .default-heading2 { color: #1F2D3D; font-family: Manrope, Arial; font-size: 32px; word-break: break-word } .default-heading3 { color: #1F2D3D; font-family: Manrope, Arial; font-size: 24px; word-break: break-word } .default-heading4 { color: #1F2D3D; font-family: Manrope, Arial; font-size: 18px; word-break: break-word } a[x-apple-data-detectors] { color: inherit !important; text-decoration: inherit !important; font-size: inherit !important; font-family: inherit !important; font-weight: inherit !important; line-height: inherit !important; } .no-show-for-you { border: none; display: none; float: none; font-size: 0; height: 0; line-height: 0; max-height: 0; mso-hide: all; overflow: hidden; table-layout: fixed; visibility: hidden; width: 0; } </style><!--[if mso]><xml> <o:OfficeDocumentSettings> <o:AllowPNG/> <o:PixelsPerInch>96</o:PixelsPerInch> </o:OfficeDocumentSettings> </xml><![endif]--><style type="text/css">a:link{color: #111119; text-decoration: underline;}</style></head><body text="#3b3f44" link="#111119" yahoo="fix"> <table cellspacing="0" cellpadding="0" border="0" role="presentation" class="nl2go-body-table" width="100%" style="width: 100%;"><tr><td> <table cellspacing="0" cellpadding="0" border="0" role="presentation" width="600" align="center" class="r0-o" style="table-layout: fixed; width: 600px;"><tr><td valign="top"> <table cellspacing="0" cellpadding="0" border="0" role="presentation" width="100%" align="center" class="r2-o" style="table-layout: fixed; width: 100%;"><tr><td class="r3-i" style="background-color: #0c8f19; padding-bottom: 20px; padding-top: 20px;"> <table width="100%" cellspacing="0" cellpadding="0" border="0" role="presentation"><tr><th width="16.67%" valign="top" class="r4-c" style="font-weight: normal;"> <table cellspacing="0" cellpadding="0" border="0" role="presentation" width="100%" class="r5-o" style="table-layout: fixed; width: 100%;"><tr><td valign="top" class="r6-i" style="padding-left: 15px; padding-right: 15px;"> <table width="100%" cellspacing="0" cellpadding="0" border="0" role="presentation"><tr><td class="r1-c" align="center"> <table cellspacing="0" cellpadding="0" border="0" role="presentation" width="100" class="r2-o" style="table-layout: fixed; width: 100px;"><tr><td style="font-size: 0px; line-height: 0px;"> <a href="https://docq.ai" target="_blank" style="color: #111119; text-decoration: underline;"> <img src="https://img.mailinblue.com/6626458/images/content_library/original/65309deb204dd208896388b3.jpg" width="100" border="0" style="display: block; width: 100%;"></a> </td> </tr></table></td> </tr></table></td> </tr></table></th> <th width="83.33%" valign="top" class="r4-c" style="font-weight: normal;"> <table cellspacing="0" cellpadding="0" border="0" role="presentation" width="100%" class="r5-o" style="table-layout: fixed; width: 100%;"><tr><td valign="top" class="r7-i" style="padding-left: 16px; padding-right: 15px;"> <table width="100%" cellspacing="0" cellpadding="0" border="0" role="presentation"><tr><td class="r8-c" align="left"> <table cellspacing="0" cellpadding="0" border="0" role="presentation" width="100%" class="r9-o" style="table-layout: fixed; width: 100%;"><tr><td align="left" valign="top" class="r10-i nl2go-default-textstyle" style="color: #3b3f44; font-family: arial,helvetica,sans-serif; font-size: 18px; word-break: break-word; line-height: 1.5; padding-top: 31px; text-align: left;"> <div><h3 class="default-heading3" style="margin: 0; color: #1f2d3d; font-family: Manrope,Arial; font-size: 24px; word-break: break-word;"><span style="color: #ffffff;">{{ subject }}</span></h3></div> </td> </tr></table></td> </tr></table></td> </tr></table></th> </tr></table></td> </tr></table><table cellspacing="0" cellpadding="0" border="0" role="presentation" width="100%" align="center" class="r2-o" style="table-layout: fixed; width: 100%;"><tr><td class="r11-i" style="background-color: #ececec; padding-bottom: 20px; padding-top: 20px;"> <table width="100%" cellspacing="0" cellpadding="0" border="0" role="presentation"><tr><th width="100%" valign="top" class="r4-c" style="font-weight: normal;"> <table cellspacing="0" cellpadding="0" border="0" role="presentation" width="100%" class="r5-o" style="table-layout: fixed; width: 100%;"><tr><td valign="top" class="r6-i"> <table width="100%" cellspacing="0" cellpadding="0" border="0" role="presentation"><tr><td class="r8-c" align="left"> <table cellspacing="0" cellpadding="0" border="0" role="presentation" width="100%" class="r9-o" style="table-layout: fixed; width: 100%;"><tr><td align="left" valign="top" class="r12-i nl2go-default-textstyle" style="color: #3b3f44; font-family: arial,helvetica,sans-serif; font-size: 18px; line-height: 1.5; word-break: break-word; padding-bottom: 15px; padding-left: 8px; padding-right: 8px; padding-top: 15px; text-align: left;"> <div><p style="margin: 0;">Hello {{ name }},</p></div> </td> </tr></table></td> </tr><tr><td class="r8-c" align="left"> <table cellspacing="0" cellpadding="0" border="0" role="presentation" width="100%" class="r9-o" style="table-layout: fixed; width: 100%;"><tr><td align="left" valign="top" class="r12-i nl2go-default-textstyle" style="color: #3b3f44; font-family: arial,helvetica,sans-serif; font-size: 18px; line-height: 1.5; word-break: break-word; padding-bottom: 15px; padding-left: 8px; padding-right: 8px; padding-top: 15px; text-align: left;"> <div><p style="margin: 0;">Thank you for signing up for Docq.AI! To complete your registration,<br>please click the button below to verify your email address.</p></div> </td> </tr></table></td> </tr><tr><td class="r13-c" align="center" style="align: center; padding-bottom: 15px; padding-top: 15px; valign: top;"> <table cellspacing="0" cellpadding="0" border="0" role="presentation" width="300" class="r14-o" style="background-color: #0c8f19; border-collapse: separate; border-color: #0c8f19; border-radius: 4px; border-style: solid; border-width: 0px; table-layout: fixed; width: 300px;"><tr><td height="18" align="center" valign="top" class="r15-i nl2go-default-textstyle" style="word-break: break-word; background-color: #0c8f19; border-radius: 4px; color: #ffffff; font-family: arial,helvetica,sans-serif; font-size: 16px; font-style: normal; line-height: 1.15; padding-bottom: 12px; padding-left: 5px; padding-right: 5px; padding-top: 12px; text-align: center;"> <a href="{{ verification_url }}" class="r16-r default-button" target="_blank" data-btn="1" style="font-style: normal; font-weight: bold; line-height: 1.15; text-decoration: none; word-break: break-word; word-wrap: break-word; display: block; -webkit-text-size-adjust: none; color: #ffffff; font-family: arial,helvetica,sans-serif; font-size: 16px;"> <span>Verify Email</span></a> </td> </tr></table></td> </tr><tr><td class="r8-c" align="left"> <table cellspacing="0" cellpadding="0" border="0" role="presentation" width="100%" class="r9-o" style="table-layout: fixed; width: 100%;"><tr><td align="left" valign="top" class="r12-i nl2go-default-textstyle" style="color: #3b3f44; font-family: arial,helvetica,sans-serif; font-size: 18px; line-height: 1.5; word-break: break-word; padding-bottom: 15px; padding-left: 8px; padding-right: 8px; padding-top: 15px; text-align: left;"> <div><p style="margin: 0;">If you did not signup for docq, please ignore this email.</p></div> </td> </tr></table></td> </tr></table></td> </tr></table></th> </tr></table></td> </tr></table><table cellspacing="0" cellpadding="0" border="0" role="presentation" width="100%" align="center" class="r2-o" style="table-layout: fixed; width: 100%;"><tr><td class="r3-i" style="background-color: #0c8f19; padding-bottom: 20px; padding-top: 20px;"> <table width="100%" cellspacing="0" cellpadding="0" border="0" role="presentation"><tr><th width="100%" valign="top" class="r4-c" style="font-weight: normal;"> <table cellspacing="0" cellpadding="0" border="0" role="presentation" width="100%" class="r5-o" style="table-layout: fixed; width: 100%;"><tr><td valign="top" class="r6-i" style="padding-left: 15px; padding-right: 15px;"> <table width="100%" cellspacing="0" cellpadding="0" border="0" role="presentation"><tr><td class="r17-c" align="center"> <table cellspacing="0" cellpadding="0" border="0" role="presentation" width="570" align="center" class="r2-o" style="table-layout: fixed; width: 570px;"><tr><td valign="top"> <table width="100%" cellspacing="0" cellpadding="0" border="0" role="presentation"><tr><td class="r18-c" style="display: inline-block;"> <table cellspacing="0" cellpadding="0" border="0" role="presentation" width="570" class="r5-o" style="table-layout: fixed; width: 570px;"><tr><td class="r19-i" style="padding-bottom: 15px; padding-left: 249px; padding-right: 249px; padding-top: 15px;"> <table width="100%" cellspacing="0" cellpadding="0" border="0" role="presentation"><tr><th width="40" class="r20-c mobshow resp-table" style="font-weight: normal;"> <table cellspacing="0" cellpadding="0" border="0" role="presentation" width="100%" class="r21-o" style="table-layout: fixed; width: 100%;"><tr><td class="r22-i" style="font-size: 0px; line-height: 0px; padding-bottom: 5px; padding-top: 5px;"> <a href="https://github.com/docqai" target="_blank" style="color: #111119; text-decoration: underline;"> <img src="https://creative-assets.mailinblue.com/editor/social-icons/squared_colored/github_32px.png" width="32" border="0" style="display: block; width: 100%;"></a> </td> <td class="nl2go-responsive-hide" width="8" style="font-size: 0px; line-height: 1px;">­ </td> </tr></table></th> <th width="32" class="r20-c mobshow resp-table" style="font-weight: normal;"> <table cellspacing="0" cellpadding="0" border="0" role="presentation" width="100%" class="r23-o" style="table-layout: fixed; width: 100%;"><tr><td class="r22-i" style="font-size: 0px; line-height: 0px; padding-bottom: 5px; padding-top: 5px;"> <a href="https://twitter.com/docqai" target="_blank" style="color: #111119; text-decoration: underline;"> <img src="https://creative-assets.mailinblue.com/editor/social-icons/squared_colored/twitter_32px.png" width="32" border="0" style="display: block; width: 100%;"></a> </td> </tr></table></th> </tr></table></td> </tr></table></td> </tr></table></td> </tr></table></td> </tr></table></td> </tr></table></th> </tr></table></td> </tr></table></td> </tr></table></td> </tr></table></body></html>
"""


def _get_verification_email_template(**kwargs: dict) -> str:
    """Get email template."""
    template = VERIFICATION_EMAIL_TEMPLATE
    for key, value in kwargs.items():
        template = template.replace("{{ " + key + " }}", value)
    return template


def _send_email(
    sender_email: str,
    recipients: list[str],
    subject: str,
    message: str,
    smtp_server: str,
    smtp_port: int,
    username: str,
    password: str,
    attachments: list[str] = None,
) -> None:
    """Send an email."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = ', '.join(recipients)
        msg.attach(MIMEText(message, "html"))

        if attachments:
            for attachment in attachments:
                with open(attachment, "rb") as f:
                    part = MIMEApplication(f.read(), Name=attachment.split("/")[-1])
                    part["Content-Disposition"] = f'attachment; filename="{attachment.split("/")[-1]}"'
                    msg.attach(part)

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(sender_email, recipients, msg.as_string())

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
    username = os.environ.get(SENDER_EMAIL_KEY)
    smtp_port = os.environ.get(SMTP_PORT_KEY)
    smtp_password = os.environ.get(SMTP_PASSWORD_KEY)
    smtp_server = os.environ.get(SMTP_SERVER_KEY)
    sender_email = os.environ.get(SMTP_SENDER_EMAIL_KEY)

    subject = "Docq.AI Sign-up - Email Verification"
    message = _get_verification_email_template(
        name=name,
        subject=subject,
        verification_url=_generate_verification_url(user_id)
    )

    _send_email(
        sender_email=sender_email,
        recipients=[reciever_email],
        subject=subject,
        message=message,
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        username=username,
        password=smtp_password,
    )


def mailer_ready() -> bool:
    """Check if the mailer is ready."""
    return all(
        [
            os.environ.get(SENDER_EMAIL_KEY),
            os.environ.get(SMTP_PORT_KEY),
            os.environ.get(SMTP_PASSWORD_KEY),
            os.environ.get(SMTP_SERVER_KEY),
            os.environ.get(SERVER_ADDRESS_KEY),
            os.environ.get(SMTP_SENDER_EMAIL_KEY),
        ]
    )
