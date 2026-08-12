from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.leave_types import router as leave_types_router
from app.api.v1.endpoints.leaves import router as leaves_router


router = APIRouter()


@router.get("/")
def api_root():
    return {"message": "Employee Leave Application API v1"}


router.include_router(auth_router)
router.include_router(leave_types_router)
router.include_router(leaves_router)