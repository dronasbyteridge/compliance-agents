from app.config import LLM_MODEL  # ensures env config is applied before `agents` loads
from agents import Agent
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from app.tools.notification_tool import send_notification

notification_agent = Agent(
    name="Compliance Notification Agent",
    model=LLM_MODEL,
    instructions=RECOMMENDED_PROMPT_PREFIX + """
    You generate executive-ready compliance alerts.

    Create:
    - Clear subject line
    - Risk-highlighted summary
    - Immediate action instruction

    Then call send_notification tool.
    """,
    tools=[send_notification]
)
