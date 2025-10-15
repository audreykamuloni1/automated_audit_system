from datetime import datetime
from db.database import get_db_connection

def run_rules():
    """
    Runs predefined compliance rules against the logs in the database
    and stores any violations in the 'alerts' table.
    """
    conn = get_db_connection()
    if not conn:
        print("Could not connect to the database to run rules.")
        return

    alerts_generated = 0
    try:
        with conn.cursor() as cur:
            # Rule 1: Flag unauthorized access attempts
            rule_id = "unauthorized_access_attempt"
            description = "Unauthorized access detected. A user attempted to access a resource they were not authorized for."

            cur.execute("""
                SELECT id, timestamp, user_id, resource
                FROM logs
                WHERE status = 'unauthorized'
            """)

            unauthorized_logs = cur.fetchall()

            for log_id, ts, user_id, resource in unauthorized_logs:
                alert_ts = datetime.now()
                cur.execute(
                    "SELECT id FROM alerts WHERE log_id = %s AND rule_id = %s",
                    (log_id, rule_id)
                )
                if cur.fetchone() is None:
                    cur.execute(
                        """
                        INSERT INTO alerts (log_id, rule_id, timestamp, description)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (log_id, rule_id, alert_ts, f"{description} User: {user_id}, Resource: {resource}")
                    )
                    alerts_generated += 1

            # Rule 2: Admin Action on Sensitive DB
            rule_id = "admin_action_sensitive_db"
            description = "Admin performed an action on a sensitive database."

            cur.execute("""
                SELECT id, timestamp, user_id, resource
                FROM logs
                WHERE user_id LIKE 'admin-%' AND resource = 'sensitive-db'
            """)
            admin_logs = cur.fetchall()
            for log_id, ts, user_id, resource in admin_logs:
                alert_ts = datetime.now()
                cur.execute(
                    "SELECT id FROM alerts WHERE log_id = %s AND rule_id = %s",
                    (log_id, rule_id)
                )
                if cur.fetchone() is None:
                    cur.execute(
                        """
                        INSERT INTO alerts (log_id, rule_id, timestamp, description)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (log_id, rule_id, alert_ts, f"{description} User: {user_id}, Resource: {resource}")
                    )
                    alerts_generated += 1

            # Rule 3: Multiple Failed Logins
            rule_id = "multiple_failed_logins"
            description = "Multiple failed login attempts detected."

            cur.execute("""
                SELECT user_id, COUNT(*) as fail_count
                FROM logs
                WHERE status = 'failed'
                GROUP BY user_id
                HAVING COUNT(*) >= 3
            """)
            failed_users = cur.fetchall()
            for user_id, fail_count in failed_users:
                alert_ts = datetime.now()
                # For failed logins, log_id is not unique, so we set it to None
                cur.execute(
                    "SELECT id FROM alerts WHERE rule_id = %s AND description LIKE %s",
                    (rule_id, f"%User: {user_id}%")
                )
                if cur.fetchone() is None:
                    cur.execute(
                        """
                        INSERT INTO alerts (log_id, rule_id, timestamp, description)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (None, rule_id, alert_ts, f"{description} User: {user_id}, Failed Attempts: {fail_count}")
                    )
                    alerts_generated += 1

            conn.commit()
        print(f"Rule engine finished. Generated {alerts_generated} new alerts.")
    except Exception as e:
        print(f"Error running rule engine: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()

def get_alerts():
    """Retrieves all alerts from the database."""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT a.id, a.timestamp, a.rule_id, a.description, l.user_id, l.action, l.resource
                FROM alerts a
                JOIN logs l ON a.log_id = l.id
                ORDER BY a.timestamp DESC
            """)
            return cur.fetchall()
    except Exception as e:
        print(f"Error fetching alerts: {e}")
        return []
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    print("Running compliance rule engine...")
    run_rules()

    print("\nFetching current alerts:")
    alerts = get_alerts()
    if alerts:
        for alert in alerts:
            print(alert)
    else:
        print("No alerts found.")