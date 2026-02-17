from agents.tool import function_tool
from app.config import NOTIFICATION_ENABLED


@function_tool
def send_notification(subject: str, message: str) -> str:
    """
    Sends compliance alert notification.
    """

    if not NOTIFICATION_ENABLED:
        return "Notification Disabled"

    # Replace with real email / Slack / MyView API
    print("\n--- Sending Notification ---")
    print("Subject:", subject)
    print("Message:", message)
    print("-----------------------------\n")

    return "Notification Sent Successfully"
