from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from unittest import mock

from jose import jwt
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.core.security import create_access_token
from app.models.employee import Employee
from app.models.leave_application import LeaveApplication
from app.models.user import User


def _create_employee_with_token(db_session, email):
    user = User(email=email, password="secret123", role="EMPLOYEE", is_active=True)
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


def _create_leave(db_session, employee_user_id, leave_status="PENDING"):
    leave = LeaveApplication(
        employee_id=employee_user_id,
        leave_type_id=None,
        start_date=date.today(),
        end_date=date.today(),
        days_count=Decimal("1"),
        reason="test leave",
        status=leave_status,
        applied_at=datetime.utcnow(),
    )
    db_session.add(leave)
    db_session.commit()
    db_session.refresh(leave)
    return leave


# --- value absent / empty / null -------------------------------------------------


def test_delete_leave_without_auth_token_returns_401(client):
    response = client.delete("/api/v1/leaves/1")

    assert response.status_code == 401


def test_delete_leave_with_missing_id_in_path_returns_404(client, db_session):
    _, _, headers = _create_employee_with_token(db_session, "missingid@example.com")

    response = client.delete("/api/v1/leaves/", headers=headers)

    assert response.status_code == 404


def test_delete_leave_with_null_literal_id_returns_422(client, db_session):
    _, _, headers = _create_employee_with_token(db_session, "nullid@example.com")

    response = client.delete("/api/v1/leaves/null", headers=headers)

    assert response.status_code == 422


# --- string where a number was expected -------------------------------------------


def test_delete_leave_with_non_numeric_id_returns_422(client, db_session):
    _, _, headers = _create_employee_with_token(db_session, "stringid@example.com")

    response = client.delete("/api/v1/leaves/abc", headers=headers)

    assert response.status_code == 422


def test_delete_leave_with_decimal_id_returns_422(client, db_session):
    _, _, headers = _create_employee_with_token(db_session, "decimalid@example.com")

    response = client.delete("/api/v1/leaves/1.5", headers=headers)

    assert response.status_code == 422


# --- rejected / unauthorized requests -----------------------------------------------


