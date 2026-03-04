from pydantic import BaseModel, Field


class LegalComplianceOutput(BaseModel):
    """Schema for Legal Compliance Output (returned exactly as JSON)."""

    country: str = Field(default="", description="Country where the regulation applies")
    effective_date: str = Field(
        default="",
        description="Effective date of the legal change in YYYY-MM-DD format",
    )
    previous_rate: float = Field(
        default=0.0,
        description="Previous rate mentioned in the text. Return 0.0 if not mentioned.",
    )
    new_rate: float = Field(
        default=0.0,
        description="New rate mentioned in the text. Return 0.0 if not mentioned.",
    )
    category: str = Field(
        default="",
        description="Policy category such as pension, social_security, minimum_wage, etc.",
    )
    summary: str = Field(
        default="", description="Brief summary of the regulatory change"
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence score between 0 and 1"
    )

    # Forbid extra fields to ensure strict JSON output matching the model
    model_config = {"extra": "forbid"}
