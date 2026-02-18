from agents.tool import function_tool
from app.db.db import get_db
from datetime import datetime
import json


def _update_payroll_config(country: str, new_rate: float, effective_date: str, regulation_type: str) -> str:
    """Updates payroll system configuration"""
    try:
        with get_db() as (conn, cursor):
            cursor.execute("""
                INSERT INTO payroll_config_updates
                (country, regulation_type, new_rate, effective_date, updated_at, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (country, regulation_type, new_rate, effective_date, datetime.now(), 'pending'))
            
        return f"✓ Payroll configuration updated for {country}: {regulation_type} set to {new_rate*100}% effective {effective_date}"
    except Exception as e:
        return f"✗ Failed to update payroll config: {str(e)}"


@function_tool
def update_payroll_config(country: str, new_rate: float, effective_date: str, regulation_type: str) -> str:
    """
    Updates payroll system configuration for a specific country and regulation.
    
    Args:
        country: Country code (e.g., "Germany", "France")
        new_rate: New rate as decimal (e.g., 0.22 for 22%)
        effective_date: Date when change becomes effective (YYYY-MM-DD)
        regulation_type: Type of regulation (e.g., "social_contribution", "pension")
    
    Returns:
        Status message confirming the update
    """
    return _update_payroll_config(country, new_rate, effective_date, regulation_type)


def _notify_payroll_team(country: str, subject: str, message: str, urgency: str) -> str:
    """Sends notification to payroll team"""
    try:
        with get_db() as (conn, cursor):
            cursor.execute("""
                INSERT INTO notifications
                (recipient_type, country, subject, message, urgency, sent_at, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, ('payroll_team', country, subject, message, urgency, datetime.now(), 'sent'))
        
        print(f"\n{'='*60}")
        print(f"📧 PAYROLL TEAM NOTIFICATION")
        print(f"{'='*60}")
        print(f"Country: {country}")
        print(f"Urgency: {urgency}")
        print(f"Subject: {subject}")
        print(f"Message:\n{message}")
        print(f"{'='*60}\n")
        
        return f"✓ Notification sent to {country} payroll team (Urgency: {urgency})"
    except Exception as e:
        return f"✗ Failed to send notification: {str(e)}"


@function_tool
def notify_payroll_team(country: str, subject: str, message: str, urgency: str) -> str:
    """
    Sends notification to payroll team about compliance changes.
    
    Args:
        country: Country affected
        subject: Email subject line
        message: Detailed message content
        urgency: Urgency level (Low/Moderate/High/Critical)
    
    Returns:
        Confirmation of notification sent
    """
    return _notify_payroll_team(country, subject, message, urgency)


@function_tool
def create_compliance_ticket(title: str, description: str, country: str, priority: str, due_date: str) -> str:
    """
    Creates a compliance tracking ticket in the system.
    
    Args:
        title: Ticket title
        description: Detailed description
        country: Country affected
        priority: Priority level (Low/Medium/High/Critical)
        due_date: Due date (YYYY-MM-DD)
    
    Returns:
        Ticket ID and confirmation
    """
    try:
        with get_db() as (conn, cursor):
            cursor.execute("""
                INSERT INTO compliance_tickets
                (title, description, country, priority, due_date, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (title, description, country, priority, due_date, 'open', datetime.now()))
            
            ticket_id = cursor.lastrowid
        
        return f"✓ Compliance ticket created: #{ticket_id} - {title} (Priority: {priority}, Due: {due_date})"
    except Exception as e:
        return f"✗ Failed to create ticket: {str(e)}"


@function_tool
def log_audit_entry(legislation_id: int, action_type: str, action_details: str, performed_by: str = "system") -> str:
    """
    Logs an audit entry for compliance traceability.
    
    Args:
        legislation_id: ID of the legislation being processed
        action_type: Type of action (e.g., "analysis", "notification", "config_update")
        action_details: Detailed description of the action
        performed_by: Who performed the action (default: "system")
    
    Returns:
        Confirmation of audit log entry
    """
    try:
        with get_db() as (conn, cursor):
            cursor.execute("""
                INSERT INTO audit_log
                (legislation_id, action_type, action_details, performed_by, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """, (legislation_id, action_type, action_details, performed_by, datetime.now()))
        
        return f"✓ Audit entry logged: {action_type} for legislation #{legislation_id}"
    except Exception as e:
        return f"✗ Failed to log audit entry: {str(e)}"


@function_tool
def generate_executive_pdf(legislation_id: int, report_data: str) -> str:
    """
    Generates an executive PDF report for compliance changes.
    
    Args:
        legislation_id: ID of the legislation
        report_data: JSON string containing report data
    
    Returns:
        Path to generated PDF
    """
    try:
        # In production, this would use a PDF generation library
        # For now, we'll log the report generation
        report_dict = json.loads(report_data) if isinstance(report_data, str) else report_data
        
        with get_db() as (conn, cursor):
            cursor.execute("""
                INSERT INTO generated_reports
                (legislation_id, report_type, report_data, generated_at, file_path)
                VALUES (%s, %s, %s, %s, %s)
            """, (legislation_id, 'executive_pdf', report_data, datetime.now(), 
                  f"reports/executive_report_{legislation_id}_{datetime.now().strftime('%Y%m%d')}.pdf"))
        
        return f"✓ Executive PDF report generated: reports/executive_report_{legislation_id}.pdf"
    except Exception as e:
        return f"✗ Failed to generate PDF: {str(e)}"


@function_tool
def tag_impacted_employees(employee_ids: str, tag: str, legislation_id: int) -> str:
    """
    Tags impacted employees in HRIS for tracking.
    
    Args:
        employee_ids: Comma-separated list of employee IDs
        tag: Tag to apply (e.g., "compliance_update_2024")
        legislation_id: Related legislation ID
    
    Returns:
        Confirmation of tagging
    """
    try:
        ids = [id.strip() for id in employee_ids.split(',')]
        
        with get_db() as (conn, cursor):
            for emp_id in ids:
                cursor.execute("""
                    INSERT INTO employee_tags
                    (employee_id, tag, legislation_id, tagged_at)
                    VALUES (%s, %s, %s, %s)
                """, (emp_id, tag, legislation_id, datetime.now()))
        
        return f"✓ Tagged {len(ids)} employees with '{tag}'"
    except Exception as e:
        return f"✗ Failed to tag employees: {str(e)}"


@function_tool
def schedule_compliance_review(title: str, date: str, attendees: str, agenda: str) -> str:
    """
    Schedules a compliance review meeting.
    
    Args:
        title: Meeting title
        date: Meeting date and time (YYYY-MM-DD HH:MM)
        attendees: Comma-separated list of attendees
        agenda: Meeting agenda
    
    Returns:
        Meeting confirmation
    """
    try:
        with get_db() as (conn, cursor):
            cursor.execute("""
                INSERT INTO scheduled_meetings
                (title, meeting_date, attendees, agenda, created_at, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (title, date, attendees, agenda, datetime.now(), 'scheduled'))
            
            meeting_id = cursor.lastrowid
        
        print(f"\n{'='*60}")
        print(f"📅 COMPLIANCE REVIEW SCHEDULED")
        print(f"{'='*60}")
        print(f"Meeting ID: {meeting_id}")
        print(f"Title: {title}")
        print(f"Date: {date}")
        print(f"Attendees: {attendees}")
        print(f"Agenda:\n{agenda}")
        print(f"{'='*60}\n")
        
        return f"✓ Compliance review meeting scheduled: #{meeting_id} - {title} on {date}"
    except Exception as e:
        return f"✗ Failed to schedule meeting: {str(e)}"
