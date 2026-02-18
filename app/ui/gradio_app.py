import gradio as gr
import matplotlib.pyplot as plt
import pandas as pd
import json

from app.agents.compliance_manager import run_compliance_flow, execute_compliance_actions
from app.tools.simulation_tool import simulate_compliance_scenario, compare_scenarios


def _handle_query(message: str):
    result = run_compliance_flow(message)

    # ----------------------------
    # Risk Heatmap Chart
    # ----------------------------
    fig = None
    try:
        if result.get("impacted_employees", 0) > 0:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # Impact bar chart
            ax1.bar(["Impacted Employees"], [result["impacted_employees"]], color='#3498db')
            ax1.set_title("Workforce Impact")
            ax1.set_ylabel("Number of Employees")
            
            # Financial exposure
            annual_cost = result.get("annual_cost_increase", 0)
            monthly_cost = result.get("monthly_cost_increase", 0)
            ax2.bar(["Monthly", "Annual"], [monthly_cost, annual_cost], color=['#e74c3c', '#c0392b'])
            ax2.set_title("Financial Exposure")
            ax2.set_ylabel("Cost Increase")
            
            plt.tight_layout()
    except Exception:
        fig = None

    # ----------------------------
    # Employee table (DataFrame)
    # ----------------------------
    employee_rows = result.get("employee_rows", [])
    if employee_rows:
        employee_table = pd.DataFrame(employee_rows)
    else:
        employee_table = pd.DataFrame()

    # ----------------------------
    # Format action items
    # ----------------------------
    action_items = result.get("action_items", [])
    action_items_text = "\n".join([
        f"• {item.get('action', '')} (Priority: {item.get('priority', '')}, Timeline: {item.get('timeline', '')}, Owner: {item.get('owner', '')})"
        for item in action_items
    ])

    return (
        result.get("executive_summary", ""),
        result.get("summary", ""),
        result.get("recommendations", ""),
        action_items_text,
        result.get("country", ""),
        result.get("new_rate", 0),
        result.get("effective_date", ""),
        result.get("days_until_effective", 0),
        result.get("impacted_employees", 0),
        result.get("annual_cost_increase", 0),
        result.get("monthly_cost_increase", 0),
        result.get("payroll_urgency", ""),
        result.get("urgency_level", ""),
        result.get("urgency_reasoning", ""),
        result.get("risk_level", ""),
        result.get("risk_reasoning", ""),
        result.get("confidence", 0),
        employee_table,
        fig,
        result.get("csv_path"),
        json.dumps(result, indent=2)  # Store full result for action execution
    )


def _execute_actions(result_json: str):
    """Execute recommended compliance actions"""
    try:
        result = json.loads(result_json)
        execution_result = execute_compliance_actions(result, auto_execute=True)
        
        if execution_result.get("status") == "success":
            return f"""
✅ Actions Executed Successfully

Auto-Executed: {execution_result.get('auto_executed')}

Actions Performed:
{chr(10).join(['• ' + action for action in execution_result.get('actions_performed', [])])}

Execution Details:
{execution_result.get('execution_output', '')}
"""
        else:
            return f"❌ Execution Failed: {execution_result.get('error', 'Unknown error')}"
    except Exception as e:
        return f"❌ Error executing actions: {str(e)}"


def _run_simulation(result_json: str, scenario_rate: float, delay_days: int, implementation_pct: float):
    """Run what-if simulation"""
    try:
        result = json.loads(result_json)
        country = result.get("country", "")
        base_rate = result.get("new_rate", 0) / 100  # Convert to decimal
        
        simulation = simulate_compliance_scenario(
            country=country,
            base_rate=base_rate,
            scenario_rate=scenario_rate / 100,  # Convert to decimal
            implementation_delay_days=int(delay_days),
            partial_implementation_pct=implementation_pct / 100
        )
        
        # Create comparison chart
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Cost comparison
        ax1.bar(
            ["Base Scenario", "Simulated Scenario"],
            [simulation["base_annual_cost"], simulation["scenario_annual_cost"]],
            color=['#3498db', '#e74c3c']
        )
        ax1.set_title("Annual Cost Comparison")
        ax1.set_ylabel("Annual Cost")
        
        # Risk comparison
        ax2.bar(
            ["Base Risk", "Adjusted Risk"],
            [50, simulation["adjusted_risk_score"]],
            color=['#2ecc71', '#e67e22']
        )
        ax2.set_title("Risk Score Comparison")
        ax2.set_ylabel("Risk Score")
        
        plt.tight_layout()
        
        simulation_summary = f"""
🔍 SIMULATION RESULTS

Scenario: {simulation['scenario_name']}

Financial Impact:
• Base Annual Cost: ${simulation['base_annual_cost']:,.2f}
• Scenario Annual Cost: ${simulation['scenario_annual_cost']:,.2f}
• Annual Cost Delta: ${simulation['annual_cost_delta']:,.2f}
• Monthly Cost Delta: ${simulation['monthly_cost_delta']:,.2f}

Workforce Impact:
• Impacted Employees: {simulation['impacted_employees']} / {simulation['total_employees']}

Risk Assessment:
• Adjusted Risk Score: {simulation['adjusted_risk_score']}
• {simulation['risk_notes']}

Implementation Parameters:
• Delay: {simulation['implementation_delay_days']} days
• Implementation: {simulation['partial_implementation_pct']*100}%
"""
        
        return simulation_summary, fig
        
    except Exception as e:
        return f"❌ Simulation Error: {str(e)}", None


