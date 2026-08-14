import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.email.base import EmailSender
from app.models.otp_code import OtpCode
from app.models.user import User

_HASH_ITERATIONS = 260_000


def _generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _hash_code(code: str, salt: bytes) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", code.encode(), salt, _HASH_ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def _verify_code(code: str, stored_hash: str) -> bool:
    salt_hex, _, digest_hex = stored_hash.partition("$")
    if not salt_hex or not digest_hex:
        return False

    candidate = hashlib.pbkdf2_hmac("sha256", code.encode(), bytes.fromhex(salt_hex), _HASH_ITERATIONS)
    return hmac.compare_digest(candidate.hex(), digest_hex)


def _as_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def request_otp(db: Session, email: str, email_sender: EmailSender) -> None:
    """Generate an OTP for the user and email it. Silently no-ops for unknown/
    inactive accounts so the endpoint can't be used to enumerate users."""

    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        return

    code = _generate_code()
    otp = OtpCode(
        user_id=user.id,
        code_hash=_hash_code(code, secrets.token_bytes(16)),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
    )
    db.add(otp)
    db.commit()

    email_sender.send(
        to=user.email,
        subject="Your Employee Leave Application login code",
        body=(
            f"Your one-time login code is {code}. "
            f"It expires in {settings.OTP_EXPIRE_MINUTES} minutes."
        ),
    )


def verify_otp(db: Session, email: str, code: str) -> User | None:
    """Validate a submitted OTP and consume it. Returns the matching User on
    success, or None if the email/code/expiry/attempt-limit checks fail."""

    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        return None

    otp = (
        db.query(OtpCode)
        .filter(OtpCode.user_id == user.id, OtpCode.consumed_at.is_(None))
        .order_by(OtpCode.id.desc())
        .first()
    )
    if otp is None:
        return None

    if otp.attempt_count >= settings.OTP_MAX_ATTEMPTS:
        return None

    if _as_aware_utc(otp.expires_at) < datetime.now(timezone.utc):
        return None

    otp.attempt_count += 1

    if not _verify_code(code, otp.code_hash):
        db.commit()
        return None

    otp.consumed_at = datetime.now(timezone.utc)
    db.commit()
    return user
