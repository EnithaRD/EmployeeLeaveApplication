from app.core.config import settings
from app.core.email.base import EmailSender
from app.core.email.smtp_sender import SmtpEmailSender


def get_email_sender() -> EmailSender:

    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        raise RuntimeError(
            "SMTP_USERNAME and SMTP_PASSWORD must be configured to send email"
        )

    return SmtpEmailSender(
        host=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USERNAME,
        password=settings.SMTP_PASSWORD,
        from_email=settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME,
    )
