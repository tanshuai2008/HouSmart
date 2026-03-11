from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.api.schemas.analysis import (
    AnalysisRunStatusResponse,
    DashboardPropertyResponse,
    PropertyAnalyzeRequest,
    PropertyAnalyzeResponse,
)
from app.services.analysis_orchestrator import analyze_property_for_user
from app.services.analysis_repository import AnalysisRepository


router = APIRouter(prefix="/api", tags=["Property Analysis"])


@router.post("/property/analyze", response_model=PropertyAnalyzeResponse)
async def analyze_property(payload: PropertyAnalyzeRequest):
    try:
        result = await analyze_property_for_user(
            user_id=payload.user_id,
            address=payload.address,
        )
        return PropertyAnalyzeResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/property/analyze/{run_id}", response_model=AnalysisRunStatusResponse)
def get_analysis_run_status(run_id: UUID):
    row = AnalysisRepository.get_run(run_id=str(run_id))
    if not row:
        raise HTTPException(status_code=404, detail="Run not found")

    return AnalysisRunStatusResponse(
        run_id=row["run_id"],
        property_id=row["property_id"],
        status=row["status"],
        error_message=row.get("error_message"),
    )


@router.get("/dashboard/property/{property_id}", response_model=DashboardPropertyResponse)
def get_dashboard_property(property_id: UUID, user_id: UUID = Query(...)):
    payload = AnalysisRepository.get_dashboard_payload(
        user_id=str(user_id),
        property_id=str(property_id),
    )
    return DashboardPropertyResponse(**payload)
