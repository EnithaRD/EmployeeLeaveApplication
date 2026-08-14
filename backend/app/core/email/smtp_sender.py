import smtplib
from email.mime.text import MIMEText

from app.core.email.base import EmailSender


class SmtpEmailSender(EmailSender):

    def __init__(self, host: str, port: int, username: str, password: str, from_email: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email

    def send(self, to: str, subject: str, body: str) -> None:
        message = MIMEText(body)
        message["Subject"] = subject
        message["From"] = self.from_email
        message["To"] = to

        with smtplib.SMTP(self.host, self.port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.sendmail(self.from_email, [to], message.as_string())
