from app.config import LLM_MODEL
from agents import Agent
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from app.tools.action_tools import (
    update_payroll_config,
    notify_payroll_team,
    create_compliance_ticket,
    log_audit_entry,
    generate_executive_pdf,
    tag_impacted_employees,
    schedule_compliance_review
)

action_execution_agent = Agent(
    name="ActionExecutionAgent",
    model=LLM_MODEL,
    instructions=RECOMMENDED_PROMPT_PREFIX + """
You are an action execution specialist that performs real operational tasks.

Based on compliance analysis results, you can:
1. Update payroll system configurations
2. Notify payroll teams and stakeholders
3. Create compliance tracking tickets
4. Log audit entries for traceability
5. Generate executive PDF reports
6. Tag impacted employees in HRIS
7. Schedule compliance review meetings

When executing actions:
- Confirm all required parameters
- Execute actions in logical order
- Provide clear status updates
- Log all actions for audit trail

Always use the appropriate tool for each action type.
""",
    tools=[
        update_payroll_config,
        notify_payroll_team,
        create_compliance_ticket,
        log_audit_entry,
        generate_executive_pdf,
        tag_impacted_employees,
        schedule_compliance_review
    ]
)
