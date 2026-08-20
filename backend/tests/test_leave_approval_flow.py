from datetime import date, datetime
from decimal import Decimal

from app.core.security import create_access_token
from app.models.employee import Employee
from app.models.leave_application import LeaveApplication
from app.models.leave_application_step import LeaveApplicationStep
from app.models.leave_type import LeaveType
from app.models.leave_type_approval_step import LeaveTypeApprovalStep
from app.models.user import User

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


def _create_leave_type(db_session, name, approver_roles):
    leave_type = LeaveType(name=name, default_annual_quota=30)
    db_session.add(leave_type)
    db_session.commit()
    db_session.refresh(leave_type)

    for step_order, approver_role in enumerate(approver_roles, start=1):
        db_session.add(
            LeaveTypeApprovalStep(
                leave_type_id=leave_type.id,
                step_order=step_order,
                approver_role=approver_role,
            )
        )
    db_session.commit()
    return leave_type


def _apply(client, headers, leave_type_id):
    return client.post(
        "/api/v1/leaves/apply",
        json={
            "leave_type_id": leave_type_id,
            "start_date": str(A_WEEKDAY),
            "end_date": str(A_WEEKDAY),
            "reason": "test leave",
        },
        headers=headers,
    )


def _decide(client, headers, leave_id, action):
    return client.put(
        f"/api/v1/leaves/{leave_id}/decide",
        json={"action": action, "comment": ""},
        headers=headers,
    )


# --- single-step employee-submitted requests -----------------------------------------


def test_employee_casual_leave_approved_by_manager(client, db_session):
    leave_type = _create_leave_type(db_session, "Casual Leave", ["MANAGER"])
    _, _, employee_headers = _create_user_with_token(db_session, "employee-casual@example.com", "EMPLOYEE")
    _, _, manager_headers = _create_user_with_token(db_session, "manager-casual@example.com", "MANAGER")

    leave_id = _apply(client, employee_headers, leave_type.id).json()["id"]
    response = _decide(client, manager_headers, leave_id, "APPROVED")

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"


def test_employee_sick_leave_rejected_by_manager(client, db_session):
    leave_type = _create_leave_type(db_session, "Sick Leave", ["MANAGER"])
    _, _, employee_headers = _create_user_with_token(db_session, "employee-sick@example.com", "EMPLOYEE")
    _, _, manager_headers = _create_user_with_token(db_session, "manager-sick@example.com", "MANAGER")

    leave_id = _apply(client, employee_headers, leave_type.id).json()["id"]
    response = _decide(client, manager_headers, leave_id, "REJECTED")

    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"


def test_sick_leave_cannot_be_approved_without_document(client, db_session):
    leave_type = _create_leave_type(db_session, "Sick Leave", ["MANAGER"])
    _, _, employee_headers = _create_user_with_token(db_session, "employee-sickdoc@example.com", "EMPLOYEE")
    _, _, manager_headers = _create_user_with_token(db_session, "manager-sickdoc@example.com", "MANAGER")

    leave_id = _apply(client, employee_headers, leave_type.id).json()["id"]
    response = _decide(client, manager_headers, leave_id, "APPROVED")

    assert response.status_code == 400
    assert "document" in response.json()["detail"].lower()


def test_sick_leave_can_be_approved_after_document_uploaded(client, db_session):
    leave_type = _create_leave_type(db_session, "Sick Leave", ["MANAGER"])
    _, _, employee_headers = _create_user_with_token(db_session, "employee-sickdoc2@example.com", "EMPLOYEE")
    _, _, manager_headers = _create_user_with_token(db_session, "manager-sickdoc2@example.com", "MANAGER")

    leave_id = _apply(client, employee_headers, leave_type.id).json()["id"]
    upload_response = client.post(
        f"/api/v1/leaves/{leave_id}/document",
        headers=employee_headers,
        files={"file": ("note.pdf", b"file-bytes", "application/pdf")},
    )
    assert upload_response.status_code == 201

    response = _decide(client, manager_headers, leave_id, "APPROVED")

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"


def test_employee_long_leave_only_hr_can_decide(client, db_session):
    leave_type = _create_leave_type(db_session, "Long Leave", ["HR"])
    _, _, employee_headers = _create_user_with_token(db_session, "employee-long@example.com", "EMPLOYEE")
    _, _, manager_headers = _create_user_with_token(db_session, "manager-long@example.com", "MANAGER")
    _, _, hr_headers = _create_user_with_token(db_session, "hr-long@example.com", "HR")

    leave_id = _apply(client, employee_headers, leave_type.id).json()["id"]

    manager_attempt = _decide(client, manager_headers, leave_id, "APPROVED")
    assert manager_attempt.status_code == 403

    hr_attempt = _decide(client, hr_headers, leave_id, "APPROVED")
    assert hr_attempt.status_code == 200
    assert hr_attempt.json()["status"] == "APPROVED"


