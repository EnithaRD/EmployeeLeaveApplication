from datetime import date

from app.core.security import create_access_token
from app.models.employee import Employee
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


def _create_leave_type(db_session, name):
    leave_type = LeaveType(name=name, default_annual_quota=30)
    db_session.add(leave_type)
    db_session.commit()
    db_session.refresh(leave_type)
    return leave_type


def test_non_admin_cannot_list_approval_routing(client, db_session):
    _, _, manager_headers = _create_user_with_token(db_session, "manager@example.com", "MANAGER")

    response = client.get("/api/v1/admin/approval-routing", headers=manager_headers)

    assert response.status_code == 403


def test_admin_sees_default_chain_for_leave_types_without_a_rule(client, db_session):
    _create_leave_type(db_session, "Sick Leave")
    _create_leave_type(db_session, "Long Leave")
    _create_leave_type(db_session, "Emergency Leave")
    _, _, admin_headers = _create_user_with_token(db_session, "admin@example.com", "ADMIN")

    response = client.get("/api/v1/admin/approval-routing", headers=admin_headers)

    assert response.status_code == 200
    chains_by_name = {row["leave_type_name"]: row["approval_chain"] for row in response.json()}
    assert chains_by_name["Sick Leave"] == ["MANAGER"]
    assert chains_by_name["Long Leave"] == ["HR"]
    assert chains_by_name["Emergency Leave"] == ["MANAGER", "HR"]


def test_admin_can_update_approval_chain_for_a_leave_type(client, db_session):
    leave_type = _create_leave_type(db_session, "Casual Leave")
    _, _, admin_headers = _create_user_with_token(db_session, "admin2@example.com", "ADMIN")

    update_response = client.put(
        f"/api/v1/admin/approval-routing/{leave_type.id}",
        json={"approval_chain": ["hr", "admin"]},
        headers=admin_headers,
    )

    assert update_response.status_code == 200
    assert update_response.json()["approval_chain"] == ["HR", "ADMIN"]

    list_response = client.get("/api/v1/admin/approval-routing", headers=admin_headers)
    updated_row = next(
        row for row in list_response.json() if row["leave_type_id"] == leave_type.id
    )
    assert updated_row["approval_chain"] == ["HR", "ADMIN"]


def test_updated_chain_applies_to_newly_submitted_leave_requests(client, db_session):
    leave_type = _create_leave_type(db_session, "Casual Leave")
    _, _, admin_headers = _create_user_with_token(db_session, "admin3@example.com", "ADMIN")
    _, _, employee_headers = _create_user_with_token(db_session, "employee3@example.com", "EMPLOYEE")

    client.put(
        f"/api/v1/admin/approval-routing/{leave_type.id}",
        json={"approval_chain": ["HR"]},
        headers=admin_headers,
    )

    apply_response = client.post(
        "/api/v1/leaves/apply",
        data={
            "leave_type_id": leave_type.id,
            "start_date": "2026-01-05",
            "end_date": "2026-01-05",
            "reason": "test",
        },
        headers=employee_headers,
    )

    assert apply_response.status_code == 200
    assert apply_response.json()["approval_chain"] == "HR"


def test_invalid_role_in_chain_is_rejected(client, db_session):
    leave_type = _create_leave_type(db_session, "Casual Leave")
    _, _, admin_headers = _create_user_with_token(db_session, "admin4@example.com", "ADMIN")

    response = client.put(
        f"/api/v1/admin/approval-routing/{leave_type.id}",
        json={"approval_chain": ["EMPLOYEE"]},
        headers=admin_headers,
    )

    assert response.status_code == 422


def test_update_for_unknown_leave_type_returns_404(client, db_session):
    _, _, admin_headers = _create_user_with_token(db_session, "admin5@example.com", "ADMIN")

    response = client.put(
        "/api/v1/admin/approval-routing/999999",
        json={"approval_chain": ["HR"]},
        headers=admin_headers,
    )

    assert response.status_code == 404
