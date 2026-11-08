import smtplib
from email.message import EmailMessage

from ..config import settings

VERIFY_PLAIN = """Hi {name},

Please verify your MyShop account by opening this link:

<{link}>

The link expires in 24 hours. If you didn't create this account, ignore this email.

Trouble with the button? The link is bracketed in < > so your mail app
doesn't wrap it into two lines — copy the whole thing if needed.
"""

VERIFY_HTML = """\
<html><body style="font-family:sans-serif;line-height:1.5">
  <h2>Welcome to MyShop</h2>
  <p>Hi {name},</p>
  <p>Click the button to verify your email address:</p>
  <p><a href="{link}"
        style="display:inline-block;padding:12px 22px;background:#0f766e;color:#fff;
               text-decoration:none;border-radius:8px;font-weight:600">
      Verify my email
   </a></p>
  <p style="color:#71716c;font-size:13px">
    Or paste this link into your browser:<br>
    <a href="{link}">{link}</a>
  </p>
  <p style="color:#71716c;font-size:13px">Link expires in 24 hours. Didn't sign up? Ignore this email.</p>
</body></html>
"""


class MailServiceUnavailable(Exception):
    pass


def _smtp_send(msg: EmailMessage) -> None:
    # Local dev default = MailHog on localhost:1025. For real email:
    # point SMTP_* at your provider (Gmail: host smtp.gmail.com, port 587,
    # a login + app password, and SMTP_USE_TLS=true).
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
        smtp.ehlo()
        if settings.SMTP_USE_TLS:
            smtp.starttls()
            smtp.ehlo()
        if settings.SMTP_USER and settings.SMTP_PASS:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASS)
        smtp.send_message(msg)


def send_verification_email(to_email: str, name: str, verify_link: str) -> None:
    """Raises on failure — callers decide whether to swallow (register) or wait (resend)."""
    msg = EmailMessage()
    msg["Subject"] = "Verify your MyShop email"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.set_content(VERIFY_PLAIN.format(name=name, link=verify_link))
    msg.add_alternative(VERIFY_HTML.format(name=name, link=verify_link))
    _smtp_send(msg)


def get_transport_name() -> str:
    return f"{settings.SMTP_HOST}:{settings.SMTP_PORT}"
