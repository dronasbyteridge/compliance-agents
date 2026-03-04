from agents import function_tool
from datetime import date, datetime


@function_tool
def calculate_days_until_effective(effective_date: str) -> dict:
    """
    Calculates the number of days remaining until the legislation's effective date.
    Also returns the urgency level based on standard thresholds:
        - Critical : fewer than 14 days OR already past due
        - High     : 14 to 30 days
        - Medium   : 31 to 90 days
        - Low      : more than 90 days

    Args:
        effective_date: The effective date of the legislation in YYYY-MM-DD format.

    Returns:
        A dictionary containing:
            - days_until_effective (int)
            - urgency_level (str)
            - effective_date (str)
            - today (str)
            - is_past_due (bool)
    """
    if not effective_date or str(effective_date).strip().lower() in (
        "none",
        "null",
        "",
    ):
        return {
            "days_until_effective": 0,
            "urgency_level": "Low",
            "effective_date": None,
            "today": date.today().isoformat(),
            "is_past_due": False,
            "error": "No effective date provided — defaulting to Low urgency.",
        }

    try:
        parsed_date = datetime.strptime(effective_date.strip(), "%Y-%m-%d").date()
    except ValueError:
        return {
            "days_until_effective": 0,
            "urgency_level": "Low",
            "effective_date": effective_date,
            "today": date.today().isoformat(),
            "is_past_due": False,
            "error": f"Invalid date format '{effective_date}' — expected YYYY-MM-DD.",
        }

    today = date.today()
    days_remaining = (parsed_date - today).days

    if days_remaining < 0:
        urgency_level = "Critical"
        is_past_due = True
    elif days_remaining < 14:
        urgency_level = "Critical"
        is_past_due = False
    elif days_remaining <= 30:
        urgency_level = "High"
        is_past_due = False
    elif days_remaining <= 90:
        urgency_level = "Medium"
        is_past_due = False
    else:
        urgency_level = "Low"
        is_past_due = False

    return {
        "days_until_effective": max(days_remaining, 0),
        "urgency_level": urgency_level,
        "effective_date": parsed_date.isoformat(),
        "today": today.isoformat(),
        "is_past_due": is_past_due,
    }
