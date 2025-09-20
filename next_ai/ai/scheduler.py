import frappe
from frappe.utils import nowdate, add_days


def delete_old_nextai_usage_logs():
    """
    Delete old NextAI usage logs based on retention policy.

    This function fetches the retention period (in days) from the 
    "NextAI Settings" doctype (field: `usage_log_retention_days`). 
    If not set, it defaults to 10 days. It then removes all records 
    from the `tabNextAI Usage Log` table that were created before 
    the cutoff date and commits the changes to the database.

    Additionally, it logs the cleanup operation for monitoring.

    Steps:
        1. Get retention days from settings (default: 10).
        2. Calculate cutoff date as today - retention_days.
        3. Delete logs older than cutoff date.
        4. Commit changes and log the operation.

    Raises:
        Exception: If database operation or logging fails.
    """
    retention_days = frappe.db.get_single_value("NextAI Settings", "usage_log_retention_days") or 10
    cutoff_date = add_days(nowdate(), -int(retention_days))
    frappe.db.sql("""
        DELETE FROM `tabNextAI Usage Log`
        WHERE usage_at < %s
    """, cutoff_date)
    
    frappe.db.commit()
    frappe.log_error(message=f"Deleted NextAI Usage Logs older than {retention_days} days", title="NextAI Cron Job - def delete_old_nextai_usage_logs")
