from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class OnboardingUpsertRequest(BaseModel):
    user_id: UUID
    primary_role_ques: Optional[str] = None
    investment_experience_level_ques: Optional[str] = None
    investment_goal_ques: Optional[str] = None
    priorities_ranking_ques: list[str] = Field(default_factory=list)
