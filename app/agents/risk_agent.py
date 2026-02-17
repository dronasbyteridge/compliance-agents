from app.config import LLM_MODEL  # ensures env config is applied before `agents` loads
from agents import Agent
from app.db.db import get_db
import json


risk_agent = Agent(
    name="RiskAgent",
    instructions="""
You are a payroll compliance risk classifier.

Classify compliance risk as:
- Low
- Medium
- High

Return STRICT JSON only in this format:

{
  "risk_level": "Low/Medium/High",
  "reasoning": "Short explanation",
  "confidence": 0.0
}

Rules:
- confidence must be between 0 and 1
- Do NOT add extra text
""",
    model=LLM_MODEL
)


def log_risk_to_db(legislation_id: int, risk_json: dict):
    """
    Persist risk classification into compliance_audit table.
    Automatically escalate if High.
    """

    risk_level = risk_json.get("risk_level")
    reasoning = risk_json.get("reasoning")

    escalated = True if risk_level == "High" else False

    with get_db() as (conn, cursor):
        cursor.execute("""
            INSERT INTO compliance_audit
            (legislation_id, action_taken, risk_level, escalated)
            VALUES (%s, %s, %s, %s)
        """, (
            legislation_id,
            reasoning,
            risk_level,
            escalated
        ))