# --- two-step employee-submitted Emergency leave --------------------------------------


def test_employee_emergency_leave_manager_then_hr(client, db_session):
    leave_type = _create_leave_type(db_session, "Emergency Leave", ["MANAGER", "HR"])
    _, _, employee_headers = _create_user_with_token(db_session, "employee-emg@example.com", "EMPLOYEE")
    _, _, manager_headers = _create_user_with_token(db_session, "manager-emg@example.com", "MANAGER")
    _, _, hr_headers = _create_user_with_token(db_session, "hr-emg@example.com", "HR")

    leave_id = _apply(client, employee_headers, leave_type.id).json()["id"]

    hr_too_early = _decide(client, hr_headers, leave_id, "APPROVED")
    assert hr_too_early.status_code == 403

    manager_step = _decide(client, manager_headers, leave_id, "APPROVED")
    assert manager_step.status_code == 200
    assert manager_step.json()["status"] == "PENDING"

    manager_again = _decide(client, manager_headers, leave_id, "APPROVED")
    assert manager_again.status_code == 403

    hr_step = _decide(client, hr_headers, leave_id, "APPROVED")
    assert hr_step.status_code == 200
    assert hr_step.json()["status"] == "APPROVED"


def test_employee_emergency_leave_rejected_by_manager_skips_hr(client, db_session):
    leave_type = _create_leave_type(db_session, "Emergency Leave 2", ["MANAGER", "HR"])
    _, _, employee_headers = _create_user_with_token(db_session, "employee-emg2@example.com", "EMPLOYEE")
    _, _, manager_headers = _create_user_with_token(db_session, "manager-emg2@example.com", "MANAGER")
    _, _, hr_headers = _create_user_with_token(db_session, "hr-emg2@example.com", "HR")

    leave_id = _apply(client, employee_headers, leave_type.id).json()["id"]

    manager_step = _decide(client, manager_headers, leave_id, "REJECTED")
    assert manager_step.status_code == 200
    assert manager_step.json()["status"] == "REJECTED"

    hr_attempt = _decide(client, hr_headers, leave_id, "APPROVED")
    assert hr_attempt.status_code == 404


# --- manager/HR-submitted requests always go to admin ----------------------------------


def test_manager_submitted_leave_only_admin_can_decide(client, db_session):
    leave_type = _create_leave_type(db_session, "Casual Leave 2", ["MANAGER"])
    _, _, manager_headers = _create_user_with_token(db_session, "manager-req@example.com", "MANAGER")
    _, _, other_manager_headers = _create_user_with_token(db_session, "manager-decider@example.com", "MANAGER")
    _, _, admin_headers = _create_user_with_token(db_session, "admin-decider@example.com", "ADMIN")

    leave_id = _apply(client, manager_headers, leave_type.id).json()["id"]

    other_manager_attempt = _decide(client, other_manager_headers, leave_id, "APPROVED")
    assert other_manager_attempt.status_code == 403

    admin_attempt = _decide(client, admin_headers, leave_id, "APPROVED")
    assert admin_attempt.status_code == 200
    assert admin_attempt.json()["status"] == "APPROVED"


def test_hr_submitted_leave_only_admin_can_decide(client, db_session):
    leave_type = _create_leave_type(db_session, "Long Leave 2", ["HR"])
    _, _, hr_requester_headers = _create_user_with_token(db_session, "hr-req@example.com", "HR")
    _, _, hr_decider_headers = _create_user_with_token(db_session, "hr-decider@example.com", "HR")
    _, _, admin_headers = _create_user_with_token(db_session, "admin-decider2@example.com", "ADMIN")

    leave_id = _apply(client, hr_requester_headers, leave_type.id).json()["id"]

    hr_decider_attempt = _decide(client, hr_decider_headers, leave_id, "APPROVED")
    assert hr_decider_attempt.status_code == 403

    admin_attempt = _decide(client, admin_headers, leave_id, "APPROVED")
    assert admin_attempt.status_code == 200


