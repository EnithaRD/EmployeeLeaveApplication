import re

import pytest

from app.core.email.base import EmailSender
from app.core.email.dependency import get_email_sender
from app.core.security import decode_access_token
from app.main import app
from app.models.otp_code import OtpCode
from app.models.user import User
from app.services import otp_service


class FakeEmailSender(EmailSender):

    def __init__(self):
        self.sent = []

    def send(self, to, subject, body):
        self.sent.append({"to": to, "subject": subject, "body": body})


@pytest.fixture()
def fake_sender():
    sender = FakeEmailSender()
    app.dependency_overrides[get_email_sender] = lambda: sender
    try:
        yield sender
    finally:
        app.dependency_overrides.pop(get_email_sender, None)


def _seed_user(db_session, email="employee@example.com", is_active=True):
    user = User(
        email=email,
        password="password",
        role="EMPLOYEE",
        is_active=is_active,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _extract_code(body):
    match = re.search(r"\d{6}", body)
    assert match is not None
    return match.group(0)


def test_request_otp_unknown_user_returns_202_and_sends_nothing(client, db_session, fake_sender):
    response = client.post(
        "/api/v1/auth/otp/request",
        json={"email": "unknown@example.com"},
    )

    assert response.status_code == 202
    assert fake_sender.sent == []


def test_request_otp_inactive_user_returns_202_and_sends_nothing(client, db_session, fake_sender):
    _seed_user(db_session, email="inactive@example.com", is_active=False)

    response = client.post(
        "/api/v1/auth/otp/request",
        json={"email": "inactive@example.com"},
    )

    assert response.status_code == 202
    assert fake_sender.sent == []


def test_request_otp_active_user_sends_email(client, db_session, fake_sender):
    _seed_user(db_session)

    response = client.post(
        "/api/v1/auth/otp/request",
        json={"email": "employee@example.com"},
    )

    assert response.status_code == 202
    assert len(fake_sender.sent) == 1
    assert fake_sender.sent[0]["to"] == "employee@example.com"
    _extract_code(fake_sender.sent[0]["body"])


def test_verify_otp_correct_code_returns_token(client, db_session, fake_sender):
    user = _seed_user(db_session)

    client.post("/api/v1/auth/otp/request", json={"email": user.email})
    code = _extract_code(fake_sender.sent[0]["body"])

    response = client.post(
        "/api/v1/auth/otp/verify",
        json={"email": user.email, "code": code},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"

    payload = decode_access_token(body["access_token"])
    assert payload["sub"] == str(user.id)
    assert payload["role"] == user.role


def test_verify_otp_wrong_code_returns_401(client, db_session, fake_sender):
    user = _seed_user(db_session)

    client.post("/api/v1/auth/otp/request", json={"email": user.email})
    real_code = _extract_code(fake_sender.sent[0]["body"])
    wrong_code = "000000" if real_code != "000000" else "111111"

    response = client.post(
        "/api/v1/auth/otp/verify",
        json={"email": user.email, "code": wrong_code},
    )

    assert response.status_code == 401


def test_verify_otp_no_request_on_record_returns_401(client, db_session, fake_sender):
    user = _seed_user(db_session)

    response = client.post(
        "/api/v1/auth/otp/verify",
        json={"email": user.email, "code": "123456"},
    )

    assert response.status_code == 401


def test_verify_otp_expired_code_returns_401(client, db_session, fake_sender):
    from datetime import datetime, timedelta

    user = _seed_user(db_session)

    salt = b"0123456789abcdef"
    code = "654321"
    otp_code = OtpCode(
        user_id=user.id,
        salt=salt.hex(),
        code_hash=otp_service._hash_code(code, salt),
        expires_at=datetime.utcnow() - timedelta(minutes=1),
        attempt_count=0,
    )
    db_session.add(otp_code)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/otp/verify",
        json={"email": user.email, "code": code},
    )

    assert response.status_code == 401


def test_verify_otp_replayed_code_returns_401(client, db_session, fake_sender):
    user = _seed_user(db_session)

    client.post("/api/v1/auth/otp/request", json={"email": user.email})
    code = _extract_code(fake_sender.sent[0]["body"])

    first = client.post(
        "/api/v1/auth/otp/verify",
        json={"email": user.email, "code": code},
    )
    assert first.status_code == 200

    second = client.post(
        "/api/v1/auth/otp/verify",
        json={"email": user.email, "code": code},
    )
    assert second.status_code == 401


def test_verify_otp_max_attempts_returns_401(client, db_session, fake_sender, monkeypatch):
    monkeypatch.setattr(otp_service.settings, "OTP_MAX_ATTEMPTS", 2)

    user = _seed_user(db_session)

    client.post("/api/v1/auth/otp/request", json={"email": user.email})
    real_code = _extract_code(fake_sender.sent[0]["body"])
    wrong_code = "000000" if real_code != "000000" else "111111"

    for _ in range(2):
        response = client.post(
            "/api/v1/auth/otp/verify",
            json={"email": user.email, "code": wrong_code},
        )
        assert response.status_code == 401

    locked_out = client.post(
        "/api/v1/auth/otp/verify",
        json={"email": user.email, "code": real_code},
    )
    assert locked_out.status_code == 401
