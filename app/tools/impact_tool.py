# app/tools/impact_tool.py

from app.db.db import get_db


def calculate_impact(country: str, new_rate: float, legislation_id: int):
    """
    Calculates employee impact and persists results in DB.
    Returns both aggregate stats and per-employee rows for UI/CSV.
    """

    impacted_count = 0
    total_cost_increase = 0
    employee_rows = []

    with get_db() as (conn, cursor):

        # Fetch affected employees
        cursor.execute(
            """
            SELECT employee_id, annual_salary, pension_rate
            FROM employees
            WHERE country = %s AND status = 'Active'
        """,
            (country,),
        )
        employees = cursor.fetchall()

        for emp in employees:
            old_rate = float(emp["pension_rate"])
            salary = float(emp["annual_salary"])

            # Calculate the change
            old_contribution = salary * old_rate
            new_contribution = salary * new_rate
            increase = new_contribution - old_contribution

            # Only count as impacted if there's an actual increase (cost goes up)
            # If increase is negative or zero, skip this employee
            if increase > 0:
                impacted_count += 1
                total_cost_increase += increase

                # Insert employee impact detail
                cursor.execute(
                    """
                    INSERT INTO employee_impact_detail
                    (legislation_id, employee_id, old_rate, new_rate, annual_salary, annual_cost_increase)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """,
                    (
                        legislation_id,
                        emp["employee_id"],
                        old_rate,
                        new_rate,
                        salary,
                        increase,
                    ),
                )

                # Row used by UI table + CSV
                employee_rows.append(
                    {
                        "employee_id": emp["employee_id"],
                        "old_rate": old_rate,
                        "new_rate": new_rate,
                        "annual_salary": salary,
                        "annual_cost_increase": round(increase, 2),
                    }
                )

        avg_cost = (
            total_cost_increase / impacted_count if impacted_count > 0 else 0
        )

        # Insert aggregate result
        cursor.execute(
            """
            INSERT INTO impact_results
            (legislation_id, impacted_employees, total_annual_cost_increase, average_cost_per_employee)
            VALUES (%s, %s, %s, %s)
        """,
            (
                legislation_id,
                impacted_count,
                total_cost_increase,
                avg_cost,
            ),
        )

    return {
        "impacted_employees": impacted_count,
        "annual_cost_increase": round(total_cost_increase, 2),
        "employee_rows": employee_rows,
    }
