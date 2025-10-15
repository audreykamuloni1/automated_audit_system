import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_db_connection():
    
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error connecting to the database: {e}")
        return None

def setup_database():
    """Reads the schema.sql file and executes it to set up the DB tables."""
    conn = get_db_connection()
    if conn is None:
        return

    try:
        with conn.cursor() as cur:
            with open('db/schema.sql', 'r') as f:
                cur.execute(f.read())
            conn.commit()
        print("Database setup complete. Tables created successfully.")
    except Exception as e:
        print(f"Error setting up database: {e}")
    finally:
        if conn:
            conn.close()

def add_rule(name, description, target_field, operator, value, is_active):
    """Adds a new dynamic rule to the database."""
    conn = get_db_connection()
    if conn is None:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO rules (name, description, target_field, operator, value, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, description, target_field, operator, value, is_active))
            conn.commit()
        return True
    except Exception as e:
        print(f"Error adding rule: {e}")
        return False
    finally:
        if conn:
            conn.close()


def get_all_rules():
    """Returns all rules from the database."""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM rules")
            return cur.fetchall()
    except Exception as e:
        print(f"Error fetching rules: {e}")
        return []
    finally:
        conn.close()

def update_rule(rule_id, name, description, target_field, operator, value, is_active):
    """Updates an existing rule in the database."""
    conn = get_db_connection()
    if conn is None:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE rules
                SET name=%s, description=%s, target_field=%s, operator=%s, value=%s, is_active=%s
                WHERE id=%s
            """, (name, description, target_field, operator, value, is_active, rule_id))
            conn.commit()
        return True
    except Exception as e:
        print(f"Error updating rule: {e}")
        return False
    finally:
        conn.close()

def delete_rule(rule_id):
    """Deletes a rule from the database."""
    conn = get_db_connection()
    if conn is None:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM rules WHERE id=%s", (rule_id,))
            conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting rule: {e}")
        return False
    finally:
        conn.close()

def get_active_rules():
    """Returns all active rules from the database."""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM rules WHERE is_active=TRUE")
            return cur.fetchall()
    except Exception as e:
        print(f"Error fetching active rules: {e}")
        return []
    finally:
        conn.close()


if __name__ == '__main__':
    # This allows running the script directly to initialize the database
    print("Setting up the database...")
    setup_database()