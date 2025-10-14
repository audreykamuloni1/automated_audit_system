import csv
from db.database import get_db_connection

def ingest_logs(file_path='data/sample_logs.csv'):
    """Reads log data from a CSV file and inserts it into the database."""
    conn = get_db_connection()
    if not conn:
        print("Could not connect to the database for ingestion.")
        return

    inserted_rows = 0
    try:
        with conn.cursor() as cur:
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Basic data validation
                    if not all(k in row for k in ['timestamp', 'user_id', 'action', 'resource', 'status']):
                        print(f"Skipping malformed row: {row}")
                        continue

                    cur.execute(
                        """
                        INSERT INTO logs (timestamp, user_id, action, resource, status)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (row['timestamp'], row['user_id'], row['action'], row['resource'], row['status'])
                    )
                    inserted_rows += 1
            conn.commit()
        print(f"Successfully ingested {inserted_rows} log entries.")
    except Exception as e:
        print(f"Error ingesting logs: {e}")
        conn.rollback()  # Rollback changes on error
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # This allows running the script directly to ingest data
    print("Starting log ingestion...")
    ingest_logs()