from fastapi import APIRouter, HTTPException
from uuid import UUID

from app.api.schemas.onboarding import OnboardingUpsertRequest
from app.services.onboarding_service import (
    get_onboarding_answers_by_user_id,
    upsert_onboarding_answers,
)


router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.get("/{user_id}")
def get_onboarding_answers(user_id: UUID):
    try:
        answers = get_onboarding_answers_by_user_id(user_id)
        return {"answers": answers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("")
def save_onboarding_answers(payload: OnboardingUpsertRequest):
    try:
        data = payload.model_dump()
        data["user_id"] = str(payload.user_id)
        row = upsert_onboarding_answers(data)
        return {"message": "Onboarding answers saved", "answers": row}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
