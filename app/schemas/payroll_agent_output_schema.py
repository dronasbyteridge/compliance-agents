from pydantic import BaseModel, Field
from typing import Literal, Annotated


class PayrollAgentOutput(BaseModel):
    """Pydantic model defining the expected output structure from the PayrollAgent."""

    payroll_action_required: str = Field(
        description="Description of the payroll action required."
    )

    requires_system_update: bool = Field(
        description="Whether a payroll system update is required."
    )

    employee_recalculation_required: bool = Field(
        description="Whether employee-level recalculation is required."
    )

    urgency: Literal["Low", "Medium", "High"] = Field(
        description="Urgency level of the payroll action."
    )

    confidence: Annotated[
        float, Field(ge=0, le=1, description="Confidence score between 0 and 1.")
    ]

    # If any field is present that is NOT defined in the model → raise a validation error.
    model_config = {"extra": "forbid"}