def launch_app():
    with gr.Blocks(title="Agentic Compliance Intelligence Platform", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🎯 Agentic Compliance Intelligence Platform
        ### Transform regulatory changes into instant workforce impact analysis, risk assessment, and automated action execution
        """)

        # Store full result for action execution
        result_state = gr.State()

        with gr.Tabs():
            # ============================================
            # TAB 1: COMPLIANCE ANALYSIS
            # ============================================
            with gr.Tab("📊 Compliance Analysis"):
                gr.Markdown("### Ask a compliance question to get instant analysis")
                
                query = gr.Textbox(
                    label="Compliance Query",
                    placeholder="e.g., Germany social contribution increased to 22% next month",
                    lines=2
                )
                
                analyze_btn = gr.Button("🔍 Analyze Compliance Impact", variant="primary", size="lg")
                
                with gr.Row():
                    with gr.Column(scale=2):
                        executive_summary = gr.Textbox(label="📋 Executive Summary", lines=3)
                        legal_summary = gr.Textbox(label="⚖️ Legal Interpretation", lines=3)
                    
                    with gr.Column(scale=1):
                        with gr.Group():
                            gr.Markdown("### 📈 Key Metrics")
                            country = gr.Textbox(label="Country")
                            rate = gr.Number(label="New Rate (%)")
                            effective_date = gr.Textbox(label="Effective Date")
                            days_until = gr.Number(label="Days Until Effective")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 💰 Financial Impact")
                        impacted = gr.Number(label="Impacted Employees")
                        annual_cost = gr.Number(label="Annual Cost Increase")
                        monthly_cost = gr.Number(label="Monthly Cost Increase")
                    
                    with gr.Column():
                        gr.Markdown("### ⚠️ Risk & Urgency")
                        risk = gr.Textbox(label="Risk Level")
                        risk_reasoning = gr.Textbox(label="Risk Reasoning", lines=2)
                        urgency_level = gr.Textbox(label="Urgency Level")
                        urgency_reasoning = gr.Textbox(label="Urgency Reasoning", lines=2)
                        payroll_urgency = gr.Textbox(label="Payroll Urgency")
                
                confidence = gr.Number(label="🎯 Confidence Score")
                
                with gr.Accordion("📝 Detailed Recommendations", open=True):
                    recommendations = gr.Textbox(label="", lines=15)
                
                with gr.Accordion("✅ Action Items", open=True):
                    action_items = gr.Textbox(label="", lines=8)
                
                with gr.Row():
                    chart = gr.Plot(label="📊 Impact Visualization")
                
                with gr.Accordion("👥 Impacted Employees Details", open=False):
                    employee_table = gr.Dataframe(label="Employee Impact Details")
                    csv_download = gr.File(label="📥 Download CSV Report")

            # ============================================
            # TAB 2: ACTION EXECUTION
            # ============================================
            with gr.Tab("⚡ Execute Actions"):
                gr.Markdown("""
                ### Execute Recommended Compliance Actions
                This will automatically:
                - Update payroll configurations
                - Notify payroll teams
                - Create compliance tickets
                - Log audit entries
                - Generate executive reports
                - Schedule compliance reviews
                """)
                
                execute_btn = gr.Button("🚀 Execute All Recommended Actions", variant="primary", size="lg")
                execution_output = gr.Textbox(label="Execution Results", lines=20)

            # ============================================
            # TAB 3: SIMULATION MODE
            # ============================================
            with gr.Tab("🔬 Simulation Mode"):
                gr.Markdown("""
                ### What-If Scenario Analysis
                Test different scenarios to understand impact variations
                """)
                
                with gr.Row():
                    scenario_rate = gr.Slider(
                        minimum=0,
                        maximum=50,
                        value=20,
                        step=0.5,
                        label="Scenario Rate (%)"
                    )
                    delay_days = gr.Slider(
                        minimum=0,
                        maximum=365,
                        value=0,
                        step=1,
                        label="Implementation Delay (days)"
                    )
                    implementation_pct = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=100,
                        step=5,
                        label="Implementation Percentage (%)"
                    )
                
                simulate_btn = gr.Button("🔬 Run Simulation", variant="primary")
                
                simulation_output = gr.Textbox(label="Simulation Results", lines=20)
                simulation_chart = gr.Plot(label="Scenario Comparison")

        # ============================================
        # EVENT HANDLERS
        # ============================================
        
        # Analysis
        analyze_btn.click(
            _handle_query,
            inputs=query,
            outputs=[
                executive_summary,
                legal_summary,
                recommendations,
                action_items,
                country,
                rate,
                effective_date,
                days_until,
                impacted,
                annual_cost,
                monthly_cost,
                payroll_urgency,
                urgency_level,
                urgency_reasoning,
                risk,
                risk_reasoning,
                confidence,
                employee_table,
                chart,
                csv_download,
                result_state
            ],
        )
        
        # Action Execution
        execute_btn.click(
            _execute_actions,
            inputs=result_state,
            outputs=execution_output
        )
        
        # Simulation
        simulate_btn.click(
            _run_simulation,
            inputs=[result_state, scenario_rate, delay_days, implementation_pct],
            outputs=[simulation_output, simulation_chart]
        )

    demo.launch(share=False)


if __name__ == "__main__":
    launch_app()
