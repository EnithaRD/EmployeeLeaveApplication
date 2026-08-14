from app.core.config import settings
from app.core.email.base import EmailSender
from app.core.email.smtp_sender import SmtpEmailSender


def get_email_sender() -> EmailSender:
    """FastAPI dependency that resolves the configured EmailSender.

    Routes and services depend on the EmailSender abstraction only, so adding
    another account/provider later means adding a new settings-driven branch
    here (or a new EmailSender implementation) - nothing that calls send()
    has to change.
    """

    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        raise RuntimeError(
            "SMTP_USERNAME and SMTP_PASSWORD must be set in the environment to send email."
        )

    return SmtpEmailSender(
        host=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USERNAME,
        password=settings.SMTP_PASSWORD,
        from_email=settings.SMTP_FROM_EMAIL,
    )
