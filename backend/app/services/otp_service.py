import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.email.base import EmailSender
from app.models.otp_code import OtpCode
from app.models.user import User


PBKDF2_ITERATIONS = 260_000


def _hash_code(code: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        code.encode(),
        salt,
        PBKDF2_ITERATIONS,
    ).hex()


def request_otp(db: Session, email: str, sender: EmailSender) -> None:

    user = (
        db.query(User)
        .filter(User.email == email.strip())
        .first()
    )

    if user is None or not user.is_active:
        return

    code = f"{secrets.randbelow(1_000_000):06d}"
    salt = os.urandom(16)

    otp_code = OtpCode(
        user_id=user.id,
        salt=salt.hex(),
        code_hash=_hash_code(code, salt),
        expires_at=datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
        attempt_count=0,
    )
    db.add(otp_code)
    db.commit()

    sender.send(
        to=user.email,
        subject="Your login code",
        body=f"Your verification code is {code}. It expires in {settings.OTP_EXPIRE_MINUTES} minutes.",
    )


def verify_otp(db: Session, email: str, code: str) -> Optional[User]:

    user = (
        db.query(User)
        .filter(User.email == email.strip())
        .first()
    )

    if user is None or not user.is_active:
        return None

    otp_code = (
        db.query(OtpCode)
        .filter(
            OtpCode.user_id == user.id,
            OtpCode.consumed_at.is_(None),
        )
        .order_by(OtpCode.created_at.desc())
        .first()
    )

    if otp_code is None:
        return None

    if otp_code.attempt_count >= settings.OTP_MAX_ATTEMPTS:
        return None

    if otp_code.expires_at < datetime.utcnow():
        return None

    otp_code.attempt_count += 1

    salt = bytes.fromhex(otp_code.salt)
    candidate_hash = _hash_code(code, salt)
    is_match = hmac.compare_digest(candidate_hash, otp_code.code_hash)

    if not is_match:
        db.commit()
        return None

    otp_code.consumed_at = datetime.utcnow()
    db.commit()

    return user
