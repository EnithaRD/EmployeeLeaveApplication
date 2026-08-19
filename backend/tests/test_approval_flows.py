from datetime import date

from app.core.security import create_access_token
from app.models.employee import Employee
from app.models.leave_type import LeaveType
from app.models.leave_type_approval_step import LeaveTypeApprovalStep
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


def _create_leave_type(db_session, name, approver_roles=None):
    leave_type = LeaveType(name=name, default_annual_quota=10)
    db_session.add(leave_type)
    db_session.commit()
    db_session.refresh(leave_type)

    for step_order, approver_role in enumerate(approver_roles or [], start=1):
        db_session.add(
            LeaveTypeApprovalStep(
                leave_type_id=leave_type.id,
                step_order=step_order,
                approver_role=approver_role,
            )
        )
    db_session.commit()
    return leave_type


def test_admin_can_list_approval_flows(client, db_session):
    _create_leave_type(db_session, "Casual Leave", ["MANAGER"])
    _, _, admin_headers = _create_user_with_token(db_session, "admin-list@example.com", "ADMIN")

    response = client.get("/api/v1/approval-flows", headers=admin_headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["leave_type_name"] == "Casual Leave"
    assert body[0]["steps"] == [{"step_order": 1, "approver_role": "MANAGER"}]


def test_non_admin_cannot_list_approval_flows(client, db_session):
    _, _, manager_headers = _create_user_with_token(db_session, "manager-list@example.com", "MANAGER")

    response = client.get("/api/v1/approval-flows", headers=manager_headers)

    assert response.status_code == 403


def test_admin_can_update_approval_flow(client, db_session):
    leave_type = _create_leave_type(db_session, "Sick Leave", ["MANAGER"])
    _, _, admin_headers = _create_user_with_token(db_session, "admin-update@example.com", "ADMIN")

    response = client.put(
        f"/api/v1/approval-flows/{leave_type.id}",
        json={"steps": ["MANAGER", "HR"]},
        headers=admin_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["steps"] == [
        {"step_order": 1, "approver_role": "MANAGER"},
        {"step_order": 2, "approver_role": "HR"},
    ]


def test_non_admin_cannot_update_approval_flow(client, db_session):
    leave_type = _create_leave_type(db_session, "Long Leave", ["HR"])
    _, _, hr_headers = _create_user_with_token(db_session, "hr-update@example.com", "HR")

    response = client.put(
        f"/api/v1/approval-flows/{leave_type.id}",
        json={"steps": ["MANAGER"]},
        headers=hr_headers,
    )

    assert response.status_code == 403


def test_update_approval_flow_rejects_empty_steps(client, db_session):
    leave_type = _create_leave_type(db_session, "Emergency Leave", ["MANAGER", "HR"])
    _, _, admin_headers = _create_user_with_token(db_session, "admin-empty@example.com", "ADMIN")

    response = client.put(
        f"/api/v1/approval-flows/{leave_type.id}",
        json={"steps": []},
        headers=admin_headers,
    )

    assert response.status_code == 400


def test_update_approval_flow_rejects_invalid_role(client, db_session):
    leave_type = _create_leave_type(db_session, "Emergency Leave 2", ["MANAGER", "HR"])
    _, _, admin_headers = _create_user_with_token(db_session, "admin-invalid@example.com", "ADMIN")

    response = client.put(
        f"/api/v1/approval-flows/{leave_type.id}",
        json={"steps": ["EMPLOYEE"]},
        headers=admin_headers,
    )

    assert response.status_code == 400


def test_update_approval_flow_for_missing_leave_type_returns_404(client, db_session):
    _, _, admin_headers = _create_user_with_token(db_session, "admin-missing@example.com", "ADMIN")

    response = client.put(
        "/api/v1/approval-flows/999999",
        json={"steps": ["MANAGER"]},
        headers=admin_headers,
    )

    assert response.status_code == 404
