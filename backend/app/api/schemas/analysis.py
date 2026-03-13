from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PropertyAnalyzeRequest(BaseModel):
    user_id: UUID
    address: str = Field(..., min_length=3)


class PropertyAnalyzeResponse(BaseModel):
    run_id: UUID
    property_id: UUID
    status: str
    source_map: Optional[dict[str, str]] = None


class AnalysisRunStatusResponse(BaseModel):
    run_id: UUID
    property_id: UUID
    status: str
    error_message: Optional[str] = None


class DashboardPropertyResponse(BaseModel):
    property: Optional[dict[str, Any]] = None
    latest_run: Optional[dict[str, Any]] = None
    facts: Optional[dict[str, Any]] = None
    scores: Optional[dict[str, Any]] = None
    comparables: list[dict[str, Any]] = Field(default_factory=list)


class RecentSearchItem(BaseModel):
    property_id: UUID
    address: str
