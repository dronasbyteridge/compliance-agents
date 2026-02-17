from app.agents.compliance_manager import run_compliance_flow


if __name__ == "__main__":
    query = "What is the pension regulation update in Germany and how many employees are impacted?"
    result = run_compliance_flow(query)
    print("\nFINAL RESPONSE:\n")
    print(result)
