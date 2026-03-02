# HouSmart/backend/app/api/routes/health.py
from fastapi import APIRouter

router = APIRouter(prefix="/api")

@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "HouSmart Backend"
    }