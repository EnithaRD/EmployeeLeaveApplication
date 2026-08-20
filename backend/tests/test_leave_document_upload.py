from datetime import date, datetime
from decimal import Decimal

from app.core.security import create_access_token
from app.models.employee import Employee
from app.models.leave_application import LeaveApplication
from app.models.leave_application_document import LeaveApplicationDocument
from app.models.leave_type import LeaveType
from app.models.user import User


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


def _create_leave_type(db_session, name="Sick Leave"):
    leave_type = LeaveType(name=name, default_annual_quota=10, description="test")
    db_session.add(leave_type)
    db_session.commit()
    db_session.refresh(leave_type)
    return leave_type


def _create_leave(db_session, employee_user_id, leave_type_id, leave_status="PENDING"):
    leave = LeaveApplication(
        employee_id=employee_user_id,
        leave_type_id=leave_type_id,
        start_date=date.today(),
        end_date=date.today(),
        days_count=Decimal("1"),
        reason="not feeling well",
        status=leave_status,
        applied_at=datetime.utcnow(),
    )
    db_session.add(leave)
    db_session.commit()
    db_session.refresh(leave)
    return leave


def _upload(client, leave_id, headers, content=b"file-bytes", filename="note.pdf", content_type="application/pdf"):
    return client.post(
        f"/api/v1/leaves/{leave_id}/document",
        headers=headers,
        files={"file": (filename, content, content_type)},
    )


# --- happy path -----------------------------------------------------------------


def test_owner_can_upload_and_manager_can_view_sick_leave_document(client, db_session):
    employee_user, _, employee_headers = _create_user_with_token(db_session, "sick@example.com", "EMPLOYEE")
    _, _, manager_headers = _create_user_with_token(db_session, "manager@example.com", "MANAGER")
    leave_type = _create_leave_type(db_session)
    leave = _create_leave(db_session, employee_user.id, leave_type.id)

    upload_response = _upload(client, leave.id, employee_headers)
    assert upload_response.status_code == 201
    assert upload_response.json()["filename"] == "note.pdf"

    view_response = client.get(f"/api/v1/leaves/{leave.id}/document", headers=manager_headers)
    assert view_response.status_code == 200
    assert view_response.content == b"file-bytes"
    assert view_response.headers["content-type"] == "application/pdf"


def test_owner_can_view_their_own_uploaded_document(client, db_session):
    employee_user, _, employee_headers = _create_user_with_token(db_session, "self@example.com", "EMPLOYEE")
    leave_type = _create_leave_type(db_session)
    leave = _create_leave(db_session, employee_user.id, leave_type.id)

    _upload(client, leave.id, employee_headers)

    response = client.get(f"/api/v1/leaves/{leave.id}/document", headers=employee_headers)
    assert response.status_code == 200
    assert response.content == b"file-bytes"


def test_uploading_twice_replaces_the_document(client, db_session):
    employee_user, _, employee_headers = _create_user_with_token(db_session, "replace@example.com", "EMPLOYEE")
    leave_type = _create_leave_type(db_session)
    leave = _create_leave(db_session, employee_user.id, leave_type.id)

    _upload(client, leave.id, employee_headers, content=b"first", filename="first.pdf")
    second = _upload(client, leave.id, employee_headers, content=b"second", filename="second.pdf")
    assert second.status_code == 201

    assert (
        db_session.query(LeaveApplicationDocument)
        .filter(LeaveApplicationDocument.leave_application_id == leave.id)
        .count()
        == 1
    )

    response = client.get(f"/api/v1/leaves/{leave.id}/document", headers=employee_headers)
    assert response.content == b"second"


# --- rejected / unauthorized ------------------------------------------------------


def test_upload_without_auth_token_returns_401(client):
    response = client.post("/api/v1/leaves/1/document", files={"file": ("a.pdf", b"x", "application/pdf")})
    assert response.status_code == 401


def test_upload_for_non_sick_leave_type_returns_400(client, db_session):
    employee_user, _, employee_headers = _create_user_with_token(db_session, "casual@example.com", "EMPLOYEE")
    leave_type = _create_leave_type(db_session, name="Casual Leave")
    leave = _create_leave(db_session, employee_user.id, leave_type.id)

    response = _upload(client, leave.id, employee_headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "Document upload is only available for Sick Leave requests."


def test_upload_by_non_owner_returns_404(client, db_session):
    owner, _, _ = _create_user_with_token(db_session, "owner2@example.com", "EMPLOYEE")
    _, _, intruder_headers = _create_user_with_token(db_session, "intruder2@example.com", "EMPLOYEE")
    leave_type = _create_leave_type(db_session)
    leave = _create_leave(db_session, owner.id, leave_type.id)

    response = _upload(client, leave.id, intruder_headers)

    assert response.status_code == 404


def test_upload_for_already_decided_leave_returns_400(client, db_session):
    employee_user, _, employee_headers = _create_user_with_token(db_session, "decided@example.com", "EMPLOYEE")
    leave_type = _create_leave_type(db_session)
    leave = _create_leave(db_session, employee_user.id, leave_type.id, leave_status="APPROVED")

    response = _upload(client, leave.id, employee_headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "A document can only be uploaded while the leave request is pending."


def test_view_document_without_auth_token_returns_401(client):
    response = client.get("/api/v1/leaves/1/document")
    assert response.status_code == 401


def test_view_document_by_unrelated_employee_returns_403(client, db_session):
    employee_user, _, employee_headers = _create_user_with_token(db_session, "docowner@example.com", "EMPLOYEE")
    _, _, other_headers = _create_user_with_token(db_session, "otheremployee@example.com", "EMPLOYEE")
    leave_type = _create_leave_type(db_session)
    leave = _create_leave(db_session, employee_user.id, leave_type.id)
    _upload(client, leave.id, employee_headers)

    response = client.get(f"/api/v1/leaves/{leave.id}/document", headers=other_headers)

    assert response.status_code == 403


def test_view_document_for_leave_with_no_document_returns_404(client, db_session):
    employee_user, _, employee_headers = _create_user_with_token(db_session, "nodoc@example.com", "EMPLOYEE")
    leave_type = _create_leave_type(db_session)
    leave = _create_leave(db_session, employee_user.id, leave_type.id)

    response = client.get(f"/api/v1/leaves/{leave.id}/document", headers=employee_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "No document uploaded for this leave request."


def test_view_document_for_nonexistent_leave_returns_404(client, db_session):
    _, _, headers = _create_user_with_token(db_session, "ghost@example.com", "MANAGER")

    response = client.get("/api/v1/leaves/999999/document", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Leave request not found."


def test_any_manager_can_view_document_not_just_a_specific_one(client, db_session):
    employee_user, _, employee_headers = _create_user_with_token(db_session, "anymanager@example.com", "EMPLOYEE")
    _, _, manager_one_headers = _create_user_with_token(db_session, "managerone@example.com", "MANAGER")
    _, _, manager_two_headers = _create_user_with_token(db_session, "managertwo@example.com", "MANAGER")
    leave_type = _create_leave_type(db_session)
    leave = _create_leave(db_session, employee_user.id, leave_type.id)
    _upload(client, leave.id, employee_headers)

    first = client.get(f"/api/v1/leaves/{leave.id}/document", headers=manager_one_headers)
    second = client.get(f"/api/v1/leaves/{leave.id}/document", headers=manager_two_headers)

    assert first.status_code == 200
    assert second.status_code == 200
