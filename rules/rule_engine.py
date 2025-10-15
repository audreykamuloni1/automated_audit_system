from datetime import datetime
from db.database import get_db_connection, get_active_rules

# Whitelist of allowed fields and operators to prevent SQL injection
ALLOWED_TARGET_FIELDS = {'user_id', 'action', 'resource', 'status'}
ALLOWED_OPERATORS = {'=', '!=', 'LIKE', 'IN'}

def run_rules():
    """
    Runs all active compliance rules from the database against the logs
    and stores any violations in the 'alerts' table.
    """
    conn = get_db_connection()
    if not conn:
        print("Could not connect to the database to run rules.")
        return

    alerts_generated = 0
    active_rules = get_active_rules()

    if not active_rules:
        print("No active rules to run.")
        return

    try:
        with conn.cursor() as cur:
            for rule_id, rule_name, description, target_field, operator, value in active_rules:
                # --- Security Check ---
                if target_field not in ALLOWED_TARGET_FIELDS or operator not in ALLOWED_OPERATORS:
                    print(f"Skipping rule '{rule_name}' due to invalid field or operator.")
                    continue

                # --- Dynamic Query Construction ---
                # This is safe because we've whitelisted the field and operator
                sql_query = f"SELECT id, timestamp, user_id, resource FROM logs WHERE {target_field} {operator} %s"
                
                # Find all logs that violate this rule
                cur.execute(sql_query, (value,))
                violating_logs = cur.fetchall()

                for log_id, ts, user_id, resource in violating_logs:
                    alert_ts = datetime.now()
                    # The description is now simpler. The full, user-friendly description
                    # will be constructed by get_alerts() by joining tables.
                    alert_description = f"User '{user_id}' triggered rule '{rule_name}'"

                    # Check if this specific alert (log_id + rule_id) already exists
                    cur.execute(
                        "SELECT id FROM alerts WHERE log_id = %s AND rule_id = %s",
                        (log_id, rule_id)
                    )
                    if cur.fetchone() is None:
                        # Insert a new alert if it doesn't exist
                        cur.execute(
                            """
                            INSERT INTO alerts (log_id, rule_id, timestamp, description)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (log_id, rule_id, alert_ts, alert_description)
                        )
                        alerts_generated += 1
            
            conn.commit()
        print(f"Rule engine finished. Generated {alerts_generated} new alerts based on {len(active_rules)} active rules.")
    except Exception as e:
        print(f"Error running dynamic rule engine: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()

def get_alerts():
    """
    Retrieves all alerts from the database, joining with logs and rules
    to get human-readable information.
    """
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor() as cur:
            # Join with the rules table to get the rule name
            cur.execute("""
                SELECT a.id, a.timestamp, r.name, a.description, l.user_id, l.action, l.resource
                FROM alerts a
                JOIN logs l ON a.log_id = l.id
                JOIN rules r ON a.rule_id = r.id
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
    print("Running dynamic compliance rule engine...")
    run_rules()
    
    print("\nFetching current alerts:")
    alerts = get_alerts()
    if alerts:
        for alert in alerts:
            # (alert_id, timestamp, rule_name, description, user_id, action, resource)
            print(f"Alert ID: {alert[0]}, Rule: '{alert[2]}', User: {alert[4]}, Action: {alert[5]}")
    else:
        print("No alerts found.")