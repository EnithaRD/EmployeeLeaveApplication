from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.email.base import EmailSender
from app.core.email.dependency import get_email_sender
from app.core.security import create_access_token, decode_access_token
from app.db.database import get_db
from app.models.employee import Employee
from app.models.user import User
from app.schemas.auth import CurrentUser, OtpRequest, OtpVerify, SignupRequest, Token
from app.services import otp_service


SIGNUP_ROLES = {"MANAGER", "EMPLOYEE"}


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
)


LOGIN_ALIASES = {
    "admin": "admin@example.com",
    "manager": "manager@example.com",
    "employee": "employee@example.com",
}


@router.post(
    "/login",
    response_model=Token,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):

    lookup_value = LOGIN_ALIASES.get(
        form_data.username.strip().lower(),
        form_data.username.strip(),
    )

    user = (
        db.query(User)
        .filter(User.email == lookup_value)
        .first()
    )

    if user is None or user.password != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    access_token = create_access_token(
        user_id=user.id,
        role=user.role,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post(
    "/signup",
    response_model=CurrentUser,
    status_code=status.HTTP_201_CREATED,
)
def signup(
    payload: SignupRequest,
    db: Session = Depends(get_db),
):

    role = payload.role.strip().upper()

    if role not in SIGNUP_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be either MANAGER or EMPLOYEE",
        )

    existing_user = (
        db.query(User)
        .filter(User.email == payload.email.strip())
        .first()
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=payload.email.strip(),
        password=payload.password,
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    employee = Employee(
        user_id=user.id,
        full_name=user.email,
        department_id=None,
        manager_id=None,
        date_of_joining=date.today(),
    )
    db.add(employee)
    db.commit()

    return user


@router.post(
    "/otp/request",
    status_code=status.HTTP_202_ACCEPTED,
)
def request_otp(
    payload: OtpRequest,
    db: Session = Depends(get_db),
    sender: EmailSender = Depends(get_email_sender),
):

    otp_service.request_otp(db, payload.email, sender)

    return {
        "detail": "If the account exists, a code has been sent.",
    }


@router.post(
    "/otp/verify",
    response_model=Token,
)
def verify_otp(
    payload: OtpVerify,
    db: Session = Depends(get_db),
):

    user = otp_service.verify_otp(db, payload.email, payload.code)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired code",
        )

    access_token = create_access_token(
        user_id=user.id,
        role=user.role,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        user_id = int(user_id)
    except (JWTError, ValueError):
        raise credentials_exception

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


@router.get(
    "/me",
    response_model=CurrentUser,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


def require_role(*allowed_roles: str):

    if len(allowed_roles) == 1 and isinstance(allowed_roles[0], (list, tuple, set)):
        allowed_roles = tuple(allowed_roles[0])

    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return role_checker