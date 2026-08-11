from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

class CurrentUser:
    def __init__(self, id: int, email: str, role: str, full_name: str | None = None, employee_id: int | None = None):
        self.id = id
        self.email = email
        self.role = role
        self.full_name = full_name
        self.employee_id = employee_id


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token == "admin":
        return CurrentUser(id=1, email="admin@example.com", role="ADMIN", full_name="Admin User", employee_id=1)
    if token == "manager":
        return CurrentUser(id=2, email="manager@example.com", role="MANAGER", full_name="Manager User", employee_id=2)

    return CurrentUser(id=3, email="user@example.com", role="EMPLOYEE", full_name="Employee User", employee_id=3)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    if payload.password != "password":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.username == "admin":
        token = "admin"
        user = CurrentUser(id=1, email="admin@example.com", role="ADMIN", full_name="Admin User", employee_id=1)
    elif payload.username == "manager":
        token = "manager"
        user = CurrentUser(id=2, email="manager@example.com", role="MANAGER", full_name="Manager User", employee_id=2)
    else:
        token = "user"
        user = CurrentUser(id=3, email="user@example.com", role="EMPLOYEE", full_name="Employee User", employee_id=3)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name,
            "employee_id": user.employee_id,
        },
    }


def require_role(allowed_roles: list[str]):
    async def role_dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_dependency
