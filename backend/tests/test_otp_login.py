import re

from app.core.email.base import EmailSender
from app.core.email.dependency import get_email_sender
from app.main import app
from app.models.user import User


class FakeEmailSender(EmailSender):
    """Test double: captures sent messages instead of hitting the network."""

    def __init__(self):
        self.sent = []

    def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append({"to": to, "subject": subject, "body": body})


def _extract_code(body: str) -> str:
    match = re.search(r"\b(\d{6})\b", body)
    assert match, f"no 6-digit code found in email body: {body!r}"
    return match.group(1)


def _override_email_sender(fake_sender):
    app.dependency_overrides[get_email_sender] = lambda: fake_sender


def test_otp_request_sends_email_for_known_active_user(client, db_session):
    db_session.add(User(email="user@example.com", password="password", role="EMPLOYEE", is_active=True))
    db_session.commit()

    fake_sender = FakeEmailSender()
    _override_email_sender(fake_sender)

    response = client.post("/api/v1/auth/otp/request", json={"email": "user@example.com"})

    assert response.status_code == 202
    assert len(fake_sender.sent) == 1
    assert fake_sender.sent[0]["to"] == "user@example.com"


def test_otp_request_does_not_send_for_unknown_user(client, db_session):
    fake_sender = FakeEmailSender()
    _override_email_sender(fake_sender)

    response = client.post("/api/v1/auth/otp/request", json={"email": "nobody@example.com"})

    assert response.status_code == 202
    assert fake_sender.sent == []


def test_otp_request_does_not_send_for_inactive_user(client, db_session):
    db_session.add(User(email="inactive@example.com", password="password", role="EMPLOYEE", is_active=False))
    db_session.commit()

    fake_sender = FakeEmailSender()
    _override_email_sender(fake_sender)

    response = client.post("/api/v1/auth/otp/request", json={"email": "inactive@example.com"})

    assert response.status_code == 202
    assert fake_sender.sent == []


def test_otp_verify_with_correct_code_returns_access_token(client, db_session):
    db_session.add(User(email="user@example.com", password="password", role="EMPLOYEE", is_active=True))
    db_session.commit()

    fake_sender = FakeEmailSender()
    _override_email_sender(fake_sender)

    client.post("/api/v1/auth/otp/request", json={"email": "user@example.com"})
    code = _extract_code(fake_sender.sent[0]["body"])

    response = client.post("/api/v1/auth/otp/verify", json={"email": "user@example.com", "code": code})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_otp_verify_with_wrong_code_is_rejected(client, db_session):
    db_session.add(User(email="user@example.com", password="password", role="EMPLOYEE", is_active=True))
    db_session.commit()

    fake_sender = FakeEmailSender()
    _override_email_sender(fake_sender)

    client.post("/api/v1/auth/otp/request", json={"email": "user@example.com"})

    response = client.post("/api/v1/auth/otp/verify", json={"email": "user@example.com", "code": "000000"})

    assert response.status_code == 401


def test_otp_cannot_be_reused_after_verification(client, db_session):
    db_session.add(User(email="user@example.com", password="password", role="EMPLOYEE", is_active=True))
    db_session.commit()

    fake_sender = FakeEmailSender()
    _override_email_sender(fake_sender)

    client.post("/api/v1/auth/otp/request", json={"email": "user@example.com"})
    code = _extract_code(fake_sender.sent[0]["body"])

    first = client.post("/api/v1/auth/otp/verify", json={"email": "user@example.com", "code": code})
    second = client.post("/api/v1/auth/otp/verify", json={"email": "user@example.com", "code": code})

    assert first.status_code == 200
    assert second.status_code == 401


def test_otp_verify_without_prior_request_is_rejected(client, db_session):
    db_session.add(User(email="user@example.com", password="password", role="EMPLOYEE", is_active=True))
    db_session.commit()

    response = client.post("/api/v1/auth/otp/verify", json={"email": "user@example.com", "code": "123456"})

    assert response.status_code == 401
