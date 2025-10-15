
from datetime import datetime
import json
from db.database import get_db_connection, get_active_rules

ALLOWED_TARGET_FIELDS = {'user_id', 'action', 'resource', 'status'}
ALLOWED_OPERATORS = {'=', '!=', 'LIKE', 'IN', 'NOT LIKE'}

def build_condition_sql(condition):
    """
    Builds a SQL WHERE clause fragment for a single condition.

    Args:
        condition: Dict with target_field, operator, value

    Returns:
        Tuple of (sql_fragment, value_for_parameterization)
    """
    target_field = condition['target_field']
    operator = condition['operator']
    value = condition['value']

    # Validate field and operator
    if target_field not in ALLOWED_TARGET_FIELDS or operator not in ALLOWED_OPERATORS:
        return None, None

    if operator == '=':
        return f"{target_field} = %s", value
    elif operator == '!=':
        return f"{target_field} != %s", value
    elif operator == 'LIKE':
        return f"{target_field} LIKE %s", value
    elif operator == 'NOT LIKE':
        return f"{target_field} NOT LIKE %s", value
    elif operator == 'IN':
        # Assuming value is a comma-separated string
        vals = tuple(value.split(','))
        placeholders = ','.join(['%s'] * len(vals))
        return f"{target_field} IN ({placeholders})", vals

    return None, None

def run_rules():
    conn = get_db_connection()
    if not conn:
        print("Could not connect to the database to run rules.")
        return

    alerts_generated = 0
    active_rules = get_active_rules()
    if not active_rules:
        print("No active rules found.")
        return

    try:
        with conn.cursor() as cur:
            for rule in active_rules:
                rule_id = rule[0]
                rule_name = rule[1]
                description = rule[2]
                match_type = rule[3]
                conditions = json.loads(rule[4]) if isinstance(rule[4], str) else rule[4]

                if not conditions:
                    continue

                # Build the WHERE clause based on match_type
                where_clauses = []
                query_params = []

                for condition in conditions:
                    sql_fragment, param = build_condition_sql(condition)
                    if sql_fragment:
                        where_clauses.append(sql_fragment)
                        if isinstance(param, tuple):
                            query_params.extend(param)
                        else:
                            query_params.append(param)

                if not where_clauses:
                    continue

                # Combine conditions with AND or OR
                connector = ' AND ' if match_type == 'AND' else ' OR '
                where_clause = connector.join(where_clauses)

                # Build and execute the query
                query = f"""
                    SELECT id, timestamp, user_id, action, resource, status 
                    FROM logs 
                    WHERE {where_clause}
                """

                cur.execute(query, tuple(query_params))
                matching_logs = cur.fetchall()

                # Create alerts for matching logs
                for log in matching_logs:
                    log_id = log[0]
                    alert_ts = datetime.now()
                    alert_description = (
                        f"User '{log[2]}' triggered rule '{rule_name}'"
                    )

                    # Check if alert already exists
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
                            (log_id, rule_id, alert_ts, alert_description)
                        )
                        alerts_generated += 1

            conn.commit()
        print(f"Rule engine finished. Generated {alerts_generated} new alerts based on {len(active_rules)} active rules.")
    except Exception as e:
        print(f"Error running rule engine: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()

def get_alerts():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT a.id, a.timestamp, r.name, a.description, l.user_id, l.action, l.resource, l.status
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
        conn.close()

if __name__ == '__main__':
    run_rules()
    alerts = get_alerts()
    for alert in alerts:
        print(alert)