def test_delete_leave_with_malformed_token_returns_401(client, db_session):
    response = client.delete(
        "/api/v1/leaves/1", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert response.status_code == 401


def test_delete_leave_with_expired_token_returns_401(client, db_session):
    user, _, _ = _create_employee_with_token(db_session, "expired@example.com")

    expired_token = jwt.encode(
        {
            "sub": str(user.id),
            "role": user.role,
            "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response = client.delete(
        "/api/v1/leaves/1", headers={"Authorization": f"Bearer {expired_token}"}
    )

    assert response.status_code == 401


def test_delete_leave_for_inactive_user_returns_403(client, db_session):
    user = User(email="inactive@example.com", password="secret123", role="EMPLOYEE", is_active=False)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(user_id=user.id, role=user.role)

    response = client.delete("/api/v1/leaves/1", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


def test_delete_leave_without_bearer_prefix_returns_401(client, db_session):
    user, _, _ = _create_employee_with_token(db_session, "nobearer@example.com")
    token = create_access_token(user_id=user.id, role=user.role)

    response = client.delete("/api/v1/leaves/1", headers={"Authorization": token})

    assert response.status_code == 401


# --- leave requests that are no longer pending --------------------------------------


def test_delete_leave_with_approved_status_returns_400(client, db_session):
    user, _, headers = _create_employee_with_token(db_session, "approved@example.com")
    leave = _create_leave(db_session, user.id, leave_status="APPROVED")

    response = client.delete(f"/api/v1/leaves/{leave.id}", headers=headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "Only pending leave requests can be deleted."


def test_delete_leave_with_rejected_status_returns_400(client, db_session):
    user, _, headers = _create_employee_with_token(db_session, "rejected@example.com")
    leave = _create_leave(db_session, user.id, leave_status="REJECTED")

    response = client.delete(f"/api/v1/leaves/{leave.id}", headers=headers)

    assert response.status_code == 400


def test_delete_leave_with_cancelled_status_returns_400(client, db_session):
    user, _, headers = _create_employee_with_token(db_session, "cancelled@example.com")
    leave = _create_leave(db_session, user.id, leave_status="CANCELLED")

    response = client.delete(f"/api/v1/leaves/{leave.id}", headers=headers)

    assert response.status_code == 400


# --- valid-looking id that matches nothing -----------------------------------------


def test_delete_leave_with_nonexistent_id_returns_404(client, db_session):
    _, _, headers = _create_employee_with_token(db_session, "noexist@example.com")

    response = client.delete("/api/v1/leaves/999999", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Leave request not found."


def test_delete_leave_owned_by_another_employee_returns_404(client, db_session):
    owner, _, _ = _create_employee_with_token(db_session, "owner@example.com")
    _, _, other_headers = _create_employee_with_token(db_session, "intruder@example.com")
    leave = _create_leave(db_session, owner.id)

    response = client.delete(f"/api/v1/leaves/{leave.id}", headers=other_headers)

    assert response.status_code == 404


# --- zero, negative, one item, ten thousand items ----------------------------------


def test_delete_leave_with_zero_id_returns_404(client, db_session):
    _, _, headers = _create_employee_with_token(db_session, "zeroid@example.com")

    response = client.delete("/api/v1/leaves/0", headers=headers)

    assert response.status_code == 404


def test_delete_leave_with_negative_id_returns_404(client, db_session):
    _, _, headers = _create_employee_with_token(db_session, "negativeid@example.com")

    response = client.delete("/api/v1/leaves/-1", headers=headers)

    assert response.status_code == 404


def test_delete_single_leave_succeeds(client, db_session):
    user, _, headers = _create_employee_with_token(db_session, "single@example.com")
    leave = _create_leave(db_session, user.id)

    response = client.delete(f"/api/v1/leaves/{leave.id}", headers=headers)

    assert response.status_code == 200
    assert response.json() == {"message": "Leave request deleted successfully."}
    assert db_session.query(LeaveApplication).filter(LeaveApplication.id == leave.id).first() is None


def test_delete_leave_succeeds_among_ten_thousand_records(client, db_session):
    user, _, headers = _create_employee_with_token(db_session, "bulk@example.com")
    target = _create_leave(db_session, user.id)

    filler_rows = [
        {
            "employee_id": user.id,
            "leave_type_id": None,
            "start_date": date.today(),
            "end_date": date.today(),
            "days_count": Decimal("1"),
            "reason": "filler",
            "status": "PENDING",
            "applied_at": datetime.utcnow(),
        }
        for _ in range(10000)
    ]
    db_session.bulk_insert_mappings(LeaveApplication, filler_rows)
    db_session.commit()

    assert db_session.query(LeaveApplication).count() == 10001

    response = client.delete(f"/api/v1/leaves/{target.id}", headers=headers)

    assert response.status_code == 200
    assert response.json() == {"message": "Leave request deleted successfully."}
    assert db_session.query(LeaveApplication).count() == 10000
    assert db_session.query(LeaveApplication).filter(LeaveApplication.id == target.id).first() is None


# --- the same request arrives twice -------------------------------------------------


def test_deleting_the_same_leave_twice_returns_404_on_second_attempt(client, db_session):
    user, _, headers = _create_employee_with_token(db_session, "duplicate@example.com")
    leave = _create_leave(db_session, user.id)

    first_response = client.delete(f"/api/v1/leaves/{leave.id}", headers=headers)
    second_response = client.delete(f"/api/v1/leaves/{leave.id}", headers=headers)

    assert first_response.status_code == 200
    assert first_response.json() == {"message": "Leave request deleted successfully."}
    assert second_response.status_code == 404
    assert second_response.json()["detail"] == "Leave request not found."


# --- the database / network is unavailable ------------------------------------------


def test_delete_leave_returns_500_when_database_commit_fails(client, db_session):
    user, _, headers = _create_employee_with_token(db_session, "dbdown@example.com")
    leave = _create_leave(db_session, user.id)

    with mock.patch.object(
        db_session,
        "commit",
        side_effect=OperationalError("DELETE", {}, Exception("connection refused")),
    ):
        response = client.delete(f"/api/v1/leaves/{leave.id}", headers=headers)

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to delete leave request."

    # The record must still exist since the failed commit should have rolled back.
    assert db_session.query(LeaveApplication).filter(LeaveApplication.id == leave.id).first() is not None


def test_delete_leave_returns_500_when_lookup_query_fails(client, db_session):
    """
    The endpoint only wraps db.delete()/db.commit() in try/except - the initial
    ownership lookup (db.query(...).first()) is unprotected. If the database
    goes down during that lookup, the failure must still surface as the
    documented 500 + "Failed to delete leave request." response, same as a
    commit failure. This is a strict assertion of that contract: it does not
    special-case the lookup call, so it will fail loudly with the raw
    OperationalError instead of a clean assertion mismatch if the endpoint
    does not actually honor the contract there.
    """
    user, _, headers = _create_employee_with_token(db_session, "lookupdown@example.com")
    leave = _create_leave(db_session, user.id)

    original_query = db_session.query

    def query_that_fails_only_for_leave_lookup(model, *args, **kwargs):
        if model is LeaveApplication:
            raise OperationalError("SELECT", {}, Exception("connection refused"))
        return original_query(model, *args, **kwargs)

    with mock.patch.object(db_session, "query", side_effect=query_that_fails_only_for_leave_lookup):
        response = client.delete(f"/api/v1/leaves/{leave.id}", headers=headers)

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to delete leave request."
