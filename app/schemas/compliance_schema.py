from pydantic import BaseModel
from typing import Literal


class ComplianceResponse(BaseModel):
    summary: str
    effective_date: str
    countries_impacted: str
    payroll_components_impacted: str
    compliance_risk_level: Literal["Low", "Medium", "High"]
    action_required: str
    recommended_timeline: str
    escalation_required: bool
    confidence_score: float
