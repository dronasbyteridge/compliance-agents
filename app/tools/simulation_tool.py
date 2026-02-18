from app.db.db import get_db
from typing import Dict, List


def simulate_compliance_scenario(
    country: str,
    base_rate: float,
    scenario_rate: float,
    implementation_delay_days: int = 0,
    partial_implementation_pct: float = 1.0
) -> Dict:
    """
    Simulates different compliance scenarios for what-if analysis.
    
    Args:
        country: Country to simulate
        base_rate: Current/baseline rate
        scenario_rate: Proposed scenario rate
        implementation_delay_days: Days to delay implementation
        partial_implementation_pct: Percentage of implementation (0.0-1.0)
    
    Returns:
        Dictionary with scenario analysis results
    """
    
    with get_db() as (conn, cursor):
        # Fetch affected employees
        cursor.execute("""
            SELECT employee_id, annual_salary, pension_rate
            FROM employees
            WHERE country = %s AND status = 'Active'
        """, (country,))
        employees = cursor.fetchall()
        
        # Calculate base scenario
        base_cost = 0
        scenario_cost = 0
        impacted_count = 0
        
        employee_details = []
        
        for emp in employees:
            salary = float(emp["annual_salary"])
            current_rate = float(emp["pension_rate"])
            
            # Base calculation
            base_contribution = salary * base_rate
            
            # Scenario calculation with adjustments
            effective_scenario_rate = scenario_rate * partial_implementation_pct
            scenario_contribution = salary * effective_scenario_rate
            
            if current_rate != effective_scenario_rate:
                impacted_count += 1
                
            base_cost += base_contribution
            scenario_cost += scenario_contribution
            
            employee_details.append({
                "employee_id": emp["employee_id"],
                "annual_salary": salary,
                "base_contribution": round(base_contribution, 2),
                "scenario_contribution": round(scenario_contribution, 2),
                "delta": round(scenario_contribution - base_contribution, 2)
            })
        
        # Calculate deltas
        cost_delta = scenario_cost - base_cost
        monthly_delta = cost_delta / 12
        
        # Risk adjustment based on delay
        risk_multiplier = 1.0
        if implementation_delay_days > 0:
            # Delayed implementation increases risk
            risk_multiplier = 1.0 + (implementation_delay_days / 365) * 0.5
        
        adjusted_risk_score = min(100, 50 * risk_multiplier)
        
        return {
            "scenario_name": f"Rate: {scenario_rate*100}%, Delay: {implementation_delay_days}d, Implementation: {partial_implementation_pct*100}%",
            "base_annual_cost": round(base_cost, 2),
            "scenario_annual_cost": round(scenario_cost, 2),
            "annual_cost_delta": round(cost_delta, 2),
            "monthly_cost_delta": round(monthly_delta, 2),
            "impacted_employees": impacted_count,
            "total_employees": len(employees),
            "implementation_delay_days": implementation_delay_days,
            "partial_implementation_pct": partial_implementation_pct,
            "adjusted_risk_score": round(adjusted_risk_score, 2),
            "risk_notes": f"Risk increased by {round((risk_multiplier-1)*100, 1)}% due to delay" if implementation_delay_days > 0 else "No delay risk",
            "employee_details": employee_details[:10]  # Return top 10 for preview
        }


def compare_scenarios(country: str, base_rate: float, scenarios: List[Dict]) -> Dict:
    """
    Compares multiple compliance scenarios side-by-side.
    
    Args:
        country: Country to analyze
        base_rate: Current baseline rate
        scenarios: List of scenario configurations
    
    Returns:
        Comparison results across all scenarios
    """
    
    results = []
    
    for scenario in scenarios:
        result = simulate_compliance_scenario(
            country=country,
            base_rate=base_rate,
            scenario_rate=scenario.get("rate", base_rate),
            implementation_delay_days=scenario.get("delay_days", 0),
            partial_implementation_pct=scenario.get("implementation_pct", 1.0)
        )
        results.append(result)
    
    # Find best and worst scenarios
    best_scenario = min(results, key=lambda x: x["annual_cost_delta"])
    worst_scenario = max(results, key=lambda x: x["annual_cost_delta"])
    
    return {
        "scenarios": results,
        "best_scenario": best_scenario["scenario_name"],
        "worst_scenario": worst_scenario["scenario_name"],
        "cost_range": {
            "min": best_scenario["annual_cost_delta"],
            "max": worst_scenario["annual_cost_delta"],
            "spread": worst_scenario["annual_cost_delta"] - best_scenario["annual_cost_delta"]
        },
        "recommendation": f"Best option: {best_scenario['scenario_name']} saves {abs(best_scenario['annual_cost_delta'] - worst_scenario['annual_cost_delta']):.2f} vs worst case"
    }
