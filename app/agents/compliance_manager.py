import json
import asyncio
import pandas as pd
from app.rag.rag_engine import query_rag
from app.tools.impact_tool import calculate_impact
from app.agents.legal_agent import legal_agent
from app.agents.payroll_agent import payroll_agent
from app.agents.risk_agent import risk_agent, log_risk_to_db
from app.db.db import get_db
from agents import Runner


async def run_compliance_flow_async(user_input: str):

    try:
        # ==================================================
        # 1️⃣ RAG – Retrieve legislation context
        # ==================================================
        rag_context = query_rag(user_input)

        if not rag_context:
            return {
                "summary": "No legislation found.",
                "country": "",
                "new_rate": 0,
                "impacted_employees": 0,
                "annual_cost_increase": 0,
                "payroll_urgency": "",
                "risk_level": "",
                "confidence": 0,
                "employee_rows": [],
                "csv_path": None
            }

        # ==================================================
        # 2️⃣ Legal Interpretation Agent
        # ==================================================
        legal_result = await Runner.run(
            legal_agent,
            input=[{"role": "user", "content": rag_context}],
        )
        legal_raw = legal_result.final_output_as(str)
        legal_json = json.loads(legal_raw)

        country = legal_json.get("country", "")
        raw_new_rate = float(legal_json.get("new_rate", 0))

        # The legal agent may return rates either as percentages (e.g. 5 for 5%)
        # or as decimals (e.g. 0.05). We normalize to:
        # - new_rate_decimal: for calculations / DB (0.05)
        # - display_new_rate: for UI (5.0 for 5%)
        if raw_new_rate > 1:
            new_rate_decimal = raw_new_rate / 100.0
            display_new_rate = raw_new_rate
        else:
            new_rate_decimal = raw_new_rate
            display_new_rate = raw_new_rate * 100.0 if raw_new_rate > 0 else 0.0

        summary = legal_json.get("summary", "")
        legal_conf = float(legal_json.get("confidence", 0.7))

        # ==================================================
        # 3️⃣ Payroll Agent
        # ==================================================
        payroll_input = f"""
        Country: {country}
        New Rate (%): {display_new_rate}
        Summary: {summary}
        """

        payroll_result = await Runner.run(
            payroll_agent,
            input=[{"role": "user", "content": payroll_input}],
        )
        payroll_raw = payroll_result.final_output_as(str)
        payroll_json = json.loads(payroll_raw)
        payroll_conf = float(payroll_json.get("confidence", 0.7))
        payroll_action_required = payroll_json.get("payroll_action_required", "")
        requires_system_update = payroll_json.get("requires_system_update")
        employee_recalculation_required = payroll_json.get("employee_recalculation_required")

        # ==================================================
        # 4️⃣ Fetch Latest Legislation ID from DB
        # ==================================================
        legislation_id = None
        with get_db() as (conn, cursor):
            cursor.execute("""
                SELECT id FROM legislation
                WHERE country = %s
                ORDER BY effective_date DESC
                LIMIT 1
            """, (country,))
            row = cursor.fetchone()
            if row:
                legislation_id = row["id"]

        # ==================================================
        # 5️⃣ Impact Calculation
        # ==================================================
        impact_data = {
            "impacted_employees": 0,
            "annual_cost_increase": 0,
            "employee_rows": []
        }

        if new_rate_decimal and legislation_id:
            impact_data = calculate_impact(
                country=country,
                new_rate=new_rate_decimal,
                legislation_id=legislation_id
            )

        impacted_count = impact_data.get("impacted_employees", 0)
        annual_cost = impact_data.get("annual_cost_increase", 0)
        employee_rows = impact_data.get("employee_rows", [])

        # ==================================================
        # 6️⃣ Risk Agent
        # ==================================================
        risk_input = f"""
        Legal Summary: {summary}
        New Rate (%): {display_new_rate}
        Payroll Urgency: {payroll_json.get('urgency')}
        Impacted Employees: {impacted_count}
        Annual Cost Increase: {annual_cost}
        """

        risk_result = await Runner.run(
            risk_agent,
            input=[{"role": "user", "content": risk_input}],
        )
        risk_raw = risk_result.final_output_as(str)
        risk_json = json.loads(risk_raw)
        risk_conf = float(risk_json.get("confidence", 0.7))
        risk_reasoning = risk_json.get("reasoning", "")

        if legislation_id:
            log_risk_to_db(legislation_id, risk_json)

        # ==================================================
        # 7️⃣ Aggregate Confidence
        # ==================================================
        final_conf = round(
            (legal_conf + payroll_conf + risk_conf) / 3,
            2
        )

        # ==================================================
        # 8️⃣ Generate CSV
        # ==================================================
        csv_path = None
        if employee_rows:
            df = pd.DataFrame(employee_rows)
            csv_path = "impacted_employees.csv"
            df.to_csv(csv_path, index=False)

        # ==================================================
        # 9️⃣ High-level Recommended Actions (for UI)
        # ==================================================
        recommendations = (
            "Recommended actions:\n"
            f"- Payroll action: {payroll_action_required or 'N/A'}\n"
            f"- Update payroll system: {'Yes' if requires_system_update else 'No'}\n"
            f"- Recalculate employee records: {'Yes' if employee_recalculation_required else 'No'}\n"
            f"- Risk level: {risk_json.get('risk_level', '')}\n"
            f"- Risk reasoning: {risk_reasoning or 'N/A'}\n"
            f"- Urgency: {payroll_json.get('urgency', '')}\n"
        )

        # ==================================================
        # 10️⃣ Final Structured JSON
        # ==================================================
        return {
            "summary": summary,
            "country": country,
            "new_rate": display_new_rate,
            "impacted_employees": impacted_count,
            "annual_cost_increase": annual_cost,
            "payroll_urgency": payroll_json.get("urgency"),
            "risk_level": risk_json.get("risk_level"),
            "confidence": final_conf,
            "employee_rows": employee_rows,
            "csv_path": csv_path,
            "payroll_action_required": payroll_action_required,
            "requires_system_update": requires_system_update,
            "employee_recalculation_required": employee_recalculation_required,
            "risk_reasoning": risk_reasoning,
            "recommendations": recommendations,
        }

    except Exception as e:
        return {
            "summary": f"Error: {str(e)}",
            "country": "",
            "new_rate": 0,
            "impacted_employees": 0,
            "annual_cost_increase": 0,
            "payroll_urgency": "",
            "risk_level": "",
            "confidence": 0,
            "employee_rows": [],
            "csv_path": None,
            "payroll_action_required": "",
            "requires_system_update": False,
            "employee_recalculation_required": False,
            "risk_reasoning": "",
            "recommendations": f"Error occurred while running compliance flow: {str(e)}",
        }


def run_compliance_flow(user_input: str):
    """
    Synchronous wrapper for UI code paths (Gradio, scripts).
    """
    return asyncio.run(run_compliance_flow_async(user_input))
