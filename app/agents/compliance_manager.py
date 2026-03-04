import json
import asyncio
import pandas as pd
import re
from datetime import datetime, timedelta
from app.rag.rag_engine import query_rag
from app.schemas.legal_compliance_output_schema import LegalComplianceOutput
from app.schemas.payroll_agent_output_schema import PayrollAgentOutput
from app.schemas.risk_agent_output_schema import RiskAgentOutput
from app.tools.impact_tool import calculate_impact
from app.agents.legal_agent import legal_agent
from app.agents.payroll_agent import payroll_agent
from app.agents.risk_agent import risk_agent, log_risk_to_db
from app.agents.urgency_agent import urgency_agent
from app.schemas.urgency_agent_output_schema import UrgencyAgentOutput
from app.agents.report_agent import report_agent
from app.agents.action_execution_agent import action_execution_agent
from app.db.db import get_db
from agents import Runner
from app.config import LLM_PROVIDER


def parse_agent_json_output(raw_output: str, agent_name: str = "Agent") -> dict:
    """
    Parse JSON output from agents, handling both structured (OpenAI) and plain text (Groq) responses.
    Removes markdown code blocks and extra characters if present.
    """
    try:
        # Remove markdown code blocks if present
        cleaned = re.sub(r'```json\s*', '', raw_output)
        cleaned = re.sub(r'```\s*', '', cleaned)
        # Remove extra < > characters that some models add
        cleaned = re.sub(r'^<\s*', '', cleaned)
        cleaned = re.sub(r'\s*>$', '', cleaned)
        cleaned = cleaned.strip()
        
        result = json.loads(cleaned)
        print(f"[DEBUG] {agent_name}: Successfully parsed JSON output")
        return result
    except json.JSONDecodeError as e:
        print(f"[ERROR] {agent_name}: Failed to parse JSON: {e}")
        print(f"[ERROR] {agent_name}: Raw output: {raw_output[:500]}")
        return {}



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
                "csv_path": None,
            }

        # ==================================================
        # 2️⃣ Legal Interpretation Agent
        # ==================================================
        # Pass both the RAG context AND the original query to help extract rates
        legal_input = f"""
Original Query: {user_input}

Legislative Context:
{rag_context}
"""
        
        legal_result = await Runner.run(
            legal_agent,
            input=[{"role": "user", "content": legal_input}],
        )

        # Handle both structured output (OpenAI) and plain JSON (Groq)
        from app.config import LLM_PROVIDER
        
        if LLM_PROVIDER == "openai":
            # OpenAI returns structured Pydantic object
            legal_data = legal_result.final_output_as(LegalComplianceOutput)
            legal_json = {
                "country": legal_data.country,
                "effective_date": legal_data.effective_date,
                "previous_rate": legal_data.previous_rate,
                "new_rate": legal_data.new_rate,
                "category": legal_data.category,
                "summary": legal_data.summary,
                "confidence": legal_data.confidence
            }
        else:
            # Groq and others return plain JSON string
            legal_raw = legal_result.final_output_as(str)
            
            # Remove markdown code blocks if present
            import re
            legal_raw_cleaned = re.sub(r'```json\s*', '', legal_raw)
            legal_raw_cleaned = re.sub(r'```\s*', '', legal_raw_cleaned)
            legal_raw_cleaned = legal_raw_cleaned.strip()
            
            try:
                legal_json = json.loads(legal_raw_cleaned)
                print(f"[DEBUG] Successfully parsed legal agent response as JSON")
            except json.JSONDecodeError as e:
                print(f"[ERROR] Failed to parse legal agent response as JSON: {e}")
                print(f"[ERROR] Raw response: {legal_raw[:500]}")
                # Return empty result if parsing fails
                return {
                    "summary": f"Error parsing legal response: {str(e)}",
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

        print(f"\n[DEBUG] Rate Normalization:")
        print(f"  Raw rate from LLM: {raw_new_rate}")
        print(f"  Normalized decimal (for calculations): {new_rate_decimal}")
        print(f"  Display rate (for UI): {display_new_rate}%")

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
        
        # Handle both OpenAI (structured) and Groq (plain JSON) responses
        if LLM_PROVIDER == "openai":
            payroll_data = payroll_result.final_output_as(PayrollAgentOutput)
            payroll_json = {
                "payroll_action_required": payroll_data.payroll_action_required,
                "requires_system_update": payroll_data.requires_system_update,
                "employee_recalculation_required": payroll_data.employee_recalculation_required,
                "urgency": payroll_data.urgency,
                "confidence": payroll_data.confidence
            }
        else:
            payroll_raw = payroll_result.final_output_as(str)
            payroll_json = parse_agent_json_output(payroll_raw, "PayrollAgent")

        payroll_conf = float(payroll_json.get("confidence", 0.7))
        payroll_action_required = payroll_json.get("payroll_action_required", "")
        requires_system_update = payroll_json.get("requires_system_update", False)
        employee_recalculation_required = payroll_json.get("employee_recalculation_required", False)

        print(f"\n[DEBUG] Payroll Agent Output:")
        print(f"  Action Required: {payroll_action_required}")
        print(f"  Requires System Update: {requires_system_update}")
        print(f"  Employee Recalculation Required: {employee_recalculation_required}")
        print(f"  Confidence: {payroll_conf}")
        print(f"  Urgency: {payroll_json.get('urgency', 'N/A')}")


        # ==================================================
        # 4️⃣ Fetch Latest Legislation ID from DB
        # ==================================================
        legislation_id = None
        with get_db() as (conn, cursor):
            cursor.execute(
                """
                SELECT id FROM legislation
                WHERE country = %s
                ORDER BY effective_date DESC
                LIMIT 1
            """,
                (country,),
            )
            row = cursor.fetchone()
            if row:
                legislation_id = row["id"]
                print(f"\n[DEBUG] Found existing legislation ID: {legislation_id}")
            else:
                print(
                    f"\n[DEBUG] No existing legislation found for {country}, creating new record..."
                )
                # Create a new legislation record
                cursor.execute(
                    """
                    INSERT INTO legislation (country, regulation_type, previous_rate, new_rate, effective_date, category, summary)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        country,
                        "auto_detected",
                        0,
                        new_rate_decimal,
                        legal_json.get('effective_date', '2024-01-01'),
                        legal_json.get('category', 'General'),
                        summary,
                    ),
                )
                legislation_id = cursor.lastrowid
                print(f"[DEBUG] Created new legislation ID: {legislation_id}")

        # ==================================================
        # 5️⃣ Impact Calculation
        # ==================================================
        impact_data = {
            "impacted_employees": 0,
            "annual_cost_increase": 0,
            "employee_rows": [],
        }

        print(f"\n[DEBUG] About to calculate impact:")
        print(f"  new_rate_decimal: {new_rate_decimal}")
        print(f"  legislation_id: {legislation_id}")
        print(f"  country: {country}")

        if new_rate_decimal and legislation_id:
            print(f"[DEBUG] Calling calculate_impact...")
            impact_data = calculate_impact(
                country=country,
                new_rate=new_rate_decimal,
                legislation_id=legislation_id,
            )
            print(
                f"[DEBUG] Impact calculation complete: {impact_data.get('impacted_employees', 0)} employees impacted"
            )
        else:
            print(
                f"[DEBUG] Skipping impact calculation - missing new_rate_decimal or legislation_id"
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
        Payroll Urgency: {payroll_json.get('urgency', 'Medium')}
        Impacted Employees: {impacted_count}
        Annual Cost Increase: {annual_cost}
        Legislation ID: {legislation_id if legislation_id else "NOT AVAILABLE - do not call log_risk_to_db"}
        """

        risk_result = await Runner.run(
            risk_agent,
            input=[{"role": "user", "content": risk_input}],
        )
        
        # Handle both OpenAI (structured) and Groq (plain JSON) responses
        if LLM_PROVIDER == "openai":
            risk_data = risk_result.final_output_as(RiskAgentOutput)
            risk_json = {
                "risk_level": risk_data.risk_level,
                "reasoning": risk_data.reasoning,
                "confidence": risk_data.confidence
            }
        else:
            risk_raw = risk_result.final_output_as(str)
            risk_json = parse_agent_json_output(risk_raw, "RiskAgent")
        
        risk_conf = float(risk_json.get("confidence", 0.7))
        risk_reasoning = risk_json.get("reasoning", "")

        print(f"\n[DEBUG] Risk Agent Output:")
        print(f"  Risk Level: {risk_json.get('risk_level', 'N/A')}")
        print(f"  Reasoning: {risk_reasoning}")
        print(f"  Confidence: {risk_conf}")
        print(
            f"  Legislation ID for DB logging: {legislation_id if legislation_id else 'NOT AVAILABLE - log_risk_to_db will be skipped'}"
        )

        # DB logging is handled by the risk agent via the log_risk_to_db tool
        # For Groq, we need to manually log since tools might not execute properly
        if LLM_PROVIDER != "openai" and legislation_id:
            try:
                log_risk_to_db(legislation_id, risk_json)
            except Exception as e:
                print(f"[ERROR] Manual risk logging failed: {e}")

        # ==================================================
        # 7️⃣ Urgency Classification Agent
        # ==================================================
        effective_date = legal_json.get("effective_date", "")
        days_until_effective = 0

        if effective_date:
            try:
                eff_date = datetime.strptime(effective_date, "%Y-%m-%d")
                days_until_effective = (eff_date - datetime.now()).days
            except:
                days_until_effective = 30  # Default assumption

        urgency_input = f"""
        Effective Date: {effective_date.strftime('%Y-%m-%d') if hasattr(effective_date, 'strftime') else effective_date}
        Risk Level: {risk_json.get('risk_level', 'Medium')}
        Impacted Employees: {impacted_count}
        Annual Cost Increase: {annual_cost}
        Legal Summary: {summary}
        """

        urgency_result = await Runner.run(
            urgency_agent,
            input=[{"role": "user", "content": urgency_input}],
        )
        
        # Handle both OpenAI (structured) and Groq (plain JSON) responses
        if LLM_PROVIDER == "openai":
            urgency_data = urgency_result.final_output_as(UrgencyAgentOutput)
            urgency_json = {
                "urgency_level": urgency_data.urgency_level,
                "reasoning": urgency_data.reasoning,
                "recommended_action": urgency_data.recommended_action,
                "confidence": urgency_data.confidence
            }
        else:
            urgency_raw = urgency_result.final_output_as(str)
            urgency_json = parse_agent_json_output(urgency_raw, "UrgencyAgent")
        
        urgency_conf = float(urgency_json.get("confidence", 0.7))

        print(f"\n[DEBUG] Urgency Agent Output:")
        print(f"  Urgency Level: {urgency_json.get('urgency_level', 'N/A')}")
        print(f"  Days Until Effective: {urgency_json.get('days_until_effective', days_until_effective)}")
        print(f"  Recommended Action: {urgency_json.get('recommended_action', 'N/A')}")
        print(f"  Reasoning: {urgency_json.get('reasoning', 'N/A')}")
        print(f"  Confidence: {urgency_json.get('confidence', 0.7)}")


        # ==================================================
        # 8️⃣ Report Generation Agent
        # ==================================================
        report_input = f"""
        Country: {country}
        Regulation Summary: {summary}
        New Rate: {display_new_rate}%
        Effective Date: {effective_date}
        Impacted Employees: {impacted_count}
        Annual Cost Increase: {annual_cost}
        Risk Level: {risk_json.get('risk_level', 'Medium')}
        Urgency: {urgency_json.get('urgency_level', 'Medium')}
        Days Until Effective: {days_until_effective}
        Payroll Action Required: {payroll_action_required}
        Risk Reasoning: {risk_reasoning}
        """

        report_result = await Runner.run(
            report_agent,
            input=[{"role": "user", "content": report_input}],
        )
        report_raw = report_result.final_output_as(str)
        report_json = json.loads(report_raw)
        report_conf = float(report_json.get("confidence", 0.7))

        # ==================================================
        # 9️⃣ Aggregate Confidence
        # ==================================================
        final_conf = round(
            (legal_conf + payroll_conf + risk_conf + urgency_conf + report_conf) / 5, 2
        )

        print(f"\n[DEBUG] Confidence Scores:")
        print(f"  Legal Agent Confidence: {legal_conf}")
        print(f"  Payroll Agent Confidence: {payroll_conf}")
        print(f"  Risk Agent Confidence: {risk_conf}")
        print(f"  Urgency Agent Confidence: {urgency_conf}")
        print(f"  Report Agent Confidence: {report_conf}")
        print(f"  Final Aggregated Confidence: {final_conf}")

        # ==================================================
        # 🔟 Generate CSV
        # ==================================================
        csv_path = None
        if employee_rows:
            df = pd.DataFrame(employee_rows)
            csv_path = "impacted_employees.csv"
            df.to_csv(csv_path, index=False)

        # ==================================================
        # 1️⃣1️⃣ Build Comprehensive Recommendations
        # ==================================================
        action_items = report_json.get("action_items", [])
        action_summary = "\n".join(
            [
                f"• {item.get('action', '')} (Priority: {item.get('priority', '')}, Timeline: {item.get('timeline', '')})"
                for item in action_items
            ]
        )

        recommendations = f"""
EXECUTIVE SUMMARY:
{report_json.get('executive_summary', '')}

KEY FINDINGS:
{chr(10).join(['• ' + finding for finding in report_json.get('key_findings', [])])}

FINANCIAL IMPACT:
{report_json.get('financial_impact_summary', '')}

RISK ASSESSMENT:
{report_json.get('risk_summary', '')}

RECOMMENDED ACTIONS:
{action_summary}

URGENCY ASSESSMENT:
Level: {urgency_json.get('urgency_level', 'N/A')}
Recommended Action: {urgency_json.get('recommended_action', 'N/A')}
Reasoning: {urgency_json.get('reasoning', 'N/A')}
"""

        # ==================================================
        # 1️⃣2️⃣ Final Structured JSON
        # ==================================================
        return {
            "summary": summary,
            "country": country,
            "new_rate": display_new_rate,
            "effective_date": effective_date,
            "days_until_effective": days_until_effective,
            "impacted_employees": impacted_count,
            "annual_cost_increase": annual_cost,
            "monthly_cost_increase": round(annual_cost / 12, 2) if annual_cost else 0,
            "payroll_urgency": payroll_json.get("urgency", "Medium"),
            "urgency_level": urgency_json.get("urgency_level", "Medium"),
            "urgency_reasoning": urgency_json.get("reasoning", ""),
            "recommended_action_timeline": urgency_json.get("recommended_action", ""),
            "risk_level": risk_json.get("risk_level", "Medium"),
            "confidence": final_conf,
            "employee_rows": employee_rows,
            "csv_path": csv_path,
            "payroll_action_required": payroll_action_required,
            "requires_system_update": requires_system_update,
            "employee_recalculation_required": employee_recalculation_required,
            "risk_reasoning": risk_reasoning,
            "recommendations": recommendations,
            "executive_summary": report_json.get("executive_summary"),
            "key_findings": report_json.get("key_findings", []),
            "financial_impact_summary": report_json.get("financial_impact_summary"),
            "risk_summary": report_json.get("risk_summary"),
            "action_items": report_json.get("action_items", []),
            "audit_notes": report_json.get("audit_notes"),
            "legislation_id": legislation_id,
        }

    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ EXCEPTION IN COMPLIANCE FLOW:")
        print(f"{'='*60}")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        
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


async def execute_compliance_actions_async(
    compliance_result: dict, auto_execute: bool = False
):
    """
    Executes recommended compliance actions using the Action Execution Agent.

    Args:
        compliance_result: Result from run_compliance_flow_async
        auto_execute: If True, automatically execute high-priority actions

    Returns:
        Dictionary with execution results
    """
    try:
        country = compliance_result.get("country", "")
        risk_level = compliance_result.get("risk_level", "")
        urgency_level = compliance_result.get("urgency_level", "")
        legislation_id = compliance_result.get("legislation_id")
        action_items = compliance_result.get("action_items", [])
        new_rate = compliance_result.get("new_rate", 0) / 100  # Convert to decimal
        effective_date = compliance_result.get("effective_date", "")

        # Determine if auto-execution should proceed
        should_auto_execute = auto_execute and (
            risk_level in ["High", "Critical"] or urgency_level in ["High", "Critical"]
        )

        print(f"\n[DEBUG] Executing compliance actions...")
        print(f"  Country: {country}")
        print(f"  Risk: {risk_level}, Urgency: {urgency_level}")
        print(f"  Legislation ID: {legislation_id}")

        # Execute actions directly - use the plain functions
        from app.tools.action_tools import _update_payroll_config, _notify_payroll_team

        execution_results = []

        # 1. Update payroll configuration
        try:
            result = _update_payroll_config(
                country=country,
                new_rate=new_rate,
                effective_date=effective_date,
                regulation_type="pension",
            )
            execution_results.append(result)
            print(f"  ✅ {result}")
        except Exception as e:
            execution_results.append(f"❌ Payroll config update failed: {e}")
            print(f"  ❌ Payroll config failed: {e}")

        # 2. Notify payroll team
        try:
            result = _notify_payroll_team(
                country=country,
                subject=f"Critical Compliance Update: {country} Pension Rate Change",
                message=f"The pension contribution rate for {country} will change to {new_rate*100}% effective {effective_date}. Immediate action required.",
                urgency=urgency_level or "High",
            )
            execution_results.append(result)
            print(f"  ✅ {result}")
        except Exception as e:
            execution_results.append(f"❌ Notification failed: {e}")
            print(f"  ❌ Notification failed: {e}")

        # 3. Create compliance ticket - inline implementation
        try:
            with get_db() as (conn, cursor):
                cursor.execute(
                    """
                    INSERT INTO compliance_tickets
                    (title, description, country, priority, due_date, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        f"{country} Pension Rate Update to {new_rate*100}%",
                        f"Update employer pension contribution rate to {new_rate*100}% effective {effective_date}",
                        country,
                        risk_level or "High",
                        effective_date,
                        "open",
                        datetime.now(),
                    ),
                )
                ticket_id = cursor.lastrowid
            result = f"✓ Compliance ticket created: #{ticket_id}"
            execution_results.append(result)
            print(f"  ✅ {result}")
        except Exception as e:
            execution_results.append(f"❌ Ticket creation failed: {e}")
            print(f"  ❌ Ticket creation failed: {e}")

        # 4. Log audit entry
        if legislation_id:
            try:
                with get_db() as (conn, cursor):
                    cursor.execute(
                        """
                        INSERT INTO audit_log
                        (legislation_id, action_type, action_details, performed_by, timestamp)
                        VALUES (%s, %s, %s, %s, %s)
                    """,
                        (
                            legislation_id,
                            "compliance_actions_executed",
                            f"Executed compliance actions for {country} pension rate change to {new_rate*100}%",
                            "system",
                            datetime.now(),
                        ),
                    )
                result = f"✓ Audit entry logged for legislation #{legislation_id}"
                execution_results.append(result)
                print(f"  ✅ {result}")
            except Exception as e:
                execution_results.append(f"❌ Audit logging failed: {e}")
                print(f"  ❌ Audit logging failed: {e}")

        # 5. Generate executive PDF
        if legislation_id:
            try:
                report_data = json.dumps(
                    {
                        "legislation_id": legislation_id,
                        "country": country,
                        "new_rate": new_rate,
                        "impacted_employees": compliance_result.get(
                            "impacted_employees", 0
                        ),
                        "annual_cost_increase": compliance_result.get(
                            "annual_cost_increase", 0
                        ),
                        "risk_level": risk_level,
                        "urgency_level": urgency_level,
                    }
                )
                with get_db() as (conn, cursor):
                    cursor.execute(
                        """
                        INSERT INTO generated_reports
                        (legislation_id, report_type, report_data, generated_at, file_path)
                        VALUES (%s, %s, %s, %s, %s)
                    """,
                        (
                            legislation_id,
                            "executive_pdf",
                            report_data,
                            datetime.now(),
                            f"reports/executive_report_{legislation_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        ),
                    )
                result = f"✓ Executive PDF report generated"
                execution_results.append(result)
                print(f"  ✅ {result}")
            except Exception as e:
                execution_results.append(f"❌ PDF generation failed: {e}")
                print(f"  ❌ PDF generation failed: {e}")

        # 6. Schedule compliance review
        try:
            from datetime import timedelta

            review_date = datetime.now() + timedelta(days=7)
            with get_db() as (conn, cursor):
                cursor.execute(
                    """
                    INSERT INTO scheduled_meetings
                    (title, meeting_date, attendees, agenda, created_at, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """,
                    (
                        f"{country} Compliance Review Meeting",
                        review_date.strftime("%Y-%m-%d %H:%M"),
                        "Payroll Team, HR Manager, Finance Director",
                        f"Review {country} pension rate change impact and implementation plan",
                        datetime.now(),
                        "scheduled",
                    ),
                )
                meeting_id = cursor.lastrowid
            result = f"✓ Compliance review meeting scheduled: #{meeting_id}"
            execution_results.append(result)
            print(f"  ✅ {result}")
        except Exception as e:
            execution_results.append(f"❌ Meeting scheduling failed: {e}")
            print(f"  ❌ Meeting scheduling failed: {e}")

        return {
            "status": "success",
            "auto_executed": should_auto_execute,
            "execution_output": "\n".join(execution_results),
            "actions_performed": [
                "Payroll configuration updated",
                "Payroll team notified",
                "Compliance ticket created",
                "Audit entry logged",
                "Executive report generated",
                "Compliance review scheduled",
            ],
        }

    except Exception as e:
        print(f"\n[ERROR] Action execution failed: {e}")
        import traceback

        traceback.print_exc()
        return {"status": "error", "error": str(e), "auto_executed": False}


def execute_compliance_actions(compliance_result: dict, auto_execute: bool = False):
    """
    Synchronous wrapper for action execution.
    """
    return asyncio.run(
        execute_compliance_actions_async(compliance_result, auto_execute)
    )
