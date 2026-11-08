import smtplib
from email.message import EmailMessage

from ..config import settings

CODE_PLAIN = """Hi {name},

Your MyShop verification code is:

    {code}

It expires in 10 minutes. If you didn't create this account, ignore this email.
"""

CODE_HTML = """\
<html><body style="font-family:sans-serif;line-height:1.5">
  <h2>MyShop</h2>
  <p>Hi {name},</p>
  <p>Your verification code is:</p>
  <p style="font-size:34px;font-weight:700;letter-spacing:8px;
            font-family:monospace;text-align:left">{code}</p>
  <p style="color:#71716c;font-size:13px">
    Expires in 10 minutes. Didn't sign up? Ignore this email.
  </p>
</body></html>
"""


class MailServiceUnavailable(Exception):
    pass


def _smtp_send(msg: EmailMessage) -> None:
    # Only used when SMTP is configured in .env (e.g. Gmail app password).
    # Otherwise codes are shown on-screen in dev and this file sleeps.
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
        smtp.ehlo()
        if settings.SMTP_USE_TLS:
            smtp.starttls()
            smtp.ehlo()
        if settings.SMTP_USER and settings.SMTP_PASS:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASS)
        smtp.send_message(msg)


def send_code_email(to_email: str, name: str, code: str) -> None:
    """Raises on failure — callers decide whether to swallow (register) or wait (resend)."""
    msg = EmailMessage()
    msg["Subject"] = "Your MyShop verification code"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.set_content(CODE_PLAIN.format(name=name, code=code))
    msg.add_alternative(CODE_HTML.format(name=name, code=code))
    _smtp_send(msg)
