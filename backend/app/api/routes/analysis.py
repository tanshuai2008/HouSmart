from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.api.schemas.analysis import (
    AnalysisRunStatusResponse,
    DashboardPropertyResponse,
    PropertyAnalyzeRequest,
    PropertyAnalyzeResponse,
    RecentSearchItem,
)
from app.core.supabase_client import supabase
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


@router.get("/property/recent-searches", response_model=list[RecentSearchItem])
def get_recent_searches(user_id: UUID = Query(...), limit: int = Query(default=3, ge=1, le=3)):
    rows = AnalysisRepository.list_recent_user_properties(user_id=str(user_id), limit=limit)
    return [
        RecentSearchItem(property_id=row["property_id"], address=row["address"])
        for row in rows
        if row.get("property_id") and row.get("address")
    ]

@router.post("/property/analyze/{run_id}/ai")
async def trigger_ai_recommendation(run_id: UUID):
    try:
        # 1. Get run details to find property and user
        run_row = AnalysisRepository.get_run(run_id=str(run_id))
        if not run_row:
            raise HTTPException(status_code=404, detail="Run not found")
        
        property_id = run_row["property_id"]
        # We need the user_id associated with this property
        prop_resp = supabase.table("user_properties").select("user_id").eq("property_id", property_id).single().execute()
        user_id = prop_resp.data["user_id"]

        # 2. Gather snapshot for AI
        snapshot = AnalysisRepository.get_ai_snapshot(
            user_id=user_id,
            property_id=property_id,
            run_id=str(run_id)
        )

        # 3. Call AI engine
        from app.ai.engine import generate_ai_recommendation
        
        result = generate_ai_recommendation(
            evaluation_id=str(run_id),
            evaluation_data=snapshot,
            priority_ranking=snapshot["onboarding"].get("priorities_ranking_ques"),
            user_profile=snapshot["onboarding"],
            db_session=supabase
        )

        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
