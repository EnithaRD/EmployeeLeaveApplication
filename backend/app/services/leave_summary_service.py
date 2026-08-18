from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.models.leave_application import LeaveApplication


def get_monthly_status_counts(db: Session, year: int) -> list[dict]:
    rows = (
        db.query(
            extract("month", LeaveApplication.start_date).label("month"),
            LeaveApplication.status,
            func.count(LeaveApplication.id),
        )
        .filter(
            extract("year", LeaveApplication.start_date) == year,
            LeaveApplication.status.in_(["APPROVED", "REJECTED"]),
        )
        .group_by(
            extract("month", LeaveApplication.start_date),
            LeaveApplication.status,
        )
        .all()
    )

    counts = {month: {"approved": 0, "rejected": 0} for month in range(1, 13)}
    for month, status, count in rows:
        key = "approved" if status == "APPROVED" else "rejected"
        counts[int(month)][key] = int(count)

    return [
        {"month": month, "approved": data["approved"], "rejected": data["rejected"]}
        for month, data in counts.items()
    ]
