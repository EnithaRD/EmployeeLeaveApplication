from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import date

from app.api.v1.router import router as api_router
from app.db.base import Base
from app.db.database import SessionLocal, engine
from app.models.approval_routing_rule import ApprovalRoutingRule
from app.models.department import Department
from app.models.employee import Employee
from app.models.holiday import Holiday
from app.models.leave_application import LeaveApplication
from app.models.leave_balance import LeaveBalance
from app.models.leave_type import LeaveType
from app.models.medical_certificate import MedicalCertificate
from app.models.otp_code import OtpCode
from app.models.user import User
from app.services.approval_routing_service import seed_default_routing_rules


app = FastAPI(
    title="Employee Leave Application API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    api_router,
    prefix="/api/v1",
)


@app.on_event("startup")
def seed_demo_data():

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:

        general_department = (
            db.query(Department)
            .filter(Department.name == "General")
            .first()
        )
        if general_department is None:
            general_department = Department(name="General")
            db.add(general_department)
            db.commit()
            db.refresh(general_department)

        role_users = {
            "admin@example.com": ("Admin User", "ADMIN"),
            "manager@example.com": ("Manager User", "MANAGER"),
            "hr@example.com": ("HR User", "HR"),
            "employee@example.com": ("Employee User", "EMPLOYEE"),
        }

        users_by_email = {}
        for email, (_, role) in role_users.items():
            user = (
                db.query(User)
                .filter(User.email == email)
                .first()
            )
            if user is None:
                user = User(
                    email=email,
                    password="password",
                    role=role,
                    is_active=True,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            users_by_email[email] = user

        employee_rows = [
            (
                "admin@example.com",
                "Admin User",
                None,
            ),
            (
                "manager@example.com",
                "Manager User",
                users_by_email["admin@example.com"].id,
            ),
            (
                "hr@example.com",
                "HR User",
                users_by_email["admin@example.com"].id,
            ),
            (
                "employee@example.com",
                "Employee User",
                users_by_email["manager@example.com"].id,
            ),
        ]

        for email, full_name, manager_id in employee_rows:
            user = users_by_email[email]
            employee = (
                db.query(Employee)
                .filter(Employee.user_id == user.id)
                .first()
            )
            if employee is None:
                db.add(
                    Employee(
                        user_id=user.id,
                        full_name=full_name,
                        department_id=general_department.id,
                        manager_id=manager_id,
                        date_of_joining=date(2026, 1, 1),
                    )
                )

        default_leave_types = [
            LeaveType(
                name="Sick Leave",
                default_annual_quota=10,
                description="Medical leave",
            ),
            LeaveType(
                name="Casual Leave",
                default_annual_quota=8,
                description="Short personal leave",
            ),
            LeaveType(
                name="Earned Leave",
                default_annual_quota=15,
                description="Annual/vacation leave",
                is_active=False,
            ),
            LeaveType(
                name="Long Leave",
                default_annual_quota=20,
                description="Extended leave requiring HR approval",
            ),
            LeaveType(
                name="Emergency Leave",
                default_annual_quota=5,
                description="Urgent leave requiring manager and HR approval",
            ),
        ]
        existing_leave_type_names = {
            name for (name,) in db.query(LeaveType.name).all()
        }
        for leave_type in default_leave_types:
            if leave_type.name not in existing_leave_type_names:
                db.add(leave_type)

        db.commit()

        seed_default_routing_rules(db)


@app.get("/")
def root():
    return {
        "message": "Employee Leave Application API"
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}
