from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_router
from app.db.base import Base
from app.db.database import engine, SessionLocal
from app.models.employee import Employee
from app.models.leave_type import LeaveType

app = FastAPI(title="Employee Leave Application")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.query(Employee).count() == 0:
            db.add_all(
                [
                    Employee(id=1, email="admin@example.com", full_name="Admin User", role="ADMIN", manager_id=None),
                    Employee(id=2, email="manager@example.com", full_name="Manager User", role="MANAGER", manager_id=1),
                    Employee(id=3, email="user@example.com", full_name="Employee User", role="EMPLOYEE", manager_id=2),
                ]
            )
            db.commit()

        if db.query(LeaveType).count() == 0:
            db.add_all(
                [
                    LeaveType(name="Annual", default_annual_quota=18, description="Standard annual leave"),
                    LeaveType(name="Sick", default_annual_quota=10, description="Sick leave"),
                    LeaveType(name="Casual", default_annual_quota=7, description="Casual leave"),
                ]
            )
            db.commit()


@app.get("/")
def read_root():
    return {"message": "Employee Leave Application API is running."}


@app.get("/health")
def health_check():
    return {"status": "ok"}
