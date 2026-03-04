from pydantic import BaseModel, Field
from typing import Literal


class UrgencyAgentOutput(BaseModel):
    """Model defining the expected output structure from the UrgencyAgent."""

    urgency_level: Literal["Critical", "High", "Medium", "Low"] = Field(
        default="Low",
        description="The urgency level of the compliance action required. Must be one of: Critical, High, Medium, Low.",
    )

    days_until_effective: int = Field(
        default=0,
        ge=0,
        description="Number of days remaining until the legislation becomes effective. Must be a non-negative integer.",
    )

    recommended_action: str = Field(
        default="Monitor and plan accordingly.",
        min_length=5,
        max_length=500,
        description="Short concrete action to take based on urgency level and deadline.",
    )

    reasoning: str = Field(
        default="No reasoning provided.",
        min_length=5,
        max_length=1000,
        description="Brief explanation of why this urgency level was assigned based on the effective date and risk level.",
    )

    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence score for the urgency classification. Must be a float between 0.0 and 1.0.",
    )

    model_config = {"extra": "forbid"}
