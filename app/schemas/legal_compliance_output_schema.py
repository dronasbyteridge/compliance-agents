from pydantic import BaseModel, Field


class LegalComplianceOutput(BaseModel):
    """Schema for Legal Compliance Output"""

    country: str = Field(description="Country where the regulation applies")
    effective_date: str = Field(description="Effective date of the legal change")
    previous_rate: float = Field(
        default=0.0,
        description="Previous rate mentioned in the text. Return 0.0 if not mentioned.",
    )
    new_rate: float = Field(
        default=0.0,
        description="New rate mentioned in the text. Return 0.0 if not mentioned.",
    )
    category: str = Field(
        description="Policy category such as income tax, social security, pension, minimum wage, etc."
    )
    summary: str = Field(description="Brief summary of the regulatory change")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence score between 0 and 1"
    )

    # If any field is present that is NOT defined in the model → raise a validation error.
    model_config = {"extra": "forbid"}
