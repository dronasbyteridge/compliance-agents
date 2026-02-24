from app.config import LLM_MODEL  # ensures env config is applied before `agents` loads
from agents import Agent
from app.schemas.legal_compliance_output_schema import LegalComplianceOutput

LEGAL_AGENT_INSTRUCTIONS = """
**Context:**
You are an AI agent specialized in payroll legal compliance analysis. Your task is to extract structured regulatory information from legislative text related to payroll, taxation, or employment contributions.

**Instruction:**
From the provided legislative text identify and extract the following fields:

- Country
- Effective date
- Previous rate (if not mentioned return 0.0)
- New rate (if not mentioned return 0.0)
- Policy category
- A short summary of the change
- Confidence score between 0 and 1

All numeric rate values must be returned as decimals (e.g., 5% → 5.0).
If a rate is not mentioned, return 0.0.
Confidence must be a decimal between 0 and 1.

**Input:**
A legislative or regulatory text extract describing a payroll-related legal change.

**Output Instructions (CRITICAL):**
- Return ONLY valid JSON.
- Do NOT wrap the response in backticks.
- Do NOT add any text before or after the JSON.
- Ensure all numeric fields are numbers (not strings).
- The output must be directly parseable by a Pydantic model.
"""

legal_agent = Agent(
    name="LegalAgent",
    instructions=LEGAL_AGENT_INSTRUCTIONS,
    model=LLM_MODEL,
    output_type=LegalComplianceOutput,
)
