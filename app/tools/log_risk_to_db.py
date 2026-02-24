from agents import function_tool
from app.db.db import get_db


@function_tool
def log_risk_to_db(legislation_id: int, risk_level: str, reasoning: str) -> str:
    """
    Persist risk classification into the compliance_audit table.
    Only logs if legislation_id is present and not null.
    Automatically escalates if risk_level is High.

    Args:
        legislation_id: The ID of the legislation record. Must be non-null.
        risk_level: The assessed risk level ("Low", "Medium", or "High").
        reasoning: Short explanation for the risk classification.

    Returns:
        A confirmation string or a skip message.
    """
    
    if not legislation_id or str(legislation_id).strip().lower() in (
        "none",
        "null",
        "0",
        "",
    ):
        return "Skipped: legislation_id is null or missing."

    escalated = risk_level == "High"

    with get_db() as (conn, cursor):
        cursor.execute(
            """
            INSERT INTO compliance_audit
            (legislation_id, action_taken, risk_level, escalated)
            VALUES (%s, %s, %s, %s)
        """,
            (
                legislation_id,
                reasoning,
                risk_level,
                escalated,
            ),
        )

    return f"Risk logged for legislation #{legislation_id}: {risk_level} (escalated={escalated})"


