from datetime import date, datetime
from decimal import Decimal

from app.core.security import create_access_token
from app.models.employee import Employee
from app.models.leave_application import LeaveApplication
from app.models.leave_type import LeaveType
from app.models.user import User

# A fixed Monday, so calculate_working_days always yields a single working day.
A_WEEKDAY = date(2026, 1, 5)


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


def _create_leave(db_session, requester_user_id, leave_type_id=None, leave_status="PENDING", approval_chain="MANAGER", approval_stage=0):
    leave = LeaveApplication(
        employee_id=requester_user_id,
        leave_type_id=leave_type_id,
        start_date=A_WEEKDAY,
        end_date=A_WEEKDAY,
        days_count=Decimal("1"),
        reason="test leave",
        status=leave_status,
        applied_at=datetime.utcnow(),
        approval_chain=approval_chain,
        approval_stage=approval_stage,
    )
    db_session.add(leave)
    db_session.commit()
    db_session.refresh(leave)
    return leave


# --- submitting leave requests -------------------------------------------------------


def test_manager_can_apply_for_leave(client, db_session):
    leave_type = _create_leave_type(db_session, "Annual - manager apply")
    manager, _, headers = _create_user_with_token(db_session, "manager-apply@example.com", "MANAGER")

    response = client.post(
        "/api/v1/leaves/apply",
        data={
            "leave_type_id": leave_type.id,
            "start_date": str(A_WEEKDAY),
            "end_date": str(A_WEEKDAY),
            "reason": "manager leave",
        },
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["employee_id"] == manager.id


def test_admin_cannot_apply_for_leave(client, db_session):
    leave_type = _create_leave_type(db_session, "Annual - admin apply")
    _, _, headers = _create_user_with_token(db_session, "admin-apply@example.com", "ADMIN")

    response = client.post(
        "/api/v1/leaves/apply",
        data={
            "leave_type_id": leave_type.id,
            "start_date": str(A_WEEKDAY),
            "end_date": str(A_WEEKDAY),
            "reason": "admin leave",
        },
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Only employees or managers may apply for leave."


# --- leave-type-based routing on apply ------------------------------------------------


def test_apply_routes_sick_and_casual_leave_to_manager_only(client, db_session):
    sick_type = _create_leave_type(db_session, "Sick Leave")
    casual_type = _create_leave_type(db_session, "Casual Leave")
    _, _, headers = _create_user_with_token(db_session, "employee-routing1@example.com", "EMPLOYEE")

    certificate = ("certificate.pdf", b"%PDF-1.4 fake", "application/pdf")
    sick_response = client.post(
        "/api/v1/leaves/apply",
        data={"leave_type_id": sick_type.id, "start_date": str(A_WEEKDAY), "end_date": str(A_WEEKDAY)},
        files={"medical_certificate": certificate},
        headers=headers,
    )
    casual_response = client.post(
        "/api/v1/leaves/apply",
        data={"leave_type_id": casual_type.id, "start_date": str(A_WEEKDAY), "end_date": str(A_WEEKDAY)},
        headers=headers,
    )

    assert sick_response.status_code == 200
    assert sick_response.json()["approval_chain"] == "MANAGER"
    assert casual_response.status_code == 200
    assert casual_response.json()["approval_chain"] == "MANAGER"


def test_apply_routes_long_leave_to_hr_only(client, db_session):
    leave_type = _create_leave_type(db_session, "Long Leave")
    _, _, headers = _create_user_with_token(db_session, "employee-routing2@example.com", "EMPLOYEE")

    response = client.post(
        "/api/v1/leaves/apply",
        data={"leave_type_id": leave_type.id, "start_date": str(A_WEEKDAY), "end_date": str(A_WEEKDAY)},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["approval_chain"] == "HR"


def test_apply_routes_emergency_leave_to_manager_then_hr(client, db_session):
    leave_type = _create_leave_type(db_session, "Emergency Leave")
    _, _, headers = _create_user_with_token(db_session, "employee-routing3@example.com", "EMPLOYEE")

    response = client.post(
        "/api/v1/leaves/apply",
        data={"leave_type_id": leave_type.id, "start_date": str(A_WEEKDAY), "end_date": str(A_WEEKDAY)},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["approval_chain"] == "MANAGER,HR"
    assert response.json()["approval_stage"] == 0


def test_manager_applying_for_sick_leave_routes_to_hr_not_manager(client, db_session):
    leave_type = _create_leave_type(db_session, "Sick Leave")
    _, _, headers = _create_user_with_token(db_session, "manager-routing1@example.com", "MANAGER")

    response = client.post(
        "/api/v1/leaves/apply",
        data={"leave_type_id": leave_type.id, "start_date": str(A_WEEKDAY), "end_date": str(A_WEEKDAY)},
        files={"medical_certificate": ("cert.pdf", b"%PDF-1.4 fake", "application/pdf")},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["approval_chain"] == "HR"


def test_manager_applying_for_emergency_leave_routes_to_hr_only(client, db_session):
    leave_type = _create_leave_type(db_session, "Emergency Leave")
    _, _, headers = _create_user_with_token(db_session, "manager-routing2@example.com", "MANAGER")

    response = client.post(
        "/api/v1/leaves/apply",
        data={"leave_type_id": leave_type.id, "start_date": str(A_WEEKDAY), "end_date": str(A_WEEKDAY)},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["approval_chain"] == "HR"


def test_manager_cannot_decide_their_own_leave_request(client, db_session):
    leave_type = _create_leave_type(db_session, "Casual Leave")
    manager, _, manager_headers = _create_user_with_token(db_session, "manager-routing3@example.com", "MANAGER")

    apply_response = client.post(
        "/api/v1/leaves/apply",
        data={"leave_type_id": leave_type.id, "start_date": str(A_WEEKDAY), "end_date": str(A_WEEKDAY)},
        headers=manager_headers,
    )
    leave_id = apply_response.json()["id"]

    decide_response = client.put(
        f"/api/v1/leaves/{leave_id}/decide",
        json={"action": "APPROVED", "comment": ""},
        headers=manager_headers,
    )

    assert decide_response.status_code == 403


# --- deciding a single-stage (manager-only) request ------------------------------------


def test_manager_can_decide_a_manager_stage_leave_request(client, db_session):
    leave_type = _create_leave_type(db_session, "Annual - manager stage decide")
    employee, _, _ = _create_user_with_token(db_session, "employee-decide@example.com", "EMPLOYEE")
    _, _, manager_headers = _create_user_with_token(db_session, "manager-decide@example.com", "MANAGER")
    leave = _create_leave(db_session, employee.id, leave_type_id=leave_type.id, approval_chain="MANAGER")

    response = client.put(
        f"/api/v1/leaves/{leave.id}/decide",
        json={"action": "APPROVED", "comment": ""},
        headers=manager_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"


def test_hr_cannot_decide_a_manager_stage_leave_request(client, db_session):
    employee, _, _ = _create_user_with_token(db_session, "employee-decide2@example.com", "EMPLOYEE")
    _, _, hr_headers = _create_user_with_token(db_session, "hr-decide2@example.com", "HR")
    leave = _create_leave(db_session, employee.id, approval_chain="MANAGER")

    response = client.put(
        f"/api/v1/leaves/{leave.id}/decide",
        json={"action": "APPROVED", "comment": ""},
        headers=hr_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Only MANAGER can decide on this leave request at its current stage."


def test_admin_can_override_and_decide_any_stage(client, db_session):
    leave_type = _create_leave_type(db_session, "Annual - admin override decide")
    employee, _, _ = _create_user_with_token(db_session, "employee-decide3@example.com", "EMPLOYEE")
    _, _, admin_headers = _create_user_with_token(db_session, "admin-decide3@example.com", "ADMIN")
    leave = _create_leave(db_session, employee.id, leave_type_id=leave_type.id, approval_chain="HR")

    response = client.put(
        f"/api/v1/leaves/{leave.id}/decide",
        json={"action": "APPROVED", "comment": ""},
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"


# --- deciding a multi-stage (manager -> HR) request -------------------------------------


def test_emergency_leave_requires_manager_then_hr_approval(client, db_session):
    leave_type = _create_leave_type(db_session, "Annual - emergency decide")
    employee, _, _ = _create_user_with_token(db_session, "employee-decide4@example.com", "EMPLOYEE")
    _, _, manager_headers = _create_user_with_token(db_session, "manager-decide4@example.com", "MANAGER")
    _, _, hr_headers = _create_user_with_token(db_session, "hr-decide4@example.com", "HR")
    leave = _create_leave(db_session, employee.id, leave_type_id=leave_type.id, approval_chain="MANAGER,HR")

    hr_attempt_before_manager = client.put(
        f"/api/v1/leaves/{leave.id}/decide",
        json={"action": "APPROVED", "comment": ""},
        headers=hr_headers,
    )
    assert hr_attempt_before_manager.status_code == 403

    manager_stage_response = client.put(
        f"/api/v1/leaves/{leave.id}/decide",
        json={"action": "APPROVED", "comment": "looks good"},
        headers=manager_headers,
    )
    assert manager_stage_response.status_code == 200
    assert manager_stage_response.json()["status"] == "PENDING"
    assert manager_stage_response.json()["approval_stage"] == 1

    manager_attempt_after_own_stage = client.put(
        f"/api/v1/leaves/{leave.id}/decide",
        json={"action": "APPROVED", "comment": ""},
        headers=manager_headers,
    )
    assert manager_attempt_after_own_stage.status_code == 403

    hr_stage_response = client.put(
        f"/api/v1/leaves/{leave.id}/decide",
        json={"action": "APPROVED", "comment": "approved"},
        headers=hr_headers,
    )
    assert hr_stage_response.status_code == 200
    assert hr_stage_response.json()["status"] == "APPROVED"


def test_rejection_at_first_stage_ends_the_request_immediately(client, db_session):
    employee, _, _ = _create_user_with_token(db_session, "employee-decide5@example.com", "EMPLOYEE")
    _, _, manager_headers = _create_user_with_token(db_session, "manager-decide5@example.com", "MANAGER")
    leave = _create_leave(db_session, employee.id, approval_chain="MANAGER,HR")

    response = client.put(
        f"/api/v1/leaves/{leave.id}/decide",
        json={"action": "REJECTED", "comment": "not eligible"},
        headers=manager_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"


# --- pending list/count scoping -------------------------------------------------------


def test_pending_list_for_manager_only_includes_manager_stage_requests(client, db_session):
    employee, _, _ = _create_user_with_token(db_session, "employee-pending@example.com", "EMPLOYEE")
    _, _, manager_headers = _create_user_with_token(db_session, "manager-pending-viewer@example.com", "MANAGER")
    manager_stage_leave = _create_leave(db_session, employee.id, approval_chain="MANAGER")
    _create_leave(db_session, employee.id, approval_chain="HR")

    response = client.get("/api/v1/leaves/pending", headers=manager_headers)

    assert response.status_code == 200
    returned_ids = {leave["id"] for leave in response.json()}
    assert returned_ids == {manager_stage_leave.id}


def test_pending_list_for_hr_only_includes_hr_stage_requests(client, db_session):
    employee, _, _ = _create_user_with_token(db_session, "employee-pending2@example.com", "EMPLOYEE")
    _, _, hr_headers = _create_user_with_token(db_session, "hr-pending-viewer@example.com", "HR")
    _create_leave(db_session, employee.id, approval_chain="MANAGER")
    hr_stage_leave = _create_leave(db_session, employee.id, approval_chain="HR")
    manager_then_hr_at_hr_stage = _create_leave(
        db_session, employee.id, approval_chain="MANAGER,HR", approval_stage=1
    )

    response = client.get("/api/v1/leaves/pending", headers=hr_headers)

    assert response.status_code == 200
    returned_ids = {leave["id"] for leave in response.json()}
    assert returned_ids == {hr_stage_leave.id, manager_then_hr_at_hr_stage.id}


def test_pending_list_for_admin_includes_everything(client, db_session):
    employee, _, _ = _create_user_with_token(db_session, "employee-pending3@example.com", "EMPLOYEE")
    _, _, admin_headers = _create_user_with_token(db_session, "admin-pending-viewer@example.com", "ADMIN")
    manager_leave = _create_leave(db_session, employee.id, approval_chain="MANAGER")
    hr_leave = _create_leave(db_session, employee.id, approval_chain="HR")

    response = client.get("/api/v1/leaves/pending", headers=admin_headers)

    assert response.status_code == 200
    returned_ids = {leave["id"] for leave in response.json()}
    assert returned_ids == {manager_leave.id, hr_leave.id}


def test_pending_count_is_scoped_the_same_way_as_pending_list(client, db_session):
    employee, _, _ = _create_user_with_token(db_session, "employee-pending4@example.com", "EMPLOYEE")
    _, _, manager_headers = _create_user_with_token(db_session, "manager-count-viewer@example.com", "MANAGER")
    _, _, hr_headers = _create_user_with_token(db_session, "hr-count-viewer@example.com", "HR")
    _create_leave(db_session, employee.id, approval_chain="MANAGER")
    _create_leave(db_session, employee.id, approval_chain="HR")

    manager_count = client.get("/api/v1/leaves/pending-count", headers=manager_headers)
    hr_count = client.get("/api/v1/leaves/pending-count", headers=hr_headers)

    assert manager_count.json() == {"count": 1}
    assert hr_count.json() == {"count": 1}
