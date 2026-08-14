from app.models.leave_type import LeaveType


def test_root_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Employee Leave Application API is running."}


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
    db_session.add(LeaveType(name="Annual", default_annual_quota=18, description="Standard annual leave"))
    db_session.commit()

    response = client.get("/api/v1/leave-types")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "Annual"
    assert body[0]["default_annual_quota"] == 18


def test_login_with_valid_credentials(client):
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "password"})

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"] == "admin"
    assert body["user"]["role"] == "ADMIN"


def test_login_with_invalid_password(client):
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong"})

    assert response.status_code == 401
