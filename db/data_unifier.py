from .database import get_db_connection

def get_unified_alerts():
    """
    Fetches both rule-based alerts and ML-based anomalies from the database
    and unifies them into a single list, sorted by timestamp.

    Returns:
        list: A list of dictionaries, where each dictionary represents an alert.
    """
    unified_list = []
    conn = get_db_connection()
    if not conn:
        print("Could not connect to the database to unify data.")
        return unified_list

    try:
        with conn.cursor() as cur:
            # 1. Fetch Rule-Based Alerts
            cur.execute("""
                SELECT a.id, a.timestamp, r.name, a.description, 'Rule-Based' as type, 'Medium' as severity
                FROM alerts a
                JOIN rules r ON a.rule_id = r.id
            """)
            rule_alerts = cur.fetchall()
            for alert in rule_alerts:
                unified_list.append({
                    "id": f"rule-{alert[0]}",
                    "timestamp": alert[1],
                    "title": alert[2],
                    "description": alert[3],
                    "type": alert[4],
                    "severity": alert[5] # Placeholder severity
                })

            # 2. Fetch ML-Based Anomalies
            cur.execute("""
                SELECT a.id, a.timestamp, a.details, a.score, 'ML-Based' as type
                FROM anomalies a
            """)
            anomalies = cur.fetchall()
            for anomaly in anomalies:
                # Assign severity based on score
                score = anomaly[3]
                severity = "Low"
                if score < -0.1:
                    severity = "Medium"
                if score < -0.2:
                    severity = "High"

                unified_list.append({
                    "id": f"ml-{anomaly[0]}",
                    "timestamp": anomaly[1],
                    "title": "Unusual Activity Detected",
                    "description": anomaly[2],
                    "type": anomaly[4],
                    "severity": severity
                })

        # 3. Sort the combined list by timestamp, most recent first
        unified_list.sort(key=lambda x: x['timestamp'], reverse=True)

        return unified_list

    except Exception as e:
        print(f"Error unifying data sources: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_all_logs():
    """
    Fetches all logs from the database, ordered by most recent first.

    Returns:
        list: A list of tuples, where each tuple is a log record.
    """
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT status, timestamp, user_id, resource, action FROM logs ORDER BY timestamp DESC")
            return cur.fetchall()
    except Exception as e:
        print(f"Error fetching all logs: {e}")
        return []
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # For testing purposes
    print("Fetching and unifying all alerts and anomalies...")
    all_alerts = get_unified_alerts()
    if all_alerts:
        for item in all_alerts:
            print(f"[{item['timestamp']}] {item['severity']} - {item['type']}: {item['title']}")
    else:
        print("No unified data found.")

    print("\nFetching all logs...")
    all_logs = get_all_logs()
    if all_logs:
        for log in all_logs:
            print(log)
    else:
        print("No logs found.")