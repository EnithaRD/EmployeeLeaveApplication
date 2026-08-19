from datetime import date
from io import BytesIO

import pytest

from app.core.security import create_access_token
from app.models.employee import Employee
from app.models.leave_type import LeaveType
from app.models.medical_certificate import MedicalCertificate
from app.models.user import User
from app.services import medical_certificate_service

# A fixed Monday, so calculate_working_days always yields a single working day.
A_WEEKDAY = date(2026, 1, 5)


@pytest.fixture(autouse=True)
def isolated_certificate_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(
        medical_certificate_service.settings,
        "MEDICAL_CERTIFICATE_STORAGE_DIR",
        str(tmp_path),
    )
    yield


def _create_user_with_token(db_session, email, role):
    user = User(email=email, password="secret123", role=role, is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    employee = Employee(
        user_id=user.id,
        full_name=email,
        department_id=None,
        manager_id=None,
        date_of_joining=date.today(),
    )
    db_session.add(employee)
    db_session.commit()

    token = create_access_token(user_id=user.id, role=user.role)
    headers = {"Authorization": f"Bearer {token}"}
    return user, employee, headers


def _create_leave_type(db_session, name):
    leave_type = LeaveType(name=name, default_annual_quota=30)
    db_session.add(leave_type)
    db_session.commit()
    db_session.refresh(leave_type)
    return leave_type


def _apply_form(leave_type_id, reason="test"):
    return {
        "leave_type_id": leave_type_id,
        "start_date": str(A_WEEKDAY),
        "end_date": str(A_WEEKDAY),
        "reason": reason,
    }


def test_sick_leave_without_certificate_is_rejected(client, db_session):
    leave_type = _create_leave_type(db_session, "Sick Leave")
    _, _, headers = _create_user_with_token(db_session, "sick-no-cert@example.com", "EMPLOYEE")

    response = client.post(
        "/api/v1/leaves/apply",
        data=_apply_form(leave_type.id),
        headers=headers,
    )

    assert response.status_code == 400
    assert "medical certificate" in response.json()["detail"].lower()


def test_sick_leave_with_valid_certificate_is_accepted(client, db_session):
    leave_type = _create_leave_type(db_session, "Sick Leave")
    _, _, headers = _create_user_with_token(db_session, "sick-with-cert@example.com", "EMPLOYEE")

    response = client.post(
        "/api/v1/leaves/apply",
        data=_apply_form(leave_type.id),
        files={"medical_certificate": ("cert.pdf", BytesIO(b"%PDF-1.4 fake certificate"), "application/pdf")},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()

    certificate = (
        db_session.query(MedicalCertificate)
        .filter(MedicalCertificate.leave_application_id == body["id"])
        .first()
    )
    assert certificate is not None
    assert certificate.original_filename == "cert.pdf"
    assert certificate.content_type == "application/pdf"


def test_non_sick_leave_without_certificate_is_allowed(client, db_session):
    leave_type = _create_leave_type(db_session, "Casual Leave")
    _, _, headers = _create_user_with_token(db_session, "casual-no-cert@example.com", "EMPLOYEE")

    response = client.post(
        "/api/v1/leaves/apply",
        data=_apply_form(leave_type.id),
        headers=headers,
    )

    assert response.status_code == 200


def test_invalid_certificate_file_type_is_rejected(client, db_session):
    leave_type = _create_leave_type(db_session, "Sick Leave")
    _, _, headers = _create_user_with_token(db_session, "sick-bad-type@example.com", "EMPLOYEE")

    response = client.post(
        "/api/v1/leaves/apply",
        data=_apply_form(leave_type.id),
        files={"medical_certificate": ("cert.exe", BytesIO(b"not a real file"), "application/x-msdownload")},
        headers=headers,
    )

    assert response.status_code == 400
    assert "unsupported file type" in response.json()["detail"].lower()


def test_oversized_certificate_is_rejected(client, db_session, monkeypatch):
    monkeypatch.setattr(medical_certificate_service.settings, "MEDICAL_CERTIFICATE_MAX_SIZE_BYTES", 10)

    leave_type = _create_leave_type(db_session, "Sick Leave")
    _, _, headers = _create_user_with_token(db_session, "sick-oversized@example.com", "EMPLOYEE")

    response = client.post(
        "/api/v1/leaves/apply",
        data=_apply_form(leave_type.id),
        files={"medical_certificate": ("cert.pdf", BytesIO(b"x" * 100), "application/pdf")},
        headers=headers,
    )

    assert response.status_code == 400
    assert "exceeds the maximum allowed size" in response.json()["detail"].lower()


def test_unauthorized_user_cannot_access_certificate(client, db_session):
    leave_type = _create_leave_type(db_session, "Sick Leave")
    _, _, owner_headers = _create_user_with_token(db_session, "sick-owner@example.com", "EMPLOYEE")
    _, _, other_headers = _create_user_with_token(db_session, "sick-other-employee@example.com", "EMPLOYEE")

    apply_response = client.post(
        "/api/v1/leaves/apply",
        data=_apply_form(leave_type.id),
        files={"medical_certificate": ("cert.pdf", BytesIO(b"%PDF-1.4 fake certificate"), "application/pdf")},
        headers=owner_headers,
    )
    leave_id = apply_response.json()["id"]

    owner_response = client.get(f"/api/v1/leaves/{leave_id}/certificate", headers=owner_headers)
    other_response = client.get(f"/api/v1/leaves/{leave_id}/certificate", headers=other_headers)

    assert owner_response.status_code == 200
    assert other_response.status_code == 403
