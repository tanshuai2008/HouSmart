from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


#Request

class EvaluatePropertyRequest(BaseModel):
    """
    Optional overrides when triggering an evaluation.
    The evaluation_id comes from the URL path parameter.
    """
    force_refresh: bool = Field(
        default=False,
        description="Re-run AI even if a cached summary already exists."
    )


#Variable snapshot (from DB)

class VariableSnapshot(BaseModel):
    status: str              # "pending" | "ready" | "failed"
    value: Optional[float]   = None
    source: Optional[str]    = None
    fetched_at: Optional[datetime] = None


class FinancialMetrics(BaseModel):
    monthly_cash_flow: Optional[float] = None
    cap_rate: Optional[float]          = None
    roi_5yr: Optional[float]           = None
    estimated_value: Optional[float]   = None


class PropertyInfo(BaseModel):
    formatted_address: Optional[str] = None
    state: Optional[str]             = None
    zip_code: Optional[str]          = None
    bedrooms: Optional[int]          = None
    bathrooms: Optional[float]       = None
    square_feet: Optional[int]       = None
    year_built: Optional[int]        = None
    property_type: Optional[str]     = None


class EvaluationData(BaseModel):
    """Full evaluation snapshot passed to the intelligence engine."""
    evaluation_id: str
    verdict_color: str = Field(..., pattern="^(green|yellow|red)$")
    property: PropertyInfo
    financials: FinancialMetrics
    variables: dict[str, VariableSnapshot] = Field(default_factory=dict)


#Policy highlight (in response)

class PolicyFinding(BaseModel):
    finding: str
    source: str


class PolicyHighlights(BaseModel):
    state: Optional[str]                       = None
    summary: Optional[str]                     = None
    threats: list[PolicyFinding]               = Field(default_factory=list)
    opportunities: list[PolicyFinding]         = Field(default_factory=list)
    key_obligations: list[PolicyFinding]       = Field(default_factory=list)
    str_restrictions: Optional[str]            = None


#AI Summary response

class AISummarySource(BaseModel):
    recommendation_model: Optional[str] = None
    policy_model: Optional[str]         = None
    policy_state: Optional[str]         = None


class EvaluatePropertyResponse(BaseModel):
    """
    Structured JSON returned to the dashboard by /evaluate-property/{evaluation_id}.
    """
    status: str = Field(..., description="complete | admin_review | error")

    # Verdict
    verdict_color: Optional[str]            = None
    data_completeness_pct: Optional[float]  = None

    # AI-generated narrative sections
    community_profile: Optional[str]        = None
    safety_and_amenities: Optional[str]     = None
    investment_suitability: Optional[str]   = None
    verdict_explanation: Optional[str]      = None
    key_strengths: list[str]                = Field(default_factory=list)
    key_risks: list[str]                    = Field(default_factory=list)
    missing_data_note: Optional[str]        = None

    # Policy (TX/WA/NC only)
    policy_highlights: Optional[PolicyHighlights] = None

    # Validation metadata
    admin_review_required: bool             = False
    validation_errors: list[str]            = Field(default_factory=list)
    validation_warnings: list[str]          = Field(default_factory=list)
    subjective_language_warning: Optional[str] = None

    # Source attribution
    sources: Optional[AISummarySource]      = None

    # Error (if status == "error")
    error: Optional[str]                    = None