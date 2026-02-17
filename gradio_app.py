import gradio as gr
import matplotlib.pyplot as plt
from app.agents.compliance_manager import run_compliance_flow


def handle_query(message):

    result = run_compliance_flow(message)

    # ============================
    # Chart
    # ============================
    fig = None
    if result["impacted_employees"] > 0:
        fig = plt.figure()
        plt.bar(
            ["Impacted Employees"],
            [result["impacted_employees"]]
        )
        plt.title("Compliance Impact")

    return (
        result["summary"],
        result["country"],
        result["new_rate"],
        result["impacted_employees"],
        result["annual_cost_increase"],
        result["payroll_urgency"],
        result["risk_level"],
        result["confidence"],
        result["employee_rows"],
        fig,
        result["csv_path"]
    )


with gr.Blocks() as demo:

    gr.Markdown("# Global Payroll Compliance Assist")

    query = gr.Textbox(label="Ask Compliance Question")

    summary = gr.Textbox(label="Summary")
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
        handle_query,
        inputs=query,
        outputs=[
            summary,
            country,
            rate,
            impacted,
            cost,
            urgency,
            risk,
            confidence,
            employee_table,
            chart,
            csv_download
        ]
    )

demo.launch()
