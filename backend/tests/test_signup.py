from app.models.employee import Employee
from app.models.user import User


def test_signup_employee_creates_user_and_employee(client, db_session):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "new.employee@example.com",
            "password": "secret123",
            "role": "employee",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new.employee@example.com"
    assert body["role"] == "EMPLOYEE"
    assert body["is_active"] is True

    user = db_session.query(User).filter(User.email == "new.employee@example.com").first()
    assert user is not None

    employee = db_session.query(Employee).filter(Employee.user_id == user.id).first()
    assert employee is not None
    assert employee.full_name == "new.employee@example.com"
    assert employee.department_id is None
    assert employee.manager_id is None


def test_signup_manager_creates_user_with_manager_role(client, db_session):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "new.manager@example.com",
            "password": "secret123",
            "role": "MANAGER",
        },
    )

    assert response.status_code == 201
    assert response.json()["role"] == "MANAGER"


def test_signup_duplicate_email_returns_409(client, db_session):
    payload = {
        "email": "duplicate@example.com",
        "password": "secret123",
        "role": "EMPLOYEE",
    }

    first = client.post("/api/v1/auth/signup", json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/auth/signup", json=payload)
    assert second.status_code == 409


def test_signup_invalid_role_returns_400(client, db_session):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "wannabe.admin@example.com",
            "password": "secret123",
            "role": "ADMIN",
        },
    )

    assert response.status_code == 400


def test_signup_then_login_succeeds(client, db_session):
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "login.after.signup@example.com",
            "password": "secret123",
            "role": "EMPLOYEE",
        },
    )
    assert signup_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "login.after.signup@example.com",
            "password": "secret123",
        },
    )

    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
