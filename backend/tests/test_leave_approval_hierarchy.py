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


def _create_leave(db_session, requester_user_id, leave_type_id=None, leave_status="PENDING"):
    leave = LeaveApplication(
        employee_id=requester_user_id,
        leave_type_id=leave_type_id,
        start_date=A_WEEKDAY,
        end_date=A_WEEKDAY,
        days_count=Decimal("1"),
        reason="test leave",
        status=leave_status,
        applied_at=datetime.utcnow(),
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


# --- deciding an employee-submitted request ------------------------------------------


def test_manager_can_decide_employee_leave_request(client, db_session):
    leave_type = _create_leave_type(db_session, "Annual - manager decides")
    employee, _, _ = _create_user_with_token(db_session, "employee-decide@example.com", "EMPLOYEE")
    _, _, manager_headers = _create_user_with_token(db_session, "manager-decide@example.com", "MANAGER")
    leave = _create_leave(db_session, employee.id, leave_type_id=leave_type.id)

    response = client.put(
        f"/api/v1/leaves/{leave.id}/decide",
        json={"action": "APPROVED", "comment": ""},
        headers=manager_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"


def test_admin_cannot_decide_employee_leave_request(client, db_session):
    employee, _, _ = _create_user_with_token(db_session, "employee-decide2@example.com", "EMPLOYEE")
    _, _, admin_headers = _create_user_with_token(db_session, "admin-decide2@example.com", "ADMIN")
    leave = _create_leave(db_session, employee.id)

    response = client.put(
        f"/api/v1/leaves/{leave.id}/decide",
        json={"action": "APPROVED", "comment": ""},
        headers=admin_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Only a manager can decide on an employee's leave request."


# --- deciding a manager-submitted request --------------------------------------------


def test_admin_can_decide_manager_leave_request(client, db_session):
    leave_type = _create_leave_type(db_session, "Annual - admin decides")
    requesting_manager, _, _ = _create_user_with_token(db_session, "manager-requester@example.com", "MANAGER")
    _, _, admin_headers = _create_user_with_token(db_session, "admin-decide3@example.com", "ADMIN")
    leave = _create_leave(db_session, requesting_manager.id, leave_type_id=leave_type.id)

    response = client.put(
        f"/api/v1/leaves/{leave.id}/decide",
        json={"action": "APPROVED", "comment": ""},
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"


def test_other_manager_cannot_decide_manager_leave_request(client, db_session):
    requesting_manager, _, _ = _create_user_with_token(db_session, "manager-requester2@example.com", "MANAGER")
    _, _, other_manager_headers = _create_user_with_token(db_session, "manager-decider@example.com", "MANAGER")
    leave = _create_leave(db_session, requesting_manager.id)

    response = client.put(
        f"/api/v1/leaves/{leave.id}/decide",
        json={"action": "APPROVED", "comment": ""},
        headers=other_manager_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Only an admin can decide on a manager's leave request."


# --- pending list/count scoping -------------------------------------------------------


def test_pending_list_for_manager_only_includes_employee_requests(client, db_session):
    employee, _, _ = _create_user_with_token(db_session, "employee-pending@example.com", "EMPLOYEE")
    requesting_manager, _, _ = _create_user_with_token(db_session, "manager-pending-req@example.com", "MANAGER")
    _, _, manager_headers = _create_user_with_token(db_session, "manager-pending-viewer@example.com", "MANAGER")
    employee_leave = _create_leave(db_session, employee.id)
    _create_leave(db_session, requesting_manager.id)

    response = client.get("/api/v1/leaves/pending", headers=manager_headers)

    assert response.status_code == 200
    returned_ids = {leave["id"] for leave in response.json()}
    assert returned_ids == {employee_leave.id}


def test_pending_list_for_admin_only_includes_manager_requests(client, db_session):
    employee, _, _ = _create_user_with_token(db_session, "employee-pending2@example.com", "EMPLOYEE")
    requesting_manager, _, _ = _create_user_with_token(db_session, "manager-pending-req2@example.com", "MANAGER")
    _, _, admin_headers = _create_user_with_token(db_session, "admin-pending-viewer@example.com", "ADMIN")
    _create_leave(db_session, employee.id)
    manager_leave = _create_leave(db_session, requesting_manager.id)

    response = client.get("/api/v1/leaves/pending", headers=admin_headers)

    assert response.status_code == 200
    returned_ids = {leave["id"] for leave in response.json()}
    assert returned_ids == {manager_leave.id}


def test_pending_count_is_scoped_the_same_way_as_pending_list(client, db_session):
    employee, _, _ = _create_user_with_token(db_session, "employee-pending3@example.com", "EMPLOYEE")
    requesting_manager, _, _ = _create_user_with_token(db_session, "manager-pending-req3@example.com", "MANAGER")
    _, _, manager_headers = _create_user_with_token(db_session, "manager-count-viewer@example.com", "MANAGER")
    _, _, admin_headers = _create_user_with_token(db_session, "admin-count-viewer@example.com", "ADMIN")
    _create_leave(db_session, employee.id)
    _create_leave(db_session, requesting_manager.id)

    manager_count = client.get("/api/v1/leaves/pending-count", headers=manager_headers)
    admin_count = client.get("/api/v1/leaves/pending-count", headers=admin_headers)

    assert manager_count.json() == {"count": 1}
    assert admin_count.json() == {"count": 1}
