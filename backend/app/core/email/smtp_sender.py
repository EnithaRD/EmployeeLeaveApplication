import smtplib
from email.mime.text import MIMEText

from app.core.email.base import EmailSender


class SmtpEmailSender(EmailSender):
    """Sends email through an SMTP account (e.g. a Gmail account with an App Password)."""

    def __init__(self, host: str, port: int, username: str, password: str, from_email: str | None = None):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_email = from_email or username

    def send(self, to: str, subject: str, body: str) -> None:
        message = MIMEText(body)
        message["Subject"] = subject
        message["From"] = self._from_email
        message["To"] = to

        with smtplib.SMTP(self._host, self._port) as server:
            server.starttls()
            server.login(self._username, self._password)
            server.sendmail(self._from_email, [to], message.as_string())
