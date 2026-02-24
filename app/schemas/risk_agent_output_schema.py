from pydantic import BaseModel, Field
from typing import Literal, Annotated


class RiskAgentOutput(BaseModel):
    """Model defining the expected output structure from the RiskAgent."""
    
    risk_level: Literal["Low", "Medium", "High"] = Field(
        description="Overall compliance risk classification."
    )

    reasoning: str = Field(
        description="Short explanation for the assigned risk level."
    )

    confidence: Annotated[
        float,
        Field(ge=0, le=1, description="Confidence score between 0 and 1.")
    ]

    model_config = {
        "extra": "forbid"
    }