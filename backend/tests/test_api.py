from app.models.leave_type import LeaveType
from app.models.leave_type_approval_step import LeaveTypeApprovalStep
from app.models.user import User


def test_root_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Employee Leave Application API"}


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_v1_root(client):
    response = client.get("/api/v1/")

    assert response.status_code == 200
    assert response.json() == {"message": "Employee Leave Application API v1"}


def test_list_leave_types_empty(client):
    response = client.get("/api/v1/leave-types")

    assert response.status_code == 200
    assert response.json() == []


def test_list_leave_types_returns_seeded_rows(client, db_session):
    leave_type = LeaveType(name="Annual", default_annual_quota=18, description="Standard annual leave")
    db_session.add(leave_type)
    db_session.commit()
    db_session.refresh(leave_type)
    db_session.add(LeaveTypeApprovalStep(leave_type_id=leave_type.id, step_order=1, approver_role="MANAGER"))
    db_session.commit()

    response = client.get("/api/v1/leave-types")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "Annual"
    assert body[0]["default_annual_quota"] == 18


def test_list_leave_types_excludes_types_with_no_configured_approval_steps(client, db_session):
    db_session.add(LeaveType(name="Earned Leave", default_annual_quota=15, description="Retired leave type"))
    db_session.commit()

    response = client.get("/api/v1/leave-types")

    assert response.status_code == 200
    assert response.json() == []


def test_login_with_valid_credentials(client, db_session):
    db_session.add(User(email="admin@example.com", password="password", role="ADMIN", is_active=True))
    db_session.commit()

    response = client.post("/api/v1/auth/login", data={"username": "admin", "password": "password"})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_with_invalid_password(client, db_session):
    db_session.add(User(email="admin@example.com", password="password", role="ADMIN", is_active=True))
    db_session.commit()

    response = client.post("/api/v1/auth/login", data={"username": "admin", "password": "wrong"})

    assert response.status_code == 401
