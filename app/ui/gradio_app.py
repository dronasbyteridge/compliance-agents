import gradio as gr
import matplotlib.pyplot as plt
import pandas as pd

from app.agents.compliance_manager import run_compliance_flow


def _handle_query(message: str):
    result = run_compliance_flow(message)

    # ----------------------------
    # Chart (optional)
    # ----------------------------
    fig = None
    try:
        if result.get("impacted_employees", 0) > 0:
            fig = plt.figure()
            plt.bar(["Impacted Employees"], [result["impacted_employees"]])
            plt.title("Compliance Impact")
    except Exception:
        fig = None

    # ----------------------------
    # Employee table (DataFrame)
    # ----------------------------
    employee_rows = result.get("employee_rows", [])
    if employee_rows:
        employee_table = pd.DataFrame(employee_rows)
    else:
        employee_table = []

    return (
        result.get("summary", ""),
        result.get("recommendations", ""),
        result.get("country", ""),
        result.get("new_rate", 0),
        result.get("impacted_employees", 0),
        result.get("annual_cost_increase", 0),
        result.get("payroll_urgency", ""),
        result.get("risk_level", ""),
        result.get("confidence", 0),
        employee_table,
        fig,
        result.get("csv_path"),
    )


def launch_app():
    with gr.Blocks(title="Compliance Assist - Global Payroll") as demo:
        gr.Markdown("## Compliance Assist – Global Payroll")

        query = gr.Textbox(label="Ask Compliance Question")

        summary = gr.Textbox(label="Summary")
        actions = gr.Textbox(label="Recommended Actions", lines=6)
        country = gr.Textbox(label="Country")
        rate = gr.Number(label="New Rate (%)")
        impacted = gr.Number(label="Impacted Employees")
        cost = gr.Number(label="Annual Cost Increase")
        urgency = gr.Textbox(label="Payroll Urgency")
        risk = gr.Textbox(label="Risk Level")
        confidence = gr.Number(label="Confidence Score")

        employee_table = gr.Dataframe(label="Impacted Employees")
        chart = gr.Plot(label="Impact Chart")
        csv_download = gr.File(label="Download CSV")

        submit_btn = gr.Button("Analyze")

        submit_btn.click(
            _handle_query,
            inputs=query,
            outputs=[
                summary,
                actions,
                country,
                rate,
                impacted,
                cost,
                urgency,
                risk,
                confidence,
                employee_table,
                chart,
                csv_download,
            ],
        )

    demo.launch()


if __name__ == "__main__":
    launch_app()