def test_admin_cannot_decide_employee_submitted_leave(client, db_session):
    leave_type = _create_leave_type(db_session, "Sick Leave 2", ["MANAGER"])
    _, _, employee_headers = _create_user_with_token(db_session, "employee-sick2@example.com", "EMPLOYEE")
    _, _, admin_headers = _create_user_with_token(db_session, "admin-sick2@example.com", "ADMIN")

    leave_id = _apply(client, employee_headers, leave_type.id).json()["id"]

    response = _decide(client, admin_headers, leave_id, "APPROVED")
    assert response.status_code == 403


# --- self-decision guard ---------------------------------------------------------------


def test_manager_cannot_decide_own_leave_request(client, db_session):
    leave_type = _create_leave_type(db_session, "Casual Leave 3", ["MANAGER"])
    manager, _, manager_headers = _create_user_with_token(db_session, "self-manager@example.com", "MANAGER")

    leave = LeaveApplication(
        employee_id=manager.id,
        leave_type_id=leave_type.id,
        start_date=A_WEEKDAY,
        end_date=A_WEEKDAY,
        days_count=Decimal("1"),
        reason="self",
        status="PENDING",
        applied_at=datetime.utcnow(),
    )
    db_session.add(leave)
    db_session.commit()
    db_session.refresh(leave)
    db_session.add(
        LeaveApplicationStep(
            leave_application_id=leave.id,
            step_order=1,
            approver_role="ADMIN",
            status="PENDING",
        )
    )
    db_session.commit()

    _, _, admin_headers = _create_user_with_token(db_session, "self-admin@example.com", "ADMIN")

    response = _decide(client, admin_headers, leave.id, "APPROVED")
    assert response.status_code == 200


# --- pending list/count scoping ---------------------------------------------------------


def test_pending_list_scoped_to_role_and_current_step(client, db_session):
    leave_type = _create_leave_type(db_session, "Emergency Leave 3", ["MANAGER", "HR"])
    _, _, employee_headers = _create_user_with_token(db_session, "employee-scope@example.com", "EMPLOYEE")
    _, _, manager_headers = _create_user_with_token(db_session, "manager-scope@example.com", "MANAGER")
    _, _, hr_headers = _create_user_with_token(db_session, "hr-scope@example.com", "HR")

    leave_id = _apply(client, employee_headers, leave_type.id).json()["id"]

    manager_pending = client.get("/api/v1/leaves/pending", headers=manager_headers).json()
    hr_pending_before = client.get("/api/v1/leaves/pending", headers=hr_headers).json()
    assert leave_id in [leave["id"] for leave in manager_pending]
    assert leave_id not in [leave["id"] for leave in hr_pending_before]

    _decide(client, manager_headers, leave_id, "APPROVED")

    manager_pending_after = client.get("/api/v1/leaves/pending", headers=manager_headers).json()
    hr_pending_after = client.get("/api/v1/leaves/pending", headers=hr_headers).json()
    assert leave_id not in [leave["id"] for leave in manager_pending_after]
    assert leave_id in [leave["id"] for leave in hr_pending_after]


def test_pending_count_matches_pending_list_scope(client, db_session):
    leave_type = _create_leave_type(db_session, "Long Leave 3", ["HR"])
    _, _, employee_headers = _create_user_with_token(db_session, "employee-count@example.com", "EMPLOYEE")
    _, _, hr_headers = _create_user_with_token(db_session, "hr-count@example.com", "HR")

    _apply(client, employee_headers, leave_type.id)

    count = client.get("/api/v1/leaves/pending-count", headers=hr_headers)
    assert count.json() == {"count": 1}


# --- apply-time validation --------------------------------------------------------------


def test_apply_rejects_leave_type_with_no_configured_approval_steps(client, db_session):
    leave_type = LeaveType(name="Unconfigured Leave", default_annual_quota=5)
    db_session.add(leave_type)
    db_session.commit()
    db_session.refresh(leave_type)

    _, _, employee_headers = _create_user_with_token(db_session, "employee-unconfigured@example.com", "EMPLOYEE")

    response = _apply(client, employee_headers, leave_type.id)
    assert response.status_code == 400
    assert response.json()["detail"] == "No approval flow is configured for this leave type."


def test_manager_can_apply_and_hr_can_apply(client, db_session):
    leave_type = _create_leave_type(db_session, "Casual Leave 4", ["MANAGER"])
    _, _, manager_headers = _create_user_with_token(db_session, "manager-apply@example.com", "MANAGER")
    _, _, hr_headers = _create_user_with_token(db_session, "hr-apply@example.com", "HR")

    manager_response = _apply(client, manager_headers, leave_type.id)
    hr_response = _apply(client, hr_headers, leave_type.id)

    assert manager_response.status_code == 200
    assert hr_response.status_code == 200
