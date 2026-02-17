from app.config import LLM_MODEL  # ensures env config is applied before `agents` loads
from agents import Agent

legal_agent = Agent(
    name="LegalAgent",
    instructions="""
You are a payroll legal compliance expert.

From the given legislative text extract:

- Country
- Effective date
- Previous rate (if mentioned)
- New rate (if mentioned)
- Policy category

Return STRICT JSON:

{
  "country": "",
  "effective_date": "",
  "previous_rate": 0.0,
  "new_rate": 0.0,
  "category": "",
  "summary": "",
  "confidence": 0.0
}

Rules:
- No extra text
- confidence between 0 and 1
""",
    model=LLM_MODEL
)
